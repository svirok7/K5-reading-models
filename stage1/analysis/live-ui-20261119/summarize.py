"""Read-only UI results snapshot; exports aggregates, never conversation text."""
import collections
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import records


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def label(row):
    model = row['response']['model']
    if model['backend'] == 'fireworks_sampler':
        return 'Muse Glimmer 30B · 600 examples · 3 epochs'
    if model['backend'] == 'qwen':
        adapter = model.get('adapter') or ''
        if 'sft600' in adapter:
            return 'Qwen3-1.7B · 600 examples · 3 epochs'
        if 'sft300' in adapter:
            return 'Qwen3-1.7B · 300 examples · 1 epoch'
        return 'Qwen3-1.7B baseline'
    return model['model']


def summarize(rows):
    counts = collections.Counter(r['effective_decision'] for r in rows)
    passed, failed = counts['acceptable'], counts['not_acceptable']
    judges = [r['evaluation'] for r in rows if r.get('evaluation')]
    times = sorted(r['response']['latency_s'] for r in rows if r['response']['status'] == 'completed')
    import math
    return {
        'saved': len(rows), 'passed': passed, 'failed': failed,
        'decided': passed + failed, 'pending': counts['pending'],
        'pass_rate_percent': round(100 * passed / (passed + failed), 1) if passed + failed else None,
        'evaluator_ratings': len(judges),
        'evaluator_passed': sum(j['verdict'] == 'acceptable' for j in judges),
        'manual_decisions': sum(bool(r.get('manual')) for r in rows),
        'manual_evaluator_disagreements': sum(
            bool(r.get('manual')) and bool(r.get('evaluation'))
            and r['manual']['decision'] != r['evaluation']['verdict'] for r in rows),
        'incomplete': sum(r['response']['status'] != 'completed' for r in rows),
        'unique_exact_inputs': len({digest([r['prompt'], r['rubric_hash'], r['messages']]) for r in rows}),
        'companion_latency_s': {
            'n': len(times),
            'p50': times[math.ceil(len(times) * .5) - 1] if times else None,
            'p95': times[math.ceil(len(times) * .95) - 1] if times else None,
        },
    }


def main():
    db = ROOT / 'runs/conversation-results.sqlite3'
    with sqlite3.connect(db.as_uri() + '?mode=ro', uri=True) as connection:
        connection.execute('PRAGMA query_only=ON')
        bodies = [json.loads(r[0]) for r in connection.execute('SELECT body FROM records ORDER BY id')]
    source_hash = digest(bodies)
    rows = [records.effective(r) for r in bodies if not r.get('archived_at')]
    groups = collections.defaultdict(list)
    for row in rows:
        groups[label(row)].append(row)
    configurations = json.loads(json.dumps(records.summaries(rows)))
    for group in configurations:
        model = group['identity']['model']
        if model.get('adapter'):
            path = Path(model['adapter'])
            model['adapter'] = path.parent.name + '/' + path.name
    result = {
        'captured_at_utc': datetime.now(timezone.utc).isoformat(),
        'source': 'Local conversation-results.sqlite3; read-only snapshot; no provider requests',
        'source_records_sha256': source_hash,
        'archived_excluded': len(bodies) - len(rows),
        'totals': summarize(rows),
        'models': {name: summarize(group) for name, group in sorted(groups.items())},
        'configuration_groups': configurations,
    }
    output = Path(__file__).with_name('summary.json')
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'configuration_groups'}, indent=2))


if __name__ == '__main__':
    main()
