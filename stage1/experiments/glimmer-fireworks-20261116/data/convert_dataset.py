#!/usr/bin/env python3
"""Verify the frozen source and export its lossless chat view. No API calls."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[2] / 'datasets' / 'sft-600-v1'
EXPECTED_MANIFEST = '932e287304906a7e8dbf1f293011d0592a2a847e9450837081e0324f31024df3'
EXPECTED_SFT = '844223c79402af7d93937c9485f182d7c5381434b4e2234381a989663466424e'
EXPECTED_REVIEW = '07a4aced136602c4c88555e93bff7a9194ba9e2bb94bea4e46059efa17e6ca81'
TRAIN_ON_WHAT = 'last_assistant_message'

def require(ok, message):
    if not ok:
        raise ValueError(message)

def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()

def sha_file(path):
    return sha_bytes(path.read_bytes())

def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')

def jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]

def verify_source(source=SOURCE):
    require(sha_file(source / 'manifest.json') == EXPECTED_MANIFEST, 'Unexpected source manifest')
    checksum, filename = (source / 'manifest.sha256').read_text().strip().split()
    require((checksum, filename) == (EXPECTED_MANIFEST, 'manifest.json'), 'Source manifest.sha256 mismatch')
    manifest = json.loads((source / 'manifest.json').read_text())
    require(manifest['artifacts']['sft.jsonl'] == EXPECTED_SFT, 'Unexpected SFT pin')
    require(manifest['artifacts']['review.jsonl'] == EXPECTED_REVIEW, 'Unexpected review pin')
    checked = {}
    for name, expected in manifest['artifacts'].items():
        require(Path(name).name == name, 'Source artifact escapes dataset directory')
        actual = sha_file(source / name)
        require(actual == expected, f'Source artifact hash mismatch: {name}')
        checked[name] = actual
    return manifest, checked

def convert_row(row):
    require(set(row) == {'prompt', 'completion'}, 'Unexpected row schema')
    prompt, completion = row['prompt'], row['completion']
    require(isinstance(prompt, list) and len(prompt) >= 2, 'Missing prompt')
    require(isinstance(completion, list) and len(completion) == 1, 'Must have one final completion')
    messages = prompt + completion
    for message in messages:
        require(set(message) == {'role', 'content'}, 'Unexpected message fields')
        require(message['role'] in {'system', 'user', 'assistant'}, 'Unsupported message role')
        require(isinstance(message['content'], str) and message['content'], 'Empty/nontext message')
    require(prompt[0]['role'] == 'system', 'Missing system prompt')
    require(prompt[-1]['role'] == 'user', 'Prompt must end at user turn')
    require(completion[0]['role'] == 'assistant', 'Completion must be assistant')
    require(all(m['role'] == ('user' if i % 2 else 'assistant')
                for i, m in enumerate(prompt[1:], 1)), 'Unexpected prompt role sequence')
    return {'messages': messages}

def validate_export(source=SOURCE, output=HERE):
    manifest, checked = verify_source(source)
    rows = jsonl(source / 'sft.jsonl')
    reviews = jsonl(source / 'review.jsonl')
    exported = jsonl(output / 'train.messages.jsonl')
    plans = jsonl(output / 'row_identity_and_mask_plan.jsonl')
    require(len(rows) == len(reviews) == len(exported) == len(plans) == manifest['count'] == 600,
            'Row count mismatch')
    ids = set()
    prior_assistant_turns = 0
    rows_with_history = 0
    annotated_flaw_rows = 0
    for index, (row, review, exported_row, plan) in enumerate(zip(rows, reviews, exported, plans), 1):
        require(exported_row == convert_row(row), f'Content identity failed on row {index}')
        require(review['id'] not in ids, 'Duplicate row id')
        ids.add(review['id'])
        messages = exported_row['messages']
        require(review['context_messages'] == row['prompt'][1:], f'Review prompt mismatch {index}')
        require(review['target_response'] == row['completion'][0]['content'], f'Review target mismatch {index}')
        historical = sum(m['role'] == 'assistant' for m in row['prompt'])
        prior_assistant_turns += historical
        rows_with_history += bool(historical)
        annotated_flaw_rows += bool(review.get('flawed_history_indices'))
        expected_mask = [0] * (len(messages) - 1) + [1]
        require(plan == {'source_line_1based': index, 'id': review['id'],
                         'source_row_canonical_sha256': sha_bytes(canonical(row)),
                         'messages_canonical_sha256': sha_bytes(canonical(messages)),
                         'prompt_message_count': len(row['prompt']),
                         'historical_assistant_turns': historical,
                         'message_loss_plan': expected_mask,
                         'final_assistant_index_0based': len(messages) - 1}, f'Invalid identity/mask plan {index}')
    return {'status': 'passed', 'row_count': len(rows), 'source_manifest_sha256': EXPECTED_MANIFEST,
            'source_artifact_hashes_verified': checked, 'originals_unchanged': True,
            'all_message_roles_and_contents_identical': True,
            'all_system_prompts_identical_to_source': True,
            'all_final_completions_identical_to_source': True,
            'all_history_messages_preserved': True, 'rows_with_history': rows_with_history,
            'historical_assistant_turns_context_only_planned': prior_assistant_turns,
            'rows_with_annotated_history_flaws': annotated_flaw_rows,
            'message_loss_plan_verified': True,
            'train_on_what_required': TRAIN_ON_WHAT,
            'token_mask_validation_performed_by_this_check': False,
            'token_verification_note': 'This check verifies content and message plans only. token_mask_validation.json separately records actual model token-mask proof.'}

def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def export(source=SOURCE, output=HERE):
    verify_source(source)
    rows, reviews = jsonl(source / 'sft.jsonl'), jsonl(source / 'review.jsonl')
    require(len(rows) == len(reviews) == 600, 'Source count mismatch')
    converted = [convert_row(row) for row in rows]
    plans = []
    for index, (row, review, target) in enumerate(zip(rows, reviews, converted), 1):
        messages = target['messages']
        plans.append({'source_line_1based': index, 'id': review['id'],
                      'source_row_canonical_sha256': sha_bytes(canonical(row)),
                      'messages_canonical_sha256': sha_bytes(canonical(messages)),
                      'prompt_message_count': len(row['prompt']),
                      'historical_assistant_turns': sum(m['role'] == 'assistant' for m in row['prompt']),
                      'message_loss_plan': [0] * (len(messages) - 1) + [1],
                      'final_assistant_index_0based': len(messages) - 1})
    for name, records in [('train.messages.jsonl', converted), ('row_identity_and_mask_plan.jsonl', plans)]:
        (output / name).write_bytes(b''.join(canonical(record) + b'\n' for record in records))
    validation = validate_export(source, output)
    write_json(output / 'validation.json', validation)
    return validation

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    result = validate_export() if args.verify_only else export()
    print(json.dumps({k: v for k, v in result.items() if k != 'source_artifact_hashes_verified'}, indent=2))

if __name__ == '__main__':
    main()
