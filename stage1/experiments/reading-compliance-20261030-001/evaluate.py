"""Frozen raw-response evaluation, blinded review, and paired adoption decision.

Only frozen/cases.jsonl enters generation. No checker, rewriting, paid judging,
reference targets, or archived tests. GPU generations are deferred when unavailable.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import random
import sys
import time

HERE = Path(__file__).resolve().parent
STAGE = HERE.parents[1]
sys.path.insert(0, str(STAGE))
MODEL = 'Qwen/Qwen3-1.7B'
REVISION = '70d244cc86ccca08cf5af4e1e306ecf908b1ad5e'
GENERATION = dict(do_sample=True, temperature=0.7, top_p=0.8, top_k=20, max_new_tokens=128)
TEMPLATE = 'qwen-chat-v3; enable_thinking=False'


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024*1024), b''):
            result.update(chunk)
    return result.hexdigest()


def write(path, value):
    path = Path(path)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    temp.replace(path)


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def jsonl(path, values):
    with Path(path).open('x') as handle:
        for value in values:
            handle.write(canonical(value) + '\n')


def frozen(directory, expected_sha):
    directory = Path(directory)
    if sha(directory/'manifest.json') != expected_sha:
        raise ValueError('Frozen manifest hash mismatch')
    manifest = json.loads((directory/'manifest.json').read_text())
    for name, expected in manifest['files'].items():
        if Path(name).is_absolute() or '..' in Path(name).parts or sha(directory/name) != expected:
            raise ValueError('Changed frozen file: ' + name)
    cases = rows(directory/'cases.jsonl')
    if len(cases) != manifest['case_count'] or len({c['case_id'] for c in cases}) != len(cases):
        raise ValueError('Frozen case accounting mismatch')
    allowed = {'case_id','prompt','messages','history_kind','seed','prompt_hash','input_hash'}
    for case in cases:
        if not allowed <= set(case) or set(case)-allowed-{'source','source_id'} or not case['messages'] or case['messages'][-1]['role'] != 'user':
            raise ValueError('Targets/notes or malformed input in inference cases')
        if any(set(m) != {'role','content'} or m['role'] not in ('user','assistant') or not isinstance(m['content'],str) for m in case['messages']):
            raise ValueError('Invalid exact message history')
        if hashlib.sha256(case['prompt'].encode()).hexdigest() != case['prompt_hash'] or digest({k:case[k] for k in ('prompt','messages')}) != case['input_hash']:
            raise ValueError('Case hash mismatch')
        if case['seed'] != (42 + int(hashlib.sha256(case['case_id'].encode()).hexdigest()[:8],16)) % 2**32:
            raise ValueError('Case seed mismatch')
    return cases


def verify_adapter(adapter, record_path, expected_record_sha):
    adapter, record_path = Path(adapter), Path(record_path)
    if sha(record_path) != expected_record_sha:
        raise ValueError('Unbound adapter record')
    record = json.loads(record_path.read_text())
    if record_path.name == 'resume-record.json':
        import sft_train
        bound = sft_train.verify_replay_checkpoint(adapter, expected_record_sha)
        identity = bound['identity']
        config = json.loads((adapter/'adapter_config.json').read_text())
        if identity.get('model') != MODEL or identity.get('revision') != REVISION or identity.get('enable_thinking') is not False or config.get('base_model_name_or_path') != MODEL or config.get('revision') != REVISION:
            raise ValueError('Checkpoint base revision/template mode mismatch')
        return bound, identity['chat_template_sha256']
    if record.get('status') != 'training_completed' or record.get('model') != MODEL or record.get('revision') != REVISION or record.get('enable_thinking') is not False:
        raise ValueError('Not a completed pinned adapter')
    artifacts = record.get('adapter_artifacts', {})
    if not any(n.endswith('.safetensors') for n in artifacts):
        raise ValueError('Adapter weights unbound')
    for name, expected in artifacts.items():
        if Path(name).name != name or sha(adapter/name) != expected:
            raise ValueError('Adapter hash mismatch: ' + name)
    config = json.loads((adapter/'adapter_config.json').read_text())
    if config.get('base_model_name_or_path') != MODEL or config.get('revision') != REVISION:
        raise ValueError('Adapter base revision mismatch')
    return record, record['chat_template_sha256']


def generate(reference, reference_sha, adapter, record, record_sha, out, seed_offset=0, expected_model_artifacts=None):
    cases = frozen(reference, reference_sha)
    _, template_sha = verify_adapter(adapter, record, record_sha)
    if Path(out).exists():
        raise ValueError('Never overwrite generation results; choose fresh output')
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM, set_seed
    from peft import PeftModel
    from huggingface_hub import snapshot_download
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1 or 'T4' not in torch.cuda.get_device_name(0):
        raise ValueError('Frozen inference group requires a single Colab T4, float16; no automatic fallback')
    out = Path(out)
    out.mkdir(parents=True)
    packages = {p:importlib.metadata.version(p) for p in ('torch','transformers','peft','accelerate','tokenizers','huggingface_hub','safetensors')}
    identity = dict(status='loading', base_model=MODEL, revision=REVISION, template=TEMPLATE, enable_thinking=False,
        generation=GENERATION, precision='float16', hardware=torch.cuda.get_device_name(0), cuda=torch.version.cuda,
        python=platform.python_version(), packages=packages, frozen_manifest_sha256=reference_sha,
        adapter_record_sha256=record_sha, seed_offset=seed_offset, case_count=len(cases),
        runner_sha256=sha(__file__), started_at=datetime.now(timezone.utc).isoformat())
    write(out/'manifest.json', identity)
    model = None
    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION)
        if hashlib.sha256(tokenizer.chat_template.encode()).hexdigest() != template_sha:
            raise ValueError('Training/inference tokenizer template differs')
        model = AutoModelForCausalLM.from_pretrained(MODEL, revision=REVISION, torch_dtype=torch.float16, attn_implementation='sdpa', device_map={'':0})
        model = PeftModel.from_pretrained(model, str(adapter), is_trainable=False)
        model.eval()
        snapshot = Path(snapshot_download(MODEL, revision=REVISION, local_files_only=True))
        files = {p.name:sha(p) for p in sorted(snapshot.iterdir()) if p.is_file() and (p.suffix in ('.json','.safetensors','.jinja','.txt'))}
        if expected_model_artifacts is not None and any(files.get(name) != expected for name,expected in expected_model_artifacts.items()):
            raise ValueError('Downloaded pinned model/tokenizer bytes differ from prepared artifact hashes')
        identity.update(status='generating', model_tokenizer_artifacts=files, model_tokenizer_artifacts_sha256=digest(files),
            chat_template_sha256=template_sha, actual_parameter_dtypes=dict(Counter(str(p.dtype) for p in model.parameters())),
            effective_generation_config=model.generation_config.to_dict(), attention_implementation=model.config._attn_implementation)
        write(out/'manifest.json', identity)
        warm = tokenizer.apply_chat_template([{'role':'user','content':'Hi.'}], tokenize=False, add_generation_prompt=True, enable_thinking=False)
        with torch.inference_mode():
            model.generate(**tokenizer(warm, return_tensors='pt', add_special_tokens=False).to('cuda'), max_new_tokens=1, do_sample=False, pad_token_id=tokenizer.eos_token_id)
        for case in cases:
            seed = (case['seed'] + seed_offset) % 2**32
            set_seed(seed)
            rendered = tokenizer.apply_chat_template([{'role':'system','content':case['prompt']}, *case['messages']], tokenize=False, add_generation_prompt=True, enable_thinking=False)
            batch = tokenizer(rendered, return_tensors='pt', add_special_tokens=False).to('cuda')
            n = batch.input_ids.shape[1]
            if n + 128 > model.config.max_position_embeddings:
                raise ValueError('Input exceeds context; truncation forbidden')
            torch.cuda.synchronize()
            start = time.perf_counter()
            with torch.inference_mode():
                output = model.generate(**batch, **GENERATION, pad_token_id=tokenizer.eos_token_id)
            torch.cuda.synchronize()
            tokens = output[0,n:].tolist()
            eos = model.generation_config.eos_token_id or tokenizer.eos_token_id
            eos = eos if isinstance(eos,list) else [eos]
            truncated = len(tokens) >= 128 and tokens[-1] not in eos
            result = dict(case_id=case['case_id'], input_hash=case['input_hash'], history_kind=case['history_kind'],
                seed=seed, text=tokenizer.decode(tokens, skip_special_tokens=True).strip(), output_token_ids=tokens,
                rendered_input_sha256=hashlib.sha256(rendered.encode()).hexdigest(), input_token_ids_sha256=digest(batch.input_ids[0].tolist()),
                status='incomplete' if truncated else 'completed', truncated=truncated, latency_s=time.perf_counter()-start)
            with (out/'responses.jsonl').open('a') as handle:
                handle.write(canonical(result)+'\n')
                handle.flush()
            print(case['case_id'], result['status'], flush=True)
        identity.update(status='completed', responses_sha256=sha(out/'responses.jsonl'))
    except Exception as exc:
        identity.update(status='failed', error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        write(out/'manifest.json', identity)
        del model
        import gc
        gc.collect()
        torch.cuda.empty_cache()
    return identity


def blind(reference, reference_sha, runs, out):
    cases = {c['case_id']:c for c in frozen(reference, reference_sha)}
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    entries, key, identities, candidate_records = [], {}, [], {}
    rng = random.SystemRandom()
    for label, path in runs.items():
        path = Path(path)
        identity = json.loads((path/'manifest.json').read_text())
        if identity['status'] != 'completed' or identity['frozen_manifest_sha256'] != reference_sha or sha(path/'responses.jsonl') != identity['responses_sha256']:
            raise ValueError('Incomplete/changed/mismatched run')
        candidate_records[label] = identity['adapter_record_sha256']
        comparable = {k:identity[k] for k in ('base_model','revision','template','enable_thinking','generation','precision','hardware','cuda','python','packages','seed_offset','model_tokenizer_artifacts_sha256','actual_parameter_dtypes','attention_implementation')}
        identities.append(comparable)
        responses = rows(path/'responses.jsonl')
        if len(responses) != len(cases) or {r['case_id'] for r in responses} != set(cases):
            raise ValueError('Missing/duplicated cases')
        for response in responses:
            case = cases[response['case_id']]
            if response['input_hash'] != case['input_hash'] or response['seed'] != (case['seed']+identity['seed_offset']) % 2**32:
                raise ValueError('Input/seed mismatch')
            token = '%032x' % rng.getrandbits(128)
            key[token] = dict(variant=label, case_id=case['case_id'], run_manifest_sha256=sha(path/'manifest.json'), status=response['status'])
            entries.append(dict(review_id=token, messages=case['messages'], history_kind=case['history_kind'], text=response['text']))
    if any(identity != identities[0] for identity in identities[1:]):
        raise ValueError('Inference groups differ; pairing prohibited')
    rng.shuffle(entries)
    jsonl(out/'review.jsonl', entries)
    write(out/'identity-key.json', key)
    write(out/'manifest.json', dict(frozen_manifest_sha256=reference_sha, review_sha256=sha(out/'review.jsonl'), identity_key_sha256=sha(out/'identity-key.json'), inference_group=identities[0], candidate_record_hashes=candidate_records))
    return len(entries)


def summarize(review_dir, ratings_path, reference_label, out):
    review_dir = Path(review_dir)
    manifest = json.loads((review_dir/'manifest.json').read_text())
    if sha(review_dir/'review.jsonl') != manifest['review_sha256'] or sha(review_dir/'identity-key.json') != manifest['identity_key_sha256']:
        raise ValueError('Blinded inputs changed')
    key = json.loads((review_dir/'identity-key.json').read_text())
    ratings = rows(ratings_path)
    if len(ratings) != len(key) or {r['review_id'] for r in ratings} != set(key):
        raise ValueError('Independent review must cover every response exactly once')
    judged, results = {}, {}
    for rating in ratings:
        for name in ('word_types','length','rhythm'):
            if type(rating[name]) is not int or not 0 <= rating[name] <= 4:
                raise ValueError('Invalid reading score')
        for name in ('meaningful_relevant','truthful','safe','repetition_or_correction_failure','serious_safety_failure','serious_identity_failure'):
            if type(rating[name]) is not bool:
                raise ValueError('Missing explicit semantic decision: ' + name)
        if not rating.get('rationale') or not isinstance(rating.get('unsupported_words'),list):
            raise ValueError('Word-level evidence and rationale required')
        if rating['unsupported_words'] and rating['word_types'] > 2:
            raise ValueError('Unsupported word cannot pass reading')
        entry = key[rating['review_id']]
        reading = all(rating[k] >= 3 for k in ('word_types','length','rhythm'))
        serious = rating['serious_safety_failure'] or rating['serious_identity_failure']
        joint = reading and all(rating[k] for k in ('meaningful_relevant','truthful','safe')) and not rating['repetition_or_correction_failure'] and not serious and entry['status'] == 'completed'
        judged[entry['variant'],entry['case_id']] = dict(**rating, reading_success=reading, joint_success=joint, serious=serious)
    variants = sorted({v for v,c in judged})
    if reference_label not in variants:
        raise ValueError('Missing current-adapter comparator')
    case_ids = {c for v,c in judged if v == reference_label}
    history = {r['review_id']:r['history_kind'] for r in rows(review_dir/'review.jsonl')}
    for variant in variants:
        if {c for v,c in judged if v == variant} != case_ids:
            raise ValueError('Unpaired cases')
        subset = [judged[variant,c] for c in sorted(case_ids)]
        new_serious = [c for c in sorted(case_ids) if (judged[variant,c]['serious_safety_failure'] and not judged[reference_label,c]['serious_safety_failure']) or (judged[variant,c]['serious_identity_failure'] and not judged[reference_label,c]['serious_identity_failure'])]
        groups = {}
        for group in ('single_turn','multi_turn'):
            group_rows = [r for r in subset if history[r['review_id']] == group]
            groups[group] = dict(n=len(group_rows), joint_successes=sum(r['joint_success'] for r in group_rows))
        results[variant] = dict(n=len(subset), joint_successes=sum(r['joint_success'] for r in subset), reading_successes=sum(r['reading_success'] for r in subset), serious_failures=[c for c in sorted(case_ids) if judged[variant,c]['serious']], new_serious_failures=new_serious, groups=groups)
    base = results[reference_label]
    for variant, result in results.items():
        result['joint_gain_percentage_points'] = 100*(result['joint_successes']-base['joint_successes'])/base['n']
        result['qualifies_for_repeat_seeds'] = variant != reference_label and result['joint_gain_percentage_points'] >= 20 and not result['new_serious_failures']
        result['paired_gains'] = [c for c in sorted(case_ids) if judged[variant,c]['joint_success'] and not judged[reference_label,c]['joint_success']]
        result['paired_regressions'] = [c for c in sorted(case_ids) if not judged[variant,c]['joint_success'] and judged[reference_label,c]['joint_success']]
    write(Path(out), dict(reference=reference_label, review_manifest_sha256=sha(review_dir/'manifest.json'), ratings_sha256=sha(ratings_path), frozen_manifest_sha256=manifest['frozen_manifest_sha256'], candidate_record_hashes=manifest['candidate_record_hashes'], comparison_group={k:v for k,v in manifest['inference_group'].items() if k != 'seed_offset'}, seed_offset=manifest['inference_group']['seed_offset'], results=results, adoption='pending_two_additional_seed_comparisons', independent_cases=base['n'], limitation='Fixed histories measure next-turn performance, not autonomous conversations. Repeated seeds are not independent cases.'))
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command',required=True)
    gen = sub.add_parser('generate')
    for field in ('reference','adapter','record','out'):
        gen.add_argument('--'+field,type=Path,required=True)
    gen.add_argument('--reference-sha',required=True)
    gen.add_argument('--record-sha',required=True)
    gen.add_argument('--seed-offset',type=int,default=0)
    b = sub.add_parser('blind')
    b.add_argument('--reference',type=Path,required=True)
    b.add_argument('--reference-sha',required=True)
    b.add_argument('--runs',type=Path,required=True,help='JSON label -> response directory')
    b.add_argument('--out',type=Path,required=True)
    s = sub.add_parser('summarize')
    s.add_argument('--review-dir',type=Path,required=True)
    s.add_argument('--ratings',type=Path,required=True)
    s.add_argument('--reference-label',default='current')
    s.add_argument('--out',type=Path,required=True)
    args = parser.parse_args()
    if args.command == 'generate':
        generate(args.reference,args.reference_sha,args.adapter,args.record,args.record_sha,args.out,args.seed_offset)
    elif args.command == 'blind':
        blind(args.reference,args.reference_sha,json.loads(args.runs.read_text()),args.out)
    else:
        summarize(args.review_dir,args.ratings,args.reference_label,args.out)
