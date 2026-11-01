"""Prepare blind manual comparisons and summarize them without any evaluator call."""
import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path

from prepare_reference import canonical, digest, file_hash, verify, FROZEN_MANIFEST_SHA256


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def read_run(folder):
    manifest = json.loads((folder / 'manifest.json').read_text())
    if manifest.get('status') != 'completed' or file_hash(folder / 'responses.jsonl') != manifest['responses_sha256']:
        raise ValueError('Run is incomplete or responses changed.')
    rows = read_jsonl(folder / 'responses.jsonl')
    by_id = {r['case_id']: r for r in rows}
    if len(by_id) != len(rows) or len(rows) != manifest['case_count']:
        raise ValueError('Duplicate or missing response rows.')
    return manifest, by_id


def blank(text):
    return {'text': text, 'text_sha256': digest(text),
            'scores': {d: None for d in ('word_types', 'length', 'rhythm')},
            'manual_decision': None, 'meaningful': None, 'unsupported_words': [],
            'repetition_or_regression': '', 'evidence': ''}


def generation_summary(rows):
    times = sorted(r['latency_s'] for r in rows if r.get('status') == 'completed' and r.get('latency_s') is not None)
    return {'responses': len(rows), 'status_counts': dict(Counter(r['status'] for r in rows)),
        'truncated': sum(bool(r.get('truncated')) for r in rows),
        'completed_latency_s': {'n': len(times),
            'p50': times[max(0, math.ceil(len(times) * .5) - 1)] if times else None,
            'p95': times[max(0, math.ceil(len(times) * .95) - 1)] if times else None}}


def prepare(args):
    verify(args.reference, FROZEN_MANIFEST_SHA256)
    sft_manifest, sft = read_run(args.sft)
    if sft_manifest.get('variant') != 'sft':
        raise ValueError('--sft must contain adapter responses.')
    if file_hash(args.reference / 'manifest.json') != sft_manifest['reference_manifest_sha256']:
        raise ValueError('Run refers to a different baseline reference.')
    limitations = []
    if args.base:
        base_manifest, base = read_run(args.base)
        if base_manifest.get('variant') != 'base':
            raise ValueError('--base must contain fresh unadapted responses.')
        for key in ('reference_manifest_sha256', 'inputs_sha256', 'selection', 'base_model',
                    'revision', 'template', 'enable_thinking', 'generation', 'device', 'precision',
                    'seed', 'seed_policy', 'packages', 'python', 'platform', 'hardware',
                    'cuda', 'chat_template_sha256', 'effective_generation_config', 'attention_implementation'):
            if base_manifest.get(key) != sft_manifest.get(key):
                raise ValueError('Matched base/SFT configuration mismatch: ' + key)
        if set(base) != set(sft):
            raise ValueError('Matched runs have different case IDs.')
        for case_id in sft:
            for key in ('seed', 'rendered_input_sha256', 'input_token_ids_sha256', 'saved_group_id',
                        'condition', 'messages', 'prompt'):
                if base[case_id][key] != sft[case_id][key]:
                    raise ValueError('Matched case mismatch: ' + key)
        comparator = 'fresh matched base'
        limitations.append('Case seeds match; floating-point kernels/hardware may still be nondeterministic.')
    else:
        originals = {r['id']: r for r in read_jsonl(args.reference / 'baseline-records.jsonl')}
        base = {}
        for case_id, row in sft.items():
            saved = originals[case_id]
            metadata = saved['response']['model']
            if row['saved_baseline_comparability'] != 'current_template_recorded':
                raise ValueError('Legacy templates require a fresh matched base; provide --base.')
            for saved_key, new_key in (('revision', 'revision'), ('device', 'device'),
                                       ('precision', 'precision'), ('template', 'template')):
                if metadata.get(saved_key) != sft_manifest.get(new_key):
                    raise ValueError('Saved baseline mismatch requires matched control: ' + saved_key)
            if any(metadata.get(k) != value for k, value in sft_manifest['generation'].items()):
                raise ValueError('Saved baseline decoding mismatch requires matched control.')
            if row['messages'] != saved['messages'] or row['prompt'] != saved['prompt']:
                raise ValueError('Saved baseline input mismatch.')
            base[case_id] = {**saved['response'], 'saved_group_id': row['saved_group_id']}
        comparator = 'saved current-template baseline'
        limitations += ['Saved baseline seeds/package versions/token hashes were not recorded.',
                        'Template labels match, but historical encoder/tokenizer artifacts cannot be independently verified.']
    if args.out.exists():
        raise ValueError('Comparison output exists; use a fresh directory.')
    args.out.mkdir(parents=True)
    review, key, generation_groups = [], {}, defaultdict(lambda: {'base': [], 'sft': []})
    for case_id in sorted(sft):
        row = sft[case_id]
        order = ('base', 'sft') if int(digest(case_id)[0], 16) % 2 else ('sft', 'base')
        sources = {'base': base[case_id], 'sft': row}
        for variant in ('base', 'sft'):
            generation_groups[(row['saved_group_id'], row['history_kind'])][variant].append(sources[variant])
        key[case_id] = dict(zip(('X', 'Y'), order))
        review.append({'case_id': case_id, 'saved_group_id': row['saved_group_id'],
            'condition': row['condition'], 'history_kind': row['history_kind'],
            'messages': row['messages'], 'responses': {
                label: blank(sources[variant]['text']) for label, variant in key[case_id].items()}})
    (args.out / 'review.jsonl').write_text(''.join(canonical(r) + '\n' for r in review))
    (args.out / 'identity-key.json').write_text(json.dumps(key, indent=2) + '\n')
    manifest = {'comparator': comparator, 'sft_manifest_sha256': file_hash(args.sft / 'manifest.json'),
        'base_manifest_sha256': file_hash(args.base / 'manifest.json') if args.base else None,
        'reference_manifest_sha256': file_hash(args.reference / 'manifest.json'),
        'review_sha256': file_hash(args.out / 'review.jsonl'),
        'identity_key_sha256': file_hash(args.out / 'identity-key.json'),
        'generation_groups': [{'saved_group_id': group, 'history_kind': kind,
            **{variant: generation_summary(rows) for variant, rows in variants.items()}}
            for (group, kind), variants in generation_groups.items()],
        'case_count': len(review), 'limitations': limitations + [
            'Selected casual development cases; fixed histories contain baseline answers.',
            'Do not pool configuration groups or interpret correlated turns as independent samples.',
            'Blind ordering hides labels only; text/content can sometimes suggest identity.',
            'No new evaluator scores or quality improvement are asserted by preparing this review.']}
    (args.out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest, indent=2))


def summarize(directory, ratings):
    manifest = json.loads((directory / 'manifest.json').read_text())
    if file_hash(directory / 'review.jsonl') != manifest['review_sha256'] or file_hash(directory / 'identity-key.json') != manifest['identity_key_sha256']:
        raise ValueError('Original blind comparison changed.')
    originals = {r['case_id']: r for r in read_jsonl(directory / 'review.jsonl')}
    key = json.loads((directory / 'identity-key.json').read_text())
    rated = read_jsonl(ratings)
    if len({r['case_id'] for r in rated}) != len(rated) or set(r['case_id'] for r in rated) != set(originals):
        raise ValueError('Ratings must contain each original case exactly once.')
    groups = defaultdict(lambda: {'responses': Counter(), 'decisions': defaultdict(Counter),
        'meaningful': defaultdict(Counter), 'scores': defaultdict(lambda: defaultdict(list)),
        'paired_reading': Counter(), 'paired_meaningful': Counter(), 'paired_examples': []})
    for row in rated:
        original = originals[row['case_id']]
        for field in ('saved_group_id', 'condition', 'history_kind', 'messages'):
            if row[field] != original[field]:
                raise ValueError('Review input/group changed.')
        group = groups[(row['saved_group_id'], row['history_kind'])]
        decisions, meanings = {}, {}
        for label in ('X', 'Y'):
            response = row['responses'][label]
            if response['text'] != original['responses'][label]['text'] or digest(response['text']) != response['text_sha256']:
                raise ValueError('Rated response text changed.')
            variant = key[row['case_id']][label]
            scores = response['scores']
            if set(scores) != {'word_types', 'length', 'rhythm'}:
                raise ValueError('Review requires the three reading dimensions.')
            for dimension, score in scores.items():
                if score is not None and (type(score) is not int or not 0 <= score <= 4):
                    raise ValueError('Scores must be null or integers 0–4.')
                if score is not None:
                    group['scores'][variant][dimension].append(score)
            manual = response['manual_decision']
            if manual not in (None, 'acceptable', 'not_acceptable'):
                raise ValueError('Invalid manual decision.')
            if manual and not response['evidence'].strip():
                raise ValueError('A manual decision requires evidence.')
            automatic = ('acceptable' if min(scores.values()) >= 3 else 'not_acceptable') if all(v is not None for v in scores.values()) else 'unscored'
            decision = manual or automatic
            meaningful = response['meaningful']
            if meaningful is not None and type(meaningful) is not bool:
                raise ValueError('Meaningful must be true, false, or null.')
            group['responses'][variant] += 1
            group['decisions'][variant][decision] += 1
            group['meaningful'][variant][str(meaningful)] += 1
            decisions[variant], meanings[variant] = decision, meaningful
        if 'unscored' not in decisions.values():
            group['paired_reading'][decisions['base'] + ' -> ' + decisions['sft']] += 1
        if all(m is not None for m in meanings.values()):
            group['paired_meaningful'][str(meanings['base']) + ' -> ' + str(meanings['sft'])] += 1
        group['paired_examples'].append({'case_id': row['case_id'], 'reading': decisions, 'meaningful': meanings,
            'responses': {key[row['case_id']][label]: row['responses'][label] for label in ('X', 'Y')}})
    report = {'comparison': manifest, 'groups': []}
    for (group_id, kind), group in groups.items():
        means = {variant: {dim: {'n': len(values), 'mean': sum(values) / len(values)}
                 for dim, values in dimensions.items()} for variant, dimensions in group.pop('scores').items()}
        report['groups'].append({'saved_group_id': group_id, 'history_kind': kind,
            **group, 'reading_score_means': means})
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, default=Path(__file__).resolve().parent / 'baseline-reference')
    parser.add_argument('--sft', type=Path)
    parser.add_argument('--base', type=Path)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--comparison', type=Path)
    parser.add_argument('--ratings', type=Path)
    args = parser.parse_args()
    if args.ratings:
        if not args.comparison:
            parser.error('--ratings requires --comparison.')
        summarize(args.comparison, args.ratings)
    else:
        if not args.sft or not args.out:
            parser.error('Preparing review requires --sft and a fresh --out directory.')
        prepare(args)
