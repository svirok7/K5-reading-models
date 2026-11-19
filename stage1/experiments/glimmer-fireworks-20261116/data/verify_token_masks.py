#!/usr/bin/env python3
"""Local renderer gate: no Fireworks client, credentials, inference, or training."""
from __future__ import annotations
import argparse
import importlib.metadata
import json
import math
from datetime import date
import subprocess
import sys
from pathlib import Path
import convert_dataset as c

COOKBOOK_REVISION = '74e103ab4249d508912ccf264793e655980eead0'
TOKENIZER_MODEL = 'meta-models/Muse-Glimmer-30B'
TOKENIZER_REVISION = 'a4e59da52a7bc87ae7251dd5545c0dd437c44b68'


def flatten(model_input):
    tokens = []
    for chunk in model_input.chunks:
        c.require(hasattr(chunk, 'tokens'), 'Unexpected nontext chunk')
        tokens.extend(int(t) for t in chunk.tokens)
    return tokens


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cookbook', type=Path, default=c.HERE.parent / 'training/vendor/cookbook')
    parser.add_argument('--tokenizer', default=str(c.HERE / 'tokenizer'), help='Pinned HF identity or local snapshot directory')
    parser.add_argument('--max-seq-len', type=int, default=4096)
    parser.add_argument('--local-files-only', action='store_true')
    args = parser.parse_args()
    revision = subprocess.check_output(['git', '-C', str(args.cookbook), 'rev-parse', 'HEAD'], text=True).strip()
    c.require(revision == COOKBOOK_REVISION, 'Unreviewed cookbook revision')
    c.validate_export()
    sys.path.insert(0, str(args.cookbook.resolve()))
    from training.renderer.muse_glimmer import MuseGlimmerRenderer, _EOT
    from training.utils.supervised import render_messages_to_datums, populate_render_worker_state, parse_train_on_what
    from training.utils.tokenizers import load_tokenizer
    snapshot = Path(args.tokenizer)
    c.require(snapshot.is_dir(), 'Use the downloaded pinned local tokenizer snapshot')
    snapshot_manifest = json.loads((snapshot / 'snapshot_manifest.json').read_text())
    c.require(snapshot_manifest['revision'] == TOKENIZER_REVISION, 'Wrong tokenizer snapshot revision')
    c.require(snapshot_manifest['repository'] == TOKENIZER_MODEL, 'Wrong tokenizer repository')
    for name, digest in snapshot_manifest['artifacts'].items():
        c.require(Path(name).name == name and c.sha_file(snapshot / name) == digest, f'Tokenizer integrity failed: {name}')
    tokenizer = load_tokenizer(args.tokenizer, TOKENIZER_REVISION, False,
                               local_files_only=args.local_files_only)
    state = {}
    # Match sft_loop._init_render_worker including processor loading, even for text.
    populate_render_worker_state(state, tokenizer_model=args.tokenizer,
                                  tokenizer_revision=TOKENIZER_REVISION,
                                  tokenizer_trust_remote_code=False,
                                  renderer_name='muse_glimmer', renderer_name_is_resolved=True,
                                  max_seq_len=args.max_seq_len,
                                  thinking_trace_history_mode='',
                                  base_model='accounts/fireworks/models/muse-glimmer-30b',
                                  train_on_what=parse_train_on_what(c.TRAIN_ON_WHAT))
    tokenizer, renderer = state['tokenizer'], state['renderer']
    rows = c.jsonl(c.HERE / 'train.messages.jsonl')
    plans = c.jsonl(c.HERE / 'row_identity_and_mask_plan.jsonl')
    proofs = []
    for index, (row, plan) in enumerate(zip(rows, plans), 1):
        messages = row['messages']
        # Use the same dispatcher and mean reduction as sft_loop._render_one_worker.
        examples = render_messages_to_datums(messages, renderer=renderer,
                                             train_on_what=c.TRAIN_ON_WHAT, reduction='mean')
        c.require(len(examples) == 1, f'Row {index} was split or dropped')
        example = examples[0]
        tokens = [int(t) for t in example.token_ids]
        weights = [float(w) for w in example.token_weights]
        context = flatten(renderer.build_generation_prompt(messages[:-1]))
        boundary = len(context)
        c.require(2 <= len(tokens) <= args.max_seq_len, f'Row {index} exceeds context budget; do not truncate/drop')
        template_tokens = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=False)
        if hasattr(template_tokens, 'input_ids'):
            template_tokens = template_tokens.input_ids
        c.require(tokens == list(template_tokens), f'Row {index} differs from pinned HF chat template')
        c.require(tokens[:boundary] == context, f'Row {index} prompt prefix differs')
        c.require(len(weights) == len(tokens), f'Row {index} unaligned token mask')
        c.require(all(w == 0 for w in weights[:boundary]), f'Row {index} leaks context loss')
        c.require(all(math.isfinite(w) and w > 0 for w in weights[boundary:]), f'Row {index} misses final output loss')
        expected_text = ' to=user<|message|>' + messages[-1]['content'] + _EOT
        c.require(tokens[boundary:] == list(tokenizer.encode(expected_text, add_special_tokens=False)),
                  f'Row {index} supervises something other than final assistant output')
        c.require(tokenizer.decode(tokens[boundary:], skip_special_tokens=False) == expected_text,
                  f'Row {index} tokenized target does not round-trip exactly')
        targets = [int(t) for t in example.datum.loss_fn_inputs['target_tokens'].data]
        training_weights = [float(w) for w in example.datum.loss_fn_inputs['weights'].data]
        c.require(targets == tokens[1:], f'Row {index} next-token targets misaligned')
        c.require(training_weights == weights[1:], f'Row {index} next-token weights misaligned')
        c.require(flatten(example.datum.model_input) == tokens[:-1], f'Row {index} model inputs misaligned')
        proofs.append({'source_line_1based': index, 'id': plan['id'], 'token_count': len(tokens),
                       'context_token_count': boundary, 'supervised_token_count': len(tokens) - boundary,
                       'context_loss_positions': 0, 'datums': 1,
                       'full_token_ids_sha256': c.sha_bytes(c.canonical(tokens)),
                       'training_weights_sha256': c.sha_bytes(c.canonical(training_weights)),
                       'target_text_sha256': c.sha_bytes(expected_text.encode('utf-8'))})
    c.require(len(proofs) == 600, 'Not all 600 rows checked')
    proof_file = c.HERE / 'token_mask_proofs.jsonl'
    proof_file.write_bytes(b''.join(c.canonical(r) + b'\n' for r in proofs))
    report = {'status': 'passed', 'row_count': 600, 'dataset_sha256': c.sha_file(c.HERE / 'train.messages.jsonl'),
              'source_manifest_sha256': c.EXPECTED_MANIFEST, 'cookbook_revision': revision,
              'tokenizer_model': TOKENIZER_MODEL, 'tokenizer_revision': TOKENIZER_REVISION,
              'tokenizer_snapshot_manifest_sha256': c.sha_file(snapshot / 'snapshot_manifest.json'),
              'tokenizer_files_sha256': snapshot_manifest['artifacts'],
              'tokenizer_trust_remote_code': False, 'renderer': 'muse_glimmer', 'train_on_what': c.TRAIN_ON_WHAT,
              'reduction': 'mean', 'rendered_current_date': date.today().isoformat(), 'max_seq_len': args.max_seq_len,
              'all_rows_match_pinned_hf_chat_template': True,
              'production_render_worker_initialization_verified': True,
              'context_loss_positions': 0, 'dropped_rows': 0, 'truncated_rows': 0, 'split_rows': 0,
              'min_sequence_tokens': min(r['token_count'] for r in proofs),
              'max_sequence_tokens': max(r['token_count'] for r in proofs),
              'total_sequence_tokens': sum(r['token_count'] for r in proofs),
              'total_supervised_tokens': sum(r['supervised_token_count'] for r in proofs),
              'proofs_sha256': c.sha_file(proof_file),
              'native_assistant_output_includes': ' to=user<|message|> + exact completion content + <|eot|>',
              'packages': {name: importlib.metadata.version(name) for name in
                           ('fireworks-ai', 'torch', 'transformers', 'huggingface-hub', 'numpy', 'pillow')}}
    c.write_json(c.HERE / 'token_mask_validation.json', report)
    print(json.dumps(report, indent=2))

if __name__ == '__main__': main()
