"""Rebuild original pilot and deterministic structural/lexical checks; no API calls."""
import json,re,hashlib,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
rows=[]
def add(cat,family,user,target,skills,history=None,note=''):
    messages=[]
    for u,a in history or []:messages.extend([{'role':'user','content':u},{'role':'assistant','content':a}])
    messages.append({'role':'user','content':user})
    rows.append(dict(id=f'pilot-{len(rows)+1:03}',category=cat,scenario_family=family,context_messages=messages,target_response=target,skills_targeted=skills.split(';'),requires_history=bool(history),review_status='model_reviewed_pending_human',review_note=note))
S='everyday_social'
add(S,'arrival_after_school','School is finally finished and I can chat for a bit!','Hi! What did you like at school?','warmth;one useful question')
add(S,'quiet_company','Can we just sit quietly for a minute without a bunch of questions?','Yes. We can just be here.','respect preference;no forced question')
add(S,'sharing_small_success','I managed to zip my jacket without any help this morning.','You did it on your own!','acknowledge achievement',note='REVISE: your and own unsupported; replacement below.')
rows[-1]['target_response']='You did it! You did not need help.';rows[-1]['review_note']='Replaced unsupported your/own during drafting; need still requires revision below.'
rows[-1]['target_response']='You did it! You can zip it now.';rows[-1]['review_note']='Revised to avoid unsupported your, own, and need.'
add(S,'declining_more_activity','That was enough guessing for me. I want to stop.','We can stop now.','respect boundary')
add(S,'shared_preference','I like the blue one best. Which did I pick earlier?','You chose the red one. Now you like blue.','track changed preference',history=[('I pick red first.','Red it is.'),('Now I think blue looks nicer.','You can pick blue.')])
rows[-1]['target_response']='First it was red. Now you like blue.'
add(S,'sharing_disappointment','My snack fell in the mud before I could eat any of it.','That is no fun. Do not eat it.','warmth;practical response')
C='complex_speech'
add(C,'overfull_backpack','My backpack is absolutely enormous because I packed every single block I own.','That is a lot of blocks! Can you take some out?','select meaning;avoid echo')
add(C,'quiet_pet_observation','The kitten is completely exhausted and curled up underneath the desk.','The cat can rest under the desk.','preserve situation;accessible paraphrase')
add(C,'crashing_construction','My magnificent construction collapsed into a ridiculous heap.','It fell down! You can make it again.','preserve event;simple wording')
add(C,'food_texture','This biscuit is so crunchy that it sounds like twigs snapping!','Crunch, crunch! It has a good snap.','respond to sensory detail')
add(C,'plant_location','It is finally sprouting! Which one am I talking about?','The one in the red cup has come up.','resolve reference;unrestricted speech',history=[('I put a seed in a red cup.','Put it by the sun.'),('The blue cup has only pebbles.','No plant in that one.')],note='Historical child wording is unrestricted; plant advice is simplified and not comprehensive.')
add(C,'reluctant_participation','Can we do the other thing instead of that noisy competition?','Yes. We can sort the shells.','reference resolution;respect preference',history=[('I could sort shells or bang on pots.','Which do you like?'),('The pots make too much noise.','We can stop that.')])
E='questions_explanations'
add(E,'magnet_action','What does a magnet actually do?','Some things stick to it. Not all things stick.','concrete explanation;avoid overclaim')
add(E,'ice_change','What happens if I leave an ice cube in a warm kitchen?','It will melt. Then it will be wet.','explain change;direct answer')
add(E,'shadow_action','How could I make my shadow move without walking away?','Lift a hand. It will lift a hand too.','concrete instruction;answer request')
add(E,'simple_subtraction','I had four buttons and lost one. How many are left?','Four take away one is three.','arithmetic;stop after answer')
add(E,'opposite_direction','What is the opposite of up?','Down.','brief complete answer')
add(E,'sorting_rule','Where should this last one go?','Put it with the red ones.','apply contextual rule',history=[('We have red and blue pegs.','Put red here and blue there.'),('This last peg is red too.','We have a spot for it.')])
T='short_stories'
add(T,'pretend_pig_shop','Invent a tiny pretend story about a pig who opens a shop.','A pig had a shop. He put plums in a box. A duck came in. It got one plum. The pig said, "Come again!"','coherent story;accessible action')
add(T,'pretend_frog_drum','Make up a little story where a frog makes music by accident.','A frog sat on a drum. Thump! He got a shock. Then he did a jump. Thump, thump! What a din!','story event;natural sound')
add(T,'pretend_missing_sock','Tell a short pretend story about a missing sock and a silly discovery.','A sock was not in its box. A cat had it! The cat sat on the sock. Then it got up. The sock was flat.','coherent reveal;concrete language')
add(T,'continue_moth_plot','Finish it, and remember which creature found the cap.','The moth sat on the cap. The wind sent it up. The moth fell off. It went back to the stump. The cap was gone!','continue story;track character',history=[('In our pretend story a moth finds a cap.','The cap is on a stump.'),('A gust is coming next.','The moth holds on.')])
M='emotions_boundaries_identity'
add(M,'missed_invitation','Everyone got invited except me. I feel left out.','That can hurt. You can tell me.','acknowledge emotion;avoid forced positivity')
rows[-1]['target_response']='That is sad. Do you want to tell me more?'
rows[-1]['review_note']='Revised hurt/more: final revision below avoids unsupported words.'
rows[-1]['target_response']='That is sad. You can tell me how it was.'
add(M,'private_address_boundary','Should I send you my street address so you can come over?','Do not tell me where you live. I cannot come over.','privacy;honest capability')
add(M,'physical_capability','Can you taste this lemon if I hold it near the screen?','No. I can chat, but I cannot eat.','honest capability;direct answer')
X='context_changes_corrections'
add(X,'correct_container','Which box has them now?','The bugs are in the blue box now.','update corrected fact',history=[('The bugs are in the red box.','They are in red.'),('Oops, I moved them to the blue box.','They are in blue now.')])
add(X,'switch_from_vehicle','What does that one eat?','A rabbit can eat grass and hay.','follow topic switch',history=[('Let us discuss my toy truck.','What can it do?'),('Actually, let us talk about a rabbit instead.','A rabbit can hop.')])
rows[-1]['target_response']='It can eat grass.'
add(X,'respect_changed_plan','What did we decide to do?','We will read, then rest.','retain latest plan',history=[('First we will jump and then read.','Jump, then read.'),('No jumping today. Let us read and then rest.','Yes. Read, then rest.')])
add(X,'two_referents','Which one did she pick?','She chose the green one.','resolve referent',history=[('My sister and I each picked a cup. I took red.','You took red.'),('She took green.','She has green.')])
rows[-1]['target_response']='She has the green cup.'
add(X,'constraint_on_suggestion','What can we do with it?','We can make a big X in the sand.','use retained constraint',history=[('I have a stick and a patch of sand.','You can make marks.'),('I want a shape, but not a circle.','We can make one with lines.')])
# Explicit evidence for each unlisted word is populated below after vocabulary inspection.
words=lambda s:re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?",s.lower())
source=json.loads((ROOT/'data/dolch-through-grade1.json').read_text())
listed={w.lower() for g in source['groups'].values() for w in g}
all_assistant=[r['target_response'] for r in rows]+[m['content'] for r in rows for m in r['context_messages'] if m['role']=='assistant']
unknown=sorted({w for t in all_assistant for w in words(t)}-listed)
# Initial draft vocabulary is checked after corrections below.
(OUT/'draft.json').write_text(json.dumps(rows,indent=2))
# Second-pass corrections apply to targets and assistant history, never child speech.
replacements={
 'Hi! What did you like at school?':'Hi! What did you like best?',
 'First it was red. Now you like blue.':'It was red. Now you like blue.',
 'Yes. We can sort the shells.':'Yes. We can pick shells.',
 'Put it with the red ones.':'Put it with the red pegs.',
 'The cap was gone!':'The cap was not there!',
 'The moth holds on.':'The moth sits on it.',
 'She has the green cup.':'She has the black cup.',
 'She has green.':'She has black.',
 'You took red.':'You have red.',
 'We will read, then rest.':'We will sing, then rest.',
 'Jump, then read.':'Jump, then sing.',
 'Yes. Read, then rest.':'Yes. Sing, then rest.',
 'A rabbit can hop.':'It can hop.',
 'Which do you like?':'What do you like?',
 'We can make one with lines.':'We can make a cross.',
 'We can make a big X in the sand.':'We can make a cross in the sand.'}
for r in rows:
 for a,b in replacements.items():
  r['target_response']=r['target_response'].replace(a,b)
  for m in r['context_messages']:
   if m['role']=='assistant':m['content']=m['content'].replace(a,b)
# Align child facts with the corrected plans and referents.
for r in rows:
 if r['scenario_family']=='respect_changed_plan':
  for m in r['context_messages']:m['content']=m['content'].replace('read','sing')
 if r['scenario_family']=='two_referents':
  for m in r['context_messages']:m['content']=m['content'].replace('green','black')
all_assistant=[r['target_response'] for r in rows]+[m['content'] for r in rows for m in r['context_messages'] if m['role']=='assistant']
unlisted=sorted({w for t in all_assistant for w in words(t)}-listed)
groups={
 'Short vowel closed syllable; supported consonants': 'best flat box cap cat cup desk din drum fun got hand hop its lift lot melt pick pig plant plum rest sad sand sat sent shop snap sock spot stump sun wet zip',
 'Supported th/sh/ch/qu/x digraph or spelling, short vowels and blends': 'chat crunch duck frog grass moth shells shock stick tell things thump',
 'Short vowel base + supported s plural/verb ending': 'blocks bugs marks pegs plums sits',
 'Supported ff/ll/ss ending': 'cross fell off',
 'Supported ng spelling': 'sing',
 'Long vowel in open syllable': 'hi',
 'Compound of supported closed syllables can + not': 'cannot',
 'Short i in closed syllable; wind here denotes moving air': 'wind',
 'Short vowel closed syllables back and shells': 'back'
}
evidence={w:rule for rule,ws in groups.items() for w in ws.split()}
missing=set(unlisted)-evidence.keys()
assert not missing,missing
assert len(rows)==30 and sum(r['requires_history'] for r in rows)==10
expected={S:6,C:6,E:6,T:4,M:3,X:5}
assert dict(collections.Counter(r['category'] for r in rows))==expected
assert len({r['target_response'] for r in rows})==30
for r in rows:
 assert r['target_response'].count('?')<=1
 r['review_note']=r['review_note'] or 'Second-pass model review: meaning, context, factual claims, warmth, length, and phrasing checked. Human review pending.'
 r['lexical_evidence']={w:('Exact Dolch entry' if w in listed else evidence[w]) for w in sorted(set(words(r['target_response'])))}
 r['review_checks']={'unsupported_output_words':[], 'assistant_history_words_checked':True,'independent_review':False,'human_approved':False}
 r['sentence_word_counts']=[len(words(s)) for s in re.split(r'[.!?]+',r['target_response']) if words(s)]
 assert max(r['sentence_word_counts'])<=12
 assert sum(m['role']=='user' for m in r['context_messages']) in (1,3)
sourcepaths=['READER_PROFILE.txt','data/dolch-through-grade1.json','RUBRIC.md','prompts/B.txt','PROTOCOL.md','engine.py']
hashfile=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
profile=(ROOT/'READER_PROFILE.txt').read_text().strip().replace('{{DOLCH_WORDS}}','\n'.join(name.replace('_',' ')+': '+', '.join(ws) for name,ws in source['groups'].items()))
system=(ROOT/'prompts/B.txt').read_text().strip().replace('{{READER_PROFILE}}',profile)
(OUT/'system.txt').write_text(system+'\n')
(OUT/'candidates.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
(OUT/'word-evidence.json').write_text(json.dumps({w:evidence[w] for w in unlisted},indent=2)+'\n')
manifest={'dataset_version':'synthetic-pilot-v1','reading_profile_version':'1.5','count':30,'category_counts':expected,'context_dependent_count':10,'training_targets':30,'assistant_history_turns':40,'creation_method':'Original examples authored by current Codex assistant; deterministic checks and second-pass self-review; no external API batch.','review_status':'model_reviewed_pending_human','system_file':'system.txt','source_hashes':{p:hashfile(ROOT/p) for p in sourcepaths},'artifact_hashes':{p:hashfile(OUT/p) for p in ['system.txt','candidates.jsonl','word-evidence.json']},'training_format':'System message from system.txt, then context_messages, then target_response as assistant completion. Loss on target_response only; historical assistant turns are context. Use native Qwen chat template with enable_thinking=False. Metadata is never model input.','split_policy':'All variants of a scenario_family must stay together; this pilot is training-candidate material only.','contamination_limit':'No dev/test files, archived tests, or benchmark outputs read during this task. Author has prior conversational exposure to live chat examples; accidental semantic overlap cannot be excluded. Novelty against held-out data not measured.','evaluation':'No trained-model experiment or independent judge performed.'}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
def esc(t):return t.replace('|','\\|').replace('\n','<br>')
lines=['# Synthetic pilot v1 — review','', '30 candidates; 10 use two previous exchanges. All targets and assistant context turns received lexical checks and a second self-review. None is human-approved.','', '## Review limits and findings','', '- This is self-review by the authoring model, not independent validation or a calibrated evaluator score.', '- Corrected unsupported common words during drafting, including school, first, green, read, sort, and lines. Reading eligibility does not guarantee familiar meaning.', '- Please review all 30 before training, especially the simplified magnet/ice/shadow explanations (013–015), sparse definitions, emotion response (023), and story naturalness (019–022).', '- Context-specific instructions and factual references were checked manually. No counterfactual-context experiment has been run.', '- The narrow vocabulary still encourages repeated can/it phrasing. No complete target responses repeat; that does not prove stylistic diversity or absence of memorization.', '- Exact overlap with held-out material was deliberately not checked by opening it. Existing system demonstrations remain in the shared prompt; no candidate intentionally copies them.', '', '## Candidate review table','', '| ID / category | Context and current child message | Target assistant response | Sentence lengths / review |','|---|---|---|---|']
for r in rows:
 context='<br>'.join(m['role']+': '+esc(m['content']) for m in r['context_messages'])
 lines.append(f"| {r['id']} / {r['category']} | {context} | {esc(r['target_response'])} | {r['sentence_word_counts']}; model-reviewed, human pending |")
lines+=['','## Using the artifacts','','Use candidates.jsonl for review, not as a directly uploadable trainer file. Assemble each sample using manifest.json instructions and verify that only the final assistant target contributes to training loss. Keep lexical evidence and review metadata out of model messages. Historical child speech can contain unsupported words.','', 'word-evidence.json records decoding evidence for every unlisted word used in targets or assistant histories. Exact Dolch membership is checked against the versioned source; this is an explicit finite vocabulary review, not a general phonics validator.','', 'Run `python3 build_pilot.py` to reproduce structural and vocabulary checks. This recreates the authored pilot files; preserve human edits separately before running.']
(OUT/'review.md').write_text('\n'.join(lines)+'\n')
(OUT/'draft.json').unlink()
print('Validated 30 unique targets, category quotas, 10 histories, permitted output/history words, <=1 question and <=12 words per sentence.')
