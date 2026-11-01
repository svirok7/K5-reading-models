"""Hash-bind independently reviewed data, exact changes and input-only annotations."""
import collections,hashlib,importlib.util,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('resumed',HERE/'resumed_audits.py');res=importlib.util.module_from_spec(spec);spec.loader.exec_module(res);a=res.a
for w,e in {'dust':'d + short u + st blend','dot':'d + short o + t','den':'d + short e + n','bags':'bag (b + short a + g) plus taught s ending'}.items():a.baselex[w]={'word':w,'eligible':True,'route':'supported_decoding','evidence':e}
# These27 historical forms were individually inspected against exact benchmark.
historical_supported={'boxes','claps','crabs','gifts','helps','hint','kid','kids','king','lands','maps','nest','plant','rad','sack','set','shelf','ship','slick','such','taps','tells','ten','test','than','track','tub'}
F=EXP/'authoring/final-candidate';sha=a.sha;canon=a.canon
expect={'sft.jsonl':'844223c79402af7d93937c9485f182d7c5381434b4e2234381a989663466424e','review.jsonl':'07a4aced136602c4c88555e93bff7a9194ba9e2bb94bea4e46059efa17e6ca81','history-flaws.jsonl':'9d12b3f10fecdb07e971aa5df91313ab1d8d36ed6f6bde5518761d33e4dbdc40','history-lexicon.json':'73f74483bfb87e9f3849a229c21da7e83e3cedb7f3336b2b60bf74fac5d0bbfb','changes.jsonl':'53c7c9faeb473311f98d05a0dfaed65a14edf963fc8c0aea64f9bc44f3122200'}
for f,h in expect.items():assert sha((F/f).read_bytes())==h,(f,sha((F/f).read_bytes()))
sft=[json.loads(x) for x in (F/'sft.jsonl').read_text().splitlines()];review=[json.loads(x) for x in (F/'review.jsonl').read_text().splitlines()];history=[json.loads(x) for x in (F/'history-flaws.jsonl').read_text().splitlines()];lex=json.loads((F/'history-lexicon.json').read_text());prov=json.loads((F/'provenance.json').read_text())
assert len(sft)==len(review)==600 and len(history)==300
assert {w for w,r in lex.items() if r['status']=='supported'}==historical_supported
assert all(r['evidence'] and not any(z in r['evidence'].lower() for z in ['replaced below','todo','placeholder']) for r in lex.values())
assert all(r['status'] in ('supported','unsupported_by_benchmark') for r in lex.values())
source_bytes=[];approvals=[]
for source in prov['sources']:
 p=ROOT/source['path'];assert sha((p/'sft.jsonl').read_bytes())==source['sft_sha256'];assert sha((p/'review.jsonl').read_bytes())==source['review_sha256']
 ap=ROOT/source['independent_approval'];assert sha(ap.read_bytes())==source['approval_sha256'];summary=json.loads(ap.read_text());assert summary['status']=='approved'
 source_bytes.append((p/'sft.jsonl').read_bytes());approvals.append({'source':source['path'],'sft_sha256':source['sft_sha256'],'independent_approval':source['independent_approval'],'approval_sha256':source['approval_sha256']})
assert b''.join(source_bytes)==(F/'sft.jsonl').read_bytes()
original_approved=[json.loads(x) for x in (HERE/'original300-corrected-approval.jsonl').read_text().splitlines()]
newapproved=[]
for b in range(1,7):
 rd=1 if b==5 else 2
 newapproved += [json.loads(x) for x in (HERE/f'batch-{b:02d}-round-{rd}.jsonl').read_text().splitlines()]
assert len(original_approved)==len(newapproved)==300
prompt=(EXP/'frozen/prompt-B.txt').read_text();allrows=[];historychecks=[]
for index,(s,r) in enumerate(zip(sft,review),1):
 assert set(s)=={'prompt','completion'}
 assert s['prompt'][0]=={'role':'system','content':prompt}
 assert len(s['completion'])==1 and s['completion'][0]['role']=='assistant'
 msgs=s['prompt'][1:];target=s['completion'][0]['content']
 assert msgs==r['context_messages'] and target==r['target_response']
 assert r['human_approved'] is False and r['supervision']=='final_completion_only'
 whash=sha(canon(s).encode())
 prior=original_approved[index-1] if index<=300 else newapproved[index-301]
 assert whash==prior['approved_record_sha256' if index<=300 else 'record_sha256']
 assert prior['semantic_review']=='pass' and prior['reading_review']=='pass'
 words=sorted(set(w.lower() for w in re.findall(r"[A-Za-z]+(?:['’][A-Za-z]+)?|\d+",target)))
 assert all(w in a.baselex and a.baselex[w]['eligible'] for w in words),(index,words)
 assert set(words)<=set(r['lexical_evidence'])
 if index>300:assert set(words)==set(r['lexical_evidence'])
 annotation=None
 if index>300:
  hr=history[index-301];assert hr['id']==r['id'];assert hr['approved_sft_sha256']==r['source_sft_sha256']
  assert hr['supervision']=='final_completion_only' and hr['human_approved'] is False
  assert hr['flawed_history_indices']==r['flawed_history_indices']
  checks=hr['historical_assistant_lexical_checks'];actual=[(i,m) for i,m in enumerate(msgs,1) if m['role']=='assistant'];assert len(checks)==len(actual)
  lexical_indices=[]
  for check,(i,m) in zip(checks,actual):
   assert check['message_index']==i and check['content']==m['content']
   tokens=set(w.lower() for w in re.findall(r"[A-Za-z]+(?:['’][A-Za-z]+)?|\d+",m['content']))
   supported=set(check['supported_words']);unsupported=set(check['unsupported_words'])
   assert not supported&unsupported and supported|unsupported==tokens
   for w in supported:assert w in a.baselex or (w in historical_supported and lex[w]['status']=='supported'),(r['id'],i,w)
   for w in unsupported:assert w not in a.baselex and lex[w]['status']=='unsupported_by_benchmark', (r['id'],i,w)
   if unsupported:lexical_indices.append(i)
  semantic=hr['intentional_semantic_flawed_history_indices'];assert semantic==r['intentional_semantic_flawed_history_indices']
  assert sorted(set(semantic+lexical_indices))==hr['flawed_history_indices']
  assert all(msgs[i-1]['role']=='assistant' for i in semantic)
  for f in hr['historical_flaws']:assert f['loss_scope']=='input_only_no_completion_loss'
  annotation={'semantic_flaw_indices_1based':semantic,'lexical_flaw_indices_1based':lexical_indices,'all_flaw_indices_1based':hr['flawed_history_indices'],'history_annotation_review':'pass'}
  historychecks.append({'id':r['id'],**annotation})
 allrows.append({'dataset_index_1based':index,'id':r['id'],'record_sha256':whash,'origin':'corrected_original300' if index<=300 else 'new300','semantic_review':'pass','reading_review':'pass','full_context_review':'pass','word_evidence':[a.baselex[w] for w in words],'history_annotation_review':annotation,'human_approved':False})
newmeta=review[300:];categories=collections.Counter(r['category'] for r in newmeta);historyrows=sum(bool(r['requires_history']) for r in newmeta);turns=collections.Counter(sum(m['role']=='assistant' for m in row['prompt']) for row in sft[300:]);semflaws=sum(bool(r['intentional_semantic_flawed_history_indices']) for r in newmeta);anyflaws=sum(bool(r['flawed_history_indices']) for r in newmeta)
assert len(categories)==6 and set(categories.values())=={50};assert historyrows==150;assert sum(n for k,n in turns.items() if 3<=k<=8)>=100 and semflaws>=50
assert len({r['id'] for r in review})==600
assert len({canon(row['prompt']) for row in sft})==600
# Verify frozen evidence has remained unchanged throughout authoring/auditing.
frozen=EXP/'frozen';fm=json.loads((frozen/'manifest.json').read_text());assert all(sha((frozen/f).read_bytes())==h for f,h in fm['files'].items());assert sha((frozen/'manifest.json').read_bytes())==(frozen/'manifest.sha256').read_text().split()[0]
for f in ['final600-independent-approval.jsonl','final600-history-annotation-check.jsonl','final600-independent-approval-summary.json']:assert not (HERE/f).exists()
(HERE/'final600-independent-approval.jsonl').write_text(''.join(canon(r)+'\n' for r in allrows));(HERE/'final600-history-annotation-check.jsonl').write_text(''.join(canon(r)+'\n' for r in historychecks))
summary={'status':'approved','scope':'Independent semantic, truthfulness, safety, naturalness, exact final-word eligibility, source integrity, frozen-evaluation semantic separation, and input-only history annotations. Runtime tokenizer length/masking and GPU quality gates remain separate.','rows':600,'corrected_original_rows':300,'new_rows':300,'changed_original_indices_1based':[32,45,65],'new_primary_category_counts':dict(categories),'new_history_rows':historyrows,'new_prior_assistant_turn_distribution':dict(turns),'new_intentionally_semantically_flawed_history_rows':semflaws,'new_rows_with_any_historical_flaw':anyflaws,'source_approvals':approvals,'files':expect|{'provenance.json':sha((F/'provenance.json').read_bytes())},'frozen_candidates_reviewed':45,'frozen_retained_cases':34,'new_close_semantic_evaluation_overlaps':[],'open_findings':[],'human_approved':False,'reviewer':'Independent delegated GPT-6.1 Sol/high session','test_accessed':False,'runs_or_quality_claims':False}
(HERE/'final600-independent-approval-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:summary[k] for k in ['status','rows','new_primary_category_counts','new_history_rows','new_prior_assistant_turn_distribution','new_intentionally_semantically_flawed_history_rows','new_rows_with_any_historical_flaw','open_findings']},indent=2))
if __name__=='__main__':pass
