"""Validate structural/data-integrity requirements; no test file access or semantic classifier.
Semantic and spelling acceptance come from independent, hash-bound full-row reviews.
"""
import json,re,hashlib,sys
from pathlib import Path
from collections import Counter
A=Path(__file__).resolve().parent; ROOT=A.parents[2];sys.path.insert(0,str(ROOT));import engine
EXP=A.parent
PAT=re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)?|[0-9]+")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return [json.loads(l)for l in p.read_text().splitlines()]
def validate(dst,require_sealed=False):
 dst=Path(dst);data=read(dst/'sft.jsonl');meta=read(dst/'review.jsonl');provenance=json.loads((dst/'provenance.json').read_text())
 assert len(data)==len(meta)==600
 assert len({m['id']for m in meta})==600
 current=engine.prompt_for('B')
 for i,(r,m)in enumerate(zip(data,meta),1):
  assert set(r)=={'prompt','completion'},i
  assert r['prompt'][0]=={'role':'system','content':current},i
  context=r['prompt'][1:]
  assert context and len(context)%2==1,i
  assert [x['role']for x in context]==['user'if j%2==0 else'assistant'for j in range(len(context))],i
  assert all(set(x)=={'role','content'}and isinstance(x['content'],str)and x['content']for x in context),i
  assert len(r['completion'])==1 and set(r['completion'][0])=={'role','content'} and r['completion'][0]['role']=='assistant',i
  target=r['completion'][0]['content'];target_words={w.lower()for w in PAT.findall(target)}
  assert target_words and target_words<=m['lexical_evidence'].keys(),(i,target_words-m['lexical_evidence'].keys())
  assert all(isinstance(m['lexical_evidence'][w],str)and m['lexical_evidence'][w].strip()for w in target_words),i
  assert m['target_response']==target and m['context_messages']==context,i
  assert m['requires_history']==(len(context)>1),i
  assert m['prior_assistant_turns']==sum(x['role']=='assistant'for x in context),i
  assert m['supervision']=='final_completion_only' and m['human_approved']is False,i
  indices=m['flawed_history_indices'];assert indices==sorted(set(indices)),i
  for j in indices:assert 1<=j<=len(context)and context[j-1]['role']=='assistant',(i,j)
  assert {x['message_index']for x in m['historical_flaws']}==set(indices),i
  assert all(x.get('loss_scope')=='input_only_no_completion_loss'for x in m['historical_flaws']),i
 new=meta[300:];cats=Counter(m['category']for m in new)
 assert len(cats)==6 and set(cats.values())=={50},cats
 history=sum(m['requires_history']for m in new);long=sum(3<=m['prior_assistant_turns']<=5 for m in new);flawed=sum(bool(m['flawed_history_indices'])for m in new);semantic=sum(bool(m['intentional_semantic_flawed_history_indices'])for m in new)
 assert history==150 and long>=100 and flawed>=50 and semantic>=50,(history,long,flawed,semantic)
 # Every assistant history word receives either sound/list evidence or an explicit reading finding.
 side=read(dst/'history-flaws.jsonl');assert len(side)==300
 for m,h in zip(new,side):
  assert m['id']==h['id'] and m['flawed_history_indices']==h['flawed_history_indices'] and m['historical_flaws']==h['historical_flaws']
  assistant=[(j,x)for j,x in enumerate(m['context_messages'],1)if x['role']=='assistant']
  assert len(assistant)==len(h['historical_assistant_lexical_checks'])
  for (j,x),c in zip(assistant,h['historical_assistant_lexical_checks']):
   assert c['message_index']==j and c['content']==x['content']
   ws={w.lower()for w in PAT.findall(x['content'])};assert ws==set(c['supported_words'])|set(c['unsupported_words'])
   assert not set(c['supported_words'])&set(c['unsupported_words'])
   if c['unsupported_words']:assert j in m['flawed_history_indices']
 # Verify all source approvals and exact byte concatenation; no hidden source mutation.
 source_bytes=[]
 for source in provenance['sources']:
  p=ROOT/source['path'];assert sha(p/'sft.jsonl')==source['sft_sha256']and sha(p/'review.jsonl')==source['review_sha256']
  report=ROOT/source['independent_approval'];assert sha(report)==source['approval_sha256']
  approval=json.loads(report.read_text());assert approval['status']=='approved'
  source_bytes.append((p/'sft.jsonl').read_bytes())
 assert b''.join(source_bytes)==(dst/'sft.jsonl').read_bytes()
 baseline=read(ROOT/'datasets/sft-300-v2/sft.jsonl');changes=read(dst/'changes.jsonl');assert len(changes)==3
 assert [c['source_index_1based']for c in changes]==[32,45,65]
 for i,(before,after)in enumerate(zip(baseline,data[:300]),1):
  if i in [32,45,65]:
   c=next(c for c in changes if c['source_index_1based']==i);assert c['before']==before and c['after']==after
  else:assert before==after,i
 assert sha(ROOT/'datasets/sft-300-v2/sft.jsonl')=='42aea06f60ce82af7e276440c3318220efa751cc4fd3c111208176366bb419b3'
 assert sha(ROOT/'datasets/sft-300-v2/review.jsonl')=='4bea6c4aaf5ecde8218d6a998c4d7435ee217faa75dddd63b719cc79815e445b'
 frozen=json.loads((EXP/'frozen/manifest.json').read_text())
 for name,digest in frozen['files'].items():assert sha(EXP/'frozen'/name)==digest,name
 # Exact overlap is checked here; semantic overlap is checked manually by the independent reviewer.
 eval_histories={json.dumps(o['messages'],sort_keys=True)for o in read(EXP/'frozen/candidates.jsonl')}
 assert not any(json.dumps(r['prompt'][1:],sort_keys=True)in eval_histories for r in data[300:])
 if require_sealed:
  manifest=json.loads((dst/'manifest.json').read_text());assert manifest['count']==600 and manifest['frozen_data']is True and manifest['human_approved']is False
  assert manifest['audit_status']=='independently_reviewed_pending_human'
  assert manifest['audit']['pass']==600 and manifest['audit']['examples_reviewed']==600 and manifest['audit']['open_findings']==0 and manifest['audit']['sft_sha256']==sha(dst/'sft.jsonl')
  for name,digest in manifest['artifacts'].items():assert sha(dst/name)==digest,name
  assert (dst/'manifest.sha256').read_text().split()[0]==sha(dst/'manifest.json')
 return {'count':600,'new_count':300,'original_changes':3,'new_category_counts':dict(cats),'new_history_required':history,'new_3_to_5_prior_assistant_turns':long,'new_intentional_semantic_flawed_rows':semantic,'new_rows_with_any_annotated_history_flaw':flawed,'sft_sha256':sha(dst/'sft.jsonl'),'review_sha256':sha(dst/'review.jsonl'),'frozen_eval_and_baseline_hashes_unchanged':True,'final_completion_only_schema':True,'all_history_words_accounted_for':True,'human_approved':False,'structural_validation':'pass','semantic_validation':'independent manual full-record review; see audit artifacts'}
if __name__=='__main__':print(json.dumps(validate(sys.argv[1]if len(sys.argv)>1 else A/'final-candidate','--sealed'in sys.argv),indent=2))
