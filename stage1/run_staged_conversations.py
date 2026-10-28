"""Run exploratory conversations into isolated files, never the live results DB."""
import argparse
import hashlib
import html
import json
import os
from pathlib import Path
import shlex
import uuid
import urllib.error

from engine import ClaudeEngine, digest
import evaluator
from records import now


def save(path, value):
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False))
    temp.replace(path)


def credentials(path):
    keys = {k: os.environ.get(k, '') for k in ('OPENAI_API_KEY', 'ANTHROPIC_API_KEY')}
    for line in path.read_text().splitlines():
        name, sep, raw = line.strip().removeprefix('export ').partition('=')
        if sep and name.strip() in keys and not keys[name.strip()]:
            parts = shlex.split(raw, comments=True)
            if parts:
                keys[name.strip()] = parts[0]
    if not all(keys.values()):
        raise ValueError('Both provider keys are required; no requests made.')
    return keys


def review(folder, plan, rows):
    judged = [r for r in rows if r.get('evaluation')]
    passed = sum(r['evaluation']['verdict'] == 'acceptable' for r in judged)
    lines = ['# Haiku conversation test — awaiting your approval', '',
             '**These results have not been added to the app. No manual decisions have been recorded.**', '',
             f"Model: `{plan['model']}`. Prompt {plan['condition']}; rubric {plan['rubric_version']}.", '',
             'Generation settings: ' + json.dumps(plan.get('generation_options', {})) + '; 512 output tokens.', '',
             f"Generated: {len(rows)}/30. Evaluated: {len(judged)}. Proposed acceptable: {passed}/{len(judged)}" +
             (f" ({passed / len(judged):.1%})." if judged else '.'), '',
             'This is an exploratory conversational test based on your two chats, with additional development prompts. '
             'It is not the separate held-out 50-case benchmark. Haiku sees its own earlier replies. '
             'The evaluator scores only reading accessibility; factual correctness and relevance need separate review. '
             'Your Luna labels were manual; these Haiku labels remain automatic proposals.', '',
             'The dog-memory example combines the setup and question into one user turn, so neither chat contains '
             'a fabricated companion reply and both stay within the app’s message limit.', '',
             'Empty or truncated responses remain failed attempts and are not retried. If no visible reply is returned, '
             'the unanswered user message remains in subsequent context, without inserting an empty assistant message.', '',
             '## Proposed decisions', '', '| Chat / turn | Input | Proposed verdict | Words / length / rhythm |',
             '|---|---|---|---|']
    for r in rows:
        ev = r.get('evaluation') or {}
        scores = ev.get('scores', {})
        scores_text = ' / '.join(str(scores.get(k, '—')) for k in evaluator.DIMENSIONS)
        text = r['messages'][-1]['content'].replace('|', '\\|').replace('\n', ' ')
        lines.append(f"| {r['chat_id']} / {r['turn']} | {text} | {ev.get('verdict', 'unscored')} | {scores_text} |")
    for chat in plan['chats']:
        lines += ['', f"## Chat {chat['id']} — complete transcript", '']
        for r in [r for r in rows if r['chat_id'] == chat['id']]:
            ev = r.get('evaluation') or {}
            lines += [f"### Turn {r['turn']}", '', '**You:** ' + r['messages'][-1]['content'], '',
                      '**Haiku:**', '', r['response']['text'], '',
                      f"**Proposed verdict:** {ev.get('verdict', 'unscored')}. {ev.get('summary', '')}", '',
                      '**Scores:** ' + json.dumps(ev.get('scores', {})), '',
                      f"**Generation:** {r['response']['status']}; {r['response']['latency_s']:.2f} s; "
                      f"{r['response']['diagnostics']['words']} words.", '']
            for issue in ev.get('issues', []):
                lines += [f"- **{issue['span']}** — {issue['explanation']} Rule: {issue['rule']}"]
            if ev.get('suggested_revision'):
                lines += ['', '**Evaluator’s suggested revision:** ' + ev['suggested_revision'], '']
            if r.get('evaluation_error'):
                lines += ['**Evaluation error:** ' + r['evaluation_error'], '']
            lines += [f"Record: `{r['id']}`. Source reference: `{r.get('reference_record_id') or 'additional development prompt'}`.", '']
    report = '\n'.join(lines)
    (folder / 'review.md').write_text(report)
    # Dependency-free readable HTML keeps all text escaped and all data local.
    (folder / 'review.html').write_text('<!doctype html><meta charset="utf-8"><title>Haiku test — pending approval</title>'
        '<style>body{max-width:1000px;margin:40px auto;padding:0 24px;background:#faf9f6;color:#222;'
        'font:16px/1.6 system-ui}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style><pre>' + html.escape(report) + '</pre>')
    manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir()
                if p.is_file() and p.name != 'SHA256.json'}
    save(folder / 'SHA256.json', manifest)


def run(folder, env_file):
    os.umask(0o077)
    plan = json.loads((folder / 'plan.json').read_text())
    rows_path = folder / 'staged-records.json'
    rows = json.loads(rows_path.read_text()) if rows_path.exists() else []
    keys = credentials(env_file)
    engine = ClaudeEngine(plan['model'], keys['ANTHROPIC_API_KEY'], max_tokens=512,
                          options=plan.get('generation_options'))
    for chat in plan['chats']:
        history = []
        for turn, case in enumerate(chat['turns'], 1):
            existing = next((r for r in rows if r['chat_id'] == chat['id'] and r['turn'] == turn), None)
            if existing:
                if existing['messages'] != history + [{'role':'user', 'content':case['input']}]:
                    raise ValueError('Saved history differs from the frozen plan; stopped.')
                row = existing
            else:
                messages = history + [{'role':'user', 'content':case['input']}]
                assert len(messages) <= 30
                response = engine.generate(plan['prompt'], messages)
                response['model'] = engine.metadata
                row = {'id':str(uuid.uuid4()), 'created_at':now(), 'messages':messages, 'response':response,
                       'condition':plan['condition'], 'prompt':plan['prompt'], 'rubric_version':plan['rubric_version'],
                       'rubric':plan['rubric'], 'rubric_hash':digest(plan['rubric']), 'evaluation':None,
                       'evaluation_error':None, 'manual':None, 'manual_history':[], 'approval_status':'pending',
                       'source':'agent-executed exploratory conversation', 'run_id':plan['run_id'],
                       'chat_id':chat['id'], 'turn':turn, 'reference_record_id':case.get('reference_record_id')}
                rows.append(row)
                save(rows_path, rows)
                review(folder, plan, rows)
                print(f"Chat {chat['id']} turn {turn}/15 generated and staged.", flush=True)
            if not row.get('evaluation') and not row.get('evaluation_error'):
                try:
                    row['evaluation'] = evaluator.evaluate(row, keys['OPENAI_API_KEY'])
                except Exception as exc:
                    row['evaluation_error'] = 'Evaluator failed: ' + type(exc).__name__
                save(rows_path, rows)
                review(folder, plan, rows)
            print(f"Progress: {len(rows)}/30 staged; chat {chat['id']} turn {turn}, "
                  f"{(row.get('evaluation') or {}).get('verdict', 'unscored')}", flush=True)
            history = list(row['messages'])
            if row['response']['text'].strip():
                history.append({'role':'assistant', 'content':row['response']['text']})
    save(folder / 'status.json', {'status':'awaiting_user_approval', 'generated':len(rows),
                                 'live_results_modified':False, 'completed_at':now()})
    review(folder, plan, rows)
    print('Complete. All 30 replies remain staged pending approval.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder', type=Path, required=True)
    parser.add_argument('--env-file', type=Path, required=True)
    args = parser.parse_args()
    try:
        run(args.folder.resolve(), args.env_file)
    except urllib.error.HTTPError as exc:
        print(f'Provider HTTP {exc.code}. Stopped; no automatic retry or result import.', flush=True)
        raise SystemExit(1)
    except Exception as exc:
        print(f'Stopped ({type(exc).__name__}); staged outputs preserved; no result import.', flush=True)
        raise SystemExit(1)
