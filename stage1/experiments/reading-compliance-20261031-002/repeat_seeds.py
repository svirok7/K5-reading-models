"""Confirm only the deterministically selected/current pair at the two frozen offsets.
Completed generations and blind packets are verified and reused on continuation.
Partial generation artifacts are preserved and stop the run; they are never overwritten.
"""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import re
import evaluate
import execute
from choose_checkpoint import REPEAT_OFFSETS, validate_primary_summary, verify_primary_decision

HERE = Path(__file__).resolve().parent


def validate_primary_execution(output, plan, summary, plan_sha):
    output = Path(output)
    status = json.loads((output / 'execution-status.json').read_text())
    if (status['plan_sha256'] != plan_sha or status.get('study_complete') is not True
            or set(status['completed_runs']) != {'same300', 'expanded600'}
            or set(status['results']) != set(summary['results'])):
        raise ValueError('Both complete training runs and all six primary evaluations are required')
    cases = evaluate.frozen(HERE / 'frozen', plan['frozen_manifest_sha256'])
    selected_runs = {}
    for experiment in plan['experiments']:
        name = experiment['name']
        binding = plan.get('reuse_training', {}).get(name)
        if binding:
            full, record = execute.verify_reused_training(output, binding, experiment, plan)
        else:
            full = output / name / 'full'
            record = json.loads((full / 'run-record.json').read_text())
            config = execute.training.TrainConfig(**experiment['config'])
            if (record['status'] != 'training_completed' or record['identity']['config'] != asdict(config)
                    or record['identity']['context']['plan_sha256'] != plan_sha
                    or record['identity']['helper_sha256'] != plan['helper_sha256']):
                raise ValueError('Primary completed run does not belong to this study')
            if record['checkpoint_index'] != json.loads((full / 'checkpoint-index.json').read_text()):
                raise ValueError('Primary completed checkpoint index changed')
            execute.training.verify_epoch_checkpoints(full, record['identity'])
        selected_runs[name] = (full, record)
        for epoch in range(1, 4):
            label = f'{name}-epoch{epoch}'
            step = epoch * execute.training.optimizer_steps_per_epoch(experiment['config']['train_examples'])
            digest = record['checkpoint_index'][f'checkpoint-{step}']['resume_record_sha256']
            if summary['candidate_record_hashes'][label] != digest:
                raise ValueError('Primary checkpoint label differs from bound epoch state')
    for label, path in status['results'].items():
        binding = plan.get('reuse_evaluations', {}).get(label)
        if binding and Path(path).resolve() != execute.reference_path(output, binding['path']):
            raise ValueError('Primary reused evaluation path changed')
        evaluate.verify_completed_generation(path, plan['frozen_manifest_sha256'], summary['candidate_record_hashes'][label], 0,
            cases=cases, expected_model_artifacts=plan['prepared_model_artifacts'], expected_group=summary['comparison_group'],
            manifest_sha256=binding['manifest_sha256'] if binding else None)
    evaluate.verify_blind_review_binding(output / 'blind-review', summary=summary)
    return cases, selected_runs


def verify_existing_blind(review, cases, runs, plan, group, records, offset):
    evaluate.verify_blind_review_binding(review, reference_sha=plan['frozen_manifest_sha256'],
        candidate_records=records, group=dict(group, seed_offset=offset))
    key = json.loads((Path(review) / 'identity-key.json').read_text())
    expected = {(label, case['case_id']) for label in runs for case in cases}
    if len(key) != len(expected) or {(entry['variant'], entry['case_id']) for entry in key.values()} != expected:
        raise ValueError('Existing repeat blind packet has missing/duplicated responses')
    for entry in key.values():
        if entry['run_manifest_sha256'] != evaluate.sha(Path(runs[entry['variant']]) / 'manifest.json'):
            raise ValueError('Existing repeat blind packet belongs to another generation')


def run(output, current_adapter, primary_summary, primary_decision):
    output, primary_summary, primary_decision = Path(output), Path(primary_summary), Path(primary_decision)
    summary = json.loads(primary_summary.read_text())
    decision = json.loads(primary_decision.read_text())
    plan_path = HERE / 'plan.json'
    plan = json.loads(plan_path.read_text())
    execute.check_plan(plan)
    metadata = validate_primary_summary(summary, plan)
    summary_sha = evaluate.sha(primary_summary)
    verify_primary_decision(summary, metadata, decision, summary_sha)
    plan_sha = evaluate.sha(plan_path)
    cases, source_runs = validate_primary_execution(output, plan, summary, plan_sha)
    if not (output / 'environment.json').is_file():
        raise ValueError('Primary execution environment record is missing')
    environment = execute.training.cuda_environment('lora')
    execute.validate_execution_environment(output, environment)
    evaluate.verify_live_inference_environment(summary['comparison_group'], environment)
    evaluate.verify_adapter(current_adapter, HERE / 'current-adapter-record.json', plan['current_adapter_record_sha256'])
    evaluate.prepare_model_snapshot(plan['prepared_model_artifacts'])
    selected = decision['selected']
    match = re.fullmatch(r'(same300|expanded600)-epoch([1-3])', selected)
    if not match:
        raise ValueError('Unrecognized selected checkpoint')
    name, epoch = match.group(1), int(match.group(2))
    full, record = source_runs[name]
    step = metadata[selected]['updates']
    checkpoint = full / 'checkpoints' / f'checkpoint-{step}'
    checkpoint_sha = record['checkpoint_index'][checkpoint.name]['resume_record_sha256']
    records = {'current': plan['current_adapter_record_sha256'], selected: checkpoint_sha}
    group = summary['comparison_group']
    for offset in REPEAT_OFFSETS:
        root = output / f'repeat-seed-{offset}'
        root.mkdir(exist_ok=True)
        state_path = root / 'repeat-state.json'
        binding = dict(plan_sha256=plan_sha, primary_summary_sha256=summary_sha,
            primary_decision_sha256=evaluate.sha(primary_decision), selected=selected, seed_offset=offset,
            candidate_record_hashes=records, comparison_group=group)
        if state_path.exists():
            previous = json.loads(state_path.read_text())
            if previous['binding'] != binding:
                raise ValueError('Existing repeat seed belongs to a different selected study')
        elif any(root.iterdir()):
            raise ValueError('Unbound existing repeat directory; preserve it and stop')
        state = dict(binding=binding, status='generating', runs={})
        evaluate.write(state_path, state)
        runs = {}
        try:
            for label, adapter, record_path, record_sha in (
                ('current', Path(current_adapter), HERE / 'current-adapter-record.json', plan['current_adapter_record_sha256']),
                (selected, checkpoint, checkpoint / 'resume-record.json', checkpoint_sha)):
                destination = root / label
                result = execute.completed_evaluation(destination, plan, record_sha, offset,
                    cases=cases, expected_group=group)
                if result is False:
                    evaluate.generate(HERE / 'frozen', plan['frozen_manifest_sha256'], adapter, record_path,
                        record_sha, destination, offset, expected_model_artifacts=plan['prepared_model_artifacts'],
                        expected_inference_group=group)
                    execute.completed_evaluation(destination, plan, record_sha, offset, cases=cases, expected_group=group)
                runs[label] = str(destination)
                state['runs'] = runs
                evaluate.write(state_path, state)
            evaluate.write(root / 'review-runs.json', runs)
            review = root / 'blind-review'
            if review.exists():
                verify_existing_blind(review, cases, runs, plan, group, records, offset)
            else:
                evaluate.blind(HERE / 'frozen', plan['frozen_manifest_sha256'], runs, review)
            state['status'] = 'generations_complete_pending_blind_review'
        except Exception as error:
            state.update(status='stopped', error_type=type(error).__name__, error=str(error))
            raise
        finally:
            evaluate.write(state_path, state)
    print('Both repeat pairs are ready for independent blind review; no adoption or UI change.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--current-adapter', type=Path, required=True)
    parser.add_argument('--primary-summary', type=Path, required=True)
    parser.add_argument('--primary-decision', type=Path, required=True)
    a = parser.parse_args()
    run(a.output, a.current_adapter, a.primary_summary, a.primary_decision)
