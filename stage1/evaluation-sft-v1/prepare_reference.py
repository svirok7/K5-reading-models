"""Freeze Qwen development records without opening the writable Reading Lab API.

Stdlib only. Never reads benchmark files, loads a model, or calls an evaluator.
Existing output directories are deliberately refused.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3

FROZEN_MANIFEST_SHA256 = '9215dc370204863e1ff58383d6e6083e709a883af54e74f80f9d7a54c82b89b6'

def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def prepare(database, out):
    if out.exists():
        raise ValueError('Reference directory already exists; never replace a frozen reference.')
    # URI mode=ro fails if missing and cannot create/modify the source database.
    with sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True) as connection:
        connection.execute('PRAGMA query_only=ON')
        connection.execute('BEGIN')
        selected = []
        for record_id, body in connection.execute('SELECT id, body FROM records ORDER BY id'):
            row = json.loads(body)
            model = row.get('response', {}).get('model', {})
            if model.get('backend') == 'qwen' and model.get('adapter') is None:
                if row['id'] != record_id:
                    raise ValueError('Database record ID mismatch.')
                selected.append((row, body))
    if not selected:
        raise ValueError('No saved Qwen baseline records found.')
    groups, inputs = {}, []
    out.mkdir(parents=True)
    with (out / 'baseline-records.jsonl').open('x') as records, (out / 'source-bodies.jsonl').open('x') as bodies:
        for row, body in selected:
            records.write(canonical(row) + '\n')
            bodies.write(canonical({'id': row['id'], 'body': body}) + '\n')
            model = row['response']['model']
            identity = {'model': model, 'condition': row['condition'],
                        'prompt_hash': digest(row['prompt']), 'rubric_hash': row['rubric_hash'],
                        'rubric_version': row['rubric_version'],
                        'archived': bool(row.get('archived_at'))}
            if digest(row['rubric']) != row['rubric_hash']:
                raise ValueError('Saved rubric integrity check failed.')
            group_id = digest(identity)
            marker = 'READING PROFILE — version '
            profile = row['rubric'].partition(marker)
            group = groups.setdefault(group_id, {'group_id': group_id, 'identity': identity,
                'prompt': row['prompt'], 'rubric': row['rubric'],
                'reader_profile': marker + profile[2] if profile[1] else None,
                'record_ids': [], 'saved_effective_decisions': {}, 'saved_evaluated': 0})
            group['record_ids'].append(row['id'])
            decision = (row.get('manual') or {}).get('decision') or (row.get('evaluation') or {}).get('verdict') or 'pending'
            group['saved_effective_decisions'][decision] = group['saved_effective_decisions'].get(decision, 0) + 1
            group['saved_evaluated'] += bool(row.get('evaluation'))
            if 'enable_thinking=False' in model.get('template', '') and not row.get('archived_at'):
                current = model['template'] == 'qwen-chat-v3; enable_thinking=False'
                inputs.append({'case_id': row['id'], 'saved_group_id': group_id,
                    'condition': row['condition'], 'prompt': row['prompt'], 'messages': row['messages'],
                    'history_kind': 'single_turn' if len(row['messages']) == 1 else 'fixed_context',
                    'saved_baseline_comparability': 'current_template_recorded' if current else 'legacy_template_unreconstructed',
                    'prompt_hash': digest(row['prompt']), 'rubric_hash': row['rubric_hash']})
    write_json(out / 'groups.json', list(groups.values()))
    with (out / 'development-inputs.jsonl').open('x') as handle:
        for case in inputs:
            handle.write(canonical(case) + '\n')
    manifest = {'schema_version': 1, 'source': str(database.resolve()),
        'source_access': 'SQLite URI mode=ro; query_only; one read transaction',
        'scope': 'Saved Qwen base-model casual development conversations only; no benchmark files read',
        'records': len(selected), 'configuration_groups': len(groups), 'development_inputs': len(inputs),
        'record_body_sha256': {r['id']: hashlib.sha256(b.encode()).hexdigest() for r, b in selected},
        'files': {p.name: file_hash(p) for p in sorted(out.iterdir())},
        'limitations': ['Saved RNG seeds and package versions are absent.',
            'Tokenizer and rendered input token hashes are absent from old records.',
            'Revision and inference precision are known only when explicitly recorded per group.',
            'Legacy qwen-chat-v1 is not assumed equivalent to the current v3 implementation.',
            'Thinking-enabled v2 records are retained for provenance and excluded from replay inputs.',
            'Histories contain saved base answers; replay measures a final turn under fixed context.',
            'These are selected casual development examples, not independent held-out evidence.']}
    write_json(out / 'manifest.json', manifest)
    # Hash verification plus refusal to overwrite is the immutable-reference contract.
    for path in out.iterdir():
        path.chmod(0o444)
    print(json.dumps({'reference_manifest': str(out / 'manifest.json'),
        'manifest_sha256': file_hash(out / 'manifest.json'), **{k: manifest[k] for k in
        ('records', 'configuration_groups', 'development_inputs')}}, indent=2))


def verify(reference, expected_manifest_sha256=None):
    if expected_manifest_sha256 and file_hash(reference / 'manifest.json') != expected_manifest_sha256:
        raise ValueError('Frozen reference manifest changed.')
    manifest = json.loads((reference / 'manifest.json').read_text())
    for name, expected in manifest['files'].items():
        if Path(name).name != name or file_hash(reference / name) != expected:
            raise ValueError('Frozen reference integrity failure: ' + name)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, default=Path(__file__).resolve().parents[1] / 'runs/conversation-results.sqlite3')
    parser.add_argument('--out', type=Path, default=Path(__file__).resolve().parent / 'baseline-reference')
    parser.add_argument('--verify', type=Path)
    args = parser.parse_args()
    if args.verify:
        manifest = verify(args.verify, FROZEN_MANIFEST_SHA256)
        print(json.dumps({'verified': True, 'records': manifest['records'], 'files': len(manifest['files'])}))
    else:
        prepare(args.database, args.out)
