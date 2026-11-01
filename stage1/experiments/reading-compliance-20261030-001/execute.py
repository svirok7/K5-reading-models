"""Execute exactly two planned fresh LoRA runs on an existing free Colab T4.

No automatic hardware/precision changes, purchases, or live UI changes.
Explicit resume accepts only hash-bound epoch checkpoints in the same run.
"""
import argparse
import json
import os
from pathlib import Path
import sys

# Must precede torch import. Never repair an already imported allocator silently.
ALLOCATOR = 'expandable_segments:True'
if 'torch' in sys.modules and os.environ.get('PYTORCH_CUDA_ALLOC_CONF') != ALLOCATOR:
    raise RuntimeError('Restart runtime: allocator must be set before importing torch')
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = ALLOCATOR
HERE = Path(__file__).resolve().parent
STAGE = HERE.parents[1]
sys.path.insert(0, str(STAGE))
import sft_train as training
import evaluate


def check_plan(plan):
    if plan['helper_sha256'] != training.sha256(STAGE/'sft_train.py'):
        raise ValueError('Training helper differs from sealed experiment')
    for name, expected in plan['code_files'].items():
        if Path(name).is_absolute() or '..' in Path(name).parts or training.sha256(STAGE/name) != expected:
            raise ValueError('Execution code differs: ' + name)
    evaluate.frozen(HERE/'frozen', plan['frozen_manifest_sha256'])
    if plan['model'] != training.MODEL_ID or plan['revision'] != training.REVISION:
        raise ValueError('Wrong pinned base')


def completed_evaluation(path, plan, record_sha, offset):
    if not path.exists():
        return False
    record = json.loads((path/'manifest.json').read_text())
    if record['status'] != 'completed' or record['adapter_record_sha256'] != record_sha or record['frozen_manifest_sha256'] != plan['frozen_manifest_sha256'] or record['seed_offset'] != offset or record['responses_sha256'] != evaluate.sha(path/'responses.jsonl'):
        raise ValueError('Existing result incomplete/incompatible; preserve it and choose fresh experiment output')
    return True


def run(plan_path, output, current_adapter, resume=None, only=None):
    if resume is not None and only is None:
        raise ValueError('Explicit resume requires --only for its matching experiment')
    plan_path, output = Path(plan_path), Path(output)
    plan = json.loads(plan_path.read_text())
    check_plan(plan)
    output.mkdir(parents=True, exist_ok=True)
    plan_sha = training.sha256(plan_path)
    status_path = output/'execution-status.json'
    if status_path.exists():
        status = json.loads(status_path.read_text())
        if status['plan_sha256'] != plan_sha:
            raise ValueError('Existing execution belongs to a different sealed plan')
    else:
        status = dict(plan_sha256=plan_sha, status='preparing', completed_runs=[], results={})
    training.write_json(status_path,status)
    try:
        environment = training.cuda_environment('lora')
        if 'T4' not in environment['gpu'] or environment['compute_dtype'] != 'float16':
            raise ValueError('Use existing T4 / float16 group; no silent precision or hardware substitution')
        if (output/'environment.json').exists():
            original_environment = json.loads((output/'environment.json').read_text())
            for field in ('packages','gpu','compute_dtype','allocator_config'):
                if original_environment[field] != environment[field]:
                    raise ValueError('Execution environment changed: ' + field)
        else:
            training.write_json(output/'environment.json',environment)
        status.setdefault('invocations',[]).append(dict(environment=environment,only=only,resume=str(resume) if resume else None))
        training.write_json(status_path,status)
        current_record = HERE/'current-adapter-record.json'
        record_sha = plan['current_adapter_record_sha256']
        reference_out = output/'evaluation'/'current'
        reference_out.parent.mkdir(exist_ok=True)
        if not completed_evaluation(reference_out,plan,record_sha,0):
            evaluate.generate(HERE/'frozen',plan['frozen_manifest_sha256'],current_adapter,current_record,record_sha,reference_out,expected_model_artifacts=plan['prepared_model_artifacts'])
        status['results']['current'] = str(reference_out)
        training.write_json(status_path,status)
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(training.MODEL_ID,revision=training.REVISION)
        tokenizer.padding_side = 'right'
        for experiment in plan['experiments']:
            name = experiment['name']
            if only and name != only:
                continue
            config = training.TrainConfig(**experiment['config'])
            data, manifest = training.verify_data(STAGE/experiment['dataset'],config)
            features = training.tokenize_rows(data,tokenizer,config.max_length)
            collator = training.CompletionCollator(tokenizer.pad_token_id,config.max_length)
            context = dict(plan_sha256=plan_sha, frozen_manifest_sha256=plan['frozen_manifest_sha256'], allocator_config=ALLOCATOR,
                comparison='current SFT adapter; no new base-model run', lr_policy='linear decay across all three epochs')
            directory = output/name
            directory.mkdir(exist_ok=True)
            training.write_json(directory/'actual-collator-report.json',training.verify_collator(features,collator,tokenizer,expected_count=config.train_examples))
            smoke_path = directory/'smoke'/'smoke-report.json'
            if smoke_path.exists():
                smoke = json.loads(smoke_path.read_text())
                if smoke.get('identity') != training.run_identity(config,tokenizer,context) or not smoke.get('passed'):
                    raise ValueError('Existing smoke incompatible/failed; preserve diagnostics and stop')
            else:
                smoke = training.smoke_test(features,collator,tokenizer,config,directory/'smoke',context)
            if not smoke.get('passed') or not smoke.get('headroom_passed'):
                raise ValueError('Stop: smoke/numerical/15% memory gate failed')
            full = directory/'full'
            if (full/'run-record.json').exists():
                record = json.loads((full/'run-record.json').read_text())
                if record['identity'] != training.run_identity(config,tokenizer,context):
                    raise ValueError('Full run identity changed')
                if record['status'] != 'training_completed':
                    if resume is None:
                        raise ValueError('Interrupted run requires explicit exact epoch checkpoint; never restart automatically')
                    record = training.full_train(features,collator,tokenizer,config,full,smoke,manifest,context,resume)
                elif resume is not None:
                    raise ValueError('Cannot resume completed run')
            else:
                if resume is not None:
                    raise ValueError('Resume requires its existing full run')
                record = training.full_train(features,collator,tokenizer,config,full,smoke,manifest,context)
            if record['status'] != 'training_completed':
                raise ValueError('Training did not pass final integrity checks')
            for epoch in range(1,config.epochs+1):
                step = epoch * ((config.train_examples+7)//8)
                checkpoint = full/'checkpoints'/f'checkpoint-{step}'
                checkpoint_record = checkpoint/'resume-record.json'
                # External checkpoint-index binding is checked by helper, not self-approved here.
                index = json.loads((full/'checkpoint-index.json').read_text())
                entries = index.get('checkpoints', index)
                if isinstance(entries,list):
                    entry = next(e for e in entries if e['global_step'] == step)
                else:
                    entry = entries[str(step)] if str(step) in entries else entries[checkpoint.name]
                expected = entry['resume_record_sha256'] if isinstance(entry,dict) else entry
                training.verify_replay_checkpoint(checkpoint,expected)
                label = f'{name}-epoch{epoch}'
                result_out = output/'evaluation'/label
                if not completed_evaluation(result_out,plan,expected,0):
                    evaluate.generate(HERE/'frozen',plan['frozen_manifest_sha256'],checkpoint,checkpoint_record,expected,result_out,expected_model_artifacts=plan['prepared_model_artifacts'])
                status['results'][label] = str(result_out)
                training.write_json(status_path,status)
            if name not in status['completed_runs']:
                status['completed_runs'].append(name)
            training.write_json(status_path,status)
        status['status'] = 'generations_complete_pending_blind_review'
        training.write_json(output/'review-runs.json',status['results'])
        return status
    except Exception as exc:
        status.update(status='stopped',error_type=type(exc).__name__,error=str(exc))
        raise
    finally:
        training.write_json(status_path,status)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',type=Path,default=HERE/'plan.json')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--current-adapter',type=Path,required=True)
    parser.add_argument('--resume',type=Path)
    parser.add_argument('--only',choices=('same300','expanded600'))
    args = parser.parse_args()
    run(args.plan,args.output,args.current_adapter,args.resume,args.only)
