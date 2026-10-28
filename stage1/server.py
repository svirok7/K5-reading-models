"""Local-only development UI. python3 server.py; visit http://127.0.0.1:8765."""
import argparse
import gc
import json
import os
import ssl
import socket
import threading
import urllib.error
import records
import evaluator
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from engine import ROOT, OpenAIEngine, ClaudeEngine, SarvamEngine, QwenEngine, prompt_for

LOCK = threading.Lock()
STATE = {'key': os.environ.get('OPENAI_API_KEY',''), 'openai_model':os.environ.get('OPENAI_MODEL',''), 'claude_key':os.environ.get('ANTHROPIC_API_KEY',''), 'claude_model':os.environ.get('ANTHROPIC_MODEL',''), 'engine':None, 'engine_id':None}
PORT = int(os.environ.get('READING_MODEL_PORT','8765'))

def registry(): return json.loads((ROOT/'models.json').read_text())

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_): pass
    def send(self, status, data, kind='application/json'):
        raw = json.dumps(data).encode() if kind == 'application/json' else data
        self.send_response(status);self.send_header('Content-Type',kind)
        self.send_header('Content-Length',str(len(raw))); self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff'); self.end_headers(); self.wfile.write(raw)
    def valid_host(self):
        return self.headers.get('Host') in (f'127.0.0.1:{PORT}',f'localhost:{PORT}')
    def do_GET(self):
        if not self.valid_host(): return self.send(403,{'error':'Localhost only.'})
        if self.path in ('/api/records', '/api/records/archived'):
            archived = self.path.endswith('/archived')
            rows = [r for r in records.all_records() if bool(r.get('archived_at')) == archived]
            return self.send(200, {'records': rows, 'summary': records.summaries(rows)})
        if self.path == '/api/config':
            models=registry()
            for value in models.values():
                value['available'] = not value.get('pending',False) or bool(value.get('adapter'))
            return self.send(200,{'models':models,'key_set':bool(STATE['key']), 'openai_model':STATE['openai_model'],
                'api_models':json.loads((ROOT/'api-models.json').read_text()), 'claude_key_set':bool(STATE['claude_key']), 'claude_model':STATE['claude_model'],
                'dev':[json.loads(x) for x in (ROOT/'data/dev.jsonl').read_text().splitlines()],
                'prompts':{k:prompt_for(k) for k in ['A','B']}})
        files={'/':('ui/index.html','text/html; charset=utf-8'),'/app.js':('ui/app.js','text/javascript'),
               '/style.css':('ui/style.css','text/css'), '/rubric':('RUBRIC.md','text/plain; charset=utf-8')}
        if self.path not in files: return self.send(404,{'error':'Not found'})
        name,kind=files[self.path];self.send(200,(ROOT/name).read_bytes(),kind)
    def do_POST(self):
        origin=self.headers.get('Origin')
        if not self.valid_host() or origin not in (f'http://127.0.0.1:{PORT}',f'http://localhost:{PORT}'):
            return self.send(403,{'error':'Use the localhost UI.'})
        if self.headers.get('Content-Type') != 'application/json': return self.send(415,{'error':'JSON required.'})
        size=int(self.headers.get('Content-Length','0'))
        if size > 100_000: return self.send(413,{'error':'Message too large.'})
        try: data=json.loads(self.rfile.read(size))
        except Exception: return self.send(400,{'error':'Invalid JSON.'})
        if self.path == '/api/settings':
            with LOCK:
                provider = data.get('provider', 'openai')
                if provider not in ('openai', 'claude'): return self.send(400, {'error':'Unknown provider.'})
                key_field = 'key' if provider == 'openai' else 'claude_key'
                if data.get('clear_key'): STATE[key_field]=''
                elif data.get('api_key'): STATE[key_field]=str(data['api_key'])
                STATE[provider+'_model']=str(data.get('model','')).strip()
            return self.send(200,{'saved':True,'key_set':bool(STATE[key_field])})
        if self.path == '/api/manual':
            try:
                row = records.set_manual(data.get('id'), data.get('decision'), data.get('reason',''))
                return self.send(200, {'record':row})
            except ValueError as exc: return self.send(400, {'error':str(exc)})
        if self.path == '/api/evaluate':
            if not LOCK.acquire(blocking=False): return self.send(409, {'error':'A generation is running; retry evaluation shortly.'})
            try:
                row = records.get(data.get('id'))
                if not row.get('evaluation'):
                    try:
                        value = evaluator.evaluate(row, STATE['key'])
                        row = records.update(row['id'], evaluation=value, evaluation_error=None)
                    except Exception as exc:
                        # Never expose provider payloads or credentials.
                        error = 'Evaluator unavailable ('+type(exc).__name__+'). Manual decision is available.'
                        row = records.update(row['id'], evaluation_error=error)
                return self.send(200, {'record':row})
            except ValueError as exc: return self.send(400, {'error':str(exc)})
            finally: LOCK.release()
        if self.path != '/api/chat': return self.send(404,{'error':'Not found'})
        if not LOCK.acquire(blocking=False): return self.send(409,{'error':'One generation is already running.'})
        try:
            model_id=data.get('model'); spec=registry().get(model_id)
            if not spec: raise ValueError('Unknown model.')
            if spec.get('pending') and not spec.get('adapter'): raise ValueError('This model has not been trained. Configure a real adapter in models.json first.')
            messages=data.get('messages',[])
            if not messages or len(messages)>30 or messages[-1].get('role')!='user': raise ValueError('Start a new chat or send a user message.')
            if any(m.get('role') not in ('user','assistant') or not isinstance(m.get('content'),str) for m in messages): raise ValueError('Invalid chat messages.')
            if spec['backend']=='openai': engine=OpenAIEngine(STATE['openai_model'],STATE['key'], options={'reasoning':{'effort':'none'}} if STATE['openai_model']=='gpt-6-luna' else {})
            elif spec['backend']=='claude': engine=ClaudeEngine(STATE['claude_model'],STATE['claude_key'],max_tokens=4096)
            else:
                identity=json.dumps(spec,sort_keys=True)
                if STATE['engine_id']!=identity:
                    STATE['engine']=None; STATE['engine_id']=None;gc.collect()
                    engine_class = {'sarvam': SarvamEngine, 'qwen': QwenEngine}.get(spec['backend'])
                    if engine_class is None: raise ValueError('Unknown local backend.')
                    engine=engine_class(adapter=spec.get('adapter'))
                    STATE['engine']=engine;STATE['engine_id']=identity
                engine=STATE['engine']
            result=engine.generate(prompt_for(data.get('condition')),messages)
            result['model']=engine.metadata
            result['record'] = records.create(messages, dict(result), data.get('condition'))
            self.send(200,result)
        except urllib.error.HTTPError as exc:
            self.send(502,{'error':f'API provider returned HTTP {exc.code}. Check model access, API key, quota, and supported settings. No automatic retry was made.'})
        except urllib.error.URLError as exc:
            reason = exc.reason
            if isinstance(reason, ssl.SSLCertVerificationError):
                message = 'Could not verify the API TLS certificate. Check the Python CA bundle or SSL_CERT_FILE.'
            elif isinstance(reason, socket.gaierror):
                message = 'Could not resolve the API address. Check your internet connection or DNS.'
            else:
                message = 'Could not connect to the API. Check your internet connection or proxy settings.'
            self.send(502, {'error': message})
        except (ValueError,RuntimeError) as exc: self.send(400,{'error':str(exc)[:500]})
        except Exception as exc: self.send(500,{'error':f'{type(exc).__name__}: generation failed. Check dependencies, available memory, and network access. No response was fabricated.'})
        finally: LOCK.release()

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--env-file', type=Path, help='Read only API keys/model IDs from an existing dotenv file.')
    args = parser.parse_args()
    if args.env_file:
        import shlex
        allowed = {'OPENAI_API_KEY':'key', 'ANTHROPIC_API_KEY':'claude_key',
                   'OPENAI_MODEL':'openai_model', 'ANTHROPIC_MODEL':'claude_model'}
        for line in args.env_file.read_text().splitlines():
            line = line.strip().removeprefix('export ')
            name, sep, raw = line.partition('=')
            if sep and name.strip() in allowed:
                parts = shlex.split(raw, comments=True)
                if parts and not STATE[allowed[name.strip()]]:
                    STATE[allowed[name.strip()]] = parts[0]
    STATE['openai_model'] = STATE['openai_model'] or 'gpt-6-luna'
    STATE['claude_model'] = STATE['claude_model'] or 'claude-haiku-5-5'
    print(f'Reading model: http://127.0.0.1:{PORT}',flush=True)
    ThreadingHTTPServer(('127.0.0.1',PORT),Handler).serve_forever()
