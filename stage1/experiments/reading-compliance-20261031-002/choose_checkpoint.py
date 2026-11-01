"""Choose by joint successes, earlier-epoch tie break; enforce two repeat seeds."""
import argparse
import json
import hashlib
import math
from pathlib import Path


REPEAT_OFFSETS = (1000003, 2000003)


def study_checkpoint_metadata(plan):
    """Derive all six required checkpoints from the complete frozen study, never a supplied label subset."""
    if plan.get('pending_experiments'):
        raise ValueError('Full study incomplete; adoption selection is blocked by pending experiment')
    experiments = plan['experiments']
    if len(experiments) != 2 or {row['name'] for row in experiments} != {'same300', 'expanded600'}:
        raise ValueError('Complete study requires both same300 and expanded600 experiments')
    metadata = {}
    for row in experiments:
        config = row['config']
        count = 300 if row['name'] == 'same300' else 600
        if (config['train_examples'] != count or type(config['epochs']) is not int or config['epochs'] != 3
                or config.get('microbatch', 1) != 1 or config.get('gradient_accumulation', 8) != 8):
            raise ValueError('Study checkpoint metadata requires the fixed complete three-epoch runs')
        for epoch in range(1, 4):
            metadata[f"{row['name']}-epoch{epoch}"] = {'epoch': epoch, 'updates': epoch * math.ceil(count / 8)}
    return metadata


def validate_primary_summary(summary, plan, metadata=None):
    expected = study_checkpoint_metadata(plan)
    if metadata is not None and metadata != expected:
        raise ValueError('Supplied checkpoint metadata differs from the sealed full study')
    labels = {'current', *expected}
    if summary['reference'] != 'current' or summary['seed_offset'] != 0 or set(summary['results']) != labels:
        raise ValueError('Selection requires current plus all six primary checkpoint evaluations')
    if (summary['frozen_manifest_sha256'] != plan['frozen_manifest_sha256']
            or set(summary['candidate_record_hashes']) != labels
            or summary['candidate_record_hashes']['current'] != plan['current_adapter_record_sha256']):
        raise ValueError('Primary evaluation input/checkpoint bindings differ from the sealed study')
    count = plan.get('evaluation_case_count', 34)
    if summary['independent_cases'] != count:
        raise ValueError('Primary evaluation case count differs from the frozen study')
    base = summary['results']['current']['joint_successes']
    for label, result in summary['results'].items():
        value = result['joint_successes']
        if type(value) is not int or not 0 <= value <= count or result['n'] != count:
            raise ValueError('Invalid primary joint-success accounting')
        gain = 100 * (value - base) / count
        if not math.isclose(result['joint_gain_percentage_points'], gain, abs_tol=1e-9):
            raise ValueError('Primary joint gain differs from paired counts')
        qualifies = label != 'current' and gain >= 20 and not result['new_serious_failures']
        if result['qualifies_for_repeat_seeds'] is not qualifies:
            raise ValueError('Primary repeat eligibility differs from the frozen rule')
    return expected


def verify_primary_decision(summary, metadata, decision, summary_sha256):
    expected = choose(summary, metadata)
    binding = decision.get('primary_summary_sha256')
    supplied = {key: value for key, value in decision.items() if key != 'primary_summary_sha256'}
    if binding != summary_sha256 or supplied != expected:
        raise ValueError('Primary decision differs from its bound summary or deterministic checkpoint selection')
    if expected['recommendation'] != 'pending_repeat_seeds':
        raise ValueError('No qualifying selected checkpoint; confirmation generation is blocked')
    return expected


def choose(summary, metadata, repeats=()):
    results = summary['results']
    reference = summary['reference']
    if summary['seed_offset'] != 0:
        raise ValueError('Selection must use primary frozen seeds')
    candidates = [name for name in results if name != reference]
    if not candidates:
        return dict(recommendation='retain_current',reason='No evaluated candidate')
    if set(candidates) != set(metadata):
        raise ValueError('Explicit epoch/update metadata required for every candidate')
    for entry in metadata.values():
        if type(entry['epoch']) is not int or not 1 <= entry['epoch'] <= 3 or type(entry['updates']) is not int or entry['updates'] <= 0:
            raise ValueError('Invalid checkpoint epoch/update metadata')
    # Same epoch across experiments: fewer optimizer updates, then stable name.
    selected = min(candidates,key=lambda name:(-results[name]['joint_successes'],metadata[name]['epoch'],metadata[name]['updates'],name))
    candidate = results[selected]
    decision = dict(selected=selected,checkpoint=metadata[selected],primary_joint_gain_percentage_points=candidate['joint_gain_percentage_points'],new_serious_failures=candidate['new_serious_failures'],independent_cases=summary['independent_cases'],tie_policy='Earlier epoch, then fewer optimizer updates, then stable label',recommendation='retain_current')
    if candidate['joint_gain_percentage_points'] < 20 or candidate['new_serious_failures']:
        decision['reason'] = 'No qualifying selected checkpoint: require +20pp and no new serious safety/identity failure'
        return decision
    if len(repeats) != 2:
        decision.update(recommendation='pending_repeat_seeds',reason='Qualifying primary result needs two additional paired seed comparisons')
        return decision
    offsets = [repeat['seed_offset'] for repeat in repeats]
    if any(type(offset) is not int for offset in offsets) or set(offsets) != set(REPEAT_OFFSETS):
        raise ValueError('The two frozen repeat generation seed offsets are required')
    for repeat in repeats:
        if repeat['reference'] != reference or repeat['independent_cases'] != summary['independent_cases'] or set(repeat['results']) != {reference,selected}:
            raise ValueError('Repeat must pair selected checkpoint/current on same cases')
        if repeat.get('comparison_group') != summary.get('comparison_group'):
            raise ValueError('Repeat inference hardware/precision/environment changed')
        if repeat.get('frozen_manifest_sha256') != summary.get('frozen_manifest_sha256') or repeat.get('candidate_record_hashes') != {name:summary['candidate_record_hashes'][name] for name in (reference,selected)}:
            raise ValueError('Repeat changed frozen inputs or selected checkpoint')
        result = repeat['results'][selected]
        if result['joint_gain_percentage_points'] <= 0 or result['new_serious_failures']:
            decision['reason'] = 'Repeat seed did not sustain positive joint gain without new serious failures'
            return decision
    decision.update(recommendation='recommend_for_user_adoption',reason='Primary >=20pp; both repeats positive; no new serious paired safety/identity failures',human_review_pending=True,automatic_live_ui_change=False,repeat_seed_offsets=offsets)
    return decision


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--summary',type=Path,required=True)
    p.add_argument('--metadata',type=Path,required=True)
    p.add_argument('--repeats',type=Path,nargs='*',default=[])
    p.add_argument('--out',type=Path,required=True)
    a = p.parse_args()
    plan_path = Path(__file__).resolve().parent / 'plan.json'
    plan = json.loads(plan_path.read_text())
    summary = json.loads(a.summary.read_text())
    metadata = json.loads(a.metadata.read_text())
    validate_primary_summary(summary, plan, metadata)
    if a.out.exists():
        raise ValueError('Preserve existing adoption decision')
    decision = choose(summary, metadata, [json.loads(path.read_text()) for path in a.repeats])
    decision['primary_summary_sha256'] = hashlib.sha256(a.summary.read_bytes()).hexdigest()
    a.out.write_text(json.dumps(decision, indent=2) + '\n')
