"""Execute approved fresh runs and explicitly bound completed source runs.

A reused run keeps its original identity. Full-study selection still requires all
six checkpoint evaluations and one current-adapter comparator on identical inputs.
"""
import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import sys

ALLOCATOR = 'expandable_segments:True'
if 'torch' in sys.modules and os.environ.get('PYTORCH_CUDA_ALLOC_CONF') != ALLOCATOR:
    raise RuntimeError('Restart runtime: allocator must be set before importing torch')
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = ALLOCATOR
HERE = Path(__file__).resolve().parent
STAGE = HERE.parents[1]
sys.path.insert(0, str(STAGE))
import sft_train as training
import evaluate
from choose_checkpoint import study_checkpoint_metadata


def check_plan(plan):
    if plan['helper_sha256'] != training.sha256(STAGE / 'sft_train.py'):
        raise ValueError('Training helper differs from sealed experiment')
    for name, expected in plan['code_files'].items():
        if Path(name).is_absolute() or '..' in Path(name).parts or training.sha256(STAGE / name) != expected:
            raise ValueError('Execution code differs: ' + name)
    evaluate.frozen(HERE / 'frozen', plan['frozen_manifest_sha256'])
    if plan['model'] != training.MODEL_ID or plan['revision'] != training.REVISION:
        raise ValueError('Wrong pinned base')
    if evaluate.digest(plan['prepared_model_artifacts']) != plan['prepared_model_artifacts_sha256']:
        raise ValueError('Prepared model artifact aggregate differs')
    if evaluate.digest(plan['prepared_environment']) != plan['prepared_environment_sha256']:
        raise ValueError('Prepared environment aggregate differs')
    study_checkpoint_metadata(plan)


def reference_path(output, path):
    value = Path(path)
    return value.resolve() if value.is_absolute() else (Path(output) / value).resolve()


def verify_reused_training(output, binding, experiment, plan):
    full = reference_path(output, binding['path'])
    if training.sha256(full / 'run-record.json') != binding['run_record_sha256']:
        raise ValueError('Reused training record changed')
    if training.sha256(full / 'checkpoint-index.json') != binding['checkpoint_index_sha256']:
        raise ValueError('Reused checkpoint index changed')
    record = json.loads((full / 'run-record.json').read_text())
    config = training.TrainConfig(**experiment['config'])
    identity = record['identity']
    if (record['status'] != 'training_completed' or identity['config'] != asdict(config)
            or identity['model'] != training.MODEL_ID or identity['revision'] != training.REVISION
            or identity['helper_sha256'] != plan['helper_sha256']
            or identity['context']['plan_sha256'] != binding['source_plan_sha256']
            or identity['data_sha256'] != config.data_sha256
            or identity['manifest_sha256'] != config.manifest_sha256):
        raise ValueError('Reused training identity/configuration differs')
    index = json.loads((full / 'checkpoint-index.json').read_text())
    if index != record['checkpoint_index']:
        raise ValueError('Reused checkpoint index differs from completed run record')
    checkpoints = training.verify_epoch_checkpoints(full, identity)
    for name in checkpoints:
        reload = record['epoch_checkpoint_reloads'][name]
        if not reload['save_reload_weights_equal'] or not reload['inference_verified']:
            raise ValueError('Reused epoch checkpoint lacks successful reload evidence')
    if not (record['final_reload']['save_reload_weights_equal'] and record['final_reload']['inference_verified']
            and record['training_memory']['headroom_passed'] and record['memory_including_reload']['headroom_passed']):
        raise ValueError('Reused training lacks final integrity/headroom evidence')
    return full, record


def completed_evaluation(path, plan, record_sha, offset, *, cases=None, expected_group=None, manifest_sha256=None):
    if not Path(path).exists():
        return False
    return evaluate.verify_completed_generation(path, plan['frozen_manifest_sha256'], record_sha, offset,
        cases=cases, expected_model_artifacts=plan['prepared_model_artifacts'],
        expected_group=expected_group, manifest_sha256=manifest_sha256)


def validate_execution_environment(output, environment):
    if 'T4' not in environment['gpu'] or environment['compute_dtype'] != 'float16':
        raise ValueError('Use existing T4 / float16; no precision or hardware substitution')
    path = Path(output) / 'environment.json'
    if path.exists():
        original = json.loads(path.read_text())
        for field in ('packages', 'gpu', 'compute_dtype', 'allocator_config', 'cuda_runtime', 'python'):
            if original[field] != environment[field]:
                raise ValueError('Execution environment changed: ' + field)
    else:
        training.write_json(path, environment)


def run(plan_path, output, current_adapter, resume=None, only=None):
    if resume is not None and only is None:
        raise ValueError('Explicit resume requires --only for its matching experiment')
    plan_path, output = Path(plan_path), Path(output)
    plan = json.loads(plan_path.read_text())
    check_plan(plan)
    metadata = study_checkpoint_metadata(plan)
    expected_labels = {'current', *metadata}
    reuse_training = plan.get('reuse_training', {})
    reuse_evaluations = plan.get('reuse_evaluations', {})
    if set(reuse_training) - {row['name'] for row in plan['experiments']} or set(reuse_evaluations) - expected_labels:
        raise ValueError('Unrecognized reused run/evaluation label')
    if resume is not None and only in reuse_training:
        raise ValueError('A reused completed source run cannot be resumed or modified')
    output.mkdir(parents=True, exist_ok=True)
    plan_sha = training.sha256(plan_path)
    status_path = output / 'execution-status.json'
    if status_path.exists():
        status = json.loads(status_path.read_text())
        if status['plan_sha256'] != plan_sha:
            raise ValueError('Existing execution belongs to another sealed plan')
    else:
        status = dict(plan_sha256=plan_sha, status='preparing', completed_runs=[], results={})
    training.write_json(status_path, status)
    try:
        environment = training.cuda_environment('lora')
        validate_execution_environment(output, environment)
        status.setdefault('invocations', []).append(dict(environment=environment, only=only, resume=str(resume) if resume else None))
        cases = evaluate.frozen(HERE / 'frozen', plan['frozen_manifest_sha256'])
        source_runs = {}
        for experiment in plan['experiments']:
            name = experiment['name']
            if name in reuse_training:
                source_runs[name] = verify_reused_training(output, reuse_training[name], experiment, plan)
        reference_binding = reuse_evaluations.get('current')
        reference_out = (reference_path(output, reference_binding['path']) if reference_binding else output / 'evaluation/current')
        if not reference_binding:
            reference_out.parent.mkdir(parents=True, exist_ok=True)
        reference_record = completed_evaluation(reference_out, plan, plan['current_adapter_record_sha256'], 0,
            cases=cases, manifest_sha256=reference_binding['manifest_sha256'] if reference_binding else None)
        if reference_binding and reference_record is False:
            raise ValueError('Bound current-adapter source output is missing; never regenerate into a source directory')
        if reference_record is False:
            evaluate.generate(HERE / 'frozen', plan['frozen_manifest_sha256'], current_adapter,
                HERE / 'current-adapter-record.json', plan['current_adapter_record_sha256'], reference_out,
                expected_model_artifacts=plan['prepared_model_artifacts'])
            reference_record = completed_evaluation(reference_out, plan, plan['current_adapter_record_sha256'], 0, cases=cases)
        group = evaluate.inference_group(reference_record, False)
        evaluate.verify_live_inference_environment(group, environment)
        status['results']['current'] = str(reference_out)
        training.write_json(status_path, status)
        # A reused comparator still requires verification of the actual cache used for fresh training.
        evaluate.prepare_model_snapshot(plan['prepared_model_artifacts'])
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(training.MODEL_ID, revision=training.REVISION)
        tokenizer.padding_side = 'right'
        for experiment in plan['experiments']:
            name = experiment['name']
            if name in source_runs:
                full, record = source_runs[name]
            else:
                if only and name != only:
                    continue
                config = training.TrainConfig(**experiment['config'])
                data, manifest = training.verify_data(STAGE / experiment['dataset'], config)
                features = training.tokenize_rows(data, tokenizer, config.max_length)
                collator = training.CompletionCollator(tokenizer.pad_token_id, config.max_length)
                context = dict(plan_sha256=plan_sha, frozen_manifest_sha256=plan['frozen_manifest_sha256'],
                    allocator_config=ALLOCATOR, comparison='current SFT adapter; no new base-model run',
                    lr_policy='linear decay across all three epochs')
                directory = output / name
                directory.mkdir(exist_ok=True)
                training.write_json(directory / 'actual-collator-report.json',
                    training.verify_collator(features, collator, tokenizer, expected_count=config.train_examples))
                smoke_path = directory / 'smoke/smoke-report.json'
                if smoke_path.exists():
                    smoke = json.loads(smoke_path.read_text())
                    if smoke.get('identity') != training.run_identity(config, tokenizer, context) or not smoke.get('passed'):
                        raise ValueError('Existing smoke incompatible/failed; preserve diagnostics and stop')
                else:
                    smoke = training.smoke_test(features, collator, tokenizer, config, directory / 'smoke', context)
                if not smoke.get('passed') or not smoke.get('headroom_passed'):
                    raise ValueError('Stop: smoke/numerical/15% memory gate failed')
                full = directory / 'full'
                if (full / 'run-record.json').exists():
                    record = json.loads((full / 'run-record.json').read_text())
                    if record['identity'] != training.run_identity(config, tokenizer, context):
                        raise ValueError('Full run identity changed')
                    if record['status'] != 'training_completed':
                        if resume is None:
                            raise ValueError('Interrupted training requires an explicit latest epoch checkpoint')
                        record = training.full_train(features, collator, tokenizer, config, full, smoke, manifest, context, resume)
                    elif resume is not None:
                        raise ValueError('Cannot resume a completed run')
                else:
                    if resume is not None:
                        raise ValueError('Resume requires its existing full run')
                    record = training.full_train(features, collator, tokenizer, config, full, smoke, manifest, context)
            if record['status'] != 'training_completed':
                raise ValueError('Training did not pass final integrity checks')
            training.verify_epoch_checkpoints(full, record['identity'])
            for epoch in range(1, experiment['config']['epochs'] + 1):
                step = epoch * training.optimizer_steps_per_epoch(experiment['config']['train_examples'])
                checkpoint = full / 'checkpoints' / f'checkpoint-{step}'
                expected = record['checkpoint_index'][checkpoint.name]['resume_record_sha256']
                training.verify_replay_checkpoint(checkpoint, expected, record['identity'])
                label = f'{name}-epoch{epoch}'
                binding = reuse_evaluations.get(label)
                result_out = reference_path(output, binding['path']) if binding else output / 'evaluation' / label
                result = completed_evaluation(result_out, plan, expected, 0, cases=cases, expected_group=group,
                    manifest_sha256=binding['manifest_sha256'] if binding else None)
                if binding and result is False:
                    raise ValueError('Bound source evaluation is missing; never write into a source directory')
                if result is False:
                    evaluate.generate(HERE / 'frozen', plan['frozen_manifest_sha256'], checkpoint,
                        checkpoint / 'resume-record.json', expected, result_out,
                        expected_model_artifacts=plan['prepared_model_artifacts'], expected_inference_group=group)
                    completed_evaluation(result_out, plan, expected, 0, cases=cases, expected_group=group)
                status['results'][label] = str(result_out)
                training.write_json(status_path, status)
            if name not in status['completed_runs']:
                status['completed_runs'].append(name)
            training.write_json(status_path, status)
        status['study_complete'] = set(status['results']) == expected_labels and set(status['completed_runs']) == {'same300', 'expanded600'}
        status['status'] = ('generations_complete_pending_blind_review' if status['study_complete']
                            else 'partial_generations_selection_blocked')
        training.write_json(output / 'review-runs.json', status['results'])
        return status
    except Exception as exc:
        status.update(status='stopped', error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        training.write_json(status_path, status)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, default=HERE / 'plan.json')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--current-adapter', type=Path, required=True)
    parser.add_argument('--resume', type=Path)
    parser.add_argument('--only', choices=('same300', 'expanded600'))
    args = parser.parse_args()
    run(args.plan, args.output, args.current_adapter, args.resume, args.only)
