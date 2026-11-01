#!/usr/bin/env python3
"""Offline tokenizer/label feasibility audit. No model loading or training."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import statistics

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

ROOT = Path(__file__).resolve().parent.parent
REVISION = '70d244cc86ccca08cf5af4e1e306ecf908b1ad5e'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summary(values):
    values = sorted(values)
    return {'min': values[0], 'median': statistics.median(values),
            'p95': values[min(len(values)-1, int(len(values)*0.95))], 'max': values[-1],
            'sum': sum(values)}


def verify_manifest(dataset):
    manifest_path = dataset / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    artifacts = manifest.get('artifacts')
    if not isinstance(artifacts, dict) or not {'sft.jsonl', 'review.jsonl'} <= set(artifacts):
        raise ValueError('Manifest must pin sft.jsonl and review.jsonl artifact hashes')
    for name, expected in artifacts.items():
        if Path(name).name != name or name in ('', '.', '..'):
            raise ValueError('Manifest artifact paths must be direct dataset files')
        if sha(dataset / name) != expected:
            raise ValueError(f'Export bytes differ from manifest: {name}')
    return manifest, sha(manifest_path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--dataset', type=Path, default=ROOT / 'datasets/sft-300-v1',
                        help='Dataset directory with exact-hash manifest (default: sft-300-v1)')
    args = parser.parse_args()
    from transformers import AutoTokenizer
    import importlib.metadata

    dataset = args.dataset.resolve()
    manifest, manifest_sha = verify_manifest(dataset)
    actual = {name: sha(dataset / name) for name in ('sft.jsonl', 'review.jsonl')}
    data = [json.loads(line) for line in (dataset / 'sft.jsonl').read_text().splitlines()]
    review = [json.loads(line) for line in (dataset / 'review.jsonl').read_text().splitlines()]
    assert len(data) == len(review) == 300
    assert manifest.get('count') == 300, 'Manifest count must be exactly 300'
    snapshot = Path.home() / '.cache/huggingface/hub/models--Qwen--Qwen3-1.7B/snapshots' / REVISION
    tokenizer = AutoTokenizer.from_pretrained(str(snapshot), local_files_only=True)
    config = json.loads((snapshot / 'config.json').read_text())
    lengths, prompts, completions, raw_target_lengths = [], [], [], []
    errors = []
    historical_assistant_turns = 0
    max_row = None
    for row, metadata in zip(data, review):
        ident = metadata['id']
        assert set(row) == {'prompt', 'completion'}
        assert len(row['completion']) == 1 and row['completion'][0]['role'] == 'assistant'
        target = row['completion'][0]['content']
        assert target == metadata['target_response']
        historical_assistant_turns += sum(m['role'] == 'assistant' for m in row['prompt'])
        prefix = tokenizer.apply_chat_template(row['prompt'], tokenize=False,
                                              add_generation_prompt=True, enable_thinking=False)
        full = tokenizer.apply_chat_template(row['prompt'] + row['completion'], tokenize=False,
                                            add_generation_prompt=False, enable_thinking=False)
        prefix_ids = tokenizer(prefix, add_special_tokens=False)['input_ids']
        full_ids = tokenizer(full, add_special_tokens=False)['input_ids']
        if not full.startswith(prefix) or full_ids[:len(prefix_ids)] != prefix_ids:
            errors.append({'id': ident, 'error': 'Prompt prefix/token boundary differs'})
            continue
        suffix = full_ids[len(prefix_ids):]
        decoded_suffix = tokenizer.decode(suffix, skip_special_tokens=False)
        if decoded_suffix != target + '<|im_end|>\n':
            errors.append({'id': ident, 'error': 'Unexpected completion serialization'})
        # Feasibility labels only: an eventual trainer/collator must reproduce this.
        labels = [-100] * len(prefix_ids) + suffix
        assert len(labels) == len(full_ids)
        assert all(x == -100 for x in labels[:len(prefix_ids)])
        assert labels[len(prefix_ids):] == full_ids[len(prefix_ids):]
        assert tokenizer.eos_token_id in suffix and suffix
        # Right-padding demonstration: mask pads explicitly; never infer via EOS equality.
        pad_count = 7
        padded_ids = full_ids + [tokenizer.pad_token_id] * pad_count
        padded_labels = labels + [-100] * pad_count
        attention = [1] * len(full_ids) + [0] * pad_count
        assert len(padded_ids) == len(padded_labels) == len(attention)
        assert all(x == -100 for x in padded_labels[-pad_count:])
        lengths.append(len(full_ids))
        prompts.append(len(prefix_ids))
        completions.append(len(suffix))
        raw_target_lengths.append(len(tokenizer(target, add_special_tokens=False)['input_ids']))
        if max_row is None or len(full_ids) > max_row['tokens']:
            max_row = {'id': ident, 'tokens': len(full_ids)}
    report = {
        'scope': 'Offline tokenization and manual label construction feasibility; no trainer/collator/model/gradient step verified',
        'dataset': str(dataset), 'row_count': len(data), 'dataset_sha256': actual,
        'manifest_sha256': manifest_sha, 'all_declared_artifacts_verified': True,
        'tokenizer_model': 'Qwen/Qwen3-1.7B', 'cached_revision': REVISION,
        'tokenizer_file_sha256': {n: sha(snapshot / n) for n in ('tokenizer.json', 'tokenizer_config.json', 'config.json')},
        'transformers_version': importlib.metadata.version('transformers'),
        'tokenizer_class': tokenizer.__class__.__name__,
        'model_config_max_position_embeddings': config.get('max_position_embeddings'),
        'tokenizer_model_max_length': tokenizer.model_max_length,
        'eos_token_id': tokenizer.eos_token_id, 'pad_token_id': tokenizer.pad_token_id,
        'native_template_supports_generation_mask': '{% generation' in tokenizer.chat_template,
        'historical_assistant_turns': historical_assistant_turns,
        'full_sequence_tokens': summary(lengths), 'prompt_tokens': summary(prompts),
        'supervised_suffix_tokens_including_termination': summary(completions),
        'raw_target_tokens': summary(raw_target_lengths), 'longest_row': max_row,
        'rows_exceeding_sequence_limit': {str(limit): sum(n > limit for n in lengths) for limit in (1024, 2048, 2560, 3072, 4096)},
        'prefix_boundary_errors': errors, 'feasibility_passed': not errors and len(lengths) == 300,
        'actual_training_collator_verified': False, 'model_loaded': False, 'training_executed': False,
        'held_out_opened': False,
    }
    # Reject a concurrent edit instead of reporting measurements against stale hashes.
    _, final_manifest_sha = verify_manifest(dataset)
    assert final_manifest_sha == manifest_sha, 'Manifest changed during preflight'
    assert actual == {name: sha(dataset / name) for name in actual}, 'Dataset changed during preflight'
    rendered = json.dumps(report, indent=2) + '\n'
    if args.out:
        args.out.write_text(rendered)
    print(rendered)
    return 0 if report['feasibility_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
