"""Fixed trained Glimmer checkpoint and shared, durable testing budget."""
import json
import os
from pathlib import Path
import subprocess
import time
import uuid

from engine import ROOT, OpenAIEngine, diagnostics
from testing_budget import BudgetLedger

MODEL = 'accounts/svirok123/models/reading-glimmer-sft600-r16-e3-20261116'
EXPERIMENT = ROOT / 'experiments/glimmer-fireworks-20261116'
PYTHON = EXPERIMENT / 'training/.venv/bin/python'
WORKER = EXPERIMENT / 'serving/worker.py'


def ledger():
    return BudgetLedger(ROOT / 'runs/glimmer-testing-budget.sqlite3', cap_usd='3.99')


class GlimmerTestingEngine:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError('Set the Fireworks API key in Settings first.')
        self.api_key = api_key
        self.metadata = {'backend':'fireworks_sampler', 'model':MODEL,
                         'training_examples':600, 'epochs':3, 'max_tokens':128,
                         'transport':'Fireworks checkpoint sampler; no deployment; no retries',
                         'options':{'temperature':0.7, 'top_p':0.8, 'top_k':20}}

    def _worker(self, payload):
        env = dict(os.environ, FIREWORKS_API_KEY=self.api_key)
        try:
            process = subprocess.run([str(PYTHON), str(WORKER)], input=json.dumps(payload),
                                     text=True, capture_output=True, timeout=180, env=env)
        except subprocess.TimeoutExpired:
            raise RuntimeError('Glimmer request timed out. No automatic retry was made.') from None
        if process.returncode:
            # Worker logs may contain provider payloads: do not expose them here.
            raise RuntimeError('Glimmer checkpoint sampler is unavailable. No automatic retry was made.')
        value = json.loads(process.stdout)
        if value.get('error') or value.get('status') == 'error':
            raise RuntimeError('Glimmer checkpoint sampler returned an error. No automatic retry was made.')
        return value

    def generate(self, instructions, messages):
        start = time.perf_counter()
        prepared = self._worker({'mode':'prepare', 'instructions':instructions, 'messages':messages})
        tokens = prepared['token_ids']
        if not isinstance(tokens, list) or any(type(t) is not int or t < 0 for t in tokens):
            raise ValueError('Invalid Glimmer tokenization result.')
        budget = ledger()
        reservation = budget.reserve('glimmer', len(tokens), 128, model=MODEL, request_id=str(uuid.uuid4()))
        try:
            result = self._worker({'mode':'generate', 'token_ids':tokens, 'max_tokens':128,
                                   'temperature':0.7, 'top_p':0.8, 'top_k':20})
        except Exception:
            budget.fail(reservation)
            raise
        # A paid reply remains visible even if local accounting encounters an
        # error. Its full reservation stays held, preventing an implicit retry.
        try:
            usage = result.get('usage') or {}
            if result.get('usage_source') == 'provider' and type(usage.get('input_tokens')) is int and type(usage.get('output_tokens')) is int:
                budget.settle(reservation, input_tokens=usage['input_tokens'], output_tokens=usage['output_tokens'])
            result['testing_budget'] = budget.status()
        except Exception:
            result['budget_warning'] = 'Reply saved; budget reconciliation needs review. No automatic retry was made.'
        text = result.get('text') or ''
        result['status'] = 'completed' if result.get('finish_reason') == 'stop' and text.strip() else 'incomplete'
        result['latency_s'] = time.perf_counter() - start
        result['finish_details'] = result.get('finish_reason')
        result['diagnostics'] = diagnostics(text)
        return result


class BudgetedReadingJudge(OpenAIEngine):
    """Same existing judge/settings, with a conservative reservation first."""
    def __init__(self, model_id, api_key, max_tokens=3000, options=None):
        super().__init__(model_id, api_key, max_tokens,
                         {**(options or {}), 'service_tier':'default'})

    def generate(self, instructions, messages):
        # UTF-8 bytes upper-bound text BPE tokens. Include schema and extra room
        # for message framing; this is deliberately more conservative than a
        # tokenizer estimate. No tools, Fast mode, or regional routing are used.
        body = {'model':self.model_id, 'instructions':instructions, 'input':messages,
                'max_output_tokens':self.max_tokens, 'store':False, **self.options}
        bound = len(json.dumps(body, ensure_ascii=False).encode('utf-8')) + 2048
        budget = ledger()
        reservation = budget.reserve('judge', bound, self.max_tokens,
                                     model=self.model_id, request_id=str(uuid.uuid4()))
        try:
            result = super().generate(instructions, messages)
        except Exception:
            budget.fail(reservation)
            raise
        try:
            usage = result.get('usage') or {}
            if type(usage.get('input_tokens')) is int and type(usage.get('output_tokens')) is int:
                budget.settle(reservation, input_tokens=usage['input_tokens'], output_tokens=usage['output_tokens'])
        except Exception:
            result['budget_warning'] = 'Judge response preserved; full budget reservation retained for review.'
        return result


def eligible_record(row):
    model = row.get('response', {}).get('model', {})
    return model.get('backend') == 'fireworks_sampler' and model.get('model') == MODEL
