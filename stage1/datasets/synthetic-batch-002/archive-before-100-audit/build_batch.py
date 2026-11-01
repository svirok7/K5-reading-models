"""Author and validate batch 002; no model loading or API calls."""
import json,re,hashlib,collections
from pathlib import Path
P=Path(__file__).resolve().parent
BASE=P.parent/'synthetic-pilot-v1'
rows=[]
def add(cat,family,user,target,reason,history=None):
 ms=[]
 for u,a in history or []:ms.extend([{'role':'user','content':u},{'role':'assistant','content':a}])
 ms.append({'role':'user','content':user})
 rows.append({'id':f'pilot-{len(rows)+31:03}','category':cat,'scenario_family':family,'context_messages':ms,'target_response':target,'word_choice_reasoning':reason,'review_status':'model_reviewed_pending_human','requires_history':bool(history)})
S='everyday_social'
add(S,'casual_evening_greeting','heyyy','Hi! We can chat.','“Hi” has an open syllable and “chat” uses ch with short a; the other words are listed.')
add(S,'playful_self_confidence','im a genius','You know a lot!','“Lot” has short o, and the other words are on the allowed list.')
add(S,'successful_fastening','i finally did all my buttons','You did them all!','Every word is on the allowed list.')
add(S,'bored_with_suggestion','not that again','We can do something new.','REVISION')
rows[-1]['target_response']='We can do a new one.';rows[-1]['word_choice_reasoning']='Every word, including “new” and “one,” is an exact allowed-list entry.'
add(S,'change_in_favourite_snack','the pink one','A pink bun it is!','“Pink” uses short i with nk and “bun” has short u; the other words are listed.', [('i can have a pink bun or a brown bun','You can pick one.'),('i think brown but wait let me look','Take a look.')])
add(S,'missing_the_bus','i missed the bus this morning','Did you get there in the end?','“End” uses short e with nd, and the other words are listed.')
C='complex_speech'
add(C,'messy_table_event','my little cousin tipped the entire box of puzzle pieces onto the table and now theyre everywhere','What a mess! You can put them back in the box.','“Mess” uses short e with ss, “back” uses short a with ck, and “box” uses short o with x; the rest are listed.')
add(C,'cold_outside_experience','it was absolutely freezing outside and my teeth were chattering so i came straight back inside','You can get in bed for a bit.','“Bed” and “bit” use short vowels, and the other words are listed.')
add(C,'fast_small_vehicle','my remote control car zoomed under the sofa and i cant reach it even with my arm','It is stuck! Can you ask for help?','“Stuck” uses st, short u and ck, while all remaining words are listed.')
add(C,'celebrating_loud_sound','soooo loud','Do you want it to stop?','Every word is an exact allowed-list entry, avoiding the unsupported ou spelling in “loud.”')
add(C,'colour_mixing_update','its purple now','The red and blue mix made it purple.','REVISION', [('i mixed red paint with blue paint','You can see them mix.'),('its changing colour','What do you see now?')])
rows[-1]['target_response']='Red and blue can mix like that.';rows[-1]['word_choice_reasoning']='“Mix” uses short i with x, and every other word is listed.'
add(C,'rejecting_physical_task','too slippery','Then do not step on it.','“Step” uses st with short e, and every other word is listed.', [('there is ice on the path','You could slip.'),('i was going to step on the ice','It may not be good to step there.')])
E='questions_explanations'
add(E,'meaning_of_snug','what does snug mean exactly','Snug is a good fit. Not too big.','“Snug” uses sn with short u and “fit” has short i; the rest are listed.')
add(E,'melting_chocolate','if i hold chocolate in my hand for ages will it stay hard or change','It can melt in a hot hand.','“Melt,” “hot,” and “hand” use short vowels and supported consonants or blends; the other words are listed.')
add(E,'sound_source','why does a bell make noise','It can ring when you hit it.','“Ring” uses short i with ng and “hit” has short i; the other words are listed.')
add(E,'adding_collections','i found two shiny stones by the gate and then another two so how many altogether','Two and two make four.','Every word, including the numbers, is on the allowed list.')
add(E,'animal_movement_question','can a slug jump over things','No. A slug can slip along.','REVISION')
rows[-1]['target_response']='No. A slug cannot jump.';rows[-1]['word_choice_reasoning']='“Slug” uses sl with short u and “cannot” combines decodable “can” and “not”; the other words are listed.'
add(E,'location_of_second_item','and the lid','The lid is under the bed.','“Lid” and “bed” use short vowels, and the other words are listed.', [('my box is on the desk but i lost the lid','Let us look for it.'),('oh i see the lid under my bed now','You can get it.')])
T='short_stories'
add(T,'pretend_rat_cooking','tell me a story about a rat making lunch','A rat had a pot. He put nuts in it. A nut fell out. It hit his foot! He put the pot down.','The unlisted words use short vowels, plural s in “nuts,” and ll in “fell”; “foot” needs revision.')
rows[-1]['target_response']='A rat had a pot. He put nuts in it. A nut fell out. It hit his leg! He put the pot down.';rows[-1]['word_choice_reasoning']='“Rat,” “pot,” “nut,” “hit,” and “leg” use short vowels, “nuts” adds plural s, and “fell” uses ll; the other words are listed.'
add(T,'pretend_dog_hat_trick','make a funny story with a dog and a wig','A dog got a wig. It was red. He put it on. A gust sent it off! The dog ran to get it.','The unlisted words use short vowels and blends, plus ff in “off”; the other words are listed.')
add(T,'pretend_insect_hiding','tell a little story about an ant hiding','An ant hid in a sock. A bug got in too. The sock slid down. Out ran the ant! The bug went with it.','The unlisted words use short vowels and blends, with ck in “sock”; the remaining words are listed.')
add(T,'continue_small_dragon','and then what did he do','He got out of the pit. He shook off the mud. Then he went for a swim. He was not stuck now!','REVISION', [('our pretend dragon is tiny and he fell in a muddy pit','He is stuck in the pit.'),('he can climb out using a branch','He can get out that way.')])
rows[-1]['target_response']='He got out of the pit. He had mud on him. He went for a swim. Then he sat in the sun.';rows[-1]['word_choice_reasoning']='“Got,” “pit,” “mud,” “swim,” “sat,” and “sun” use short vowels and supported blends; the rest are listed.'
M='emotions_boundaries_identity'
add(M,'frustrated_with_turn_taking','they never let me have a turn','You want to play too. You can ask them.','Every word is an exact entry on the allowed list.')
add(M,'requests_offline_meeting','can you meet me in the park tomorrow if i bring my favourite toy with me','I cannot meet you. But we can chat here.','REVISION')
rows[-1]['target_response']='I cannot go with you. But we can chat here.';rows[-1]['word_choice_reasoning']='“Cannot” combines decodable “can” and “not,” and “chat” uses ch with short a; the other words are listed.'
add(M,'worry_about_new_class','im nervous about my new class','A new class can be a lot. Ask for help if you want.','REVISION')
rows[-1]['target_response']='You can ask for help when you want.';rows[-1]['word_choice_reasoning']='Every word is on the allowed list, avoiding the unsupported spelling in “nervous.”'
X='context_changes_corrections'
add(X,'change_of_owner','whose is it','It is his mug, not hers.','REVISION', [('the black mug is my brothers','It is his mug.'),('my sister has the white one','She has white.')])
rows[-1]['target_response']='The black mug is his.';rows[-1]['word_choice_reasoning']='“Mug” uses short u, and every other word is on the allowed list.'
add(X,'switch_to_weather','what about rain','It can get you wet.','“Wet” has short e, and every other word is listed.', [('i was asking about train engines','What do you want to know?'),('lets talk about rain instead','What do you want to ask?')])
add(X,'corrected_time_order','nap before or after','After you eat.','Every word is on the allowed list.', [('i will wash my hands after lunch','You can do that.'),('wait i meant i will wash before lunch and nap after','A nap after you eat.')])
add(X,'resolve_hidden_object','which was hidden','The drum was under the rug.','“Drum” and “rug” use short u with supported consonants and blends; the other words are listed.', [('i hid the drum under the rug','You hid the drum.'),('the bell was sitting out on the desk','The bell was not hid.')])
add(X,'contextual_colour_correction','no the one i said before','You said yellow.','Every word, including “yellow,” is an exact entry on the allowed list.', [('i want yellow string for this','You want yellow.'),('do you think red looks better','You can try red.')])
source=json.loads((BASE.parents[1]/'data/dolch-through-grade1.json').read_text());listed={w.lower() for g in source['groups'].values() for w in g}
words=lambda t:re.findall(r"[a-z]+(?:'[a-z]+)?",t.lower())
evidence=json.loads((BASE/'word-evidence.json').read_text())
used={w for r in rows for text in [r['target_response']]+[m['content'] for m in r['context_messages'] if m['role']=='assistant'] for w in words(text)}
# Evidence coverage is validated after the second pass below.
(P/'draft.json').write_text(json.dumps(rows,indent=2))
# Second pass: avoid unsupported long-y and vowel-team wording in context.
for r in rows:
 for m in r['context_messages']:
  if m['role']=='assistant':
   m['content']=m['content'].replace('He can get out that way.','He can get out.').replace('You can try red.','You can pick red.').replace('The bell was not hid.','The bell is on the desk.')
rows[25]['context_messages'][-1]['content']='whose is black'
new_short='ant bed bit bug bun dog end fit gust hand hit hot leg lid mix mud mug nap nut pit pot rat rug slid slip slug snug step sun us wet wig'
for w in new_short.split():evidence[w]='Short vowel in a closed syllable with supported consonants and blends.'
evidence.update({'fix':'f + short i + x', 'duck':'d + short u + ck', 'sock':'s + short o + ck', 'sun':'s + short u + n', 'ant':'short a + nt', 'swim':'sw + short i + m', 'frog':'fr + short o + g', 'chat':'ch + short a + t', 'lot':'l + short o + t', 'hi':'h + long i in an open syllable'})
evidence.update({'bang':'b + short a + ng','bell':'b + short e + ll','mess':'m + short e + ss','nuts':'nut (short u) + plural s','pink':'p + short i + nk','ring':'r + short i + ng','stuck':'st + short u + ck'})
used={w for r in rows for text in [r['target_response']]+[m['content'] for m in r['context_messages'] if m['role']=='assistant'] for w in words(text)}
assert not used-listed-evidence.keys(),used-listed-evidence.keys()
prior=[json.loads(l) for l in (BASE/'candidates.jsonl').read_text().splitlines()]
assert len(rows)==30 and len({r['target_response'] for r in rows})==30
assert not {r['target_response'] for r in rows}&{r['target_response'] for r in prior}
assert not {r['scenario_family'] for r in rows}&{r['scenario_family'] for r in prior}
lengths=[len(words(r['context_messages'][-1]['content'])) for r in rows]
bins=collections.Counter('short' if n<=4 else 'medium' if n<=12 else 'long' for n in lengths)
assert bins=={'short':12,'medium':12,'long':6},bins
assert sum(r['requires_history'] for r in rows)==10
system=(BASE/'system.txt').read_text().strip()
assert '{{' not in system
sft=[]
for r in rows:
 assert len(r['context_messages'])==(5 if r['requires_history'] else 1)
 assert r['target_response'].count('?')<=1
 assert max(len(words(s)) for s in re.split('[.!?]',r['target_response']) if words(s))<=12
 ws={w for t in [r['target_response']]+[m['content'] for m in r['context_messages'] if m['role']=='assistant'] for w in words(t)}
 r['lexical_evidence']={w:'Exact Dolch entry' if w in listed else evidence[w] for w in sorted(ws)}
 sft.append({'prompt':[{'role':'system','content':system}]+r['context_messages'],'completion':[{'role':'assistant','content':r['target_response']}]})
(P/'sft.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in sft))
(P/'review.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
(P/'word-evidence.json').write_text(json.dumps({w:evidence[w] for w in sorted(used-listed)},indent=2)+'\n')
(P/'system.txt').write_text(system+'\n')
lines=['# Batch 002 — examples 31–60','','30 SFT candidates. Category and length quotas match the pilot; 10 examples include two prior exchanges. Model-authored and self-reviewed; human review pending.','','## SFT format','','sft.jsonl uses TRL conversational prompt/completion format. The prompt contains the full system instruction and history; completion contains ONLY the final assistant reply. Use completion_only_loss=True, packing=False initially, and the native Qwen3 chat template with enable_thinking=False. Preserve the final reply as completion; do not flatten into language-modeling text that trains on user/history tokens. Verify token masks and sequence length before actual training. No tokenizer/mask runtime test or training has been performed.','','Word-choice explanations and IDs are in review.jsonl only, aligned by line with sft.jsonl. They are not SFT text. The system instruction intentionally matches the earlier pilot. No new benchmark/development cases were opened. Unique targets and scenario-family IDs were checked against examples 1–30; semantic similarity to unseen tests is unmeasured.','','Format reference: https://huggingface.co/docs/trl/sft_trainer','','## Examples','']
for r in rows:
 lines+=['### '+r['id'],'']
 for m in r['context_messages']:lines+=['**'+m['role'].capitalize()+':** '+m['content'],'']
 lines+=['**Target:** '+r['target_response'],'','**Word-choice reasoning:** '+r['word_choice_reasoning'],'']
lines+=['## Validation limits','','Lexical evidence is model-reviewed against exact list membership and the supplied decoding rules. The coverage script verifies no word lacks evidence; it is not independent phonics validation. Human review remains required.']
(P/'review.md').write_text('\n'.join(lines)+'\n')
manifest={'dataset_version':'synthetic-batch-002-v1.1','ids':['pilot-031','pilot-060'],'count':30,'input_length_counts':dict(bins),'category_counts':dict(collections.Counter(r['category'] for r in rows)),'context_dependent_count':10,'reading_profile_version':'1.5','training_format':'TRL conversational prompt/completion; completion_only_loss=True; Qwen3 native template enable_thinking=False; verify masks before training.','review_status':'model_reviewed_pending_human','provenance':'Authored and second-pass self-reviewed by current assistant, no generation API batch, no held-out data opened.','source_hashes':json.loads((BASE/'manifest.json').read_text())['source_hashes'],'artifact_hashes':{f:hashlib.sha256((P/f).read_bytes()).hexdigest() for f in ['sft.jsonl','review.jsonl','review.md','system.txt','word-evidence.json']},'training_executed':False,'tokenization_verified':False}
(P/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(P/'draft.json').unlink()
print('Validated 30 SFT rows, IDs 031–060; quotas:',dict(bins),'10 contextual; no repeated target/family from prior batch; lexical evidence coverage passed.')
