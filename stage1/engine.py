"""Shared inference and diagnostics. No network/model loading at import time."""
import hashlib
import json
import re
import ssl
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
def api_tls_context():
    # Respect configured CA paths; python.org macOS installs may lack their own bundle.
    paths = ssl.get_default_verify_paths()
    if paths.cafile is None and paths.capath is None and sys.platform == 'darwin':
        system_ca = Path('/etc/ssl/cert.pem')
        if system_ca.is_file():
            return ssl.create_default_context(cafile=str(system_ca))
    return ssl.create_default_context()

DIMENSIONS = ['readability', 'correctness', 'relevance', 'flow', 'warmth']

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

def reader_profile():
    source = json.loads((ROOT/'data/dolch-through-grade1.json').read_text())
    lines = [name.replace('_', ' ') + ': ' + ', '.join(words) for name, words in source['groups'].items()]
    return (ROOT/'READER_PROFILE.txt').read_text().strip().replace('{{DOLCH_WORDS}}', '\n'.join(lines))

def prompt_for(condition):
    if condition not in ('A', 'B'):
        raise ValueError('Condition must be A or B')
    text = (ROOT / 'prompts' / f'{condition}.txt').read_text().strip()
    return text.replace('{{READER_PROFILE}}', reader_profile()) if condition == 'B' else text

def diagnostics(text):
    words = re.findall(r"[A-Za-z]+(?:['’][A-Za-z]+)?|\d+", text)
    sentences = [s for s in re.split(r'[.!?]+', text) if re.search(r'\w', s)]
    sizes = [len(re.findall(r"[A-Za-z]+(?:['’][A-Za-z]+)?|\d+", s)) for s in sentences]
    return {'words': len(words), 'sentences': len(sizes), 'longest_sentence': max(sizes, default=0),
            'sentences_over_12_words': sum(n > 12 for n in sizes)}

def transcript(instructions, messages):
    labels = {'user': 'Child', 'assistant': 'Companion'}
    return instructions + '\n\n' + '\n'.join(f"{labels[m['role']]}: {m['content']}" for m in messages) + '\nCompanion:'

class OpenAIEngine:
    def __init__(self, model_id, api_key, max_tokens=512, options=None):
        if not model_id or not api_key:
            raise ValueError('Set an OpenAI model ID and API key first.')
        self.model_id, self.api_key = model_id, api_key
        self.max_tokens, self.options = max_tokens, options or {}
        if set(self.options) - {'temperature', 'top_p', 'reasoning', 'text'}:
            raise ValueError('Unsupported OpenAI override; use temperature, top_p, reasoning, or text.')
        self.metadata = {'backend': 'openai', 'model': model_id, 'max_output_tokens': max_tokens,
                         'options': self.options, 'transport': 'Responses API; non-streaming; no retries'}

    def generate(self, instructions, messages):
        start = time.perf_counter()
        body = {'model': self.model_id, 'instructions': instructions, 'input': messages,
                'max_output_tokens': self.max_tokens, 'store': False, **self.options}
        req = urllib.request.Request('https://api.openai.com/v1/responses',
            data=json.dumps(body).encode(), headers={'Authorization': 'Bearer ' + self.api_key,
            'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=180, context=api_tls_context()) as response:
            obj = json.load(response)
        texts = []
        for item in obj.get('output', []):
            if item.get('type') == 'message':
                for part in item.get('content', []):
                    if part.get('type') == 'output_text': texts.append(part.get('text', ''))
                    elif part.get('type') == 'refusal': texts.append(part.get('refusal', ''))
        text = '\n'.join(texts)
        status = obj.get('status', 'unknown')
        return {'text': text, 'latency_s': time.perf_counter()-start, 'status': status,
                'truncated': status == 'incomplete', 'usage': obj.get('usage'),
                'resolved_model': obj.get('model'), 'response_id': obj.get('id'),
                'finish_details': obj.get('incomplete_details'), 'diagnostics': diagnostics(text)}

class ClaudeEngine:
    def __init__(self, model_id, api_key, max_tokens=512, options=None):
        if not model_id or not api_key:
            raise ValueError('Set a Claude model ID and Anthropic API key first.')
        self.model_id, self.api_key, self.max_tokens = model_id, api_key, max_tokens
        self.options = options or {}
        if set(self.options) - {'thinking', 'output_config'}:
            raise ValueError('Unsupported Claude override; use thinking or output_config.')
        self.metadata = {'backend': 'claude', 'model': model_id, 'max_tokens': max_tokens,
                         'transport': 'Anthropic Messages API; no retries'}
        if self.options:
            self.metadata['options'] = self.options

    def generate(self, instructions, messages):
        start = time.perf_counter()
        body = {'model': self.model_id, 'system': instructions,
                'messages': messages, 'max_tokens': self.max_tokens, **self.options}
        req = urllib.request.Request('https://api.anthropic.com/v1/messages',
            data=json.dumps(body).encode(), headers={'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01', 'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=180, context=api_tls_context()) as response:
            obj = json.load(response)
        text = '\n'.join(p.get('text', '') for p in obj.get('content', []) if p.get('type') == 'text')
        truncated = obj.get('stop_reason') == 'max_tokens'
        return {'text': text, 'latency_s': time.perf_counter()-start,
                'status': 'incomplete' if truncated else 'completed', 'truncated': truncated,
                'usage': obj.get('usage'), 'resolved_model': obj.get('model'),
                'response_id': obj.get('id'), 'finish_details': obj.get('stop_reason'),
                'diagnostics': diagnostics(text)}

class SarvamEngine:
    base_model = 'sarvamai/sarvam-1'
    backend = 'sarvam'
    generation_options = {'do_sample': False}
    def __init__(self, adapter=None, max_tokens=128):
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
            from huggingface_hub import model_info
        except ImportError as exc:
            raise RuntimeError('Install requirements-model.txt in the Python environment running the server, or use Colab.') from exc
        self.torch = torch
        self.max_tokens = max_tokens
        base = self.base_model
        revision = model_info(base).sha
        kwargs = {'revision': revision}
        if torch.cuda.is_available():
            device, precision = 'cuda', '4-bit NF4 / float16 compute'
            kwargs.update(device_map={'': 0}, quantization_config=BitsAndBytesConfig(
                load_in_4bit=True, bnb_4bit_quant_type='nf4', bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True))
        elif torch.backends.mps.is_available():
            device, precision = 'mps', 'float16'
            kwargs['torch_dtype'] = torch.float16
        else:
            device, precision = 'cpu', 'float32'
            kwargs['torch_dtype'] = torch.float32
        self.tokenizer = AutoTokenizer.from_pretrained(base, revision=revision)
        self.model = AutoModelForCausalLM.from_pretrained(base, **kwargs)
        if device != 'cuda': self.model = self.model.to(device)
        adapter_hash = None
        if adapter:
            from peft import PeftModel
            path = Path(adapter).expanduser().resolve()
            if not (path / 'adapter_config.json').exists():
                raise ValueError('Adapter directory must contain adapter_config.json.')
            config = json.loads((path / 'adapter_config.json').read_text())
            if config.get('base_model_name_or_path') != base:
                raise ValueError(f'Adapter must be trained on {base}.')
            hasher = hashlib.sha256()
            for file in sorted(path.glob('*')):
                if file.is_file() and file.suffix in ('.json', '.bin', '.safetensors'):
                    hasher.update(file.name.encode())
                    with file.open('rb') as f:
                        for chunk in iter(lambda: f.read(1024*1024), b''): hasher.update(chunk)
            adapter_hash = hasher.hexdigest()
            self.model = PeftModel.from_pretrained(self.model, str(path))
        self.model.eval()
        self.device = device
        self.metadata = {'backend': self.backend, 'model': base, 'revision': revision,
            'adapter': str(adapter) if adapter else None, 'adapter_hash': adapter_hash,
            'device': device, 'precision': precision, 'max_new_tokens': max_tokens, **self.generation_options,
            'template': 'qwen-chat-v1; enable_thinking=False' if self.backend == 'qwen' else 'child-companion-transcript-v1',
            'hardware': torch.cuda.get_device_name(0) if device == 'cuda' else device}
        # One excluded warm-up, also catches device/runtime incompatibility early.
        self.generate(prompt_for('A'), [{'role': 'user', 'content': 'Hi.'}])

    def sync(self):
        if self.device == 'cuda': self.torch.cuda.synchronize()
        if self.device == 'mps': self.torch.mps.synchronize()

    def encode(self, instructions, messages):
        return self.tokenizer(transcript(instructions, messages), return_tensors='pt')

    def generate(self, instructions, messages):
        self.sync()
        start = time.perf_counter()
        inputs = self.encode(instructions, messages).to(self.device)
        if inputs.input_ids.shape[1] + self.max_tokens > self.model.config.max_position_embeddings:
            raise ValueError('Conversation exceeds model context; start a new chat.')
        with self.torch.inference_mode():
            output = self.model.generate(**inputs, max_new_tokens=self.max_tokens, **self.generation_options,
                pad_token_id=self.tokenizer.eos_token_id)
        self.sync()
        generated = output[0, inputs.input_ids.shape[1]:]
        text = self.tokenizer.decode(generated, skip_special_tokens=True).strip()
        eos = self.model.generation_config.eos_token_id or self.tokenizer.eos_token_id
        eos = eos if isinstance(eos, list) else [eos]
        ended = bool(len(generated) and generated[-1].item() in eos)
        truncated = len(generated) >= self.max_tokens and not ended
        return {'text': text, 'latency_s': time.perf_counter()-start,
                'status': 'incomplete' if truncated else 'completed', 'truncated': truncated,
                'usage': {'input_tokens': inputs.input_ids.shape[1], 'output_tokens': len(generated)},
                'diagnostics': diagnostics(text)}


class QwenEngine(SarvamEngine):
    base_model = 'Qwen/Qwen3-1.7B'
    backend = 'qwen'
    generation_options = {'do_sample': True, 'temperature': 0.7, 'top_p': 0.8, 'top_k': 20}

    def encode(self, instructions, messages):
        text = self.tokenizer.apply_chat_template(
            [{'role': 'system', 'content': instructions}, *messages],
            tokenize=False, add_generation_prompt=True, enable_thinking=False)
        return self.tokenizer(text, return_tensors='pt', add_special_tokens=False)
