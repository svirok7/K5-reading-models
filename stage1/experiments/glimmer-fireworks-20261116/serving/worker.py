#!/usr/bin/env python3
"""One JSON request on stdin, one JSON response on stdout. No implicit retries.

Use training/.venv/bin/python. prepare is completely offline. generate must be
called only after the host app reserves the maximum possible token cost.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import uuid

HERE = Path(__file__).resolve().parent
EXPERIMENT = HERE.parent
TRAINING = EXPERIMENT / 'training'
TOKENIZER = EXPERIMENT / 'data/tokenizer'
BASE_MODEL = 'accounts/fireworks/models/muse-glimmer-30b'
MODEL = 'accounts/svirok123/models/reading-glimmer-sft600-r16-e3-20261116'
RUN = 'accounts/svirok123/trainingRuns/run-4b603d583d83427fa832495d3974576c'
CHECKPOINT = 'svirok123/run-4b603d583d83427fa832495d3974576c/step-114-5490cecd'
SAMPLER_MODEL = 'accounts/svirok123/trainingSamplers/checkpoints/' + CHECKPOINT
API = 'https://api.fireworks.ai/training/v1/serverless'
MAX_INPUT_TOKENS = 8064
MAX_OUTPUT_TOKENS = 128
PREFIX = ' to=user<|message|>'


def identity():
    return {'resolved_model': MODEL, 'sampler_model': SAMPLER_MODEL,
            'checkpoint': CHECKPOINT, 'base_model': BASE_MODEL,
            'tokenizer_revision': 'a4e59da52a7bc87ae7251dd5545c0dd437c44b68',
            'renderer': 'muse_glimmer', 'generation_prefix': PREFIX}


def native():
    sys.path.insert(0, str(TRAINING / 'vendor/cookbook'))
    from transformers import AutoTokenizer
    from training.renderer.muse_glimmer import MuseGlimmerRenderer
    # Hash-check the local tokenizer against the completed training proof.
    proof = json.loads((EXPERIMENT / 'data/token_mask_validation.json').read_text())
    for name, digest in proof['tokenizer_files_sha256'].items():
        if hashlib.sha256((TOKENIZER / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Pinned tokenizer file changed: ' + name)
    tokenizer = AutoTokenizer.from_pretrained(str(TOKENIZER), local_files_only=True, trust_remote_code=False)
    return tokenizer, MuseGlimmerRenderer(tokenizer)


def validate_tokens(tokens):
    if not isinstance(tokens, list) or not tokens or any(type(t) is not int or t < 0 or t >= 202048 for t in tokens):
        raise ValueError('token_ids must be a nonempty list of valid integer token IDs')
    if len(tokens) > MAX_INPUT_TOKENS:
        raise ValueError(f'Input exceeds {MAX_INPUT_TOKENS} token limit')
    return tokens


def prepare(request):
    tokenizer, renderer = native()
    messages = request.get('messages', [])
    if not isinstance(messages, list) or not messages:
        raise ValueError('messages must be a nonempty list')
    clean = []
    instructions = request.get('instructions', '')
    if not isinstance(instructions, str):
        raise ValueError('instructions must be text')
    if instructions:
        clean.append({'role': 'system', 'content': instructions})
    for message in messages:
        if not isinstance(message, dict) or message.get('role') not in ('system', 'user', 'assistant') or not isinstance(message.get('content'), str):
            raise ValueError('messages require text content and system/user/assistant role')
        clean.append({'role': message['role'], 'content': message['content']})
    prompt = renderer.build_generation_prompt(clean, prefill=PREFIX)
    tokens = validate_tokens([int(t) for chunk in prompt.chunks for t in chunk.tokens])
    suffix = tokenizer.encode('<|start|>assistant' + PREFIX, add_special_tokens=False)
    if tokens[-len(suffix):] != suffix:
        raise ValueError('Native final response prefix mismatch')
    return {'status': 'prepared', 'token_ids': tokens, 'input_count': len(tokens),
            'input_tokens': len(tokens), 'max_output_tokens': MAX_OUTPUT_TOKENS, **identity()}


def http_post(path, body, request_id):
    key = os.environ.get('FIREWORKS_API_KEY', '')
    if not key or any(c in key for c in '\r\n"\\'):
        raise ValueError('FIREWORKS_API_KEY is missing or invalid')
    # Credential is sent via curl stdin config; absent from argv and disk.
    config = f'header = "Authorization: Bearer {key}"\n'
    with tempfile.TemporaryDirectory(prefix='glimmer-http-') as tmp:
        payload = Path(tmp) / 'request.json'
        headers = Path(tmp) / 'headers.txt'
        payload.write_text(json.dumps(body))
        proc = subprocess.run(['curl', '--disable', '-4', '--silent', '--show-error', '--retry', '0',
            '--connect-timeout', '15', '--max-time', '180', '--request', 'POST',
            '--config', '-', '--header', 'Content-Type: application/json',
            '--header', 'X-Request-Id: ' + request_id, '--dump-header', str(headers),
            '--data-binary', '@' + str(payload), '--write-out', '\n%{http_code}', API + path],
            input=config, capture_output=True, text=True, timeout=185)
        raw, _, code = proc.stdout.rpartition('\n')
        try:
            parsed = json.loads(raw)
        except ValueError:
            parsed = {'raw_body': raw}
        header_text = headers.read_text() if headers.exists() else ''
        response_headers = {}
        for line in header_text.splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                if k.lower() in ('x-request-id', 'request-id', 'prompt-tokens', 'cached-prompt-tokens', 'completion-tokens', 'server-processing-ms'):
                    response_headers[k.lower()] = v.strip()
        return {'http_status': int(code) if code.isdigit() else 0, 'curl_exit_code': proc.returncode,
                'raw_response': parsed, 'response_headers': response_headers}


def generate(request):
    tokens = validate_tokens(request.get('token_ids'))
    limit = request.get('max_tokens', MAX_OUTPUT_TOKENS)
    if type(limit) is not int or not 1 <= limit <= MAX_OUTPUT_TOKENS:
        raise ValueError('max_tokens must be an integer from 1 to 128')
    temperature = request.get('temperature', 0.0)
    if type(temperature) not in (int, float) or not 0 <= temperature <= 2:
        raise ValueError('temperature must be from 0 to 2')
    top_p = request.get('top_p', 0.8)
    top_k = request.get('top_k', 20)
    if type(top_p) not in (int, float) or not 0 < top_p <= 1:
        raise ValueError('top_p must be greater than 0 and at most 1')
    if type(top_k) is not int or not 0 <= top_k <= 100:
        raise ValueError('top_k must be an integer from 0 to 100')
    tokenizer, _ = native()
    suffix = tokenizer.encode('<|start|>assistant' + PREFIX, add_special_tokens=False)
    if tokens[-len(suffix):] != suffix:
        raise ValueError('Generate requires native final response prefix from prepare')
    request_id = uuid.uuid4().hex
    route = http_post('/api/v1/create_sampling_route', {'training_run': RUN}, request_id + '-route')
    if route['http_status'] != 200 or route['curl_exit_code']:
        return {'status': 'error', 'error': 'sampler_route_failed', 'generation_attempted': False,
                'text': '', 'truncated': False, 'usage': {}, **identity(), **route}
    response = http_post('/inference/v1/completions', {
        'model': SAMPLER_MODEL, 'prompt': tokens, 'max_tokens': limit,
        'temperature': temperature, 'n': 1, 'stream': False, 'raw_output': True,
        'stop': ['<|eot|>'], 'top_p': top_p, 'top_k': top_k,
    }, request_id)
    raw = response['raw_response']
    choice = (raw.get('choices') or [{}])[0]
    raw_output = choice.get('raw_output') or {}
    output_ids = raw_output.get('completion_token_ids')
    raw_text = choice.get('text', '')
    if isinstance(output_ids, list):
        raw_text = tokenizer.decode(output_ids, skip_special_tokens=False)
    text = raw_text.split('<|eot|>', 1)[0]
    usage = raw.get('usage') or {}
    normalized_usage = dict(usage)
    provider_usage = (type(usage.get('prompt_tokens')) is int and usage['prompt_tokens'] >= 0
                      and type(usage.get('completion_tokens')) is int and usage['completion_tokens'] >= 0)
    normalized_usage['input_tokens'] = usage.get('prompt_tokens') if provider_usage else None
    normalized_usage['output_tokens'] = usage.get('completion_tokens') if provider_usage else None
    ok = response['http_status'] == 200 and response['curl_exit_code'] == 0 and bool(raw.get('choices'))
    return {'status': 'ok' if ok else 'error', 'text': text, 'raw_text': raw_text,
            'truncated': choice.get('finish_reason') == 'length', 'finish_reason': choice.get('finish_reason'),
            'usage': normalized_usage, 'usage_source': 'provider' if provider_usage else 'missing',
            'provider_usage': provider_usage, 'input_count': len(tokens), 'response_id': raw.get('id'), 'request_id': request_id,
            'generation_attempted': True, 'max_tokens': limit, 'completion_token_ids': output_ids,
            **identity(), **response}


def main():
    started = time.monotonic()
    try:
        request = json.load(sys.stdin)
        mode = request.get('mode', 'prepare')
        result = prepare(request) if mode == 'prepare' else generate(request) if mode == 'generate' else identity() if mode == 'identity' else {'status': 'error', 'error': 'invalid_mode'}
    except Exception as error:
        # Do not emit stack traces or subprocess input carrying credentials.
        result = {'status': 'error', 'error': type(error).__name__, 'message': str(error), **identity()}
    result['latency_s'] = time.monotonic() - started
    json.dump(result, sys.stdout, ensure_ascii=False)
    sys.stdout.write('\n')

if __name__ == '__main__':
    main()
