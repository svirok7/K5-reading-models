"""Explicit, pinned local base/adapter development replay; no paid judge or DB writes.

Without --run this only verifies the frozen inputs and optional adapter metadata.
Generation uses saved prompts/histories and the current v3 no-thinking encoder.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import time

from prepare_reference import canonical, digest, file_hash, verify, FROZEN_MANIFEST_SHA256

MODEL = 'Qwen/Qwen3-1.7B'
REVISION = '70d244cc86ccca08cf5af4e1e306ecf908b1ad5e'
GENERATION = {'do_sample': True, 'temperature': 0.7, 'top_p': 0.8, 'top_k': 20,
              'max_new_tokens': 128}
TEMPLATE = 'qwen-chat-v3; enable_thinking=False'


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def prepare(args):
    reference = args.reference.resolve()
    manifest = verify(reference, FROZEN_MANIFEST_SHA256)
    cases = [json.loads(line) for line in (reference / 'development-inputs.jsonl').read_text().splitlines()]
    if args.selection == 'current-only':
        cases = [case for case in cases if case['saved_baseline_comparability'] == 'current_template_recorded']
    if not cases:
        raise ValueError('No replay inputs selected.')
    for case in cases:
        if digest(case['prompt']) != case['prompt_hash'] or not case['messages'] or case['messages'][-1]['role'] != 'user':
            raise ValueError('Invalid frozen input.')
        if any(m.get('role') not in ('user', 'assistant') or not isinstance(m.get('content'), str) for m in case['messages']):
            raise ValueError('Invalid frozen message history.')
    adapter_record = None
    if args.adapter:
        if not args.run_record:
            raise ValueError('Adapter replay requires the completed training --run-record.')
        adapter_record = json.loads(args.run_record.read_text())
        config = json.loads((args.adapter / 'adapter_config.json').read_text())
        if (config.get('base_model_name_or_path') != MODEL or adapter_record.get('model') != MODEL
                or adapter_record.get('revision') != REVISION or adapter_record.get('status') != 'training_completed'
                or adapter_record.get('enable_thinking') is not False):
            raise ValueError('Adapter must have a completed run record for the pinned no-thinking base.')
        expected = adapter_record.get('adapter_artifacts')
        if not expected:
            raise ValueError('Training run record must bind adapter file hashes.')
        for name, sha in expected.items():
            if Path(name).name != name or file_hash(args.adapter / name) != sha:
                raise ValueError('Adapter artifact hash mismatch: ' + name)
        if not any(name.endswith(('.safetensors', '.bin')) for name in expected):
            raise ValueError('Training run record does not bind adapter weights.')
    elif args.run_record:
        raise ValueError('--run-record belongs to --adapter only.')
    identity = {'reference_manifest_sha256': file_hash(reference / 'manifest.json'),
        'inputs_sha256': digest(cases), 'selection': args.selection,
        'base_model': MODEL, 'revision': REVISION, 'template': TEMPLATE,
        'enable_thinking': False, 'generation': GENERATION,
        'device': args.device, 'precision': args.precision, 'seed': args.seed,
        'seed_policy': 'seed + first 8 hex digits of SHA256(case_id), modulo 2**32',
        'variant': 'sft' if args.adapter else 'base',
        'adapter_path': str(args.adapter.resolve()) if args.adapter else None,
        'training_record_sha256': file_hash(args.run_record) if args.run_record else None,
        'adapter_artifacts': adapter_record.get('adapter_artifacts') if adapter_record else None,
        'case_count': len(cases), 'saved_configuration_groups': sorted({c['saved_group_id'] for c in cases})}
    return cases, identity, adapter_record


def run(args, cases, identity, adapter_record):
    if not args.out:
        raise ValueError('--run requires a fresh --out directory.')
    if args.out.exists():
        raise ValueError('Output exists; preserve previous results and select a fresh directory.')
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed
    if args.device == 'mps' and not torch.backends.mps.is_available():
        raise ValueError('MPS unavailable; choose an explicit supported device for both variants.')
    if args.device == 'cuda' and not torch.cuda.is_available():
        raise ValueError('CUDA unavailable; choose an explicit supported device for both variants.')
    if args.device == 'cpu' and args.precision != 'float32':
        raise ValueError('Use float32 on CPU; this is a different precision group from the saved MPS baseline.')
    if args.device == 'mps' and args.precision == 'bfloat16':
        raise ValueError('Use float16 on MPS for this comparison.')
    versions = {}
    for package in ('torch', 'transformers', 'peft', 'accelerate', 'tokenizers', 'safetensors'):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            pass
    args.out.mkdir(parents=True, exist_ok=False)
    identity.update(started_at=datetime.now(timezone.utc).isoformat(), status='loading',
        python=platform.python_version(), platform=platform.platform(), packages=versions,
        hardware=torch.cuda.get_device_name(0) if args.device == 'cuda' else args.device,
        cuda=torch.version.cuda, runner_sha256=file_hash(Path(__file__)))
    write_json(args.out / 'manifest.json', identity)
    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION)
        template_hash = hashlib.sha256(tokenizer.chat_template.encode()).hexdigest()
        if adapter_record and adapter_record.get('chat_template_sha256') != template_hash:
            raise ValueError('Adapter training chat template differs from pinned inference tokenizer.')
        dtype = {'float16': torch.float16, 'float32': torch.float32, 'bfloat16': torch.bfloat16}[args.precision]
        model = AutoModelForCausalLM.from_pretrained(MODEL, revision=REVISION, torch_dtype=dtype).to(args.device)
        if args.adapter:
            from peft import PeftModel
            model = PeftModel.from_pretrained(model, str(args.adapter), is_trainable=False)
        model.eval()
        # PEFT can upcast adapter storage; retain actual dtype counts for interpretation.
        dtypes = {}
        for _, parameter in model.named_parameters():
            key = str(parameter.dtype)
            dtypes[key] = dtypes.get(key, 0) + parameter.numel()
        identity.update(status='generating', tokenizer_revision=REVISION,
            chat_template_sha256=template_hash, actual_parameter_dtypes=dtypes,
            effective_generation_config=model.generation_config.to_dict(),
            attention_implementation=getattr(model.config, '_attn_implementation', None))
        write_json(args.out / 'manifest.json', identity)
        def sync():
            if args.device == 'mps': torch.mps.synchronize()
            if args.device == 'cuda': torch.cuda.synchronize()
        # Identical excluded warm-up in both runs; case seeds are reset afterwards.
        warmup = tokenizer.apply_chat_template([{'role': 'user', 'content': 'Hi.'}],
            tokenize=False, add_generation_prompt=True, enable_thinking=False)
        warm_inputs = tokenizer(warmup, return_tensors='pt', add_special_tokens=False).to(args.device)
        with torch.inference_mode():
            model.generate(**warm_inputs, max_new_tokens=1, do_sample=False,
                pad_token_id=tokenizer.eos_token_id)
        for case in cases:
            seed = (args.seed + int(hashlib.sha256(case['case_id'].encode()).hexdigest()[:8], 16)) % 2**32
            set_seed(seed)
            rendered = tokenizer.apply_chat_template([{'role': 'system', 'content': case['prompt']}, *case['messages']],
                tokenize=False, add_generation_prompt=True, enable_thinking=False)
            encoded = tokenizer(rendered, return_tensors='pt', add_special_tokens=False).to(args.device)
            if encoded.input_ids.shape[1] + GENERATION['max_new_tokens'] > model.config.max_position_embeddings:
                raise ValueError('Frozen input exceeds model context; do not silently truncate.')
            sync()
            start = time.perf_counter()
            with torch.inference_mode():
                generated = model.generate(**encoded, **GENERATION, pad_token_id=tokenizer.eos_token_id)
            sync()
            latency = time.perf_counter() - start
            token_ids = generated[0, encoded.input_ids.shape[1]:].tolist()
            eos = model.generation_config.eos_token_id or tokenizer.eos_token_id
            eos = eos if isinstance(eos, list) else [eos]
            truncated = len(token_ids) >= GENERATION['max_new_tokens'] and token_ids[-1] not in eos
            row = {**case, 'variant': identity['variant'], 'seed': seed,
                'text': tokenizer.decode(token_ids, skip_special_tokens=True).strip(),
                'output_token_ids': token_ids, 'rendered_input_sha256': hashlib.sha256(rendered.encode()).hexdigest(),
                'input_token_ids_sha256': digest(encoded.input_ids[0].tolist()),
                'input_tokens': encoded.input_ids.shape[1], 'latency_s': latency,
                'status': 'incomplete' if truncated else 'completed', 'truncated': truncated}
            with (args.out / 'responses.jsonl').open('a') as output:
                output.write(canonical(row) + '\n')
                output.flush()
            print(case['case_id'], row['status'], flush=True)
        identity['status'] = 'completed'
    except Exception as exc:
        identity.update(status='failed', error_type=type(exc).__name__)
        write_json(args.out / 'manifest.json', identity)
        raise
    identity['completed_at'] = datetime.now(timezone.utc).isoformat()
    identity['responses_sha256'] = file_hash(args.out / 'responses.jsonl')
    write_json(args.out / 'manifest.json', identity)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, default=Path(__file__).resolve().parent / 'baseline-reference')
    parser.add_argument('--selection', choices=('current-only', 'all-no-thinking'), default='current-only')
    parser.add_argument('--adapter', type=Path)
    parser.add_argument('--run-record', type=Path)
    parser.add_argument('--device', choices=('mps', 'cuda', 'cpu'), default='mps')
    parser.add_argument('--precision', choices=('float16', 'float32', 'bfloat16'), default='float16')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--run', action='store_true', help='Explicitly load local model and generate; may download pinned weights.')
    args = parser.parse_args()
    cases, identity, record = prepare(args)
    if args.run:
        run(args, cases, identity, record)
    else:
        print(json.dumps({'verified_only': True, 'no_model_loaded': True, 'plan': identity}, indent=2))
