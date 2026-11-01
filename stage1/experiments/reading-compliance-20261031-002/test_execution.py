"""Mechanical provenance/control-flow fixtures only; no new behavioral cases or GPU calls."""
import copy
from dataclasses import asdict
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock

import evaluate as e
import execute as x
import repeat_seeds as r
from choose_checkpoint import (choose, study_checkpoint_metadata, validate_primary_summary,
                               verify_primary_decision)


def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n')


def environment():
    return dict(gpu='Tesla T4', cuda_runtime='12.fixture', python='3.fixture', compute_dtype='float16',
                packages={key:'fixture' for key in ('torch','transformers','peft','accelerate','tokenizers','huggingface_hub','safetensors')},
                allocator_config={'PYTORCH_CUDA_ALLOC_CONF':x.ALLOCATOR})


def model_files():
    return {'config.json':'a' * 64, 'model.safetensors':'b' * 64}


def comparison_group():
    env = environment()
    return dict(base_model=e.MODEL, revision=e.REVISION, template=e.TEMPLATE, enable_thinking=False,
                generation=e.GENERATION, precision='float16', hardware=env['gpu'], cuda=env['cuda_runtime'],
                python=env['python'], packages=env['packages'], model_tokenizer_artifacts_sha256=e.digest(model_files()),
                actual_parameter_dtypes={'torch.float16':1,'torch.float32':1}, attention_implementation='sdpa')


def cases():
    return [dict(case_id='mechanical-only', input_hash='mechanical-input', seed=42,
                 prompt='Fixture', messages=[{'role':'user','content':'Fixture'}], history_kind='single_turn')]


def generation(path, record_sha, offset=0):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=False)
    data = [dict(case_id=c['case_id'], input_hash=c['input_hash'], seed=c['seed'] + offset,
                 text='Mechanical response', history_kind=c['history_kind'], status='completed') for c in cases()]
    e.jsonl(path / 'responses.jsonl', data)
    record = dict(comparison_group(), status='completed', seed_offset=offset, frozen_manifest_sha256='frozen',
                  adapter_record_sha256=record_sha, responses_sha256=e.sha(path / 'responses.jsonl'),
                  model_tokenizer_artifacts=model_files(), case_count=1)
    write(path / 'manifest.json', record)
    return record


def plan():
    config600 = x.training.TrainConfig(epochs=3, dataset_version='mechanical-600', train_examples=600,
                                     data_sha256='c' * 64, manifest_sha256='d' * 64)
    return dict(model=e.MODEL, revision=e.REVISION, frozen_manifest_sha256='frozen', helper_sha256='helper',
                current_adapter_record_sha256='current-record', prepared_model_artifacts=model_files(),
                prepared_model_artifacts_sha256=e.digest(model_files()), evaluation_case_count=1,
                experiments=[{'name':'same300','dataset':'mechanical300','config':asdict(x.training.TrainConfig(epochs=3))},
                             {'name':'expanded600','dataset':'mechanical600','config':asdict(config600)}])


def primary_summary(value):
    metadata = study_checkpoint_metadata(value)
    labels = ['current', *metadata]
    results = {}
    for label in labels:
        success = int(label == 'same300-epoch1')
        results[label] = dict(n=1, joint_successes=success, joint_gain_percentage_points=100 * success,
                             new_serious_failures=[], qualifies_for_repeat_seeds=bool(success))
    return dict(reference='current', seed_offset=0, independent_cases=1, frozen_manifest_sha256='frozen',
                comparison_group=comparison_group(), candidate_record_hashes={label:label + '-record' for label in labels},
                results=results)


class ExecutionIntegrity(unittest.TestCase):
    def test_model_hash_guard_rejects_changed_or_missing_bytes_before_model_loading(self):
        with tempfile.TemporaryDirectory() as temporary:
            snapshot = Path(temporary)
            (snapshot / 'config.json').write_bytes(b'mechanical-config')
            (snapshot / 'model.safetensors').write_bytes(b'mechanical-weights-not-loadable')
            bound = {name:e.sha(snapshot / name) for name in ('config.json','model.safetensors')}
            self.assertEqual(e.verify_prepared_model_files(snapshot, bound), bound)
            (snapshot / 'model.safetensors').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'bytes differ'):
                e.verify_prepared_model_files(snapshot, bound)
            (snapshot / 'model.safetensors').unlink()
            with self.assertRaisesRegex(ValueError, 'bytes differ'):
                e.verify_prepared_model_files(snapshot, bound)
            with self.assertRaisesRegex(ValueError, 'Invalid'):
                e.verify_prepared_model_files(snapshot, {'../outside':'a' * 64})

    def test_reused_generation_requires_external_manifest_input_seed_and_group_binding(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'generation'
            generation(path, 'adapter')
            expected = e.sha(path / 'manifest.json')
            self.assertEqual(e.verify_completed_generation(path, 'frozen', 'adapter', 0, cases=cases(),
                expected_model_artifacts=model_files(), expected_group=comparison_group(), manifest_sha256=expected)['status'], 'completed')
            with self.assertRaisesRegex(ValueError, 'manifest changed'):
                e.verify_completed_generation(path, 'frozen', 'adapter', 0, manifest_sha256='wrong')
            changed = dict(comparison_group(), precision='bfloat16')
            with self.assertRaisesRegex(ValueError, 'group differs'):
                e.verify_completed_generation(path, 'frozen', 'adapter', 0, expected_group=changed)
            with self.assertRaisesRegex(ValueError, 'incomplete/incompatible'):
                e.verify_completed_generation(path, 'frozen', 'adapter', 1)
            (path / 'responses.jsonl').write_text('changed')
            with self.assertRaisesRegex(ValueError, 'incomplete/incompatible'):
                e.verify_completed_generation(path, 'frozen', 'adapter', 0)

    def test_inference_environment_rejects_changes_before_model_allocation(self):
        e.verify_live_inference_environment(comparison_group(), environment())
        for key, value in (('gpu','A100'), ('cuda_runtime','changed'), ('python','changed'), ('compute_dtype','bfloat16')):
            with self.subTest(field=key), self.assertRaises(ValueError):
                e.verify_live_inference_environment(comparison_group(), dict(environment(), **{key:value}))
        changed = environment()
        changed['packages'] = dict(changed['packages'], torch='changed')
        with self.assertRaisesRegex(ValueError, 'package versions'):
            e.verify_live_inference_environment(comparison_group(), changed)

    def test_full_coverage_and_decision_hash_prevent_partial_or_changed_primary_selection(self):
        value = plan()
        summary = primary_summary(value)
        metadata = validate_primary_summary(summary, value)
        self.assertEqual(metadata['same300-epoch3']['updates'], 114)
        self.assertEqual(metadata['expanded600-epoch3']['updates'], 225)
        decision = dict(choose(summary, metadata), primary_summary_sha256='bound-summary')
        verify_primary_decision(summary, metadata, decision, 'bound-summary')
        for change in ('remove-candidate', 'wrong-metadata', 'wrong-gain', 'wrong-decision', 'wrong-summary-hash'):
            with self.subTest(change=change):
                other, other_meta, other_decision = copy.deepcopy(summary), copy.deepcopy(metadata), copy.deepcopy(decision)
                with self.assertRaises(ValueError):
                    if change == 'remove-candidate':
                        del other['results']['expanded600-epoch3']
                        validate_primary_summary(other, value)
                    elif change == 'wrong-metadata':
                        other_meta['same300-epoch1']['updates'] = 37
                        validate_primary_summary(other, value, other_meta)
                    elif change == 'wrong-gain':
                        other['results']['same300-epoch1']['joint_gain_percentage_points'] = 20
                        validate_primary_summary(other, value)
                    elif change == 'wrong-decision':
                        other_decision['selected'] = 'expanded600-epoch1'
                        verify_primary_decision(other, other_meta, other_decision, 'bound-summary')
                    else:
                        verify_primary_decision(other, other_meta, other_decision, 'changed-summary')
        value['pending_experiments'] = [{'name':'expanded600'}]
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            validate_primary_summary(summary, value)

    def test_reused_training_preserves_source_context_and_rejects_changed_config_or_index(self):
        value = plan()
        experiment = value['experiments'][0]
        config = experiment['config']
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            full = root / 'source/full'
            index = {'checkpoint-38':{'resume_record_sha256':'checkpoint'}}
            identity = dict(config=config, model=e.MODEL, revision=e.REVISION, helper_sha256='helper',
                            context={'plan_sha256':'original-plan'}, data_sha256=config['data_sha256'],
                            manifest_sha256=config['manifest_sha256'])
            record = dict(status='training_completed', identity=identity, checkpoint_index=index,
                          epoch_checkpoint_reloads={'checkpoint-38':{'save_reload_weights_equal':True,'inference_verified':True}},
                          final_reload={'save_reload_weights_equal':True,'inference_verified':True},
                          training_memory={'headroom_passed':True}, memory_including_reload={'headroom_passed':True})
            write(full / 'run-record.json', record)
            write(full / 'checkpoint-index.json', index)
            binding = dict(path='../source/full', run_record_sha256=e.sha(full / 'run-record.json'),
                           checkpoint_index_sha256=e.sha(full / 'checkpoint-index.json'), source_plan_sha256='original-plan')
            with patch.object(x.training, 'verify_epoch_checkpoints', return_value={'checkpoint-38':{}}):
                self.assertEqual(x.verify_reused_training(root / 'new-output', binding, experiment, value)[0], full.resolve())
                self.assertEqual(json.loads((full / 'run-record.json').read_text())['identity']['context']['plan_sha256'], 'original-plan')
                with self.assertRaisesRegex(ValueError, 'identity/configuration'):
                    x.verify_reused_training(root / 'new-output', dict(binding, source_plan_sha256='new-plan'), experiment, value)
                write(full / 'checkpoint-index.json', {})
                with self.assertRaisesRegex(ValueError, 'index changed'):
                    x.verify_reused_training(root / 'new-output', binding, experiment, value)

    def test_executor_reuses_bound_same300_and_current_then_trains_only600(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output, source = root / 'output002', root / 'source001'
            value = plan()
            old_record = dict(status='training_completed', identity={'config':value['experiments'][0]['config']},
                              checkpoint_index={f'checkpoint-{step}':{'resume_record_sha256':f'old-{step}'} for step in (38,76,114)})
            value['reuse_training'] = {'same300':{'path':'../source001/full'}}
            value['reuse_evaluations'] = {}
            for label, record_sha in [('current',value['current_adapter_record_sha256']), *[(f'same300-epoch{epoch}',f'old-{epoch * 38}') for epoch in (1,2,3)]]:
                path = source / 'evaluation' / label
                generation(path, record_sha)
                value['reuse_evaluations'][label] = dict(path=str(path), manifest_sha256=e.sha(path / 'manifest.json'))
            before = {str(path):e.sha(path) for path in source.rglob('*') if path.is_file()}
            write(root / 'plan.json', value)
            def train(*args, **kwargs):
                config, full = args[3], args[4]
                self.assertEqual(config.train_examples, 600)
                return dict(status='training_completed', identity={'config':asdict(config)},
                    checkpoint_index={f'checkpoint-{step}':{'resume_record_sha256':f'new-{step}'} for step in (75,150,225)})
            def generate(*args, **kwargs):
                generation(args[5], args[4], args[6] if len(args) > 6 else 0)
            with patch.object(x, 'check_plan'), patch.object(e, 'frozen', return_value=cases()), \
                 patch.object(x.training, 'cuda_environment', return_value=environment()), \
                 patch.object(x, 'verify_reused_training', return_value=(source / 'full', old_record)), \
                 patch.object(e, 'prepare_model_snapshot'), patch('transformers.AutoTokenizer.from_pretrained', return_value=Mock()), \
                 patch.object(x.training, 'verify_data', return_value=([], {})), patch.object(x.training, 'tokenize_rows', return_value=[]), \
                 patch.object(x.training, 'verify_collator', return_value={}), \
                 patch.object(x.training, 'smoke_test', return_value={'passed':True,'headroom_passed':True}) as smoke, \
                 patch.object(x.training, 'full_train', side_effect=train) as full_train, \
                 patch.object(x.training, 'verify_epoch_checkpoints'), patch.object(x.training, 'verify_replay_checkpoint'), \
                 patch.object(e, 'generate', side_effect=generate) as generated:
                status = x.run(root / 'plan.json', output, 'unused-current-adapter')
            self.assertTrue(status['study_complete'])
            self.assertEqual(len(status['results']), 7)
            self.assertEqual(full_train.call_count, 1)
            self.assertEqual(smoke.call_count, 1)
            self.assertEqual(generated.call_count, 3)
            self.assertEqual(before, {str(path):e.sha(path) for path in source.rglob('*') if path.is_file()})
            self.assertFalse((output / 'same300').exists())

    def test_executor_without_reuse_runs_both_fresh_and_evaluates_all_seven_variants(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            value = plan()
            write(root / 'plan.json', value)
            trained = []
            def train(*args, **kwargs):
                config = args[3]
                trained.append(config.train_examples)
                steps = (config.train_examples + 7) // 8
                return dict(status='training_completed', identity={'config':asdict(config)},
                    checkpoint_index={f'checkpoint-{epoch * steps}':{'resume_record_sha256':f'{config.train_examples}-{epoch}'} for epoch in (1,2,3)})
            def generate(*args, **kwargs):
                generation(args[5], args[4], args[6] if len(args) > 6 else 0)
            with patch.object(x, 'check_plan'), patch.object(e, 'frozen', return_value=cases()), \
                 patch.object(x.training, 'cuda_environment', return_value=environment()), \
                 patch.object(e, 'prepare_model_snapshot'), patch('transformers.AutoTokenizer.from_pretrained', return_value=Mock()), \
                 patch.object(x.training, 'verify_data', return_value=([], {})), patch.object(x.training, 'tokenize_rows', return_value=[]), \
                 patch.object(x.training, 'verify_collator', return_value={}), \
                 patch.object(x.training, 'smoke_test', return_value={'passed':True,'headroom_passed':True}) as smoke, \
                 patch.object(x.training, 'full_train', side_effect=train), \
                 patch.object(x.training, 'verify_epoch_checkpoints'), patch.object(x.training, 'verify_replay_checkpoint'), \
                 patch.object(e, 'generate', side_effect=generate) as generated:
                status = x.run(root / 'plan.json', root / 'output', 'unused-current-adapter')
            self.assertEqual(trained, [300, 600])
            self.assertEqual(smoke.call_count, 2)
            self.assertEqual(generated.call_count, 7)
            self.assertTrue(status['study_complete'])
            self.assertEqual(set(status['results']), {'current', *study_checkpoint_metadata(value)})

    def test_repeat_continuation_keeps_completed_generations_and_checks_environment_before_gpu(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / 'output'
            output.mkdir()
            value = plan()
            summary = primary_summary(value)
            summary['candidate_record_hashes']['current'] = value['current_adapter_record_sha256']
            metadata = study_checkpoint_metadata(value)
            write(root / 'plan.json', value)
            write(root / 'summary.json', summary)
            decision = dict(choose(summary, metadata), primary_summary_sha256=e.sha(root / 'summary.json'))
            write(root / 'decision.json', decision)
            write(output / 'environment.json', environment())
            selected = decision['selected']
            record = {'checkpoint_index':{'checkpoint-38':{'resume_record_sha256':summary['candidate_record_hashes'][selected]}}}
            successful = []
            fail_once = [True]
            def generate(*args, **kwargs):
                destination, offset = Path(args[5]), args[6]
                if offset == 1000003 and destination.name == selected and fail_once[0]:
                    fail_once[0] = False
                    raise RuntimeError('Mechanical interruption between completed generations')
                generation(destination, args[4], offset)
                successful.append((destination.name, offset))
            with patch.object(r, 'HERE', root), patch.object(x, 'check_plan'), \
                 patch.object(r, 'validate_primary_execution', return_value=(cases(), {'same300':(root / 'source-full', record)})), \
                 patch.object(x.training, 'cuda_environment', return_value=environment()), \
                 patch.object(e, 'verify_adapter'), patch.object(e, 'prepare_model_snapshot'), \
                 patch.object(e, 'frozen', return_value=cases()), patch.object(e, 'generate', side_effect=generate):
                with self.assertRaisesRegex(RuntimeError, 'Mechanical interruption'):
                    r.run(output, 'unused-current', root / 'summary.json', root / 'decision.json')
                r.run(output, 'unused-current', root / 'summary.json', root / 'decision.json')
                r.run(output, 'unused-current', root / 'summary.json', root / 'decision.json')
                self.assertEqual(len(successful), 4)
                self.assertEqual(set(successful), {(label,offset) for label in ('current',selected) for offset in (1000003,2000003)})
                changed = environment()
                changed['packages'] = dict(changed['packages'], torch='different')
                with patch.object(x.training, 'cuda_environment', return_value=changed), \
                     patch.object(e, 'generate') as never:
                    with self.assertRaisesRegex(ValueError, 'environment changed'):
                        r.run(output, 'unused-current', root / 'summary.json', root / 'decision.json')
                    never.assert_not_called()


if __name__ == '__main__':
    unittest.main()
