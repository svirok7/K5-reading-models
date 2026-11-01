# Run immediately after the failed full_train cell, before clearing exception state.
import sys, json, math
import torch
trace = getattr(sys, 'last_traceback', None)
if trace is None:
    trace = getattr(getattr(sys, 'last_exc', None), '__traceback__', None)
assert trace is not None, 'No saved exception traceback; do not restart until diagnostics are recovered'
frames = []
while trace is not None:
    frames.append(trace.tb_frame)
    trace = trace.tb_next
trainer_diag = next((frame.f_locals['self'] for frame in reversed(frames)
    if 'self' in frame.f_locals and hasattr(frame.f_locals['self'], 'accelerator')
    and hasattr(frame.f_locals['self'], 'state')), None)
assert trainer_diag is not None, 'Trainer frame not found'
model_diag = trainer_diag.model
scaler_diag = trainer_diag.accelerator.scaler

def finite_scalar(value):
    if torch.is_tensor(value):
        if value.numel() != 1:
            return {'shape': list(value.shape)}
        value = value.detach().float().cpu().item()
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    return value

stats = []
for name, parameter in model_diag.named_parameters():
    if not parameter.requires_grad:
        continue
    grad = parameter.grad
    row = {'name': name, 'parameter_dtype': str(parameter.dtype), 'has_grad': grad is not None}
    if grad is not None:
        finite = torch.isfinite(grad)
        row.update(gradient_dtype=str(grad.dtype), elements=grad.numel(),
                   finite_elements=int(finite.sum()), nan_elements=int(torch.isnan(grad).sum()),
                   inf_elements=int(torch.isinf(grad).sum()),
                   finite_abs_max=float(grad[finite].abs().max()) if finite.any() else None)
    stats.append(row)
inner = next((frame for frame in frames if frame.f_code.co_name == '_inner_training_loop'), None)
loop_state = {name: finite_scalar(inner.f_locals[name]) for name in
              ('grad_norm', '_grad_norm', 'tr_loss', 'tr_loss_step', 'step', 'epoch', 'total_batched_samples')
              if inner is not None and name in inner.f_locals}
found_inf = []
if scaler_diag is not None:
    for state in getattr(scaler_diag, '_per_optimizer_states', {}).values():
        found_inf.append({'stage': str(state.get('stage')),
                          'found_inf_per_device': {str(device): finite_scalar(value)
                          for device, value in state.get('found_inf_per_device', {}).items()}})
diagnostic = {'global_step': trainer_diag.state.global_step,
    'mode': config.mode, 'scaler_enabled': scaler_diag.is_enabled() if scaler_diag is not None else False,
    'scaler_state': scaler_diag.state_dict() if scaler_diag is not None else None,
    'scaler_found_inf_readonly_diagnostics': found_inf, 'loop_state': loop_state,
    'actual_batch_ids': getattr(trainer_diag, 'actual_batch_ids', []),
    'parameter_gradient_stats': stats,
    'finite_gradient_tensor_count': sum(row.get('finite_elements') == row.get('elements') for row in stats if row['has_grad']),
    'nonfinite_gradient_tensor_count': sum(row.get('finite_elements') != row.get('elements') for row in stats if row['has_grad']),
    'traceback_functions': [frame.f_code.co_name for frame in frames]}
training.write_json(EXPERIMENT / 'full' / 'gradient-failure-diagnostic.json', diagnostic)
print(json.dumps(diagnostic, indent=2))
# Keep frames/trainer_diag/model_diag until any controlled diagnostic backward is complete.
