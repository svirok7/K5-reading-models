# Requires read-only traceback diagnostic to have recovered trainer_diag/model_diag.
# Diagnostic only: no optimizer step; full production training must start fresh later.
import torch, json, math
from transformers import set_seed
assert trainer_diag.state.global_step == 0, 'Only replay the failed fresh initialization'
assert trainer_diag.model_accepts_loss_kwargs, 'Unexpected loss API: stop and diagnose normalization'
assert trainer_diag.accelerator.gradient_accumulation_steps == 1, 'Unexpected Accelerator accumulation'
assert not training.native_bf16_supported(), 'This diagnostic is for native-FP16 GPUs'
replay_ids = list(trainer_diag.actual_batch_ids)
assert len(replay_ids) == config.gradient_accumulation == 8, replay_ids
lookup = {feature['id']: feature for feature in features}
replay_features = [lookup[feature_id] for feature_id in replay_ids]
cpu_batches = [collator([feature]) for feature in replay_features]
total_target_tokens = sum(int((batch['labels'] != -100).sum()) for batch in cpu_batches)
replay_report = {'purpose': 'same-initial-weights/same-eight-rows no-optimizer-step FP16 scale comparison',
    'row_ids': replay_ids, 'supervised_tokens': total_target_tokens,
    'global_step_before': trainer_diag.state.global_step,
    'model_accepts_loss_kwargs': trainer_diag.model_accepts_loss_kwargs,
    'accelerator_gradient_accumulation_steps': trainer_diag.accelerator.gradient_accumulation_steps,
    'initial_adapter_fingerprint': training.adapter_fingerprint(model_diag), 'trials': []}
parameters = [parameter for parameter in model_diag.parameters() if parameter.requires_grad]
replay_optimizer = torch.optim.SGD(parameters, lr=1.0)  # Used ONLY by public unscale_; never stepped.
model_diag.train()
for initial_scale in (65536.0, 1024.0, 256.0):
    model_diag.zero_grad(set_to_none=True)
    set_seed(config.seed)  # Identical dropout/RNG across scale trials.
    replay_scaler = torch.amp.GradScaler('cuda', init_scale=initial_scale)
    trial = {'initial_scale': initial_scale, 'microbatch_losses': [], 'optimizer_steps': 0}
    for cpu_batch in cpu_batches:
        gpu_batch = {name: tensor.to('cuda:0') for name, tensor in cpu_batch.items()}
        with torch.autocast('cuda', dtype=torch.float16):
            # Same Qwen loss normalization as pinned Trainer: SUM CE / group's target-token count.
            outputs = model_diag(**gpu_batch, num_items_in_batch=total_target_tokens)
            replay_loss = outputs.loss
        assert torch.isfinite(replay_loss).item(), 'Replay forward loss is nonfinite'
        trial['microbatch_losses'].append(float(replay_loss.detach()))
        replay_scaler.scale(replay_loss).backward()
        del gpu_batch, outputs, replay_loss
    scaled_grads = [parameter.grad for parameter in parameters if parameter.grad is not None]
    trial['scaled_nonfinite_elements'] = sum(int((~torch.isfinite(grad)).sum()) for grad in scaled_grads)
    replay_scaler.unscale_(replay_optimizer)  # No clipping, optimizer.step or scaler.step/update.
    unscaled_grads = [parameter.grad for parameter in parameters if parameter.grad is not None]
    trial['unscaled_nonfinite_elements'] = sum(int((~torch.isfinite(grad)).sum()) for grad in unscaled_grads)
    trial['all_grads_present'] = len(unscaled_grads) == len(parameters)
    trial['any_nonzero_gradient'] = any(torch.count_nonzero(grad).item() for grad in unscaled_grads)
    trial['finite_unscaled_norm'] = float(torch.linalg.vector_norm(torch.stack([
        torch.linalg.vector_norm(grad.detach().double()) for grad in unscaled_grads]))) if trial['unscaled_nonfinite_elements'] == 0 else None
    trial['adapter_fingerprint_unchanged'] = training.adapter_fingerprint(model_diag) == replay_report['initial_adapter_fingerprint']
    assert trial['adapter_fingerprint_unchanged'], 'Diagnostic unexpectedly changed adapter weights'
    replay_report['trials'].append(trial)
    training.write_json(EXPERIMENT / 'full' / 'fp16-scale-replay.json', replay_report)
    print(json.dumps(trial, indent=2))
    del scaled_grads, unscaled_grads, replay_scaler
model_diag.zero_grad(set_to_none=True)
replay_report['global_step_after'] = trainer_diag.state.global_step
replay_report['optimizer_steps_total'] = 0
training.write_json(EXPERIMENT / 'full' / 'fp16-scale-replay.json', replay_report)
print('Saved no-update replay:', EXPERIMENT / 'full' / 'fp16-scale-replay.json')
# Preserve failed run/replay evidence. Do not reuse these live models for final training.
