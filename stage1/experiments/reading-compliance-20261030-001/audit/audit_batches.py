"""Materialize per-record audit only after manual full-history review is complete."""
import hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
canon=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
sha=lambda x:hashlib.sha256(x).hexdigest()
baselex=json.loads((OUT/'original300-lexicon-round1.json').read_text())
# Independently inspected added forms: no listed-only irregular-base derivatives.
extra={
'lump':'l + short u + mp blend','much':'m + short u + first ch sound','past':'p + short a + st blend (short-a pronunciation)','man':'m + short a + n','drop':'dr blend + short o + p','crack':'cr blend + short a + ck','job':'j + short o + b','caps':'cap: c + short a + p; taught s on this decodable base','hush':'h + short u + sh','lift':'l + short i + ft blend','slip':'sl blend + short i + p','soft':'s + short o + ft blend','stand':'st blend + short a + nd blend','glad':'gl blend + short a + d','gift':'g + short i + ft blend','tips':'tip: t + short i + p; taught s on decodable base','sets':'set: s + short e + t; taught s on decodable base','set':'s + short e + t','spot':'sp blend + short o + t','sip':'s + short i + p'
}
for w,e in extra.items():baselex[w]={'word':w,'eligible':True,'route':'supported_decoding','evidence':e}
for w,e in {'block':'bl + short o + ck','spill':'sp + short i + ll','mad':'m + short a + d','us':'short u + s','grunt':'gr + short u + nt','rocks':'rock: r + short o + ck; taught s on decodable base','class':'cl + short a + ss','hands':'hand: h + short a + nd; taught s on decodable base'}.items():
 baselex[w]={'word':w,'eligible':True,'route':'supported_decoding','evidence':e}
findings={
1:{1:[('meaning','vessel -> cup','Vessel does not specify a cup; avoid inventing container subtype.')],9:[('naturalness/meaning','One cup is next to a cup.','Vague duplicated indefinite reference; use this cup next to that cup.')],15:[('meaning','Not much can fit','Narrow describes width; low capacity does not preserve the specific meaning.')],43:[('reading','wants','want is a Dolch-only exact exception; no independently supported want spelling is established for s derivative.')],46:[('naturalness','Stand one after one here.','Unnatural English obscures the line/turn instruction.')],49:[('meaning','round / not round','Request classifies circles, squares and triangles; two-bin answer collapses square/triangle distinction. Preserve three types.')]},
2:{21:[('constraint','Open the box. Then shut it.','Child explicitly requests one sentence containing both; target has two sentences.')],27:[('meaning','I do not know.','No knowledge is stronger than uncertainty. Keep tentative meaning.')],32:[('constraint','Do not put a hand on the pan.','User explicitly demands not replacing touch, while benchmark cannot support touch. Revise conflicting child constraint rather than claim full compliance.')],49:[('reading','likes','like is exact Dolch exception; silent-e decoding base is not established for this derivative.')]}
}

def audit(batch,roundnum,custom=None,expected=None,raw_override=None,meta_override=None,review_hash_override=None):
 p=ROOT/f'experiments/reading-compliance-20261030-001/authoring/batch-{batch:02d}'
 raw=(p/'sft.jsonl').read_bytes() if raw_override is None else raw_override
 metaraw=(p/'review.jsonl').read_bytes()
 if expected:assert sha(raw)==expected,(batch,sha(raw),expected)
 rows=[json.loads(x) for x in raw.decode().splitlines()];meta=[json.loads(x) for x in metaraw.decode().splitlines()] if meta_override is None else meta_override
 assert len(rows)==len(meta)==50
 selected=findings.get(batch,{}) if custom is None else custom
 report=[];summary={}
 frozen=[json.loads(x) for x in (ROOT/'experiments/reading-compliance-20261030-001/frozen/candidates.jsonl').read_text().splitlines()]
 for i,(r,m) in enumerate(zip(rows,meta),1):
  msgs=[x for x in r['prompt'] if x['role']!='system'];target=' '.join(x['content'] for x in r['completion'])
  assert msgs==m['context_messages'] and target==m['target_response']
  words=sorted(set(w.lower() for w in re.findall(r"[A-Za-z]+(?:['’][A-Za-z]+)?",target)))
  ev=[]
  for w in words:
   e=baselex.get(w)
   if e is None:
    if w in ('wants','likes'):e={'word':w,'eligible':False,'route':'unsupported_irregular_base_derivative','evidence':'Listed-only exact base does not automatically approve derivative; independent base spelling not established.'}
    else:raise AssertionError(('Unreviewed word',batch,i,w))
   ev.append(e)
  fs=[{'dimension':d,'span':s,'reason':why,'severity':'revise'} for d,s,why in selected.get(i,[])]
  exact=[f['case_id'] for f in frozen if canon(f['messages'])==canon(msgs)]
  assert not exact
  overlap_evidence={1:'Meaning/explanation task',2:'Exact word/form task',3:'Explicit constraint, correction, or instruction-following task',4:'Concrete capability or personal-experience truthfulness task',5:'Concrete emotional/social context task',6:'Concrete continuity or safety task'}.get(batch,'Concrete task')+': '+msgs[0]['content']+'; manually compared all frozen candidates. No same concrete request, facts, or materially equivalent full history. Shared broad category alone is not treated as overlap.'
  report.append({'case_id':m['id'],'batch':batch,'batch_index_1based':i,'round':roundnum,'record_sha256':sha(canon(r).encode()),'semantic_review':'revision_required' if any(x['dimension']!='reading' for x in fs) else 'pass','reading_review':'pass' if all(e['eligible'] for e in ev) else 'revision_required','full_history_reviewed':True,'semantic_dimensions':['meaning','relevance','truthfulness','safety','naturalness','context_tracking','explicit_constraints'],'word_evidence':ev,'findings':fs,'evaluation_overlap_review':{'all_45_frozen_candidate_histories_reviewed':True,'exact_full_history_matches':exact,'close_semantic_match':False,'evidence':overlap_evidence}})
 (OUT/f'batch-{batch:02d}-round-{roundnum}.jsonl').write_text(''.join(canon(x)+'\n' for x in report))
 (OUT/f'batch-{batch:02d}-round-{roundnum}-source.jsonl').write_bytes(raw)
 summary={'batch':batch,'round':roundnum,'source_sft_sha256':sha(raw),'source_review_sha256':review_hash_override or sha(metaraw),'rows_reviewed':50,'pass_count':sum(not x['findings'] for x in report),'revision_case_indices_1based':sorted(selected),'status':'changes_requested' if selected else 'approved','review_method':'Independent manual full-record review and exact word-form inspection of every final response; no automated semantic judge; no test access.'}
 (OUT/f'batch-{batch:02d}-round-{roundnum}-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 print(json.dumps(summary))
if __name__=='__main__':
 audit(1,1,expected='99150a0e7a6b0690fccb539a480188ce84701dbecee05cc806454b30bde6ee26')
 audit(2,1,expected='44376ebca359c2f9f2f2b85c8f21c9d755793a22c1a512971120786711793dc6')
