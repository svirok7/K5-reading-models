"""Local persistent response records; manual decisions take precedence."""
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from engine import ROOT

DB = ROOT/'runs'/'conversation-results.sqlite3'
VERDICTS = ('acceptable', 'not_acceptable')
def now(): return datetime.now(timezone.utc).isoformat()
def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB, timeout=15)
    c.execute('CREATE TABLE IF NOT EXISTS records (id TEXT PRIMARY KEY, body TEXT NOT NULL)')
    return c

def effective(row):
    manual = row.get('manual')
    judge = row.get('evaluation') or {}
    row['effective_decision'] = manual['decision'] if manual else judge.get('verdict', 'pending')
    row['decision_source'] = 'manual' if manual else ('evaluator' if judge.get('verdict') else 'pending')
    return row

def create(messages, response, condition):
    from engine import reader_profile
    rubric = (ROOT/'RUBRIC.md').read_text() + '\n\n' + reader_profile()
    from engine import digest, prompt_for
    row = {'id':str(uuid.uuid4()), 'created_at':now(), 'messages':messages,
        'response':response, 'condition':condition, 'prompt':prompt_for(condition),
        'rubric_version':'1.5', 'rubric':rubric, 'rubric_hash':digest(rubric),
        'evaluation':None, 'evaluation_error':None, 'manual':None, 'manual_history':[]}
    with connect() as c: c.execute('INSERT INTO records VALUES (?, ?)', (row['id'],json.dumps(row)))
    return effective(row)

def get(record_id):
    with connect() as c: result = c.execute('SELECT body FROM records WHERE id=?',(record_id,)).fetchone()
    if not result: raise ValueError('Response record not found.')
    return effective(json.loads(result[0]))

def update(record_id, **changes):
    with connect() as c:
        c.execute('BEGIN IMMEDIATE')
        result = c.execute('SELECT body FROM records WHERE id=?',(record_id,)).fetchone()
        if not result: raise ValueError('Response record not found.')
        row = json.loads(result[0]); row.update(changes)
        c.execute('UPDATE records SET body=? WHERE id=?', (json.dumps(row),record_id))
    return effective(row)

def set_manual(record_id, decision, reason):
    if decision not in (None, *VERDICTS): raise ValueError('Invalid decision.')
    if not isinstance(reason,str) or len(reason)>4000: raise ValueError('Invalid manual reason.')
    with connect() as c:
        c.execute('BEGIN IMMEDIATE')
        found = c.execute('SELECT body FROM records WHERE id=?',(record_id,)).fetchone()
        if not found: raise ValueError('Response record not found.')
        row = json.loads(found[0])
        entry = {'decision':decision,'reason':reason.strip(),'at':now()}
        row['manual_history'].append(entry)
        row['manual'] = entry if decision else None
        c.execute('UPDATE records SET body=? WHERE id=?',(json.dumps(row),record_id))
    return effective(row)

def all_records():
    with connect() as c: rows = c.execute('SELECT body FROM records ORDER BY rowid DESC').fetchall()
    return [effective(json.loads(r[0])) for r in rows]

def archive_existing(reason):
    stamp = now()
    with connect() as c:
        c.execute('BEGIN IMMEDIATE')
        rows = c.execute('SELECT id, body FROM records').fetchall()
        count = 0
        for record_id, body in rows:
            row = json.loads(body)
            if row.get('archived_at'): continue
            row.update(archived_at=stamp, archive_reason=reason)
            c.execute('UPDATE records SET body=? WHERE id=?', (json.dumps(row), record_id))
            count += 1
    return count

def summaries(rows):
    """Keep models/settings, prompt conditions and rubric versions separate."""
    from engine import DIMENSIONS, digest
    import math
    groups={}
    for row in rows:
        identity={'model':row['response']['model'],'condition':row['condition'],'rubric_hash':row['rubric_hash'],'prompt_hash':digest(row['prompt'])}
        groups.setdefault(digest(identity), {'identity':identity,'rows':[]})['rows'].append(row)
    def percentile(values,q):
        if not values:return None
        values=sorted(values)
        return values[max(0,math.ceil(len(values)*q)-1)]
    output=[]
    for group in groups.values():
        items=group.pop('rows'); response_times=[r['response']['latency_s'] for r in items if r['response']['status']=='completed']
        judge_times=[r['evaluation']['latency_s'] for r in items if r.get('evaluation')]
        means={};counts={}
        for dimension in (*DIMENSIONS, 'word_types', 'length', 'rhythm'):
            values=[r['evaluation']['scores'][dimension] for r in items if r.get('evaluation') and dimension in r['evaluation']['scores']]
            means[dimension]=sum(values)/len(values) if values else None
            counts[dimension]=len(values)
        output.append({**group,'responses':len(items),'evaluated':sum(bool(r.get('evaluation')) for r in items),
            'manual_overrides':sum(bool(r.get('manual')) for r in items),
            'effective_decisions':{v:sum(r['effective_decision']==v for r in items) for v in VERDICTS},
            'pending':sum(r['decision_source']=='pending' for r in items),
            'incomplete_responses':sum(r['response']['status']!='completed' for r in items),
            'companion_latency_s':{'n':len(response_times),'p50':percentile(response_times,.5),'p95':percentile(response_times,.95)},
            'evaluator_latency_s':{'n':len(judge_times),'p50':percentile(judge_times,.5),'p95':percentile(judge_times,.95)},
            'evaluator_score_means':means,'score_counts':counts})
    return output
