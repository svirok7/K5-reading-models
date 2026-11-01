"""Materialize independent manual semantic and word-form audit of original300."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
canon=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
sha=lambda x:hashlib.sha256(x).hexdigest()
source=ROOT/'datasets/sft-300-v2/sft.jsonl'
rows=[json.loads(x) for x in source.read_text().splitlines()]
dolch={w.lower() for group in json.loads((ROOT/'data/dolch-through-grade1.json').read_text())['groups'].values() for w in group}
# Each non-list form below was individually read against the benchmark and each
# of its target contexts. This explicit set is an audit decision, not a regex pass.
reviewed='''add ant ants back bad bag bath bed bell bells ben bench bends bent bill bin bit blend blocks box branch brisk bug bugs bum bun buns bus camp cannot cap cat cats chat check chest chick chin clam clap cluck crab cross crunch cup cups cut dad damp dash dent desk dip dish dishes dog dogs doll dots dress drink drops drum duck ducks dunk dusk egg eggs end fast fell fins fish fit fits fix flag flags flat fog fox frog fun gap gills glum got gran grass gull gust hand hat held hen hi hid hill hit hop hot hug hum if jam jill last left leg legs less lid list lock log long lot lunch lungs map mask mat meg melt mend mess milk miss mix moth mud mug mum nap next nut nuts off or pack pan path peg pegs pen pens pet pick pig pin pink pit plan plod plum plums pond pot press quack quick quilt rag rags rat rest rex ring rip rock rug rush sad sand sat sent shell shells shock shop shut sing sink sip sit six skip slid slug slugs smell snap snug sock socks song spin splint sprang sprint stack stacks stamps step stick sticks still strings strum stuck stump sun sunset swim tap tell tent thick thin thing things thump tin tip top trim trip truck trunk tug twig vet wet wig win wind wings wink zip'''.split()
reviewed=set(reviewed)
inflections={'ants':'ant','bells':'bell','bends':'bend','blocks':'block','bugs':'bug','buns':'bun','cats':'cat','cups':'cup','dishes':'dish','dogs':'dog','dots':'dot','drops':'drop','ducks':'duck','eggs':'egg','fins':'fin','fits':'fit','flags':'flag','gills':'gill','legs':'leg','lungs':'lung','nuts':'nut','pegs':'peg','pens':'pen','plums':'plum','rags':'rag','shells':'shell','slugs':'slug','socks':'sock','stacks':'stack','stamps':'stamp','sticks':'stick','strings':'string','things':'thing','wings':'wing'}
lex={}
for w in sorted(dolch|reviewed):
 if w in dolch:route='exact_dolch';evidence='Exact case-insensitive form in frozen cumulative133 list.'
 elif w=='or':route='curriculum_leap';evidence='Explicit curriculum Leap Word or.'
 elif w=='hi':route='open_syllable';evidence='h + long i in an open syllable, explicitly exemplified by profile.'
 elif w in ('cannot','sunset'):route='supported_compound';evidence=('can + not' if w=='cannot' else 'sun + set')+'; both parts supported closed syllables.'
 elif w in inflections:route='supported_s_es';evidence='Supported closed-syllable base '+inflections[w]+' plus taught s/es inflection.'
 else:route='supported_closed_syllable';evidence='Manually checked short-vowel closed syllable with taught consonants/blends/digraphs, ff/ll/ss/ck/ng/nk as applicable.'
 lex[w]={'word':w,'eligible':True,'route':route,'evidence':evidence}
findings={32:[{'dimension':'truthfulness','severity':'revise','span':'You know a lot!','reason':'Child self-label genius provides no evidence for broad knowledge praise. Prefer grounded neutral engagement.'}],45:[{'dimension':'relevance','severity':'revise','span':'It can ring when you hit it.','reason':'Answers when the bell rings rather than why it makes noise. Add an easy causal account or otherwise answer the actual why request without false science.'}],65:[{'dimension':'context/relevance','severity':'revise','span':'Not hot, then.','reason':'Child selects cold over warm; merely not hot does not retain that choice because warm is also not hot. Refer clearly to the milk not rejected.'}]}
report=[]
for i,row in enumerate(rows,1):
 words=sorted(set(w.lower() for w in re.findall(r"[A-Za-z]+(?:['’][A-Za-z]+)?",' '.join(m['content'] for m in row['completion']))))
 missing=set(words)-set(lex);assert not missing,missing
 report.append({'training_index_1based':i,'record_sha256':sha(canon(row).encode()),'semantic_review':'revision_required' if i in findings else 'pass','dimensions_reviewed':['relevance','context_tracking','factual_truthfulness','safety','naturalness','length','rhythm','exact_word_form_eligibility'],'reading_review':'pass','target_word_types':words,'word_evidence':[lex[w] for w in words],'findings':findings.get(i,[]),'review_method':'Independent manual full-record and full-target review; every non-Dolch word individually checked, explicit word evidence materialized.'})
(OUT/'original300-round1.jsonl').write_text(''.join(canon(r)+'\n' for r in report))
(OUT/'original300-lexicon-round1.json').write_text(json.dumps(lex,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
(OUT/'original300-round1-summary.json').write_text(json.dumps({'source':'datasets/sft-300-v2/sft.jsonl','source_sha256':sha(source.read_bytes()),'rows_reviewed':300,'semantic_pass':297,'semantic_revision_required':[32,45,65],'reading_pass':300,'non_dolch_forms_individually_reviewed':240,'test_accessed':False,'status':'changes_requested'},indent=2)+'\n')
print('Wrote all300 independent row audits + explicit word evidence; semantic revisions32,45,65; reading300 pass.')
