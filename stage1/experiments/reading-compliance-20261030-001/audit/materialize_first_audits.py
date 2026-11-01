import copy,importlib.util,json
from pathlib import Path
P=Path(__file__).resolve().parent;s=importlib.util.spec_from_file_location('audit',P/'audit_batches.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
base=P.parent/'authoring'
initial={1:{1:'The cup has a little milk in it.',9:'One cup is next to a cup.',15:'Not much can fit in the gap.',43:'No. It wants to eat a lot now.',46:'Stand one after one here.',49:'Put all that are round here. Put all that are not round there.'},2:{21:'Open the box. Then shut it.',27:'I do not know.',49:'Meg likes plums too.'},3:{45:'You have a lot to tell them. What will you say?'}}
expected={1:'99150a0e7a6b0690fccb539a480188ce84701dbecee05cc806454b30bde6ee26',2:'44376ebca359c2f9f2f2b85c8f21c9d755793a22c1a512971120786711793dc6',3:'7776eb156e6992e4433e59a70feb5bf9f9800a4c85e60d9f57e59766da7905a8'}
rhash={1:'0af6be3a9937b583e60b1d7df67ab03501282e3b87b4e34f8124aef95eb1789d',2:'7d777bb660a3194796484d7a38cc145d7ae31d617e1e359c726a4f6f50baf7fa',3:'eff1d185bd96c2ddab9a74b3505abf7789bb3983e8fad861074852656cee0d47'}
for b in [1,2,3]:
 rows=[json.loads(x) for x in (base/f'batch-{b:02d}/sft.jsonl').read_text().splitlines()]
 meta=[json.loads(x) for x in (base/f'batch-{b:02d}/review.jsonl').read_text().splitlines()]
 for idx,t in initial[b].items():rows[idx-1]['completion'][0]['content']=t
 if b==1:
  row=rows[45]
  row['prompt']=[row['prompt'][0],*[
   {'role':'user','content':'I saw a sign saying queue here.'},
   {'role':'assistant','content':'Where was it?'},
   {'role':'user','content':'At a ticket desk.'},
   {'role':'assistant','content':'People wait there.'},
   {'role':'user','content':'I do not know queue.'},
   {'role':'assistant','content':'We can use an easy phrase.'},
   {'role':'user','content':'What does the sign mean?'}]]
 if b==2:
  rows[26]['prompt'][1]['content']="My note says I'm not sure."
  rows[31]['prompt'][5]['content']='And do not replace touch with hold.'
 for r,m in zip(rows,meta):m['context_messages']=[x for x in r['prompt'] if x['role']!='system'];m['target_response']=r['completion'][0]['content']
 raw=(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows)).encode()
 assert a.sha(raw)==expected[b],(b,a.sha(raw))
 custom={45:[('truthfulness','You have a lot to tell them.','Excited to write does not establish a lot of content; use grounded reflection.')]} if b==3 else None
 a.audit(b,1,custom=custom,expected=expected[b],raw_override=raw,meta_override=meta,review_hash_override=rhash[b])
a.audit(1,2,custom={},expected='d6c72ae616e6a698f77632d6b1e24447e8d1dd18d3ca6fb46d709eac06805315')
a.audit(2,2,custom={},expected='2e499841106d39bb085045d43cc2d654585deb4f291ce893e0f2d0fbb8bb3d54')
