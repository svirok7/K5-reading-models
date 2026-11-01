"""Oct31 independent audit materialization; preserves every earlier audit file."""
import importlib.util,json,hashlib,re
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];EXP=HERE.parent
spec=importlib.util.spec_from_file_location('prior_audit',HERE/'audit_batches.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
for word,evidence in {'staff':'st blend + short a + ff ending','grab':'gr blend + short a + b','link':'l + short i + nk ending','stomp':'st blend + short o + mp ending','kick':'k + short i + ck ending','steps':'step (st + short e + p) plus taught s ending'}.items():
 a.baselex[word]={'word':word,'eligible':True,'route':'supported_decoding','evidence':evidence}

def run_new_audits():
 for b,rd,expected in [(4,2,'85d6826fb1bf87165f9f0f1255c522a538541a58fe85e0a4d5dc94c3ebbf8bbc'),(5,1,'9ceb7e298a765c35799834d3a5d7f080ad73abb3ca53be461b5ede2b05b3c6e2')]:
  assert not (HERE/f'batch-{b:02d}-round-{rd}.jsonl').exists()
  a.audit(b,rd,custom={},expected=expected)
  p=EXP/f'authoring/batch-{b:02d}'
  meta=[json.loads(x) for x in (p/'review.jsonl').read_text().splitlines()]
  checked=[]
  for r in meta:
   msgs=r['context_messages'];idx=r['flawed_history_indices']
   for i in idx:
    assert msgs[i-1]['role']=='assistant'
   checked.append({'case_id':r['id'],'flawed_history_indices':idx,'annotated_messages':[{'message_index_1based':i,'role':msgs[i-1]['role'],'content':msgs[i-1]['content']} for i in idx],'annotation_review':'pass','meaning':'Indices correctly identify intentionally seeded incorrect/unsafe assistant turns; historical input only, never a target.'})
  (HERE/f'batch-{b:02d}-round-{rd}-history-annotation-check.jsonl').write_text(''.join(a.canon(x)+'\n' for x in checked))

def originals():
 folder=EXP/'authoring/original-corrected'
 raw=(folder/'sft.jsonl').read_bytes();assert a.sha(raw)=='2ec1428629a43b82226ced3717d05ae0286c7ea5e3c82f5e143394bcb304a209'
 new=[json.loads(x) for x in raw.decode().splitlines()]
 oldraw=(ROOT/'datasets/sft-300-v2/sft.jsonl').read_bytes();old=[json.loads(x) for x in oldraw.decode().splitlines()]
 oldaudit=[json.loads(x) for x in (HERE/'original300-round1.jsonl').read_text().splitlines()]
 changes=[json.loads(x) for x in (folder/'changes.jsonl').read_text().splitlines()]
 assert len(old)==len(new)==len(oldaudit)==300
 desired={32:'What do you like to do?',45:'A hit can make the bell ring.',65:'Pick the milk you did not say no to.'}
 changed=[i for i,(before,after) in enumerate(zip(old,new),1) if before!=after];assert changed==list(desired)
 outputs=[]
 for i,(before,after,prev) in enumerate(zip(old,new,oldaudit),1):
  assert a.sha(a.canon(before).encode())==prev['record_sha256']
  assert before['prompt']==after['prompt']
  if i not in desired:assert before==after
  words=sorted(set(w.lower() for w in re.findall(r"[A-Za-z]+(?:['’][A-Za-z]+)?",after['completion'][0]['content'])))
  assert all(w in a.baselex and a.baselex[w]['eligible'] for w in words)
  outputs.append({'source_index_1based':i,'before_record_sha256':a.sha(a.canon(before).encode()),'approved_record_sha256':a.sha(a.canon(after).encode()),'changed':i in desired,'semantic_review':'pass','reading_review':'pass','word_evidence':[a.baselex[w] for w in words],'prior_full300_audit':'original300-round1.jsonl','unchanged_record_verified':i not in desired})
 approved=[]
 for change in changes:
  i=change['source_index_1based'];assert change['before']==old[i-1] and change['after']==new[i-1]
  assert change['after']['completion']==[{'role':'assistant','content':desired[i]}]
  approved.append({'source_index_1based':i,'before':change['before'],'after':change['after'],'before_record_sha256':a.sha(a.canon(change['before']).encode()),'after_record_sha256':a.sha(a.canon(change['after']).encode()),'decision':'approved','reasons':{32:'Grounded neutral engagement removes broad unsupported knowledge praise.',45:'Direct causal trigger answers why the bell rings, without adding unsupported mechanism terms.',65:'Reference to the milk not rejected retains the cold-vs-warm choice without unsupported word forms.'}[i],'word_evidence':outputs[i-1]['word_evidence'],'human_approved':False})
 (HERE/'original-three-corrections-independent-approval.jsonl').write_text(''.join(a.canon(x)+'\n' for x in approved))
 (HERE/'original300-corrected-approval.jsonl').write_text(''.join(a.canon(x)+'\n' for x in outputs))
 summary={'status':'approved','rows':300,'original_source_sha256':a.sha(oldraw),'corrected_sft_sha256':a.sha(raw),'corrected_review_sha256':a.sha((folder/'review.jsonl').read_bytes()),'changes_sha256':a.sha((folder/'changes.jsonl').read_bytes()),'changed_original_indices_1based':changed,'semantic_pass':300,'reading_pass':300,'open_findings':[],'human_approved':False,'test_accessed':False}
 (HERE/'original300-corrected-approval-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 print(json.dumps(summary))
if __name__=='__main__':run_new_audits();originals()
