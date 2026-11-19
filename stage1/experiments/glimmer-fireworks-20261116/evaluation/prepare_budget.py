"""Offline exact44 Glimmer token accounting. Never loads keys or creates clients."""
import argparse
from datetime import datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
import sys
import ui_evaluation as ui

HERE = Path(__file__).resolve().parent
EXPERIMENT = HERE.parent
TOKENIZER_REVISION = 'a4e59da52a7bc87ae7251dd5545c0dd437c44b68'
SOURCE_MANIFEST = '5779ee65a6da973d56df6684a42ab39cb809200471e239b34b0d2d60647cb565'
SOURCE_PLAN = 'a27d06c0ae39821ced02e8d9552e89e71c033eb85b844876fccd7387bff710b1'
FINAL_PREFIX = ' to=user<|message|>'


def cost(tokens, rate):
    return Decimal(tokens) * Decimal(str(rate)) / Decimal(1_000_000)


def prepare(out):
    from training.renderer.muse_glimmer import MuseGlimmerRenderer
    from training.utils.tokenizers import load_tokenizer
    source = HERE/'existing-ui-baseline'
    source_rows = {r['id']:r for r in ui.load_export(source,SOURCE_MANIFEST)}
    plan_path = HERE/'existing-qwen600-fireworks-offline-plan.jsonl'
    if ui.sha(plan_path) != SOURCE_PLAN:
        raise ValueError('Changed existing44 source plan.')
    plan = ui.rows(plan_path)
    ui.validate_plan(plan)
    if len(plan) != 44:
        raise ValueError('Must use exactly the existing44 unique UI histories.')
    snapshot = EXPERIMENT/'data/tokenizer'
    snapshot_manifest = json.loads((snapshot/'snapshot_manifest.json').read_text())
    if snapshot_manifest['revision'] != TOKENIZER_REVISION:
        raise ValueError('Wrong tokenizer pin.')
    for name, expected in snapshot_manifest['artifacts'].items():
        if Path(name).name != name or ui.sha(snapshot/name) != expected:
            raise ValueError('Changed pinned tokenizer file.')
    tokenizer = load_tokenizer(str(snapshot), TOKENIZER_REVISION, False, local_files_only=True)
    renderer = MuseGlimmerRenderer(tokenizer)
    tokenized = []
    for item in plan:
        row = source_rows[item['source_ids'][0]]
        messages = [{'role':'system','content':row['prompt']},*row['messages']]
        prompt = renderer.build_generation_prompt(messages,prefill=FINAL_PREFIX)
        tokens = [int(t) for chunk in prompt.chunks for t in chunk.tokens]
        plain = renderer.build_generation_prompt(messages)
        plain_tokens = [int(t) for chunk in plain.chunks for t in chunk.tokens]
        if plain_tokens != list(tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False)):
            raise ValueError('Native renderer differs from the pinned chat template.')
        if tokens != plain_tokens + list(tokenizer.encode(FINAL_PREFIX, add_special_tokens=False)):
            raise ValueError('Unexpected native final-recipient prefill.')
        tokenized.append({'source_input_hash':item['source_input_hash'], 'source_ids':item['source_ids'],
                          'messages':row['messages'], 'prompt':row['prompt'], 'condition':row['condition'],
                          'rubric':row['rubric'], 'rubric_version':row['rubric_version'], 'rubric_hash':row['rubric_hash'],
                          'prompt_tokens':tokens, 'prompt_token_count':len(tokens),
                          'prompt_tokens_sha256':ui.digest(tokens)})
    total = sum(r['prompt_token_count'] for r in tokenized)
    # Existing Qwen UI cap, including ALL sampled protocol/reasoning/output tokens.
    per_request_cap = 128
    single_generation = cost(total,'1.96') + cost(44*per_request_cap,'4.88')
    # Input tokens are checked before each real judge call; this is a reserved
    # ceiling, not a claim that GPT tokenization matches Glimmer or characters.
    judge_input_cap = 15000
    judge_output_cap = 3000
    # Highest published short-context input/cache-write rate, no cache discount.
    single_judging = cost(44*judge_input_cap,'5.00') + cost(44*judge_output_cap,'10.00')
    options = {}
    for gen_arms,judge_arms in ((1,1),(2,1),(2,2)):
        amount = gen_arms*single_generation + judge_arms*single_judging
        options[f'{gen_arms}_generated_{judge_arms}_judged'] = {
            'sampling_requests':44*gen_arms,'judge_requests':44*judge_arms,
            'generation_usd_upper_bound':str(gen_arms*single_generation),
            'judge_usd_upper_bound':str(judge_arms*single_judging),
            'total_usd_upper_bound':str(amount),'strictly_below_5_usd':amount < Decimal('5')}
    out = Path(out);out.mkdir(parents=True,exist_ok=False)
    ui.jsonl(out/'tokenized-existing44.jsonl',tokenized)
    report = {'status':'offline_prepared_not_authorized_for_spend',
              'created_at':datetime.now(timezone.utc).isoformat(),
              'case_count':44,'source_export_manifest_sha256':SOURCE_MANIFEST,'source_plan_sha256':SOURCE_PLAN,
              'tokenized_inputs_sha256':ui.sha(out/'tokenized-existing44.jsonl'),
              'tokenizer_revision':TOKENIZER_REVISION,
              'tokenizer_snapshot_manifest_sha256':ui.sha(snapshot/'snapshot_manifest.json'),
              'prefill_tokens_per_arm':total,'min_prompt_tokens':min(r['prompt_token_count'] for r in tokenized),
              'max_prompt_tokens':max(r['prompt_token_count'] for r in tokenized),
              'sampling':{'max_tokens':per_request_cap,'num_samples':1,'temperature':0.7,'top_p':0.8,'top_k':20,'seed':42,
                          'native_final_recipient_prefill':FINAL_PREFIX,'stop':renderer.get_stop_sequences(),
                          'reasoning_strength_override':None,'retry_attempts':1,
                          'all_generated_tokens_including_reasoning_count_toward_cap':True},
              'judge':{'model':'gpt-6.1-sol','max_output_tokens':judge_output_cap,'reasoning_effort':'low',
                       'input_tokens_per_request_ceiling':judge_input_cap,'retry_attempts':1,
                       'actual_input_count_required_before_each_call':True,'rubric':'unchanged stage1/evaluator.py'},
              'rates_usd_per_million':{'glimmer_prefill':1.96,'glimmer_sample':4.88,
                                       'judge_input_or_cachewrite_reserve':5,'judge_output':10},
              'options':options,
              'price_sources':['https://fireworks.ai/pricing','https://docs.fireworks.ai/fine-tuning/training-api/serverless',
                               'https://developers.openai.com/api/docs/pricing'],
              'budget_caveat':'Judge input ceilings must be enforced with exact model input-token counts before calls; no unknown-token-count judge call is allowed. Failed submitted requests reserve their full bound; no retries. Prices exclude tax.'}
    ui.write(out/'budget.json',report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    print(json.dumps(prepare(parser.parse_args().out),indent=2))
