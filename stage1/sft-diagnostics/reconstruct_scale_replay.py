"""Reconstruct the failed first LoRA accumulation group; never update model weights.

Run after installing the notebook dependencies and mounting Drive:
  python reconstruct_scale_replay.py --kit /content/reading-sft-colab-v2 \
      --output /content/drive/MyDrive/Reading-Model/sft/<fresh-name>/scale-replay \
      --reference-smoke-report /.../prior-passing-run/smoke/smoke-report.json

Alternatively import this file and call run_replay(kit_dir, output_dir, reference_smoke_report).
This diagnostic loads a fresh pinned base and fresh adapters. It has no dependency on
an old Trainer, exception traceback, optimizer checkpoint, or previous live runtime.
"""
import argparse
import gc
import importlib.util
import json
from pathlib import Path
import sys

FAILED_ROW_IDS = ('pilot-043', 'pilot-062', 'pilot-287', 'pilot-161',
                  'pilot-031', 'pilot-266', 'pilot-173', 'pilot-206')
SCALES = (65536.0, 1024.0, 256.0)
EXPECTED_HELPER_SHA256 = '31fd122e1f4b4a6f3a4169a3f0a0265ba89b23b704943919e2cf7adc02a7c96f'


def load_helper(kit_dir):
    """Import the exact supplied kit helper, regardless of notebook import caches."""
    helper = Path(kit_dir).resolve() / 'sft_train.py'
    import hashlib
    actual = hashlib.sha256(helper.read_bytes()).hexdigest()
    if actual != EXPECTED_HELPER_SHA256:
        raise ValueError(f'Unexpected diagnostic helper bytes: {actual}')
    spec = importlib.util.spec_from_file_location('_sft_replay_training', helper)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def trial_replay(model, batches, parameters, optimizer, initial_scale, seed, training):
    """Accumulate exactly eight forwards/backwards; unscale for inspection only."""
    import torch
    from transformers import set_seed
    model.zero_grad(set_to_none=True)
    set_seed(seed)  # Identical dropout/RNG stream for every scale trial.
    model.train()
    fingerprint_before = training.adapter_fingerprint(model)
    scaler = torch.amp.GradScaler('cuda', init_scale=initial_scale)
    target_tokens = sum(int((batch['labels'] != -100).sum()) for batch in batches)
    result = {'initial_scale': initial_scale, 'microbatch_losses': [],
              'supervised_tokens': target_tokens, 'optimizer_steps': 0,
              'adapter_fingerprint_before': fingerprint_before}
    for cpu_batch in batches:
        gpu_batch = {name: tensor.to('cuda:0') for name, tensor in cpu_batch.items()}
        with torch.autocast('cuda', dtype=torch.float16):
            # Same single-GPU Qwen/Trainer normalization: sum CE / all group target tokens.
            # Accelerator accumulation was 1 in the failed Trainer; do not divide by 8 again.
            outputs = model(**gpu_batch, num_items_in_batch=target_tokens)
            loss = outputs.loss
        if not torch.isfinite(loss).item():
            raise ValueError(f'Nonfinite diagnostic forward at scale {initial_scale}')
        result['microbatch_losses'].append(float(loss.detach()))
        scaler.scale(loss).backward()
        del gpu_batch, outputs, loss
    grads = [parameter.grad for parameter in parameters if parameter.grad is not None]
    result['scaled_nonfinite_elements'] = sum(int((~torch.isfinite(grad)).sum()) for grad in grads)
    # SGD is used only to supply the public unscale_ API's parameter collection.
    # Neither optimizer.step, scaler.step, nor scaler.update is called anywhere.
    scaler.unscale_(optimizer)
    result['unscaled_nonfinite_elements'] = sum(int((~torch.isfinite(grad)).sum()) for grad in grads)
    result['all_grads_present'] = len(grads) == len(parameters)
    result['gradient_tensor_count'] = len(grads)
    result['nonfinite_gradient_tensor_count'] = sum(not torch.isfinite(grad).all().item() for grad in grads)
    result['any_nonzero_gradient'] = any(torch.count_nonzero(grad).item() for grad in grads)
    result['finite_unscaled_norm'] = (float(torch.linalg.vector_norm(torch.stack([
        torch.linalg.vector_norm(grad.detach().double()) for grad in grads])))
        if result['unscaled_nonfinite_elements'] == 0 else None)
    result['adapter_fingerprint_after'] = training.adapter_fingerprint(model)
    result['adapter_fingerprint_unchanged'] = result['adapter_fingerprint_after'] == fingerprint_before
    if not result['adapter_fingerprint_unchanged']:
        raise ValueError('Diagnostic unexpectedly changed adapter weights')
    return result


def run_replay(kit_dir, output_dir, reference_smoke_report=None):
    import torch
    from transformers import AutoTokenizer
    training = load_helper(kit_dir)
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise ValueError('Use a fresh diagnostic output directory; preserve previous evidence')
    output_dir.mkdir(parents=True)
    report_path = output_dir / 'fp16-scale-replay.json'
    config = training.TrainConfig(mode='lora')
    report = {'status': 'started', 'diagnostic_only': True,
              'purpose': 'fresh-identical-weights/same-failed-eight-rows no-update FP16 scale comparison',
              'failed_run_evidence': {'global_step': 0, 'scale': 65536.0, 'found_inf': 1,
                  'finite_accumulated_forward_loss': 7.057, 'nonfinite_gradient_tensor_count': 392},
              'row_ids': list(FAILED_ROW_IDS), 'scales': list(SCALES),
              'config': training.asdict(config), 'helper_sha256': training.sha256(training.__file__),
              'optimizer_steps_total': 0, 'trials': []}
    training.write_json(report_path, report)
    model = optimizer = parameters = None
    try:
        environment = training.cuda_environment(config.mode)
        report['environment'] = environment
        if environment['compute_dtype'] != 'float16' or training.native_bf16_supported():
            raise ValueError('This comparison requires a GPU selecting native FP16, matching the failed T4 run')
        data_dir = Path(kit_dir) / 'data'
        rows, manifest = training.verify_data(data_dir)
        tokenizer = AutoTokenizer.from_pretrained(training.MODEL_ID, revision=training.REVISION)
        tokenizer.padding_side = 'right'
        features = training.tokenize_rows(rows, tokenizer, max_length=config.max_length)
        collator = training.CompletionCollator(tokenizer.pad_token_id, max_length=config.max_length)
        report['mask_report'] = training.verify_collator(features, collator, tokenizer)
        report['identity'] = training.run_identity(config, tokenizer)
        lookup = {feature['id']: feature for feature in features}
        selected = [lookup[feature_id] for feature_id in FAILED_ROW_IDS]
        batches = [collator([feature]) for feature in selected]
        report['sequence_lengths'] = [len(feature['input_ids']) for feature in selected]
        report['supervised_tokens'] = sum(int((batch['labels'] != -100).sum()) for batch in batches)
        report['normalization'] = 'sum CE per microbatch / total supervised tokens in all 8 microbatches; no additional division'
        model = training.load_model(config)
        model.train()
        report['parameter_checks'] = training.check_trainable(model)
        initial_fingerprint = training.adapter_fingerprint(model)
        report['initial_adapter_fingerprint'] = initial_fingerprint
        if reference_smoke_report is not None:
            reference_path = Path(reference_smoke_report)
            reference = json.loads(reference_path.read_text())
            if not reference.get('passed') or reference['mode'] != 'lora':
                raise ValueError('Reference must be the prior passing ordinary-LoRA smoke report')
            if reference['identity']['config'] != training.asdict(config):
                raise ValueError('Reference smoke configuration differs from failed full-run configuration')
            if reference['initial_adapter_fingerprint'] != initial_fingerprint:
                raise ValueError('Fresh adapters differ from the prior pre-smoke/full initialization')
            report['reference_smoke'] = {'path': str(reference_path), 'sha256': training.sha256(reference_path),
                                       'fresh_initial_fingerprint_matches': True}
        parameters = [parameter for parameter in model.parameters() if parameter.requires_grad]
        optimizer = torch.optim.SGD(parameters, lr=1.0)
        training.write_json(report_path, report)
        for scale in SCALES:
            trial = trial_replay(model, batches, parameters, optimizer, scale, config.seed, training)
            if trial['adapter_fingerprint_before'] != initial_fingerprint:
                raise ValueError('Scale trials did not start from identical adapter weights')
            report['trials'].append(trial)
            training.write_json(report_path, report)
            print(json.dumps(trial, indent=2), flush=True)
        report.update(status='completed', final_adapter_fingerprint=training.adapter_fingerprint(model))
        report['all_trials_same_weights'] = report['final_adapter_fingerprint'] == initial_fingerprint
        report['observed_high_scale_overflow_and_lower_scale_finite'] = (
            report['trials'][0]['unscaled_nonfinite_elements'] > 0 and any(
                trial['unscaled_nonfinite_elements'] == 0 and trial['any_nonzero_gradient']
                for trial in report['trials'][1:]))
        training.write_json(report_path, report)
        return report
    except Exception as error:
        report.update(status='failed', error_type=type(error).__name__, error=str(error))
        training.write_json(report_path, report)
        raise
    finally:
        if model is not None:
            model.zero_grad(set_to_none=True)
        del model, optimizer, parameters
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kit', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--reference-smoke-report')
    args = parser.parse_args()
    result = run_replay(args.kit, args.output, args.reference_smoke_report)
    print(json.dumps({key: result[key] for key in ('status', 'optimizer_steps_total',
        'all_trials_same_weights', 'observed_high_scale_overflow_and_lower_scale_finite')}, indent=2))


if __name__ == '__main__':
    main()
