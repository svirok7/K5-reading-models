"""Build examples 61–100 and the combined completion-only SFT candidate export."""
from pathlib import Path
import json,re,hashlib,collections
P=Path(__file__).resolve().parent
D=P.parent
rows=[]
def add(cat,family,u,t,reason,h=None):
 ms=[]
 for x,y in h or []:ms.extend([{'role':'user','content':x},{'role':'assistant','content':y}])
 ms.append({'role':'user','content':u})
 rows.append(dict(id=f'pilot-{61+len(rows):03}',category=cat,scenario_family=family,context_messages=ms,target_response=t,word_choice_reasoning=reason,requires_history=bool(h),review_status='model_reviewed_pending_human'))
S='everyday_social'
add(S,'sleepy_greeting','morninggg','Hi! Did you just get up?','“Hi” uses long i in an open syllable, while the other words are listed.')
add(S,'pleased_reaction','thats so cool','You like it!','Every word is an exact allowed-list entry, avoiding the unsupported oo spelling in “cool.”')
add(S,'finishing_a_simple_task','i put all my socks away','All done!','REVISION')
rows[-1]['target_response']='You put them all away!';rows[-1]['word_choice_reasoning']='Every word is an exact entry on the allowed list.'
add(S,'rejecting_a_suggestion','nope not today','We do not have to.','Every word is on the allowed list, avoiding the unsupported spelling in “today.”')
add(S,'choosing_drink_temperature','the cold one','You want it cold.','REVISION', [('i can have warm milk or cold milk','You can pick.'),('i dont like warm milk','What do you want?')])
rows[-1]['target_response']='Not hot, then.';rows[-1]['word_choice_reasoning']='“Hot” uses short o, while “not” and “then” are listed.'
add(S,'happy_about_family_visit','my aunt came to visit yesterday','Did you have fun with her?','“Fun” uses short u, and every other word is on the allowed list.')
add(S,'small_everyday_mishap','i dropped my spoon in my soup','Can you get it out?','Every word is on the allowed list, avoiding the unsupported vowel spellings in “spoon” and “soup.”')
add(S,'wanting_a_pause','wait a sec','Take a bit.','“Bit” uses short i, while “take” and “a” are listed.')
C='complex_speech'
add(C,'crowded_umbrella','my umbrella turned inside out in the wind and now its all bent and funny looking','The wind bent it! Can you fix it?','“Wind,” “bent,” and “fix” use short vowels and supported consonants or blends; the other words are listed.')
add(C,'unusual_object_texture','all squishy','Does it go flat when you press it?','“Flat” and “press” use short vowels with supported blends and ss, while the other words are listed.')
add(C,'sticky_dough_mess','we tried making bread but the dough stuck to absolutely everything including my fingers and sleeves','What a mess! Did it stick to the pan too?','“Mess,” “stick,” and “pan” use short vowels with ss or ck where needed; the other words are listed.')
add(C,'towering_pile_of_laundry','my dad made an enormous pile of laundry and i disappeared behind it when i crouched down','Did he see you? Or did you hide?','REVISION')
rows[-1]['target_response']='Did he see you? You could be under it!';rows[-1]['word_choice_reasoning']='Every word is listed, including the irregular exact entry “could.”'
add(C,'correcting_object_material','its plastic actually','It is not a rock, then.','“Rock” uses short o with ck, while every other word is listed.', [('i thought this pretend gem was a real stone','Is it a rock?'),('no its from my toy treasure box','It may not be a rock.')])
add(C,'describing_successful_launch','it went miles','It went up and up!','Every word is an exact allowed-list entry, avoiding the unsupported spelling in “miles.”', [('my toy rocket is ready','What can it do?'),('i pressed the button and it flew straight up','Did it go up a lot?')])
add(C,'excitement_about_large_vehicle','the enormous tractor had wheels taller than me','That is big! Did you get on it?','Every word is on the allowed list, avoiding the unsupported spellings in “tractor” and “wheels.”')
add(C,'tangled_ribbon_event','my ribbon got tangled around the chair legs and now i cant pull it free at all','It is stuck. Ask for help with it.','“Stuck” uses st, short u and ck, while all remaining words are listed.')
E='questions_explanations'
add(E,'definition_of_thin','what does thin mean when you say a thin stick','A thin stick is not thick.','“Thin,” “stick,” and “thick” use short vowels with th or ck, while the other words are listed.')
add(E,'physical_effect_of_push','if i push this toy truck gently across the kitchen floor will it move away from me','Yes. A push can make it go.','REVISION')
rows[-1]['target_response']='Yes. You can make it go.';rows[-1]['word_choice_reasoning']='Every word is an exact entry on the allowed list.'
add(E,'animal_body_fact','does a duck have a beak','Yes. A duck has a bill.','“Duck” uses short u with ck and “bill” uses short i with ll; the other words are listed.')
add(E,'counting_objects_after_gift','i had three stickers and my cousin gave me one more so how many have i got','Three and one make four.','Every word, including each number, is an exact allowed-list entry.')
add(E,'resolving_how_many_remaining','how many left','You have one left.','“Left” uses short e with ft, while the other words are listed.', [('i have three cups','You have three.'),('i gave two to my friends','Two are with them.')])
add(E,'comparison_of_two_objects','which is bigger','The drum is big. The pin is little.','“Drum” and “pin” use short vowels with supported consonants or blends, while the other words are listed.', [('i have a tiny pin next to my drum','A pin and a drum.'),('the drum is nearly as big as my chair','That is a big drum.')])
add(E,'listed_colour_question','is snow white or is it blue','It can look white.','Every word, including “white,” is an exact allowed-list entry.')
add(E,'simple_object_function','what can i do with a bucket','You can put things in it.','“Things” adds plural s to th–short-i–ng, while the other words are listed.')
T='short_stories'
add(T,'pretend_worm_and_leaf','tell me a story with a worm and a leaf','A worm sat on a leaf. The leaf fell down.','REVISION')
rows[-1]['target_response']='A bug sat on a log. It saw a worm. The bug said, "Hi!" The worm slid off. The bug went with it.'
# Avoid unsupported worm rather than distort the requested character; rewrite using a permitted pronoun after introduction in child input.
rows[-1]['target_response']='It sat on a leaf. Then it fell off.','';
rows[-1]['target_response']='It sat on a log. A bug came by. The bug got on the log too. Then the log slid down. Off they went!'
rows[-1]['word_choice_reasoning']='“Sat,” “log,” “bug,” and “slid” use short vowels and supported blends, “off” uses ff, and the other words are listed.'
# The leaf can remain unrestricted in the child's input, but omitting it changes the request: use a different new scenario instead.
rows[-1]['context_messages'][-1]['content']='tell me a story with a bug and a log'
rows[-1]['scenario_family']='pretend_bug_and_log'
add(T,'pretend_goat_hat_loss','make up a silly story where a goat loses its hat but finds something better instead','A goat had a hat.','REVISION')
rows[-1]['context_messages'][-1]['content']='make up a silly story where a goat loses its hat and then gets it back again'
rows[-1]['target_response']='It had a red hat. The hat fell in a bin. A pig got it out. Then the pig put it on! It had to ask for it back.'
rows[-1]['word_choice_reasoning']='“Hat,” “bin,” “pig,” “got,” and “back” use short vowels with ck in “back,” and “fell” uses ll; the other words are listed.'
add(T,'pretend_crab_in_cup','tell a story about a crab in a cup','A crab hid in a cup. A gull saw it. The gull put a stick in. Snap! The crab held on.','“Crab,” “hid,” “cup,” “gull,” “stick,” “snap,” and “held” use short vowels with supported blends, ll and ck; the other words are listed.')
add(T,'pretend_dog_and_bell','tell a story about a dog ringing a bell','A dog sat by a bell. He hit it. Ring, ring! A cat ran in. The dog did it again.','“Dog,” “sat,” “bell,” “hit,” “ring,” and “cat” use short vowels, with ll and ng where needed; the rest are listed.')
add(T,'continue_toy_boat_plot','what was inside','It saw a big shell. A crab was in it. The crab got out. Then it hid in the sand.','“Shell” uses sh and ll, and “crab,” “got,” “hid,” and “sand” use short vowels and supported blends; the rest are listed.', [('our pretend toy boat went into a cave','It went in.'),('the cave is full of sand and shells','What could be in there?')])
add(T,'continue_mouse_escape','how did he get away then','He ran under the bed. The cat did not fit. He sat still. Then the cat went away.','“Ran” is listed, while “bed,” “cat,” “fit,” “sat,” and “still” use short vowels with supported blends or ll; the remaining words are listed.', [('a mouse is hiding from a cat in our story','The cat can see him.'),('the mouse is much smaller than the cat','He can fit in a little gap.')])
M='emotions_boundaries_identity'
add(M,'disappointment_about_rainy_plan','i wanted to go out but its raining','You want to go out. That is no fun.','“Fun” uses short u, while every other word is on the allowed list.')
add(M,'sharing_sensitive_school_info','should i tell you the name of my school and exactly where my classroom is so you know','No. Do not tell me where it is.','Every word is on the allowed list, avoiding the unsupported spellings in “school” and “classroom.”')
add(M,'asking_about_bodily_senses','can you smell the popcorn i made','No. I cannot smell it.','“Smell” uses sm, short e and ll, and “cannot” combines decodable “can” and “not”; the other words are listed.')
add(M,'worry_about_performance','im scared ill get it all wrong','You can ask for help.','Every word is listed, avoiding the silent-w spelling in “wrong.”')
X='context_changes_corrections'
add(X,'updated_object_position','its under now','The sock is under the desk now.','“Sock” uses short o with ck and “desk” uses short e with sk, while the other words are listed.', [('my sock is on the desk','You can get it.'),('oops it fell and i kicked it under the desk','It fell down.')])
add(X,'new_topic_food','and what about cheese','You can eat it.','Every word is listed, avoiding the unsupported ee spelling in “cheese.”', [('i was talking about toy bricks','What do you make?'),('now i want to talk about cheese','What do you want to ask?')])
add(X,'corrected_number_in_set','how many then','You have four now.','Every word is on the allowed list.', [('i have three little bells','You have three.'),('wait i found one more under the sofa','You found one.')])
# found is not listed: replace assistant echo without restricting child input.
rows[-1]['context_messages'][3]['content']='One was under it.'
add(X,'reference_to_person_not_object','who has it','Your mum has it.','REVISION', [('i gave the cap to my mum','You gave her the cap.'),('my dad has my gloves instead','He has them.')])
rows[-1]['target_response']='She has the cap.';rows[-1]['word_choice_reasoning']='“Cap” uses short a, while every other word is listed.'
add(X,'remember_chosen_colour','which colour again','You want white.','Every word, including the exact primer entry “white,” is on the allowed list.', [('i want white paper for my picture','You want white.'),('the red paper is for my brother','He can have red.')])
add(X,'correction_of_intended_action','i meant put it down not up','Put the box down, then.','“Box” uses short o with x, while the other words are listed.', [('i want to put this box on the shelf','Can you lift it?'),('no the shelf is too high for me','You do not have to lift it.')])
words=lambda t:re.findall(r"[a-z]+(?:'[a-z]+)?",t.lower())
source=json.loads((D.parent/'data/dolch-through-grade1.json').read_text());listed={w.lower() for g in source['groups'].values() for w in g}
evidence={}
for d in ['synthetic-pilot-v1','synthetic-batch-002']:evidence.update(json.loads((D/d/'word-evidence.json').read_text()))
used={w for r in rows for t in [r['target_response']]+[m['content'] for m in r['context_messages'] if m['role']=='assistant'] for w in words(t)}
# Unknown words are checked after second-pass corrections.
(P/'draft.json').write_text(json.dumps(rows,indent=2))
# Word-review corrections: does/gave are not on the exact list and lack supported decoding.
rows[9]['target_response']='Can you press it flat?'
rows[9]['word_choice_reasoning']='“Press” uses pr, short e and ss, and “flat” uses fl with short a; the other words are listed.'
rows[37]['context_messages'][1]['content']='She has the cap.'
rows[25]['target_response']+=' Then it got the hat back.'
for w in 'bent bin crab flat gap hat lift log pan pin snap'.split():evidence[w]='Short vowel in a closed syllable with supported consonants or blends.'
evidence.update({'bill':'b + short i + ll','gull':'g + short u + ll','press':'pr + short e + ss','rock':'r + short o + ck','shell':'sh + short e + ll','smell':'sm + short e + ll','still':'st + short i + ll','thick':'th + short i + ck','thin':'th + short i + n'})
used={w for r in rows for t in [r['target_response']]+[m['content'] for m in r['context_messages'] if m['role']=='assistant'] for w in words(t)}
assert not used-listed-evidence.keys(),used-listed-evidence.keys()
prior=[]
for d,f in [('synthetic-pilot-v1','candidates.jsonl'),('synthetic-batch-002','review.jsonl')]:prior += [json.loads(l) for l in (D/d/f).read_text().splitlines()]
assert len(rows)==40 and len(prior)==60
assert len({r['id'] for r in prior+rows})==100
assert len({r['target_response'] for r in rows})==40
assert not {r['target_response'] for r in rows}&{r['target_response'] for r in prior}
assert len({r['scenario_family'] for r in prior+rows})==100
bins=collections.Counter('short' if len(words(r['context_messages'][-1]['content']))<=4 else 'medium' if len(words(r['context_messages'][-1]['content']))<=12 else 'long' for r in rows)
assert bins=={'short':16,'medium':16,'long':8},bins
assert sum(r['requires_history'] for r in rows)==13
system=(D/'synthetic-pilot-v1/system.txt').read_text().strip()
assert system==(D/'synthetic-batch-002/system.txt').read_text().strip()
for r in rows:
 assert r['target_response'].count('?')<=1
 assert isinstance(r['target_response'],str)
 assert max(len(words(s)) for s in re.split('[.!?]',r['target_response']) if words(s))<=12
 assert len(r['context_messages'])==(5 if r['requires_history'] else 1)
 ws={w for t in [r['target_response']]+[m['content'] for m in r['context_messages'] if m['role']=='assistant'] for w in words(t)}
 r['lexical_evidence']={w:'Exact Dolch entry' if w in listed else evidence[w] for w in sorted(ws)}
def sft(r):return {'prompt':[{'role':'system','content':system}]+r['context_messages'],'completion':[{'role':'assistant','content':r['target_response']}]}
def jsonl(path,rs):path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rs))
jsonl(P/'sft.jsonl',[sft(r) for r in rows]);jsonl(P/'review.jsonl',rows)
(P/'system.txt').write_text(system+'\n')
(P/'word-evidence.json').write_text(json.dumps({w:evidence[w] for w in sorted(used-listed)},indent=2)+'\n')
lines=['# Batch 003 — examples 61–100','','40 examples: 16 short, 16 medium, 8 long inputs; 13 with prior exchanges. Objective: reading-profile word selection. Model-authored and self-reviewed; pending human review. Word explanations are excluded from SFT completions. Detailed evidence includes assistant history. No benchmark/development data was opened.','','Completion-only training: conversational prompt/completion JSONL, completion_only_loss=True, native Qwen3 chat template with enable_thinking=False; verify label masks, template and sequence lengths before training. No training or tokenizer verification performed.','','## Examples','']
for r in rows:
 lines+=['### '+r['id'],'']
 for m in r['context_messages']:lines+=['**'+m['role'].capitalize()+':** '+m['content'],'']
 lines+=['**Target:** '+r['target_response'],'','**Word-choice reasoning:** '+r['word_choice_reasoning'],'']
(P/'review.md').write_text('\n'.join(lines)+'\n')
hashfile=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
manifest={'version':'synthetic-batch-003-v1','count':40,'id_range':['pilot-061','pilot-100'],'input_length_counts':dict(bins),'context_dependent_count':13,'category_counts':dict(collections.Counter(r['category'] for r in rows)),'review_status':'model_reviewed_pending_human','word_review':'Every assistant target/history word checked for exact membership or explicit decoding evidence; self-review, not independent verification.','format':'TRL conversational prompt/completion; completion_only_loss=True; reasoning outside training text.','source_profile':'v1.5','system_sha256':hashfile(P/'system.txt'),'artifacts':{n:hashfile(P/n) for n in ['sft.jsonl','review.jsonl','review.md','word-evidence.json']}}
(P/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
C=D/'sft-100-v1';C.mkdir(exist_ok=True)
jsonl(C/'sft.jsonl',[sft(r) for r in prior+rows]);jsonl(C/'review.jsonl',prior+rows)
(C/'README.md').write_text('''# 100-example SFT candidate dataset

Exactly 100 examples in stable order: pilot-001 through pilot-100. sft.jsonl contains only conversational prompt/completion fields. review.jsonl is line-aligned and contains IDs, one-sentence word-choice reasoning and audit metadata; never feed that metadata to normal SFT.

Use completion_only_loss=True and the Qwen3 native chat template with enable_thinking=False. The full v1.5 system profile is included in every prompt. Only the final assistant completion is a target; historical assistant turns are prompt context. Avoid silent truncation; verify sequence lengths and masks using the selected training runtime before training.

All examples are model-authored and self-reviewed, pending human review. This export is not proof of independent lexical validation or training success. No held-out data was opened. Earlier batches were retained as authored; this task checked new targets/history and export alignment. No new eligibility Q&A training task was added: reasoning stays outside the completion.
''')
(C/'manifest.json').write_text(json.dumps({'count':100,'ids':[r['id'] for r in prior+rows],'sources':[{'path':str(D/d/f),'sha256':hashfile(D/d/f)} for d,f in [('synthetic-pilot-v1','candidates.jsonl'),('synthetic-batch-002','review.jsonl'),('synthetic-batch-003','review.jsonl')]],'review_status':'model_reviewed_pending_human','sft_sha256':hashfile(C/'sft.jsonl'),'review_sha256':hashfile(C/'review.jsonl'),'tokenization_verified':False,'training_executed':False},indent=2)+'\n')
for r,export in zip(prior+rows,[json.loads(l) for l in (C/'sft.jsonl').read_text().splitlines()]):
 assert export['prompt'][1:]==r['context_messages']
 assert export['completion']==[{'role':'assistant','content':r['target_response']}]
(P/'draft.json').unlink()
print('Validated 40 new examples; 100 combined SFT rows aligned with review records; no repeated new targets/families; quotas and lexical coverage passed.')
