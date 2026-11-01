"""Choose by joint successes, earlier-epoch tie break; enforce two repeat seeds."""
import argparse
import json
from pathlib import Path


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
    if len(set(offsets)) != 2 or any(type(offset) is not int or offset <= 0 for offset in offsets):
        raise ValueError('Two distinct non-primary repeat generation seeds required')
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
    plan_path=Path(__file__).resolve().parent/'plan.json'
    if plan_path.exists() and json.loads(plan_path.read_text()).get('pending_experiments'):
        raise ValueError('Full study incomplete; adoption selection is blocked by pending experiment')
    if a.out.exists():
        raise ValueError('Preserve existing adoption decision')
    decision = choose(json.loads(a.summary.read_text()),json.loads(a.metadata.read_text()),[json.loads(path.read_text()) for path in a.repeats])
    a.out.write_text(json.dumps(decision,indent=2)+'\n')
