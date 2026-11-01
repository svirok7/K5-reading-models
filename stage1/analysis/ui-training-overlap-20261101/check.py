from pathlib import Path
import json,sqlite3,re,hashlib,difflib
from collections import Counter
root=Path(__file__).resolve().parents[2]
training=root/'datasets/sft-600-v1/sft.jsonl'
data=[json.loads(x) for x in training.read_text().splitlines()]
norm=lambda s:' '.join(re.findall(r"[a-z0-9]+(?:'[a-z]+)?",s.lower()))
def msgs(ms):return [(m['role'],norm(m['content'])) for m in ms if m['role']!='system']
def last(d):return [m['content'] for m in d['prompt'] if m['role']=='user'][-1]
c=sqlite3.connect('file:'+str(root/'runs/conversation-results.sqlite3')+'?mode=ro',uri=True)
rows=[json.loads(x[0]) for x in c.execute('select body from records order by rowid')]
rows=[r for r in rows if not r.get('archived_at') and 'sft600' in str(r['response'].get('model',{}))]
results=[]
for r in rows:
 q=r['messages'][-1]['content']; answer=r['response']['text']
 exact=[i+1 for i,d in enumerate(data) if last(d)==q]
 normal=[i+1 for i,d in enumerate(data) if norm(last(d))==norm(q)]
 full=[i+1 for i,d in enumerate(data) if msgs(d['prompt'])==msgs(r['messages'])]
 replies=[i+1 for i,d in enumerate(data) if norm(d['completion'][0]['content'])==norm(answer)]
 nearest=sorted([(difflib.SequenceMatcher(None,norm(q),norm(last(d))).ratio(),i+1) for i,d in enumerate(data)],reverse=True)[:3]
 results.append({'record_id':r['id'],'user':q,'reply':answer,'history_turns':len(r['messages']),'evaluated':bool(r.get('evaluation')),'verdict':(r.get('evaluation') or {}).get('verdict'),'exact_last_user_lines':exact,'normalized_last_user_lines':normal,'normalized_full_history_lines':full,'normalized_target_reply_lines':replies,'nearest_last_user_texts':[{'similarity':round(s,3),'line':i,'user':last(data[i-1])} for s,i in nearest]})
judged=[r for r in results if r['evaluated']]
summary={'training_rows':len(data),'training_sha256':hashlib.sha256(training.read_bytes()).hexdigest(),'active_adapter_training_sha256':json.loads((root/'runs/qwen-sft600-v1-epoch3-20261101/adapter/sft-adapter-record.json').read_text())['data_sha256'],'total_live_rows':len(results),'judged':len(judged),'passes':sum(r['verdict']=='acceptable' for r in judged),'exact_last_user_matches':sum(bool(r['exact_last_user_lines']) for r in judged),'normalized_last_user_matches':sum(bool(r['normalized_last_user_lines']) for r in judged),'normalized_full_history_matches':sum(bool(r['normalized_full_history_lines']) for r in judged),'normalized_target_reply_matches':sum(bool(r['normalized_target_reply_lines']) for r in judged)}
for k,subset in [('seen_last_user',[r for r in judged if r['normalized_last_user_lines']]),('unseen_last_user',[r for r in judged if not r['normalized_last_user_lines']])]:summary[k]={'n':len(subset),'passes':sum(r['verdict']=='acceptable' for r in subset)}
out=Path(__file__).parent
(out/'overlap.json').write_text(json.dumps({'summary':summary,'records':results},indent=2)+'\n')
print(json.dumps(summary,indent=2))
for r in results:print(json.dumps({k:r[k] for k in ['user','reply','exact_last_user_lines','normalized_last_user_lines','normalized_full_history_lines','normalized_target_reply_lines']}))
