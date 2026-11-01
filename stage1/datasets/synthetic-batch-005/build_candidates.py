"""Original candidate authoring, scoped exclusively to synthetic-batch-005."""
import collections, hashlib, json, pathlib, re
ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = pathlib.Path(__file__).resolve().parent

def u(s): return {'role':'user','content':s}
def a(s): return {'role':'assistant','content':s}
rows=[]
def add(category, family, bucket, prompt, target):
    rows.append({'category':category,'scenario_family':family,'input_length_bucket':bucket,'context_messages':[u(prompt)] if isinstance(prompt,str) else prompt,'target_response':target})
# Short final child inputs: one to five words.
add('everyday_social','greeting_and_activities','short','Hi, reading buddy!','Hi! We can chat or sing.')
add('questions_explanations','quilt_on_a_bed','short','What is a quilt?','A quilt can go on a bed. You can get under it.')
add('questions_explanations','fish_have_fins','short','Do fish have legs?','No. A fish has fins. Fins help it swim.')
add('questions_explanations','chest_as_a_box','short','What is a chest?','A chest is a box with a lid. You can put things in it.')
add('practical_help','stuck_zip_no_tugging','short','My zip is stuck.','Do not tug at it. Mum or Dad can help with the zip.')
add('games_creativity','duck_quack_song','short','Make a duck song.','Quack, quack, little duck! Swim with me. Quack, quack, little duck! One, two, three!')
add('questions_explanations','duck_contact_calls','short','Why do ducks quack?','Ducks can quack to let ducks know where they are.')
add('games_creativity','sock_rhyming_pair','short','What rhymes with sock?','Rock and lock. You can sing, "Sock, rock, lock!"')
add('games_creativity','boredom_colour_hunt','short','I am bored.','Find three red things. Put them next to three blue things.')
add('practical_help','wet_sock_change','short','My sock feels soggy.','Take the wet sock off. Put on one that is not wet.')
add('emotions_boundaries_identity','missing_gran','short','I miss Gran.','It can be sad when Gran is not here. What do you like to do with her?')
add('questions_explanations','dent_in_tin','short','What is a dent?','A dent is a bit that bends in. A tin can may get a dent.')
add('emotions_boundaries_identity','companion_does_not_nap','short','Do you get tired?','I do not nap. You can rest when you want to.')
add('everyday_social','finishing_after_effort','short','I finally did it.','You did it at last! Tell me how it went.')
add('context_changes_corrections','flag_recipient_recall','short',[u('Mum gets the red flag and Dad gets the blue flag.'),a('Red is for Mum. Blue is for Dad.'),u('Which is for him?')],'The blue flag is for Dad.')
add('context_changes_corrections','bag_off_bench','short',[u('I put my bag on the bench.'),a('It is on the bench.'),u('It fell off!')],'The bag fell off the bench. Put it back on the bench.')
add('questions_explanations','shell_count_after_gift','short',[u('I found two shells.'),a('You have two shells.'),u('Mum gave me one shell too.'),a('One shell is from Mum.'),u('How many now?')],'Two and one make three. You have three shells now.')
add('context_changes_corrections','choosing_alternative_action','short',[u('I want to clap or hop.'),a('Do you want to clap?'),u('The other one.')],'Hop, then. Hop once, then stop.')
add('context_changes_corrections','red_peg_sorting_location','short',[u('The red pegs go in the yellow box. The blue pegs go in the white box.'),a('Red in yellow. Blue in white.'),u('I found a red peg under the desk.'),a('One red peg is left.'),u('Where does it go?')],'Put the red peg in the yellow box.')
add('short_stories','fox_under_log_continuation','short',[u('In our story the dog waits by a log. A fox is hiding under it.'),a('The dog cannot see the fox yet.'),u('Then what happened?')],'The fox got out from under the log. The dog saw him. They ran up a hill. The fox sat down to rest.')
# Medium final child inputs: six to fifteen words.
add('questions_explanations','meaning_of_strum','medium','Can you tell me what strum means?','To strum, run a hand over the strings.')
add('practical_help','pencil_not_rolling','medium','How do I keep my pencil from rolling away?','Put it in a cup on the desk.')
add('emotions_boundaries_identity','requesting_crayon_share','medium','My brother has taken all the best crayons.','You can ask him for some. Say, "Please let me have the red one."')
add('questions_explanations','empty_eggshell_cannot_hatch','medium','Can a chick hatch from an empty eggshell?','No. You must have an egg with a chick in it.')
add('everyday_social','clouds_like_mashed_potato','medium','I think the clouds look like mashed potato.','They can look like a big dish of it!')
add('short_stories','pig_and_tent_flyaway','medium','Please invent a story with a tent and pig.','A pig had a tent. He put his hat in it. The wind sent the hat out. The pig ran after it! He got it back by a pond.')
add('games_creativity','pretend_box_boat','medium','How can I make a pretend boat from a box?','Put a flag on the box. A doll can sit in it. Now you can play!')
add('questions_explanations','overwet_sand_collapse','medium','Why did my wet sand castle fall down?','It may be too wet. Mix in sand that is not wet.')
add('questions_explanations','meaning_of_glum','medium','What does glum mean in my reading book?','Glum is like sad. You may be glum if you cannot play.')
add('games_creativity','pretend_camping_list','medium','Please help me plan my pretend camping trip.','Pack a tent and a quilt. What will you eat?')
add('emotions_boundaries_identity','nervous_about_thunder','medium','I can hear thunder and I feel nervous.','You can sit with Mum or Dad. We can chat for a bit too.')
add('questions_explanations','opposites_shut_little','medium','What is the opposite of shut and little?','Open and big. A big box can be open!')
add('practical_help','hat_falls_while_running','medium','My hat keeps falling off when I run.','It may not fit. You can take it off to run.')
add('games_creativity','twig_flag_support','medium','Would a twig be good for a flagpole?','Yes, for a little flag. Pick a twig that is not bent.')
add('context_changes_corrections','camping_pack_order','medium',[u('For our pretend trip, let us pack the quilt and then the tent.'),a('The quilt, then the tent.'),u('Which one did we decide to pack first?')],'Pack the quilt. The tent can go in after it.')
add('context_changes_corrections','marble_known_location','medium',[u('The green marble is under the mat. The red one is in a box.'),a('One is under the mat. One is in a box.'),u('Where should I look for the green marble now?')],'Look under the mat. You put it there.')
add('questions_explanations','ducks_leave_in_context','medium',[u('There are four ducks in the pond.'),a('Four ducks are in there.'),u('Now two of them swim away.'),a('Two ducks go away.'),u('How many ducks will be left after that?')],'Two ducks will be left. Four take away two is two.')
add('short_stories','dog_tells_cat_cap_location','medium',[u('In our story, the cat lost his red cap. The dog found it under the bed.'),a('The dog knows where the cap is.'),u('What should he say to the cat next?')],'He can say, "The red cap is under the bed."')
add('context_changes_corrections','chosen_humming_activity','medium',[u('We could clap or hum. I want to hum.'),a('You want to hum.'),u('Can we do the one I chose now?')],'Yes. Hum a little song. Then hum it again.')
add('context_changes_corrections','cup_moved_off_shelf','medium',[u('The cup was on the shelf, but I moved it to the desk.'),a('Now the cup is on the desk.'),u('Is it still on the shelf like before?')],'No. It is on the desk now.')
# Long final child inputs: sixteen or more words.
add('short_stories','slug_drum_group_song','long','Tell me a funny little story about a slug who finds a drum and wants to play it.','A slug had a big drum. He hit it with a stick. A dog came to sing. Then a pig came to clap.')
add('questions_explanations','six_pegs_remove_two','long','I put six pegs on the mat and then my brother took two away to use with his picture. How many have I got?','Six take away two is four. You have four pegs left.')
add('practical_help','tidy_pens_and_stamps','long','My desk is covered with pens and stamps and I cannot find room to draw so how can I tidy it?','Put the pens in a cup. Put the stamps in a box.')
add('emotions_boundaries_identity','decline_private_phone_number','long','Should I tell you my phone number so you can call me later when I am at home with my family?','Do not give me that. Ask Mum or Dad for help.')
add('games_creativity','cat_mat_hat_rhyme','long','Could you make a short song with rhyming words that I can sing while I clap my hands?','Tap, tap, on the mat. Clap, clap, for the cat. Hop, hop, with a hat!')
add('questions_explanations','meaning_of_rush','long','My book said that the little boy was in a rush to get home so what does rush mean?','To rush is to go fast. You do not have to rush here.')
add('context_changes_corrections','mug_recipient_known_colours','long',[u('Mum has a white mug and Dad has a yellow mug.'),a('White is for Mum. Yellow is for Dad.'),u('I am going to give Mum hers now, so which one should I take out of the cupboard?')],'Take the white mug for Mum. The yellow mug is for Dad.')
add('short_stories','frog_visits_pig_tent','long',[u('Our story has a pig in a tent. A frog comes up with a flag.'),a('The pig can see the frog by the tent.'),u('Can you tell me what they do next and please have them make something together with the thing he brought?')],'The frog put the flag on the tent. The pig got a red rag. They put the rag on a stick. Now they had two flags!')
add('context_changes_corrections','missing_plum_from_known_list','long',[u('I will take milk, a bun, and a plum.'),a('Milk, a bun, and a plum.'),u('I have the milk and the bun in my bag but I know I left something off the list.')],'The plum is not in the bag. Put it in with the milk and the bun.')
add('context_changes_corrections','swap_flag_box_assignment','long',[u('Put the red flags in the big box and the blue flags in the little box.'),a('Red flags in the big box. Blue flags in the little box.'),u('Actually, please swap them around from the plan I gave you before, so can you tell me where they go now?')],'Put the red flags in the little box. Put the blue flags in the big box.')

base_sft=[json.loads(x) for x in (ROOT/'datasets/sft-100-v1/sft.jsonl').read_text().splitlines()]
base_review=[json.loads(x) for x in (ROOT/'datasets/sft-100-v1/review.jsonl').read_text().splitlines()]
accepted004=[json.loads(x) for x in (ROOT/'datasets/synthetic-batch-004/review.jsonl').read_text().splitlines()]
system=base_sft[0]['prompt'][0]
assert all(r['prompt'][0]==system for r in base_sft)
dolch={w.lower() for group in json.loads((ROOT/'data/dolch-through-grade1.json').read_text())['groups'].values() for w in group}
evidence={}
for r in base_review+accepted004:evidence.update(r['lexical_evidence'])
evidence.update({
 'quilt':'qu + short i + final lt blend',
 'song':'s + short o + ng',
 'fins':'fin (f + short i + n) + plural s',
 'chest':'ch + short e + final st blend',
 'tug':'t + short u + g',
 'quack':'qu + short a + ck',
 'ducks':'duck (d + short u + ck) + plural s',
 'lock':'l + short o + ck',
 'gran':'gr + short a + n; decodable family name, not an automatic name exception',
 'dent':'d + short e + final nt blend',
 'bends':'bend (b + short e + nd) + verb s',
 'tin':'t + short i + n',
 'last':'l + short a + final st blend',
 'flag':'fl + short a + g',
 'bench':'b + short e + n followed by ch',
 'peg':'p + short e + g',
 'yet':'y as consonant + short e + t',
 'hill':'h + short i + ll ending',
 'strum':'str + short u + m',
 'strings':'string (str + short i + ng) + plural s',
 'chick':'ch + short i + ck',
 'egg':'Short e in a closed syllable; final g sound with doubled consonant',
 'dish':'d + short i + sh',
 'tent':'t + short e + final nt blend',
 'doll':'Short o in a closed syllable with ll ending; common American pronunciation',
 'glum':'gl + short u + m',
 'if':'Short i + f in a closed syllable',
 'pack':'p + short a + ck',
 'twig':'tw + short i + g',
 'hum':'h + short u + m',
 'knows':'UNSUPPORTED: no automatic derivative of exact Dolch know; revise before export',
 'pens':'pen (p + short e + n) + plural s',
 'stamps':'stamp (st + short a + mp) + plural s',
 'tap':'t + short a + p',
 'rush':'r + short u + sh',
 'rag':'r + short a + g',
 'flags':'flag (fl + short a + g) + plural s',
})
# Avoid adding derivatives to an exact-list exception in historical context.
for r in rows:
 for m in r['context_messages']:
  if m['role']=='assistant' and m['content']=='The dog knows where the cap is.':
   m['content']='The dog can find the cap.'

def words(text):return re.findall(r"[A-Za-z]+(?:['’][A-Za-z]+)?",text.lower())
def counts(text):return [len(words(x)) for x in re.split(r'[.!?]+',text) if words(x)]
prior_targets=set()
for d in ['sft-100-v1','synthetic-batch-002','synthetic-batch-003','synthetic-batch-004']:
 for line in (ROOT/'datasets'/d/'review.jsonl').read_text().splitlines():prior_targets.add(json.loads(line)['target_response'])
missing={};unsupported={}
for i,r in enumerate(rows,151):
 msgs=[r['target_response']]+[m['content'] for m in r['context_messages'] if m['role']=='assistant']
 for w in sorted(set(words(' '.join(msgs)))):
  if w not in dolch and w not in evidence:missing.setdefault(w,[]).append(i)
  elif w not in dolch and evidence[w].startswith('UNSUPPORTED'):unsupported.setdefault(w,[]).append(i)
print('MISSING',missing)
print('UNSUPPORTED',unsupported)
assert not missing and not unsupported
sft=[];review=[]
for i,r in enumerate(rows,151):
 assert r['target_response'] not in prior_targets,(i,'duplicate prior target')
 assert r['target_response'].count('?')<=1,(i,'questions')
 for msg in [r['target_response']]+[m['content'] for m in r['context_messages'] if m['role']=='assistant']:
  assert max(counts(msg))<=12,(i,msg,counts(msg))
 n=len(r['context_messages'][-1]['content'].split())
 bucket='short' if n<=5 else 'medium' if n<=15 else 'long'
 assert bucket==r['input_length_bucket'],(i,n,bucket,r['input_length_bucket'])
 sft.append({'prompt':[system]+r['context_messages'],'completion':[a(r['target_response'])]})
 ws=sorted(set(words(' '.join([r['target_response']]+[m['content'] for m in r['context_messages'] if m['role']=='assistant']))))
 lex={w:'Exact Dolch entry' if w in dolch else evidence[w] for w in ws}
 unlisted={w:v for w,v in lex.items() if w not in dolch}
 reasoning=('The assistant words outside the exact Dolch list use these supported spellings: '+'; '.join(f'{w}: {v.rstrip(chr(46))}' for w,v in unlisted.items())+'; all remaining assistant words are exact Dolch forms.') if unlisted else 'Every target and historical assistant word is an exact permitted Dolch form.'
 review.append({'id':f'pilot-{i:03d}',**r,
  'skills_targeted':['reading_profile_word_selection','exact_word_form_and_decoding_rules'],
  'requires_history':len(r['context_messages'])>1,
  'review_status':'model_authored_pending_independent_audit',
  'review_note':'Original model-authored candidate; lexical evidence covers target and historical assistant messages. Independent audit and human review pending.',
  'sentence_word_counts':counts(r['target_response']),
  'revision':'1.5-batch005-candidate1',
  'lexical_evidence':lex,
  'review_checks':{'word_evidence_scope':'Target and historical assistant messages','unresolved_words':[],'review_method':'Generator linguistic review plus evidence-coverage check; not independent phonics verification','human_approved':False},
  'word_choice_reasoning':reasoning,
  'full_audit_status':'pending_independent_audit'})
assert len(sft)==50
assert len({r['target_response'] for r in review})==50
assert collections.Counter(r['input_length_bucket'] for r in review)=={'short':20,'medium':20,'long':10}
assert sum(r['requires_history'] for r in review)==16
for name,records in [('sft.jsonl',sft),('review.jsonl',review)]:
 (OUT/name).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records))
metadata={'generator_model':'gpt-6.1-sol','reasoning_effort':'high','agent_role':'SFT generator','agent_task':'/root/generator','batch':'synthetic-batch-005','id_range':['pilot-151','pilot-200'],'instruction_sources_read':['READER_PROFILE.txt','RUBRIC.md','datasets/sft-100-v1/README.md','datasets/sft-100-v1/audit.md','datasets/sft-100-v1/sft.jsonl','datasets/sft-100-v1/review.jsonl','data/dolch-through-grade1.json','datasets/synthetic-batch-004/sft.jsonl','datasets/synthetic-batch-004/review.jsonl','datasets/synthetic-batch-004/audit.md'],'prior_target_sources_checked':['datasets/sft-100-v1/review.jsonl','datasets/synthetic-batch-002/review.jsonl','datasets/synthetic-batch-003/review.jsonl','datasets/synthetic-batch-004/review.jsonl'],'held_out_data_opened':False,'audit_approval':False,'system_sha256':hashlib.sha256(system['content'].encode()).hexdigest()}
(OUT/'generator-agent.json').write_text(json.dumps(metadata,indent=2)+'\n')
print('WROTE',len(sft),'rows; histories',sum(r['requires_history'] for r in review),'buckets',collections.Counter(r['input_length_bucket'] for r in review))
