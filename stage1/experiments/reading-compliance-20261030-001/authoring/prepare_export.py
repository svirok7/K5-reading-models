"""Assemble approved source bytes into a reviewable candidate; never edit baseline."""
import json,shutil
from pathlib import Path
import build_corpus as b
A=Path(__file__).resolve().parent; EXP=A.parent; ROOT=b.ROOT

def rows(p):return [json.loads(l)for l in p.read_text().splitlines()]
def main():
 dst=A/'final-candidate';dst.mkdir(exist_ok=True)
 original=A/'original-corrected'
 approval=json.loads((EXP/'audit/original300-corrected-approval-summary.json').read_text())
 assert approval['status']=='approved' and approval['corrected_sft_sha256']==b.sha(original/'sft.jsonl') and approval['corrected_review_sha256']==b.sha(original/'review.jsonl')
 sources=[original];reports=[EXP/'audit/original300-corrected-approval-summary.json']
 for n,r in [(1,2),(2,2),(3,2),(4,2),(5,1),(6,2)]:
  source=A/f'batch-{n:02d}'; report=EXP/f'audit/batch-{n:02d}-round-{r}-summary.json';obj=json.loads(report.read_text())
  assert obj['status']=='approved' and obj['pass_count']==50 and obj['source_sft_sha256']==b.sha(source/'sft.jsonl') and obj['source_review_sha256']==b.sha(source/'review.jsonl'),(n,obj)
  sources.append(source);reports.append(report)
 sft_bytes=b''.join((p/'sft.jsonl').read_bytes()for p in sources)
 (dst/'sft.jsonl').write_bytes(sft_bytes)
 histories={r['id']:r for r in rows(A/'history-flaws.jsonl')}
 meta=[]
 for si,source in enumerate(sources):
  data=rows(source/'sft.jsonl');ms=rows(source/'review.jsonl')
  for i,(r,m)in enumerate(zip(data,ms),1):
   # Preserve source metadata in source artifacts; normalize only this successor.
   m['review_status']='independently_reviewed_pending_human';m['full_audit_status']='independently_reviewed_pending_human';m['human_approved']=False
   m['source_artifact']=str(source.relative_to(ROOT));m['source_row_1based']=i;m['source_sft_sha256']=b.sha(source/'sft.jsonl');m['source_review_sha256']=b.sha(source/'review.jsonl')
   m['target_response']=r['completion'][0]['content'];m['context_messages']=r['prompt'][1:];m['requires_history']=len(r['prompt'])>2;m['supervision']='final_completion_only'
   m['prior_assistant_turns']=sum(x['role']=='assistant'for x in r['prompt'][1:])
   import re
   m['sentence_word_counts']=[len(re.findall(r"[A-Za-z]+(?:['’][A-Za-z]+)?|[0-9]+",t))for t in re.split(r'[.!?]+',m['target_response'])if re.search(r'\w',t)]
   if si:
    h=histories[m['id']];m['flawed_history_indices']=h['flawed_history_indices'];m['historical_flaws']=h['historical_flaws'];m['intentional_semantic_flawed_history_indices']=h['intentional_semantic_flawed_history_indices'];m['history_annotations_sha256']=b.sha(A/'history-flaws.jsonl')
   else:
    m['flawed_history_indices']=[];m['historical_flaws']=[];m['intentional_semantic_flawed_history_indices']=[]
   meta.append(m)
 b.write_jsonl(dst/'review.jsonl',meta)
 for name,src in [('changes.jsonl',original/'changes.jsonl'),('history-flaws.jsonl',A/'history-flaws.jsonl'),('history-lexicon.json',A/'history-lexicon.json')]:shutil.copy2(src,dst/name)
 provenance={'sources':[{'path':str(p.relative_to(ROOT)),'sft_sha256':b.sha(p/'sft.jsonl'),'review_sha256':b.sha(p/'review.jsonl'),'count':300 if i==0 else 50,'independent_approval':str(report.relative_to(ROOT)),'approval_sha256':b.sha(report)}for i,(p,report)in enumerate(zip(sources,reports))], 'baseline_sft_sha256':b.sha(ROOT/'datasets/sft-300-v2/sft.jsonl'),'baseline_review_sha256':b.sha(ROOT/'datasets/sft-300-v2/review.jsonl'),'frozen_manifest_sha256':b.sha(EXP/'frozen/manifest.json'),'frozen_cases_sha256':b.sha(EXP/'frozen/cases.jsonl'),'human_approved':False}
 (dst/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
 print(json.dumps({'candidate':str(dst),'count':len(meta),'sft_sha256':b.sha(dst/'sft.jsonl'),'review_sha256':b.sha(dst/'review.jsonl'),'history_sha256':b.sha(dst/'history-flaws.jsonl'),'lexicon_sha256':b.sha(dst/'history-lexicon.json')},indent=2))
if __name__=='__main__':main()
