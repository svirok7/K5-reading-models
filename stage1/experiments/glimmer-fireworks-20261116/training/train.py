#!/usr/bin/env python3
"""Pinned Fireworks Serverless SFT. Plan/status are local; account-check is GET only."""
from __future__ import annotations
import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import logging
import os
from pathlib import Path
import re
import subprocess
import socket
import sys
from datetime import date, datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
DATA = HERE.parent / 'data'
DATASET = DATA / 'train.messages.jsonl'
RUN = HERE / 'run'
PIN = '74e103ab4249d508912ccf264793e655980eead0'
DEADLINE = datetime(2026, 12, 1, 8, tzinfo=timezone.utc)


def prefer_fireworks_ipv4():
    """Avoid this host's unreachable Fireworks IPv6 routes; retain TLS validation."""
    original = getattr(socket.getaddrinfo, '_original_resolver', socket.getaddrinfo)
    def resolve(host, port, family=0, type=0, proto=0, flags=0):
        hostname = host.decode('ascii') if isinstance(host, bytes) else host
        fireworks = isinstance(hostname, str) and (hostname == 'fireworks.ai' or hostname.endswith('.fireworks.ai'))
        selected = socket.AF_INET if fireworks else family
        return original(host, port, selected, type, proto, flags)
    resolve._original_resolver = original
    socket.getaddrinfo = resolve


def send_heartbeat(session_id):
    """Send only the SDK keepalive through this host's working curl transport."""
    if not re.fullmatch(r'ts-[A-Za-z0-9-]+', session_id):
        raise ValueError('Invalid heartbeat session ID')
    request_config = ('url = "https://api.fireworks.ai/training/v1/serverless/api/v1/session_heartbeat"\n'
                      'header = "Authorization: Bearer ' + os.environ['FIREWORKS_API_KEY'] + '"\n'
                      'header = "Content-Type: application/json"\n')
    result = subprocess.run(['curl', '-4', '--silent', '--show-error', '--max-time', '15',
                             '--config', '-', '--data', json.dumps({'session_id': session_id}),
                             '-w', '\n%{http_code}'], input=request_config, text=True,
                            capture_output=True, timeout=20)
    return result.returncode == 0 and result.stdout.rpartition('\n')[2] == '200'


def install_heartbeat_transport():
    """Preserve the SDK ten-second keepalive without its failing async HTTP path."""
    from fireworks.training.sdk._core.lib.internal_client_holder import InternalClientHolder
    async def heartbeat(self, session_id):
        last_success = None
        while True:
            try:
                success = await asyncio.to_thread(send_heartbeat, session_id)
            except Exception:
                success = False
            if success:
                last_success = datetime.now(timezone.utc).isoformat()
            RUN.mkdir(exist_ok=True)
            (RUN / 'heartbeat.json').write_text(json.dumps({
                'session_id': session_id, 'transport': 'curl IPv4; TLS verified',
                'checked_at': datetime.now(timezone.utc).isoformat(),
                'success': success, 'last_success_utc': last_success}) + '\n')
            if not success:
                logging.getLogger(__name__).warning('Training keepalive failed; no credentials or provider payload logged.')
            await asyncio.sleep(10)
    InternalClientHolder._session_heartbeat = heartbeat


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_credentials():
    """Load only Fireworks keys; never print or persist their values."""
    path = PROJECT / '.env'
    if path.exists():
        for line in path.read_text().splitlines():
            m = re.match(r'\s*(?:export\s+)?(FIREWORKS_API_KEY|FIREWORKS_ACCOUNT_ID)\s*=\s*(.*?)\s*$', line)
            if m:
                value = m[2].strip('"\'')
                os.environ.setdefault(m[1], value)
    return {'api_key_available': bool(os.environ.get('FIREWORKS_API_KEY')),
            'account_id_available': bool(os.environ.get('FIREWORKS_ACCOUNT_ID'))}


def config():
    return json.loads((HERE / 'config.json').read_text())


def validate_config(cfg):
    expected = {'serverless': True, 'base_model': 'accounts/fireworks/models/muse-glimmer-30b',
                'tokenizer_model': 'meta-models/Muse-Glimmer-30B',
                'tokenizer_revision': 'a4e59da52a7bc87ae7251dd5545c0dd437c44b68',
                'renderer_name': 'muse_glimmer', 'train_on_what': 'last_assistant_message',
                'lora_rank': 16, 'epochs': 3, 'eval_auto_carveout': False, 'generation_eval': False,
                'evaluation_dataset': '', 'max_examples': None, 'sampler_save_interval': 0,
                'max_seq_len': 8192, 'save_final_checkpoint': True}
    for key, value in expected.items():
        if cfg.get(key) != value:
            raise ValueError(f'Unsafe/changed configuration: {key}')


def data_gate(cfg):
    identity = json.loads((DATA / 'validation.json').read_text())
    mask = json.loads((DATA / 'token_mask_validation.json').read_text())
    if identity.get('status') != 'passed' or identity.get('row_count') != 600:
        raise ValueError('Dataset identity validation must pass for all 600 rows')
    required = {'status': 'passed', 'row_count': 600, 'train_on_what': 'last_assistant_message',
                'renderer': 'muse_glimmer', 'context_loss_positions': 0, 'dropped_rows': 0,
                'truncated_rows': 0, 'dataset_sha256': sha256(DATASET)}
    for key, value in required.items():
        if mask.get(key) != value:
            raise ValueError(f'Token/loss validation gate failed: {key}')
    rows = [json.loads(line) for line in DATASET.read_text().splitlines() if line.strip()]
    if len(rows) != 600 or any(row['messages'][-1]['role'] != 'assistant' for row in rows):
        raise ValueError('Expected exactly 600 rows ending in final assistant')
    maximum = mask.get('max_rendered_tokens', mask.get('max_sequence_tokens'))
    if maximum is not None and maximum > cfg['max_seq_len']:
        raise ValueError('Configured max_seq_len would drop a validated row')
    if mask.get('tokenizer_revision') != cfg['tokenizer_revision']:
        raise ValueError('Tokenizer revision differs from the actual loss-mask proof')
    if mask.get('cookbook_revision') != PIN:
        raise ValueError('Renderer source differs from the actual loss-mask proof')
    snapshot = DATA / 'tokenizer'
    if sha256(snapshot / 'snapshot_manifest.json') != mask.get('tokenizer_snapshot_manifest_sha256'):
        raise ValueError('Pinned tokenizer snapshot manifest changed since token-mask validation')
    for name, digest in mask.get('tokenizer_files_sha256', {}).items():
        if Path(name).name != name or sha256(snapshot / name) != digest:
            raise ValueError('Pinned tokenizer snapshot file changed since token-mask validation')
    if not mask.get('tokenizer_files_sha256'):
        raise ValueError('Token-mask proof must pin the tokenizer snapshot files')
    proof_path = DATA / 'token_mask_proofs.jsonl'
    if sha256(proof_path) != mask.get('proofs_sha256'):
        raise ValueError('Token-mask proof file changed after validation')
    proofs = [json.loads(line) for line in proof_path.read_text().splitlines() if line.strip()]
    if len(proofs) != 600 or any(p.get('context_loss_positions') != 0 or p.get('datums') != 1 for p in proofs):
        raise ValueError('Each of the 600 rows must have exactly one datum and zero context-loss positions')
    return mask


def source_gate():
    vendor = HERE / 'vendor/cookbook'
    actual = subprocess.check_output(['git', '-C', str(vendor), 'rev-parse', 'HEAD'], text=True).strip()
    if actual != PIN:
        raise ValueError('Cookbook source commit mismatch')
    lock = json.loads((HERE / 'sources.json').read_text())
    for relative, expected in lock['local_source_sha256'].items():
        if sha256(vendor / relative) != expected:
            raise ValueError(f'Pinned source file modified: {relative}')


def recipe_preflight(cfg):
    """Initialize and render all rows through the exact recipe locally, before any session."""
    import training.renderer.muse_glimmer as muse
    frozen_date = json.loads((DATA / 'token_mask_validation.json').read_text())['rendered_current_date']
    class FrozenRenderDate(date):
        @classmethod
        def today(cls):
            return date.fromisoformat(frozen_date)
    muse.date = FrozenRenderDate
    if cfg['render_workers'] != 0:
        raise ValueError('Resume uses in-process rendering to preserve the frozen template date')
    # Resume must retain the original native-template date, even after midnight.
    # In-process rendering keeps this runtime override in every recipe render.
    import training.renderer.muse_glimmer as muse
    frozen_date = date.fromisoformat(json.loads((DATA / 'token_mask_validation.json').read_text())['rendered_current_date'])
    class TrainingDate(date):
        @classmethod
        def today(cls):
            return frozen_date
    muse.date = TrainingDate
    if cfg['render_workers'] != 0:
        raise ValueError('Date-pinned resume requires in-process rendering')
    import training.recipes.sft_loop as recipe
    if Path(recipe.__file__).resolve() != (HERE / 'vendor/cookbook/training/recipes/sft_loop.py').resolve():
        raise ValueError('Imported recipe does not resolve to the verified pinned cookbook checkout')
    recipe._init_render_worker(str(DATA / 'tokenizer'), cfg['renderer_name'], cfg['train_on_what'],
                               cfg['max_seq_len'], cfg['tokenizer_revision'],
                               tokenizer_trust_remote_code=False, base_model=cfg['base_model'])
    proofs = [json.loads(line) for line in (DATA / 'token_mask_proofs.jsonl').read_text().splitlines()]
    def digest(value):
        return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    for index, line in enumerate(DATASET.read_text().splitlines(), 1):
        rendered = recipe._render_one_worker(json.loads(line))
        if rendered is None or not hasattr(rendered, 'loss_fn_inputs'):
            raise ValueError(f'Actual recipe failed to produce a training datum for row {index}')
        tokens = [int(t) for chunk in rendered.model_input.chunks for t in chunk.tokens]
        targets = [int(t) for t in rendered.loss_fn_inputs['target_tokens'].data]
        weights = [float(w) for w in rendered.loss_fn_inputs['weights'].data]
        if digest(tokens + [targets[-1]]) != proofs[index-1]['full_token_ids_sha256'] or digest(weights) != proofs[index-1]['training_weights_sha256']:
            raise ValueError(f'Resume rendering differs from the original token/mask proof at row {index}')


def plan():
    cfg = config()
    validate_config(cfg)
    return {'surface': 'Serverless Training API', 'advertised_training_usd': 0 if datetime.now(timezone.utc) < DEADLINE else None,
            'promotion_deadline_utc': DEADLINE.isoformat(), 'credentials': load_credentials(),
            'dataset': str(DATASET), 'rows': 600, 'optimizer_steps_expected': 114,
            'config': cfg, 'cookbook_commit': PIN, 'inference_calls': 0,
            'dedicated_training_or_deployment': False,
            'promotion_eligibility': 'Public and logged-in account UI advertise free serverless SFT through Nov30. No inference or dedicated resources allowed.'}


def read_account():
    if not load_credentials()['api_key_available']:
        return {'status': 'blocked', 'reason': 'FIREWORKS_API_KEY unavailable; account eligibility cannot be verified'}
    request = Request('https://api.fireworks.ai/v1/accounts?pageSize=10',
                      headers={'Authorization': 'Bearer ' + os.environ['FIREWORKS_API_KEY']})
    try:
        completed = subprocess.run(['curl', '--silent', '--show-error', '--fail', '--max-time', '30', '--config', '-'], input='url = "https://api.fireworks.ai/v1/accounts?pageSize=10"\nheader = "Authorization: Bearer ' + os.environ['FIREWORKS_API_KEY'] + '"\n', text=True, capture_output=True, timeout=35)
        if completed.returncode:
            return {'status': 'blocked', 'reason': 'Read-only Fireworks account GET failed', 'curl_exit_code': completed.returncode}
        result = json.loads(completed.stdout)
        accounts = result.get('accounts', [])
        result = {'status': 'authenticated', 'accounts': [a.get('name') for a in accounts],
                'single_account_key': len(accounts) == 1,
                'eligibility': 'Account authentication verified; public SFT promotion applies, no account-specific price quote exposed by this GET.'}
        (HERE / 'account-check.json').write_text(json.dumps(result, indent=2) + '\n')
        return result
    except HTTPError as exc:
        return {'status': 'blocked', 'http_status': exc.code, 'reason': 'Fireworks account GET rejected'}
    except (URLError, TimeoutError, subprocess.TimeoutExpired):
        return {'status': 'blocked', 'reason': 'Network unavailable for read-only account GET'}


def latest_checkpoint():
    path = RUN / 'dataloader.json'
    if not path.exists():
        raise ValueError('No committed dataloader checkpoint manifest exists yet')
    payload = json.loads(path.read_text())
    entries = payload.get('checkpoints', payload)
    if not entries:
        raise ValueError('No resumable checkpoint has been saved yet')
    key = max(entries, key=lambda k: entries[k].get('step', 0) if isinstance(entries[k], dict) else entries[k])
    text = (HERE / 'train.log').read_text() if (HERE / 'train.log').exists() else ''
    matches = re.findall(r"init_from_checkpoint='([^']+)/<checkpoint>'", text)
    if not matches:
        raise ValueError('Cannot recover account/run from train.log; provide --checkpoint account/run-hex/step-N')
    run_id = matches[-1].split('/')[-1]
    for separator in ('-', ':'):
        prefix = run_id + separator
        if key.startswith(prefix):
            key = key[len(prefix):]
            break
    return matches[-1] + '/' + key


def launch(checkpoint=None):
    cfg = config()
    validate_config(cfg)
    source_gate()
    data_gate(cfg)
    recipe_preflight(cfg)
    subprocess.run([sys.executable, str(DATA / 'convert_dataset.py'), '--verify-only'],
                   check=True, stdout=subprocess.DEVNULL)
    if datetime.now(timezone.utc) >= DEADLINE:
        raise ValueError('Free SFT promotion ended; this runner never opts into paid training')
    if not load_credentials()['api_key_available']:
        raise ValueError('FIREWORKS_API_KEY unavailable; set it privately in project .env or process environment')
    account = json.loads((HERE / 'account-check.json').read_text())
    if account.get('status') != 'authenticated' or not account.get('single_account_key'):
        raise ValueError('Read-only account authentication must succeed for a single-account key')
    previous = HERE / 'launch-record.json'
    if previous.exists() and checkpoint is None:
        raise ValueError('A launch record exists. Use resume to avoid starting a duplicate experiment.')
    if not cfg.get('tokenizer_revision'):
        raise ValueError('Pin tokenizer_revision to the commit used in data/token_mask_validation.json first')
    prefer_fireworks_ipv4()
    install_heartbeat_transport()
    # No remote resources exist before these checks. Fail imports before writing a launch marker.
    from training.recipes.sft_loop import Config, main
    import training.recipes.sft_loop as executed_recipe
    if Path(executed_recipe.__file__).resolve() != (HERE / 'vendor/cookbook/training/recipes/sft_loop.py').resolve():
        raise ValueError('Imported recipe does not resolve to the verified pinned cookbook checkout')
    from training.utils import RunnerConfig, WandBConfig
    RUN.mkdir(exist_ok=True)
    cfg.update(dataset=str(DATASET), log_path=str(RUN), render_samples_file=str(RUN / 'rendered-training.jsonl'),
               tokenizer_model=str(DATA / 'tokenizer'), tokenizer_trust_remote_code=False,
               runner=RunnerConfig(status_file=str(RUN / 'status.json'), metadata_file=str(RUN / 'metadata.json'),
                                   metrics_file=str(RUN / 'metrics.jsonl'), output_model_path=str(RUN / 'output-model.json')),
               wandb=WandBConfig(), init_from_checkpoint=checkpoint)
    if checkpoint:
        cfg['prefer_current_run_checkpoint'] = True
    record = {'started_utc': datetime.now(timezone.utc).isoformat(), 'dataset_sha256': sha256(DATASET),
              'config_sha256': sha256(HERE / 'config.json'), 'cookbook_commit': PIN, 'checkpoint': checkpoint,
              'dependencies': {n: importlib.metadata.version(n) for n in ('fireworks-ai', 'fireworks-training-cookbook', 'transformers', 'torch')}}
    previous.write_text(json.dumps(record, indent=2) + '\n')
    logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler(HERE / 'train.log'), logging.StreamHandler()])
    main(Config(**cfg))


def status():
    result = {'credentials': load_credentials(), 'launch_record_exists': (HERE / 'launch-record.json').exists()}
    for name in ('status.json', 'metadata.json', 'output-model.json'):
        p = RUN / name
        if p.exists():
            result[name] = json.loads(p.read_text())
    return result


def cli():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['plan', 'preflight', 'account-check', 'launch', 'resume', 'status'])
    p.add_argument('--checkpoint')
    args = p.parse_args()
    try:
        if args.command == 'plan': result = plan()
        elif args.command == 'account-check': result = read_account()
        elif args.command == 'status': result = status()
        elif args.command == 'preflight':
            cfg = config(); validate_config(cfg); source_gate()
            mask = data_gate(cfg); recipe_preflight(cfg)
            result = {'status': 'passed', 'data_validation': mask, 'credentials': load_credentials()}
        else:
            launch(args.checkpoint or (latest_checkpoint() if args.command == 'resume' else None))
            return 0
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, FileNotFoundError, ImportError) as exc:
        print(json.dumps({'status': 'blocked', 'reason': str(exc)}))
        return 2

if __name__ == '__main__':
    sys.exit(cli())
