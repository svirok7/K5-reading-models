"""Local read-only progress monitor. Exposes reports only, never credentials/data."""
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parent
REPORTS = ['STATUS.md', 'data/DATA_REPORT.md', 'training/TRAINING_REPORT.md',
           'training/run/status.json', 'training/run/output-model.json',
           'evaluation/EVALUATION_REPORT.md', 'INTEGRATION_REPORT.md']
HTML = '''<!doctype html><meta charset="utf-8"><title>Glimmer experiment</title>
<style>body{font:16px system-ui;background:#101923;color:#e5edf5;max-width:1100px;margin:40px auto;padding:20px}h1{color:#8fddca}pre{white-space:pre-wrap;background:#182634;padding:22px;border-radius:12px}a{color:#8fddca}</style>
<h1>Muse Glimmer · Reading Model</h1><p>Sol agents · refreshes every 5 seconds · local progress reports</p><main id="reports"></main>
<script>async function update(){try{const data=await(await fetch('/status')).json();const main=document.querySelector('main');main.replaceChildren();for(const [name,body] of Object.entries(data)){const h=document.createElement('h2');h.textContent=name;const p=document.createElement('pre');p.textContent=body;main.append(h,p)}}catch(e){}}update();setInterval(update,5000)</script>'''

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_): pass
    def do_GET(self):
        if self.headers.get('Host') not in ('127.0.0.1:8766', 'localhost:8766'):
            self.send_error(403); return
        if self.path == '/':
            body, kind = HTML.encode(), 'text/html; charset=utf-8'
        elif self.path == '/status':
            data = {name: (ROOT/name).read_text() if (ROOT/name).exists() else 'Agent working; report pending.' for name in REPORTS}
            body, kind = json.dumps(data).encode(), 'application/json'
        else:
            self.send_error(404); return
        self.send_response(200)
        self.send_header('Content-Type', kind)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers(); self.wfile.write(body)

if __name__ == '__main__':
    print('Experiment monitor: http://127.0.0.1:8766', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8766), Handler).serve_forever()
