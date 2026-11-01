"""Qwen SFT notebook helpers. Importing this module never loads/trains a model."""
from dataclasses import asdict, dataclass
import gc
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform

MODEL_ID = 'Qwen/Qwen3-1.7B'
REVISION = '70d244cc86ccca08cf5af4e1e306ecf908b1ad5e'
SFT_SHA256 = '42aea06f60ce82af7e276440c3318220efa751cc4fd3c111208176366bb419b3'
MANIFEST_SHA256 = '40d27ee7931fff21c9312a5820d5923d5ddf9cca6998482965abd13a078f4aa3'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    temp.replace(path)


@dataclass(frozen=True)
class TrainConfig:
    mode: str = 'lora'
    seed: int = 42
    max_length: int = 2048
    rank: int = 16
    alpha: int = 32
    dropout: float = 0.05
    learning_rate: float = 1e-4
    epochs: int = 1
    dataset_version: str = 'sft-300-v2'
    data_sha256: str = SFT_SHA256
    manifest_sha256: str = MANIFEST_SHA256
    train_examples: int = 300
    microbatch: int = 1
    gradient_accumulation: int = 8
    fp16_initial_scale: float = 1024.0

    def __post_init__(self):
        require(self.mode in ('lora', 'qlora'), 'Select lora or qlora explicitly')
        require(type(self.epochs) is int and self.epochs > 0, 'Epochs must be a positive integer')
        require(self.seed == 42 and self.max_length == 2048 and self.rank == 16
                and self.alpha == 32 and self.dropout == 0.05 and self.learning_rate == 1e-4,
                'Keep the fixed seed42 / length2048 / r16 / alpha32 / dropout0.05 / LR1e-4 experiment')
        require(self.train_examples in (300, 600), 'Only the baseline300 or approved successor600 is supported')
        for digest in (self.data_sha256, self.manifest_sha256):
            require(isinstance(digest, str) and len(digest) == 64
                    and all(c in '0123456789abcdef' for c in digest), 'Dataset bindings require SHA256 digests')
        if self.train_examples == 300:
            require((self.dataset_version, self.data_sha256, self.manifest_sha256) ==
                    ('sft-300-v2', SFT_SHA256, MANIFEST_SHA256), 'Baseline dataset binding differs')
        else:
            require(self.dataset_version != 'sft-300-v2' and self.data_sha256 != SFT_SHA256
                    and self.manifest_sha256 != MANIFEST_SHA256, 'Successor requires explicit immutable dataset bindings')
        require(isinstance(self.fp16_initial_scale, (int, float))
                and not isinstance(self.fp16_initial_scale, bool)
                and math.isfinite(self.fp16_initial_scale) and self.fp16_initial_scale > 0,
                'FP16 initial scale must be finite and positive')
        require(self.microbatch == 1 and self.gradient_accumulation == 8,
                'Initial experiment requires microbatch 1 / accumulation 8')


def verify_data(directory, config=None):
    """Only explicit experiment-plan hashes authorize data; a manifest cannot approve itself."""
    config = config or TrainConfig()
    directory = Path(directory)
    require(sha256(directory / 'manifest.json') == config.manifest_sha256, 'Unapproved manifest bytes')
    manifest = json.loads((directory / 'manifest.json').read_text())
    require(sha256(directory / 'sft.jsonl') == config.data_sha256 == manifest['artifacts']['sft.jsonl'], 'Unapproved SFT bytes')
    require(manifest['version'] == config.dataset_version and manifest['count'] == config.train_examples,
            'Wrong dataset version/count')
    require(manifest.get('frozen_data') is True, 'Dataset must be immutable')
    audit = manifest['audit']
    require(manifest['audit_status'] == 'independently_reviewed_pending_human'
            and audit['pass'] == config.train_examples and audit['open_findings'] == 0
            and audit['sft_sha256'] == config.data_sha256, 'Independent model approval missing')
    data = [json.loads(line) for line in (directory / 'sft.jsonl').read_text().splitlines()]
    require(len(data) == config.train_examples, 'Expected every manifest-bound training example')
    for row in data:
        require(set(row) == {'prompt', 'completion'}, 'Only prompt/completion may enter SFT')
    return data, manifest


def tokenize_rows(data, tokenizer, max_length=2048):
    """Construct actual labels from the exact inference prefix, never all-assistant masks."""
    require(max_length > 0, 'max_length must be positive')
    result = []
    for index, row in enumerate(data):
        require(set(row) == {'prompt', 'completion'}, 'Unexpected training fields')
        prompt, completion = row['prompt'], row['completion']
        require(len(completion) == 1 and completion[0]['role'] == 'assistant', 'One final assistant target required')
        require(prompt[0]['role'] == 'system' and prompt[-1]['role'] == 'user', 'Prompt must begin with system/end with user')
        target = completion[0]['content']
        require(isinstance(target, str) and bool(target.strip()), 'Empty final target')
        prefix = tokenizer.apply_chat_template(prompt, tokenize=False, add_generation_prompt=True, enable_thinking=False)
        full = tokenizer.apply_chat_template(prompt + completion, tokenize=False, add_generation_prompt=False, enable_thinking=False)
        prompt_ids = tokenizer(prefix, add_special_tokens=False)['input_ids']
        full_ids = tokenizer(full, add_special_tokens=False)['input_ids']
        require(full.startswith(prefix) and full_ids[:len(prompt_ids)] == prompt_ids, f'Row {index+1}: changed template/token boundary')
        suffix = full_ids[len(prompt_ids):]
        expected_suffix = target + '<|im_end|>\n'
        require(tokenizer.decode(suffix, skip_special_tokens=False) == expected_suffix, f'Row {index+1}: suffix mismatch')
        require(len(full_ids) <= max_length, f'Row {index+1}: {len(full_ids)} tokens exceeds {max_length}; no silent truncation')
        require(suffix and tokenizer.eos_token_id in suffix, f'Row {index+1}: no target/termination')
        feature = {'input_ids': full_ids, 'attention_mask': [1] * len(full_ids),
                   'labels': [-100] * len(prompt_ids) + suffix,
                   'prompt_length': len(prompt_ids), 'expected_suffix': expected_suffix,
                   'id': f'pilot-{index+1:03}',
                   'has_assistant_history': any(m['role'] == 'assistant' for m in prompt)}
        validate_feature(feature)
        result.append(feature)
    return result


def validate_feature(feature):
    ids, labels, attention = feature['input_ids'], feature['labels'], feature['attention_mask']
    boundary = feature['prompt_length']
    require(len(ids) == len(labels) == len(attention), 'Token/label/attention lengths differ')
    require(0 < boundary < len(ids), 'Empty prompt or completion supervision')
    require(all(value == -100 for value in labels[:boundary]), 'Prompt/history leaked into loss')
    require(labels[boundary:] == ids[boundary:], 'Final target labels missing or altered')
    require(all(value == 1 for value in attention), 'Unpadded feature has invalid attention')


class CompletionCollator:
    """The exact collator passed to Trainer; preserves EOS even when EOS==PAD."""
    def __init__(self, pad_token_id, max_length=2048, pad_to_multiple_of=8):
        self.pad_token_id = pad_token_id
        self.max_length = max_length
        self.multiple = pad_to_multiple_of

    def __call__(self, features):
        import torch
        require(bool(features), 'Empty training batch')
        for feature in features:
            validate_feature(feature)
        longest = max(len(f['input_ids']) for f in features)
        length = math.ceil(longest / self.multiple) * self.multiple
        require(length <= self.max_length, 'Padded batch exceeds max_length')
        batch = {'input_ids': [], 'attention_mask': [], 'labels': []}
        for feature in features:
            padding = length - len(feature['input_ids'])
            batch['input_ids'].append(feature['input_ids'] + [self.pad_token_id] * padding)
            batch['attention_mask'].append(feature['attention_mask'] + [0] * padding)
            batch['labels'].append(feature['labels'] + [-100] * padding)
        return {name: torch.tensor(values, dtype=torch.long) for name, values in batch.items()}


class FeatureDataset:
    def __init__(self, features):
        self.features = features

    def __len__(self):
        return len(self.features)

    def __getitem__(self, index):
        return self.features[index]


def verify_collator(features, collator, tokenizer, expected_count=300):
    require(len(features) == expected_count, 'The full manifest-bound collator audit is required')
    supervised = 0
    for start in range(0, len(features), 8):
        group = features[start:start+8]
        batch = collator(group)
        require(set(batch) == {'input_ids', 'attention_mask', 'labels'}, 'Metadata reached model batch')
        for index, feature in enumerate(group):
            ids = batch['input_ids'][index].tolist()
            labels = batch['labels'][index].tolist()
            attention = batch['attention_mask'][index].tolist()
            length, boundary = len(feature['input_ids']), feature['prompt_length']
            require(ids[:length] == feature['input_ids'], 'Collator altered real tokens')
            require(labels[:boundary] == [-100] * boundary, 'Prompt/history mask lost')
            require(labels[boundary:length] == ids[boundary:length], 'Final completion not supervised')
            require(all(v == -100 for v in labels[length:]), 'Padding contributes to loss')
            require(attention == [1] * length + [0] * (len(ids)-length), 'Padding attention incorrect')
            active = [value for value in labels if value != -100]
            require(tokenizer.decode(active, skip_special_tokens=False) == feature['expected_suffix'], 'Decoded actual labels differ from target')
            supervised += len(active)
    return {'examples_checked': len(features), 'all_actual_collator_masks_pass': True,
            'supervised_tokens': supervised, 'max_sequence_tokens': max(len(f['input_ids']) for f in features),
            'model_or_gradients_tested': False}


def native_bf16_supported():
    """Require native CUDA BF16; tensor-creation emulation on T4 is insufficient."""
    import torch
    # including_emulation is supported by our minimum torch 2.4 release.
    return torch.cuda.is_bf16_supported(including_emulation=False)


def cuda_environment(mode='lora'):
    import torch
    from packaging.version import Version
    require(mode in ('lora', 'qlora'), 'Unknown training mode')
    require(Version(torch.__version__.split('+')[0]) >= Version('2.4'), 'Use a CUDA torch>=2.4 runtime')
    require(torch.cuda.is_available(), 'A Colab NVIDIA GPU runtime is required')
    require(torch.cuda.device_count() == 1, 'This first notebook supports one GPU')
    names = ['torch', 'transformers', 'peft', 'accelerate', 'tokenizers', 'huggingface_hub', 'safetensors']
    packages = {p: importlib.metadata.version(p) for p in names}
    try:
        packages['bitsandbytes'] = importlib.metadata.version('bitsandbytes')
    except importlib.metadata.PackageNotFoundError:
        require(mode != 'qlora', 'Explicit QLoRA requires bitsandbytes==0.49.2')
    free, total = torch.cuda.mem_get_info(0)
    bf16 = native_bf16_supported()
    return {'python': platform.python_version(), 'packages': packages, 'mode': mode,
            'gpu': torch.cuda.get_device_name(0), 'cuda_runtime': torch.version.cuda,
            'gpu_memory_bytes': total, 'initial_free_bytes': free,
            'allocator_config': {key: os.environ.get(key) for key in ('PYTORCH_ALLOC_CONF', 'PYTORCH_CUDA_ALLOC_CONF')},
            'allocator_backend': torch.cuda.memory.get_allocator_backend(),
            'native_bf16_supported': bf16,
            'compute_dtype': 'bfloat16' if bf16 else 'float16'}


def check_trainable(model):
    import torch
    trainable = [(name, p) for name, p in model.named_parameters() if p.requires_grad]
    require(trainable and all('lora_' in name for name, p in trainable), 'Base parameters are not frozen, or no LoRA parameters')
    require(all(p.dtype == torch.float32 for name, p in trainable), 'Trainable adapters must be FP32 for safe FP16 gradient scaling')
    require(all(p.grad is None for name, p in model.named_parameters() if not p.requires_grad), 'Frozen base has gradients')
    return {'trainable_parameters': sum(p.numel() for name, p in trainable),
            'total_parameters': sum(p.numel() for p in model.parameters()),
            'base_frozen': True, 'trainable_dtype': 'float32'}


def validate_adapter_base(adapter, config):
    adapter = Path(adapter)
    metadata = json.loads((adapter / 'adapter_config.json').read_text())
    require(metadata['base_model_name_or_path'] == MODEL_ID, 'Adapter base model differs')
    require(metadata.get('revision') == REVISION, 'Adapter revision differs')
    record = adapter / 'sft-adapter-record.json'
    if record.exists():
        require(json.loads(record.read_text())['mode'] == config.mode, 'Adapter training mode differs')


def load_model(config, adapter=None, training=True):
    """No automatic fallback: ordinary LoRA never constructs or prepares a quantized model."""
    import torch
    from transformers import AutoModelForCausalLM, set_seed
    from peft import LoraConfig, PeftModel, get_peft_model
    cuda_environment(config.mode)
    set_seed(config.seed)
    dtype = torch.bfloat16 if native_bf16_supported() else torch.float16
    kwargs = dict(revision=REVISION, torch_dtype=dtype, device_map={'': 0}, attn_implementation='sdpa')
    if config.mode == 'qlora':
        from transformers import BitsAndBytesConfig
        kwargs['quantization_config'] = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type='nf4',
            bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=dtype)
    base = AutoModelForCausalLM.from_pretrained(MODEL_ID, **kwargs)
    require(getattr(base.config, '_commit_hash', None) == REVISION, 'Loaded base revision differs')
    base.config.use_cache = not training
    if training:
        if config.mode == 'qlora':
            from peft import prepare_model_for_kbit_training
            base = prepare_model_for_kbit_training(base, use_gradient_checkpointing=True,
                gradient_checkpointing_kwargs={'use_reentrant': False})
        else:
            base.requires_grad_(False)
            base.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
    if adapter:
        validate_adapter_base(adapter, config)
        model = PeftModel.from_pretrained(base, str(adapter), is_trainable=training, autocast_adapter_dtype=True)
    else:
        require(training, 'Inference requires a saved adapter')
        lora = LoraConfig(task_type='CAUSAL_LM', r=config.rank, lora_alpha=config.alpha,
            lora_dropout=config.dropout, bias='none', target_modules='all-linear',
            base_model_name_or_path=MODEL_ID, revision=REVISION)
        model = get_peft_model(base, lora, autocast_adapter_dtype=True)
    # PEFT normally promotes these. Enforce this explicitly, including after checkpoint reload.
    for name, parameter in model.named_parameters():
        if 'lora_' in name:
            parameter.data = parameter.data.to(torch.float32)
    if training:
        check_trainable(model)
    return model


def training_args(config, output_dir, smoke=False):
    import torch
    from transformers import TrainingArguments
    bf16 = native_bf16_supported()
    return TrainingArguments(output_dir=str(output_dir), per_device_train_batch_size=config.microbatch,
        gradient_accumulation_steps=config.gradient_accumulation,
        num_train_epochs=config.epochs, max_steps=2 if smoke else -1,
        learning_rate=config.learning_rate, lr_scheduler_type='linear',
        warmup_ratio=0.03, max_grad_norm=1.0, weight_decay=0.0,
        fp16=not bf16, bf16=bf16, optim='adamw_torch',
        gradient_checkpointing=True, gradient_checkpointing_kwargs={'use_reentrant': False},
        logging_steps=1, logging_strategy='steps', logging_nan_inf_filter=False,
        save_strategy='no' if smoke else 'epoch',
        save_total_limit=None, save_only_model=False, eval_strategy='no', report_to='none',
        remove_unused_columns=False, dataloader_num_workers=0,
        seed=config.seed, data_seed=config.seed, label_names=['labels'],
        label_smoothing_factor=0.0)


def configure_fp16_scaler(trainer, config):
    """Configure a fresh Trainer before train(); checkpoint restoration happens afterward.

    Use only GradScaler's public state API. Never reset the scale in a callback:
    Trainer must restore the full checkpoint's scaler.pt unchanged when resuming.
    """
    require(trainer.state.global_step == 0, 'Configure precision before training or checkpoint restoration')
    scaler = trainer.accelerator.scaler
    record = {'configured_fp16_initial_scale': float(config.fp16_initial_scale),
              'applied': bool(trainer.args.fp16),
              'checkpoint_restore_order': 'Trainer restores checkpoint scaler after this initialization'}
    if trainer.args.fp16:
        require(scaler is not None and scaler.is_enabled(), 'FP16 Trainer requires an enabled GradScaler')
        state = scaler.state_dict()
        require(state and state['_growth_tracker'] == 0, 'Do not reset an already-used scaler')
        scaler.load_state_dict({**state, 'scale': float(config.fp16_initial_scale)})
        require(scaler.get_scale() == config.fp16_initial_scale, 'Configured initial FP16 scale was not applied')
        record['initial_scaler_state_before_checkpoint_restore'] = scaler.state_dict()
    else:
        require(scaler is None or not scaler.is_enabled(), 'Unexpected enabled scaler without FP16')
        record['initial_scaler_state_before_checkpoint_restore'] = None
    return record


class MemoryMonitor:
    def __init__(self):
        import torch
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats(0)
        self.minimum_free, self.total = torch.cuda.mem_get_info(0)
        self.initial_nonallocator_bytes = max(0, self.total - self.minimum_free - torch.cuda.memory_reserved(0))

    def sample(self):
        import torch
        free, _ = torch.cuda.mem_get_info(0)
        self.minimum_free = min(self.minimum_free, free)

    def report(self):
        import torch
        self.sample()
        allocated = torch.cuda.max_memory_allocated(0)
        reserved = torch.cuda.max_memory_reserved(0)
        # Driver free captures other GPU users; peak reserved captures transient allocator growth.
        margin = min(self.minimum_free / self.total,
                     (self.total - self.initial_nonallocator_bytes - reserved) / self.total)
        return {'total_bytes': self.total, 'peak_allocated_bytes': allocated,
                'peak_reserved_bytes': reserved, 'minimum_sampled_driver_free_bytes': self.minimum_free,
                'initial_nonallocator_bytes': self.initial_nonallocator_bytes,
                'free_memory_margin_fraction': margin, 'required_margin_fraction': 0.15,
                'headroom_passed': margin >= 0.15,
                'margin_scope': 'Operational target: sampled driver free and peak reserved plus initial nonallocator use; external changes between samples may be missed'}


def gradient_callback(memory=None):
    import torch
    from transformers import TrainerCallback
    class FiniteAdapterGradients(TrainerCallback):
        def __init__(self):
            self.steps_checked = 0
            self.nonzero_gradient_steps = 0
            self.applied_optimizer_steps = 0
            self.skipped_optimizer_steps = 0
            self.starting_global_step = 0
            self.scaler = None
            self.training_start_scaler_state = None
        def on_train_begin(self, args, state, control, **kwargs):
            self.starting_global_step = state.global_step
            self.training_start_scaler_state = self.scaler.state_dict() if self.scaler is not None else None
        def report(self):
            return {'gradient_steps_checked': self.steps_checked,
                    'applied_optimizer_steps': self.applied_optimizer_steps,
                    'skipped_optimizer_steps': self.skipped_optimizer_steps,
                    'starting_global_step': self.starting_global_step,
                    'training_start_scaler_state': self.training_start_scaler_state,
                    'scaler_state_after_last_update': self.scaler.state_dict() if self.scaler is not None else None}
        def on_pre_optimizer_step(self, args, state, control, model=None, **kwargs):
            check_trainable(model)
            grads = [p.grad for p in model.parameters() if p.requires_grad and p.grad is not None]
            require(grads and all(torch.isfinite(g).all().item() for g in grads), 'Missing/nonfinite adapter gradients')
            require(any(torch.count_nonzero(g).item() for g in grads), 'Adapter gradients are all zero')
            self.steps_checked += 1
            self.nonzero_gradient_steps += 1
            if memory:
                memory.sample()
        def on_optimizer_step(self, args, state, control, optimizer=None, **kwargs):
            require(optimizer is not None, 'Missing optimizer for applied-update verification')
            if args.fp16:
                require(hasattr(optimizer, 'step_was_skipped'), 'Cannot verify FP16 optimizer update status')
            skipped = bool(getattr(optimizer, 'step_was_skipped', False))
            if skipped:
                self.skipped_optimizer_steps += 1
            require(not skipped, 'Optimizer update was skipped; stop rather than consume training rows')
            self.applied_optimizer_steps += 1
            if memory:
                memory.sample()
        def on_log(self, args, state, control, logs=None, **kwargs):
            for key in ('loss', 'grad_norm'):
                if logs and key in logs:
                    require(math.isfinite(float(logs[key])), f'Nonfinite {key}')
    return FiniteAdapterGradients()


def audit_actual_batch(inputs, features_by_ids):
    require(set(inputs) == {'input_ids', 'attention_mask', 'labels'}, 'Unexpected actual model inputs')
    checked = []
    for ids, labels, attention in zip(inputs['input_ids'].tolist(), inputs['labels'].tolist(), inputs['attention_mask'].tolist()):
        length = sum(attention)
        require(attention == [1] * length + [0] * (len(ids) - length), 'Invalid actual padding attention')
        feature = features_by_ids.get(tuple(ids[:length]))
        require(feature is not None, 'Actual training sequence is not an approved feature')
        require(labels[:length] == feature['labels'] and labels[length:] == [-100] * (len(ids) - length),
                'Actual training batch labels differ from approved final-completion mask')
        checked.append(feature['id'])
    return checked


def optimizer_steps_per_epoch(count, accumulation=8):
    require(type(count) is int and count > 0, 'Positive dataset count required')
    return math.ceil(count / accumulation)


def validate_training_ledger(ledger, approved_ids, completed_epochs, steps_per_epoch):
    """Validate cumulative row exposure and one finite loss record per applied update."""
    require(len(approved_ids) == len(set(approved_ids)), 'Training IDs must be unique')
    require(len(ledger['epochs']) == completed_epochs, 'Checkpoint epoch ledger count differs')
    for epoch, record in enumerate(ledger['epochs'], 1):
        require(record['epoch'] == epoch and record['complete'] is True,
                'Only completed epoch boundaries may be resumed')
        ids = record['actual_batch_ids']
        require(len(ids) == len(approved_ids) and set(ids) == set(approved_ids),
                'Every approved row must be consumed exactly once per epoch')
    updates = ledger['updates']
    require(len(updates) == completed_epochs * steps_per_epoch, 'Missing optimizer-update losses')
    for step, record in enumerate(updates, 1):
        require(record['step'] == step and math.isfinite(record['loss'])
                and math.isfinite(record['learning_rate']), 'Invalid optimizer-update loss/LR record')
    return True


def make_trainer(*, audit_features, sequential=False, memory=None, enforce_epochs=False, **kwargs):
    import torch
    from transformers import Trainer, TrainerCallback
    class FiniteLossTrainer(Trainer):
        def __init__(self, **inner):
            self.actual_batch_ids = []
            self.features_by_ids = {tuple(f['input_ids']): f for f in audit_features}
            self.approved_ids = [f['id'] for f in audit_features]
            if enforce_epochs:
                require(len(self.features_by_ids) == len(audit_features), 'Duplicate training sequences cannot be audited by row')
                require(len(set(self.approved_ids)) == len(self.approved_ids), 'Training IDs must be unique')
            self.training_ledger = {'epochs': [], 'updates': []}
            self.active_epoch = None
            super().__init__(**inner)
            if enforce_epochs:
                self.add_callback(EpochAudit(self))
        def train(self, *args, **inner):
            checkpoint = inner.get('resume_from_checkpoint', args[0] if args else None)
            if enforce_epochs and checkpoint:
                self.training_ledger = json.loads((Path(checkpoint) / 'training-ledger.json').read_text())
                state = json.loads((Path(checkpoint) / 'trainer_state.json').read_text())
                validate_training_ledger(self.training_ledger, self.approved_ids, int(state['epoch']),
                                         optimizer_steps_per_epoch(len(self.approved_ids), self.args.gradient_accumulation_steps))
            return super().train(*args, **inner)
        def _get_train_sampler(self, train_dataset=None):
            if sequential:
                return torch.utils.data.SequentialSampler(train_dataset if train_dataset is not None else self.train_dataset)
            return super()._get_train_sampler(train_dataset)
        def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):
            ids = audit_actual_batch(inputs, self.features_by_ids)
            self.actual_batch_ids.extend(ids)
            if enforce_epochs:
                require(self.active_epoch is not None, 'Actual batch outside an audited epoch')
                record = self.training_ledger['epochs'][self.active_epoch]
                require(not (set(ids) & set(record['actual_batch_ids'])) and len(ids) == len(set(ids)),
                        'Approved training row repeated within an epoch')
                record['actual_batch_ids'].extend(ids)
            result = super().compute_loss(model, inputs, return_outputs=return_outputs,
                                          num_items_in_batch=num_items_in_batch)
            loss = result[0] if return_outputs else result
            require(torch.isfinite(loss).all().item(), 'Nonfinite actual forward loss')
            if memory:
                memory.sample()
            return result
    class EpochAudit(TrainerCallback):
        def __init__(self, trainer):
            self.trainer = trainer
        def on_epoch_begin(self, args, state, control, **kwargs):
            trainer = self.trainer
            epoch = len(trainer.training_ledger['epochs'])
            require(math.isclose(float(state.epoch or 0), epoch), 'Resume must begin at a completed epoch boundary')
            trainer.training_ledger['epochs'].append({'epoch': epoch + 1, 'actual_batch_ids': [], 'complete': False})
            trainer.active_epoch = epoch
        def on_log(self, args, state, control, logs=None, **kwargs):
            if logs and 'loss' in logs:
                updates = self.trainer.training_ledger['updates']
                require(state.global_step == len(updates) + 1, 'Require loss at every optimizer update')
                require(math.isfinite(float(logs['loss'])), 'Nonfinite optimizer-update loss')
                updates.append({'step': state.global_step, 'loss': float(logs['loss']),
                                'learning_rate': float(logs['learning_rate'])})
        def on_epoch_end(self, args, state, control, **kwargs):
            trainer = self.trainer
            trainer.training_ledger['epochs'][trainer.active_epoch]['complete'] = True
            validate_training_ledger(trainer.training_ledger, trainer.approved_ids, trainer.active_epoch + 1,
                                     optimizer_steps_per_epoch(len(trainer.approved_ids), args.gradient_accumulation_steps))
            trainer.active_epoch = None
    return FiniteLossTrainer(**kwargs)


def adapter_fingerprint(model):
    import torch
    from peft import get_peft_model_state_dict
    result = hashlib.sha256()
    for name, tensor in sorted(get_peft_model_state_dict(model).items()):
        result.update(name.encode())
        result.update(tensor.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes())
    return result.hexdigest()


def release_memory():
    import torch
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def run_identity(config, tokenizer, context=None):
    return {'model': MODEL_ID, 'revision': REVISION, 'mode': config.mode,
            'data_sha256': config.data_sha256, 'manifest_sha256': config.manifest_sha256,
            'dataset_version': config.dataset_version,
            'config': asdict(config), 'helper_sha256': sha256(__file__),
            'chat_template_sha256': hashlib.sha256(tokenizer.chat_template.encode()).hexdigest(),
            'enable_thinking': False, 'packing': False, 'train_examples': config.train_examples,
            'internal_validation_examples': 0, 'context': context or {}}


def identity_hash(identity):
    return hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()


def representative_smoke_features(features, config):
    require(len(features) == config.train_examples, 'Smoke requires the full approved feature collection')
    longest = max(features, key=lambda feature: len(feature['input_ids']))
    history = next((f for f in features if f.get('has_assistant_history')), None)
    require(history is not None, 'Smoke must include historical assistant turns')
    import torch
    # Match the pinned Trainer's first seeded full-run accumulation group from fresh weights.
    indices = torch.randperm(len(features), generator=torch.Generator().manual_seed(config.seed)).tolist()
    first_full_group = [features[index] for index in indices[:config.gradient_accumulation]]
    longest_history_group = [longest, history] * (config.gradient_accumulation // 2)
    return first_full_group + longest_history_group


def reload_check(config, adapter_dir, tokenizer, feature, expected_fingerprint):
    import torch
    model = batch = generated = None
    try:
        model = load_model(config, adapter=adapter_dir, training=False)
        require(adapter_fingerprint(model) == expected_fingerprint, 'Reloaded adapter weights differ')
        model.eval()
        batch = CompletionCollator(tokenizer.pad_token_id, config.max_length)([feature])
        batch = {k: v.to('cuda:0') for k, v in batch.items()}
        with torch.no_grad():
            # Autocast is required: ordinary half base + FP32 adapters without Trainer's wrapper.
            dtype = torch.bfloat16 if native_bf16_supported() else torch.float16
            with torch.autocast('cuda', dtype=dtype):
                loss = model(**batch).loss
                prefix = batch['input_ids'][:, :feature['prompt_length']]
                generated = model.generate(input_ids=prefix, attention_mask=torch.ones_like(prefix),
                    do_sample=False, max_new_tokens=8, pad_token_id=tokenizer.pad_token_id,
                    eos_token_id=tokenizer.eos_token_id, use_cache=True)
        require(torch.isfinite(loss).item(), 'Reloaded adapter loss is nonfinite')
        new_ids = generated[0, feature['prompt_length']:].tolist()
        require(bool(new_ids) and all(0 <= token < model.config.vocab_size for token in new_ids), 'Reloaded inference did not generate valid tokens')
        return {'save_reload_weights_equal': True, 'reload_loss': float(loss),
                'inference_verified': True, 'generated_token_ids': new_ids,
                'generated_text': tokenizer.decode(new_ids, skip_special_tokens=False)}
    finally:
        del model, batch, generated
        release_memory()


def failure_record(error):
    import torch
    return {'error_type': type(error).__name__, 'error': str(error),
            'failure_kind': 'out_of_memory' if isinstance(error, torch.cuda.OutOfMemoryError) else 'runtime_error',
            'automatic_fallback': False}


def smoke_test(features, collator, tokenizer, config, directory, context=None):
    """Two real optimizer updates with unchanged accumulation; discards all live smoke state."""
    directory = Path(directory)
    require(not directory.exists(), 'Smoke directory exists; use a fresh run name')
    directory.mkdir(parents=True)
    report = {'passed': False, 'mode': config.mode, 'identity': run_identity(config, tokenizer, context),
              'feature_collection_sha256': identity_hash(features), 'status': 'started'}
    write_json(directory / 'smoke-report.json', report)
    model = trainer = callback = memory = None
    try:
        report['environment'] = cuda_environment(config.mode)
        report['mask_report'] = verify_collator(features, collator, tokenizer, config.train_examples)
        smoke_features = representative_smoke_features(features, config)
        report['representative_ids'] = [f['id'] for f in smoke_features]
        report['longest_sequence_tokens'] = max(len(f['input_ids']) for f in smoke_features)
        memory = MemoryMonitor()
        model = load_model(config)
        report['parameter_checks'] = check_trainable(model)
        report['initial_adapter_fingerprint'] = adapter_fingerprint(model)
        callback = gradient_callback(memory)
        trainer = make_trainer(model=model, args=training_args(config, directory / 'checkpoints', smoke=True),
            train_dataset=FeatureDataset(smoke_features), data_collator=collator, processing_class=tokenizer,
            callbacks=[callback], audit_features=features, sequential=True, memory=memory)
        report['precision'] = configure_fp16_scaler(trainer, config)
        callback.scaler = trainer.accelerator.scaler
        write_json(directory / 'smoke-report.json', report)
        result = trainer.train()
        require(math.isfinite(result.training_loss) and callback.steps_checked == 2
                and callback.applied_optimizer_steps == 2 and trainer.state.global_step == 2,
                'Smoke requires exactly two finite optimizer updates')
        require(trainer.actual_batch_ids == report['representative_ids'], 'Smoke representative examples were not all actually trained')
        fingerprint = adapter_fingerprint(model)
        require(fingerprint != report['initial_adapter_fingerprint'], 'Adapter weights did not update')
        report.update(optimizer_steps=trainer.state.global_step, training_loss=result.training_loss,
            actual_batch_ids=trainer.actual_batch_ids, actual_batch_masks_verified=True,
            nonzero_finite_gradient_steps=callback.nonzero_gradient_steps, adapter_updated=True, base_frozen=True,
            smoke_adapter_fingerprint=fingerprint, training_memory=memory.report(),
            optimizer_update_checks=callback.report())
        adapter_dir = directory / 'adapter'
        trainer.save_model(str(adapter_dir))
        tokenizer.save_pretrained(adapter_dir)
        write_json(adapter_dir / 'sft-adapter-record.json', report['identity'])
        del trainer, model, callback
        trainer = model = callback = None
        release_memory()
        report.update(reload_check(config, adapter_dir, tokenizer, smoke_features[0], fingerprint))
        report['memory_including_reload'] = memory.report()
        report['headroom_passed'] = report['training_memory']['headroom_passed'] and report['memory_including_reload']['headroom_passed']
        report.update(passed=report['headroom_passed'], status='passed' if report['headroom_passed'] else 'insufficient_headroom',
            failure_kind=None if report['headroom_passed'] else 'insufficient_headroom',
            smoke_weights_discarded_before_full_run=True)
    except Exception as error:
        report.update(status='failed', **failure_record(error))
        if callback is not None:
            report['optimizer_update_checks'] = callback.report()
        if memory:
            report['failure_memory'] = memory.report()
        write_json(directory / 'smoke-report.json', report)
        raise
    finally:
        del trainer, model, callback
        release_memory()
        write_json(directory / 'smoke-report.json', report)
    return report


def validate_checkpoint(checkpoint, directory, identity, environment):
    from packaging.version import Version
    require(Version(environment['packages']['torch'].split('+')[0]) >= Version('2.6'),
            'Safe Transformers optimizer/RNG resume requires torch>=2.6; preserve this run and use a compatible runtime')
    checkpoint, directory = Path(checkpoint).resolve(), Path(directory).resolve()
    require(checkpoint.parent == directory / 'checkpoints', 'Resume checkpoint must belong to this full run')
    metadata = json.loads((checkpoint / 'resume-record.json').read_text())
    require(metadata['identity'] == identity, 'Checkpoint run metadata mismatch')
    require(metadata['packages'] == environment['packages'] and metadata['compute_dtype'] == environment['compute_dtype'],
            'Resume dependency versions/precision mismatch')
    required = {'adapter_model.safetensors', 'adapter_config.json', 'optimizer.pt', 'scheduler.pt', 'trainer_state.json', 'rng_state.pth'}
    if environment['compute_dtype'] == 'float16':
        required.add('scaler.pt')
    require(required <= set(metadata['files']), 'Checkpoint lacks optimizer/scheduler/RNG/precision state')
    for name, expected in metadata['files'].items():
        require(Path(name).name == name and sha256(checkpoint / name) == expected, f'Checkpoint state changed: {name}')
    state = json.loads((checkpoint / 'trainer_state.json').read_text())
    require(state['global_step'] == metadata['global_step'] > 0, 'Checkpoint step mismatch')
    if metadata.get('format_version') == 2:
        index = json.loads((directory / 'checkpoint-index.json').read_text())
        verify_replay_checkpoint(checkpoint, index[checkpoint.name]['resume_record_sha256'], identity)
    return str(checkpoint)


def verify_replay_checkpoint(checkpoint, expected_record_sha256, identity=None):
    """Verify a frozen external checkpoint binding before evaluation or replay.

    The caller must obtain expected_record_sha256 from its immutable experiment plan
    or checkpoint-index.json frozen before development generation, never from the
    untrusted checkpoint itself. This checks bytes; reload_check checks live weights.
    """
    checkpoint = Path(checkpoint)
    require(sha256(checkpoint / 'resume-record.json') == expected_record_sha256,
            'Checkpoint replay record hash differs from frozen binding')
    record = json.loads((checkpoint / 'resume-record.json').read_text())
    require(record.get('format_version') == 2, 'Checkpoint lacks audited epoch replay metadata')
    if identity is not None:
        require(record['identity'] == identity, 'Checkpoint run metadata mismatch')
    required = {'adapter_model.safetensors', 'adapter_config.json', 'optimizer.pt', 'scheduler.pt',
                'trainer_state.json', 'rng_state.pth', 'training-ledger.json', 'sft-adapter-record.json'}
    if record['compute_dtype'] == 'float16':
        required.add('scaler.pt')
    require(required <= set(record['files']), 'Checkpoint lacks optimizer/scheduler/RNG/precision/replay state')
    actual = {p.name for p in checkpoint.iterdir() if p.is_file() and p.name != 'resume-record.json'}
    require(actual == set(record['files']), 'Checkpoint file inventory changed')
    for name, digest in record['files'].items():
        require(Path(name).name == name and not (checkpoint / name).is_symlink()
                and sha256(checkpoint / name) == digest, f'Checkpoint state changed: {name}')
    state = json.loads((checkpoint / 'trainer_state.json').read_text())
    require(type(record['completed_epoch']) is int and record['completed_epoch'] > 0
            and state['epoch'] == record['completed_epoch'], 'Checkpoint is not a completed epoch boundary')
    expected_steps = record['completed_epoch'] * optimizer_steps_per_epoch(record['identity']['train_examples'])
    require(record['global_step'] == state['global_step'] == expected_steps, 'Checkpoint epoch/update count differs')
    require(checkpoint.name == f"checkpoint-{record['global_step']}", 'Checkpoint directory/update binding differs')
    require(json.loads((checkpoint / 'sft-adapter-record.json').read_text()) == record['identity'],
            'Checkpoint adapter identity differs')
    ledger = json.loads((checkpoint / 'training-ledger.json').read_text())
    require(len(record['approved_ids']) == record['identity']['train_examples'], 'Approved checkpoint row count differs')
    validate_training_ledger(ledger, record['approved_ids'], record['completed_epoch'],
                             optimizer_steps_per_epoch(record['identity']['train_examples']))
    require(isinstance(record['adapter_fingerprint'], str) and len(record['adapter_fingerprint']) == 64,
            'Missing checkpoint adapter fingerprint')
    return record


def checkpoint_callback(identity, environment, directory, trainer=None):
    from transformers import TrainerCallback
    class BoundCheckpoint(TrainerCallback):
        def on_save(self, args, state, control, model=None, **kwargs):
            checkpoint = Path(args.output_dir) / f'checkpoint-{state.global_step}'
            record = {'identity': identity, 'packages': environment['packages'],
                'compute_dtype': environment['compute_dtype'], 'global_step': state.global_step}
            if trainer is not None:
                epoch = int(state.epoch)
                require(state.epoch == epoch, 'Only complete epoch checkpoints are retained')
                validate_training_ledger(trainer.training_ledger, trainer.approved_ids, epoch,
                                         optimizer_steps_per_epoch(identity['train_examples']))
                write_json(checkpoint / 'training-ledger.json', trainer.training_ledger)
                write_json(checkpoint / 'sft-adapter-record.json', identity)
                record.update(format_version=2, completed_epoch=epoch, approved_ids=trainer.approved_ids,
                              adapter_fingerprint=adapter_fingerprint(model))
            record['files'] = {p.name: sha256(p) for p in checkpoint.iterdir()
                               if p.is_file() and p.name != 'resume-record.json'}
            write_json(checkpoint / 'resume-record.json', record)
            if trainer is not None:
                digest = sha256(checkpoint / 'resume-record.json')
                verify_replay_checkpoint(checkpoint, digest, identity)
                index_path = Path(directory) / 'checkpoint-index.json'
                index = json.loads(index_path.read_text()) if index_path.exists() else {}
                previous = index.get(checkpoint.name)
                binding = {'completed_epoch': epoch, 'global_step': state.global_step,
                           'resume_record_sha256': digest}
                require(previous is None or previous == binding, 'Retained checkpoint cannot be overwritten with changed state')
                index[checkpoint.name] = binding
                write_json(index_path, index)
        def on_log(self, args, state, control, logs=None, **kwargs):
            write_json(Path(directory) / 'trainer-log.json', state.log_history)
    return BoundCheckpoint()


def verify_epoch_checkpoints(directory, identity):
    directory = Path(directory)
    index = json.loads((directory / 'checkpoint-index.json').read_text())
    steps = optimizer_steps_per_epoch(identity['train_examples'])
    expected = {f'checkpoint-{epoch * steps}' for epoch in range(1, identity['config']['epochs'] + 1)}
    actual = {p.name for p in (directory / 'checkpoints').glob('checkpoint-*') if p.is_dir()}
    require(set(index) == actual == expected, 'Retain exactly one resumable checkpoint for every epoch')
    records = {}
    for name in sorted(expected, key=lambda value: int(value.split('-')[-1])):
        records[name] = verify_replay_checkpoint(directory / 'checkpoints' / name,
                                                index[name]['resume_record_sha256'], identity)
        require(index[name]['completed_epoch'] == records[name]['completed_epoch']
                and index[name]['global_step'] == records[name]['global_step'], 'Checkpoint index epoch/update binding differs')
    return records


def full_train(features, collator, tokenizer, config, directory, smoke_report, manifest,
               context=None, resume_checkpoint=None):
    """Fresh base/adapter after smoke; explicit metadata-bound optimizer-state resume only."""
    directory = Path(directory)
    identity = run_identity(config, tokenizer, context)
    require(smoke_report.get('passed') is True and smoke_report.get('identity') == identity,
            'Passing smoke with identical mode/config/data/template/helper/context is required')
    require(smoke_report.get('headroom_passed') is True, 'Smoke did not meet 15% operational headroom target')
    require(len(features) == config.train_examples, 'Train every manifest-bound example')
    require(manifest['count'] == config.train_examples and manifest['version'] == config.dataset_version
            and manifest['artifacts']['sft.jsonl'] == config.data_sha256, 'Manifest binding differs')
    require(smoke_report.get('feature_collection_sha256') == identity_hash(features),
            'Full features differ from the passing smoke collection')
    environment = cuda_environment(config.mode)
    require(smoke_report['environment']['packages'] == environment['packages'] and
            smoke_report['environment']['compute_dtype'] == environment['compute_dtype'],
            'Environment/precision changed after smoke')
    if resume_checkpoint:
        record = json.loads((directory / 'run-record.json').read_text())
        require(record['identity'] == identity and record['status'] in ('training_started', 'failed', 'resuming', 'trained_pending_reload'),
                'Run is incompatible or already completed; never silently restart')
        resume_checkpoint = validate_checkpoint(resume_checkpoint, directory, identity, environment)
        index = json.loads((directory / 'checkpoint-index.json').read_text())
        latest = max(index, key=lambda name: index[name]['global_step'])
        require(Path(resume_checkpoint).name == latest, 'Resume latest retained epoch; preserve all historical checkpoints')
        verify_replay_checkpoint(resume_checkpoint, index[latest]['resume_record_sha256'], identity)
        record['status'] = 'resuming'
        record.setdefault('resume_history', []).append(resume_checkpoint)
    else:
        require(not directory.exists(), 'Full run directory exists; choose a new run or explicit matching checkpoint')
        directory.mkdir(parents=True)
        record = {**identity, 'identity': identity, 'environment': environment,
            'audit_status': manifest['audit_status'], 'fresh_after_smoke': True,
            'baseline_rerun': False, 'status': 'training_started', 'quality_improvement_verified': False,
            'smoke_report_sha256': identity_hash(smoke_report)}
    write_json(directory / 'run-record.json', record)
    (directory / 'environment-freeze.txt').write_text('\n'.join(f'{p}=={v}' for p, v in sorted(environment['packages'].items())) + '\n')
    model = trainer = callback = memory = None
    try:
        record['mask_report'] = verify_collator(features, collator, tokenizer, config.train_examples)
        memory = MemoryMonitor()
        model = load_model(config)  # Always fresh; Trainer restores state only for explicitly validated resume.
        require(adapter_fingerprint(model) == smoke_report['initial_adapter_fingerprint'], 'Fresh initialization differs from pre-smoke state')
        callback = gradient_callback(memory)
        trainer = make_trainer(model=model, args=training_args(config, directory / 'checkpoints'),
            train_dataset=FeatureDataset(features), data_collator=collator, processing_class=tokenizer,
            callbacks=[callback], audit_features=features, memory=memory, enforce_epochs=True)
        trainer.add_callback(checkpoint_callback(identity, environment, directory, trainer))
        record['precision'] = configure_fp16_scaler(trainer, config)
        callback.scaler = trainer.accelerator.scaler
        write_json(directory / 'run-record.json', record)
        result = trainer.train(resume_from_checkpoint=resume_checkpoint)
        steps_per_epoch = optimizer_steps_per_epoch(len(features), config.gradient_accumulation)
        expected_steps = config.epochs * steps_per_epoch
        require(math.isfinite(result.training_loss) and trainer.state.global_step == expected_steps,
                'Full run failed loss/integer-epoch step checks')
        require(callback.applied_optimizer_steps == trainer.state.global_step - callback.starting_global_step
                and callback.steps_checked == callback.applied_optimizer_steps
                and callback.skipped_optimizer_steps == 0, 'Full run did not apply every checked optimizer update')
        validate_training_ledger(trainer.training_ledger, trainer.approved_ids, config.epochs, steps_per_epoch)
        require(len(trainer.actual_batch_ids) == (expected_steps - callback.starting_global_step) // steps_per_epoch * len(features),
                'Invocation row exposure differs from remaining complete epochs')
        checkpoints = verify_epoch_checkpoints(directory, identity)
        record['training_ledger'] = trainer.training_ledger
        record['checkpoint_index'] = json.loads((directory / 'checkpoint-index.json').read_text())
        adapter_dir = directory / 'adapter'
        trainer.save_model(str(adapter_dir))
        tokenizer.save_pretrained(adapter_dir)
        write_json(adapter_dir / 'sft-adapter-record.json', identity)
        trainer.save_state()
        fingerprint = adapter_fingerprint(model)
        require(fingerprint != smoke_report['initial_adapter_fingerprint'], 'Full adapter did not change')
        record.update(status='trained_pending_reload', training_metrics=result.metrics,
            optimizer_steps=trainer.state.global_step, adapter_fingerprint=fingerprint,
            actual_batch_masks_verified=True, actual_batch_ids_this_invocation=trainer.actual_batch_ids,
            nonzero_finite_gradient_steps_this_invocation=callback.steps_checked, training_memory=memory.report(),
            optimizer_update_checks=callback.report())
        write_json(directory / 'run-record.json', record)
        del trainer, model, callback
        trainer = model = callback = None
        release_memory()
        record['epoch_checkpoint_reloads'] = {}
        for name, checkpoint_record in checkpoints.items():
            checkpoint = directory / 'checkpoints' / name
            binding = record['checkpoint_index'][name]['resume_record_sha256']
            verify_replay_checkpoint(checkpoint, binding, identity)
            record['epoch_checkpoint_reloads'][name] = reload_check(
                config, checkpoint, tokenizer, features[0], checkpoint_record['adapter_fingerprint'])
            verify_replay_checkpoint(checkpoint, binding, identity)
            write_json(directory / 'run-record.json', record)
        record['final_reload'] = reload_check(config, adapter_dir, tokenizer, features[0], fingerprint)
        require(record['training_memory']['headroom_passed'] and memory.report()['headroom_passed'],
                'Full run/reload did not meet unchanged 15% operational headroom target')
        record.update(status='training_completed', memory_including_reload=memory.report(),
            adapter_artifacts={p.name: sha256(p) for p in sorted(adapter_dir.iterdir()) if p.is_file()})
        write_json(directory / 'run-record.json', record)
    except Exception as error:
        record.update(status='failed', **failure_record(error))
        if callback is not None:
            record['optimizer_update_checks'] = callback.report()
        if memory:
            record['failure_memory'] = memory.report()
        write_json(directory / 'run-record.json', record)
        raise
    finally:
        del trainer, model, callback
        release_memory()
    return record
