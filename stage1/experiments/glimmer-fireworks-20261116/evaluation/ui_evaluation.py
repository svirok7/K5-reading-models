"""Read-only UI record export and offline replay plans for the existing UI.

No new cases, benchmark, judge, generation defaults, or manual decisions are made.
This helper has no HTTP client or execution command; it never generates or judges.
"""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

HERE = Path(__file__).resolve().parent
STAGE = HERE.parents[2]
sys.path.insert(0, str(STAGE))
import engine
import records


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def write(path, value):
    with Path(path).open('x') as handle:
        handle.write(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def jsonl(path, values):
    with Path(path).open('x') as handle:
        for value in values:
            handle.write(canonical(value) + '\n')


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def read_active(db):
    """Never create/migrate/write the UI DB or load archived row contents."""
    db = Path(db).resolve()
    if not db.is_file():
        raise ValueError('UI database does not exist.')
    with sqlite3.connect(db.as_uri() + '?mode=ro', uri=True) as connection:
        connection.execute('PRAGMA query_only=ON')
        result = connection.execute("SELECT body FROM records WHERE json_extract(body, '$.archived_at') IS NULL ORDER BY rowid")
        return [json.loads(row[0]) for row in result]


def input_key(row):
    return digest({key: row[key] for key in ('prompt', 'rubric_hash', 'messages', 'condition')})


def summarize(items):
    """Use UI's existing effective-decision precedence and grouping unchanged."""
    items = [records.effective(copy.deepcopy(row)) for row in items]
    summary = records.summaries(items)
    inputs = {}
    for row in items:
        identity = {'model': row['response']['model'], 'condition': row['condition'],
                    'rubric_hash': row['rubric_hash'], 'prompt_hash': engine.digest(row['prompt'])}
        group = engine.digest(identity)
        inputs.setdefault(group, {}).setdefault(input_key(row), []).append(row['id'])
    overlaps = []
    groups = sorted(inputs)
    for i, left in enumerate(groups):
        for right in groups[i+1:]:
            shared = set(inputs[left]) & set(inputs[right])
            if shared:
                overlaps.append({'left_group': left, 'right_group': right,
                                 'exact_shared_inputs': len(shared),
                                 'unambiguous_one_record_each': sum(len(inputs[left][key]) == len(inputs[right][key]) == 1 for key in shared)})
    for group in summary:
        identity_hash = engine.digest(group['identity'])
        group['identity_hash'] = identity_hash
        group['unique_exact_inputs'] = len(inputs[identity_hash])
        group['repeated_input_records'] = group['responses'] - len(inputs[identity_hash])
    return {'record_count': len(items), 'groups': summary, 'exact_input_overlap': overlaps,
            'limitation': 'Standard UI reading-only decisions. Unpaired or repeated histories do not establish a controlled quality improvement.'}


def export(db, out, backend=None, adapter='any', condition=None, rubric_version=None, adapter_hash=None):
    selected = []
    for row in read_active(db):
        model = row['response']['model']
        if backend and model.get('backend') != backend:
            continue
        if adapter != 'any' and bool(model.get('adapter')) != (adapter == 'present'):
            continue
        if condition and row['condition'] != condition:
            continue
        if rubric_version and row['rubric_version'] != rubric_version:
            continue
        if adapter_hash and model.get('adapter_hash') != adapter_hash:
            continue
        selected.append(row)
    if not selected:
        raise ValueError('No active UI records match the selection.')
    if len({r['id'] for r in selected}) != len(selected):
        raise ValueError('Duplicate saved UI record IDs.')
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    jsonl(out/'records.jsonl', selected)
    write(out/'summary.json', summarize(selected))
    manifest = {'kind': 'existing-active-ui-record-export',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'source_database': str(Path(db).resolve()), 'source_read_only': True,
                'archived_rows_loaded': False, 'record_count': len(selected),
                'selection': dict(backend=backend, adapter=adapter, condition=condition,
                                  rubric_version=rubric_version, adapter_hash=adapter_hash),
                'files': {name: sha(out/name) for name in ('records.jsonl', 'summary.json')}}
    write(out/'manifest.json', manifest)
    return manifest


def load_export(directory, manifest_sha):
    directory = Path(directory)
    if sha(directory/'manifest.json') != manifest_sha:
        raise ValueError('Export manifest hash mismatch.')
    manifest = json.loads((directory/'manifest.json').read_text())
    if manifest['kind'] != 'existing-active-ui-record-export':
        raise ValueError('Not an existing UI export.')
    if set(manifest['files']) != {'records.jsonl', 'summary.json'}:
        raise ValueError('Invalid export file binding.')
    for name, expected in manifest['files'].items():
        if sha(directory/name) != expected:
            raise ValueError('Changed UI export file: ' + name)
    values = rows(directory/'records.jsonl')
    if len(values) != manifest['record_count'] or len({r['id'] for r in values}) != len(values):
        raise ValueError('Export record accounting mismatch.')
    if any(row.get('archived_at') for row in values):
        raise ValueError('Archived records are excluded from this workflow.')
    return values


def current_rubric():
    return (STAGE/'RUBRIC.md').read_text() + '\n\n' + engine.reader_profile()


def replay_plan(source, manifest_sha, target_model, out, record_ids=None):
    """Plan exact histories already saved by the UI; deduplicate repeated inputs."""
    values = load_export(source, manifest_sha)
    if record_ids:
        wanted = set(record_ids)
        values = [row for row in values if row['id'] in wanted]
        if {row['id'] for row in values} != wanted:
            raise ValueError('Selected record ID not in UI export.')
    registry = json.loads((STAGE/'models.json').read_text())
    if target_model not in registry:
        raise ValueError('Target must be an existing models.json UI key.')
    spec = registry[target_model]
    if spec.get('pending') and not spec.get('adapter'):
        raise ValueError('Target UI model is not available yet.')
    unique = {}
    for row in values:
        if row['prompt'] != engine.prompt_for(row['condition']):
            raise ValueError('Saved prompt differs from current UI; cannot replay exactly.')
        if row['rubric_hash'] != engine.digest(current_rubric()):
            raise ValueError('Saved rubric differs from current UI; select matching v1.5 records.')
        key = input_key(row)
        if key not in unique:
            unique[key] = {'source_ids': [], 'source_input_hash': key,
                           'source_export_manifest_sha256': manifest_sha,
                           'expected_prompt_hash': engine.digest(row['prompt']),
                           'expected_rubric_hash': row['rubric_hash'],
                           'execution_permitted': False, 'spend_limit_usd': 0,
                           'request': {'model': target_model, 'condition': row['condition'], 'messages': row['messages']}}
        unique[key]['source_ids'].append(row['id'])
    jsonl(out, list(unique.values()))
    return len(unique)


def validate_plan(plan):
    if not plan or len({row['source_input_hash'] for row in plan}) != len(plan):
        raise ValueError('Replay plan must contain unique existing inputs.')
    for item in plan:
        request = item['request']
        if set(request) != {'model', 'condition', 'messages'} or not item['source_ids']:
            raise ValueError('Invalid replay request.')
        messages = request['messages']
        if not messages or len(messages) > 30 or messages[-1].get('role') != 'user':
            raise ValueError('Invalid UI message history.')
        if any(set(m) != {'role','content'} or m['role'] not in ('user','assistant') or not isinstance(m['content'],str) for m in messages):
            raise ValueError('Invalid UI message history.')
        if engine.digest(engine.prompt_for(request['condition'])) != item['expected_prompt_hash']:
            raise ValueError('UI prompt changed after planning.')
        if engine.digest(current_rubric()) != item['expected_rubric_hash']:
            raise ValueError('UI rubric changed after planning.')
        expected_key = digest(dict(prompt=engine.prompt_for(request['condition']), rubric_hash=item['expected_rubric_hash'],
                                   messages=messages, condition=request['condition']))
        if expected_key != item['source_input_hash']:
            raise ValueError('Replay input binding mismatch.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    exp = sub.add_parser('export', help='Read active saved UI records; no network or DB writes.')
    exp.add_argument('--db', type=Path, default=records.DB)
    exp.add_argument('--out', type=Path, required=True)
    exp.add_argument('--backend')
    exp.add_argument('--adapter', choices=('any','present','absent'), default='any')
    exp.add_argument('--adapter-hash')
    exp.add_argument('--condition', choices=('A','B'))
    exp.add_argument('--rubric-version')
    plan = sub.add_parser('plan', help='Write replay requests for existing inputs; no network.')
    plan.add_argument('--source', type=Path, required=True)
    plan.add_argument('--manifest-sha', required=True)
    plan.add_argument('--model', required=True, help='Registered target UI model key.')
    plan.add_argument('--record-id', action='append')
    plan.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'export':
        result = export(args.db,args.out,args.backend,args.adapter,args.condition,args.rubric_version,args.adapter_hash)
        print(canonical(dict(records=result['record_count'], manifest_sha256=sha(args.out/'manifest.json'))))
    elif args.command == 'plan':
        print(canonical(dict(requests=replay_plan(args.source,args.manifest_sha,args.model,args.out,args.record_id), plan_sha256=sha(args.out))))


if __name__ == '__main__':
    main()
