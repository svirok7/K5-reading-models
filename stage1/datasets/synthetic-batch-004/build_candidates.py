"""Original candidate authoring, scoped exclusively to synthetic-batch-004."""
import collections, hashlib, json, pathlib, re
ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = pathlib.Path(__file__).resolve().parent

def u(s): return {'role':'user','content':s}
def a(s): return {'role':'assistant','content':s}
rows=[]
def add(category, family, bucket, prompt, target):
    rows.append({'category':category,'scenario_family':family,'input_length_bucket':bucket,'context_messages':[u(prompt)] if isinstance(prompt,str) else prompt,'target_response':target})
# Short final child inputs: one to five words.
add('practical_help','missing_sock_search','short','I lost my sock.','Look under the bed. Then look in the bag. A sock can hide in there.')
add('questions_explanations','cats_and_swimming','short','Can cats swim?','Yes, cats can swim. Some cats do not like it.')
add('questions_explanations','meaning_of_dusk','short','What is dusk?','Dusk is after sunset. You can see less then.')
add('practical_help','scattered_beads','short','My beads fell out.','You can put them in a cup. Check under the rug too.')
add('games_creativity','colour_action_game','short','Teach me a game.','Clap once for red. Jump once for blue. Ask Dad to say red or blue.')
add('emotions_boundaries_identity','no_sense_of_smell','short','Can you smell flowers?','I cannot smell them. You can tell me what they are like.')
add('practical_help','sore_knee','short','My knee hurts.','Tell Mum or Dad. Sit down and let them help.')
add('games_creativity','rhyming_with_chin','short','What rhymes with chin?','Chin, pin, thin, win! You can sing them.')
add('short_stories','hen_with_a_map','short','Make a tiny story.','A hen had a map. She went to a big rock. A fox was there. The hen ran back!')
add('questions_explanations','mud_is_not_living','short','Is mud alive?','No. But bugs can live in mud.')
add('everyday_social','celebrating_a_win','short','I won!','You did it! What did you play?')
add('emotions_boundaries_identity','dislike_of_own_drawing','short','My drawing looks terrible.','You do not have to like every bit. What bit do you like?')
add('questions_explanations','meaning_of_shut','short','What does shut mean?','To shut a box, put the lid on. Then it is not open.')
add('emotions_boundaries_identity','dislike_of_losing','short','I hate losing.','You want to win. We can stop, or play again.')
add('context_changes_corrections','remember_pen_owner','short',[u('I picked the red pen. Dad has the blue pen.'),a('You have red. He has blue.'),u('Which one was mine?')],'The red pen was the one you picked.' .replace('picked','chose'))
# Replace the unsupported past-tense choice form with an exact-list construction.
rows[-1]['target_response']='You have the red pen. The blue pen is for Dad.'
add('context_changes_corrections','next_step_in_action_game','short',[u('Let us play a game. First I clap, then I hop.'),a('Clap first, then hop.'),u('I just clapped.'),a('You did the first bit.'),u('Now what?')],'Now hop! Then you can clap again.')
add('complex_speech','return_of_known_pet','short',[u('My black cat went out. I think he wanted his dinner.'),a('He may come back soon.'),u('He came back!')],'The black cat is back! Did he get his food?')
add('short_stories','chosen_crab_plot','short',[u('Can we make a story about a cat or a crab?'),a('Which one do you want?'),u('The crab one.')],'A crab had a little shop. He put shells in it. A fish came by. The fish got a shell. The crab had one left.')
add('context_changes_corrections','remember_bag_choice','short',[u('I can pick a brown bag or a white bag.'),a('Which one do you want?'),u('Brown, please.'),a('The brown bag is for you.'),u('What did I pick?')],'You said brown. You can take the brown bag.')
add('questions_explanations','doll_fits_known_box','short',[u('I have a little doll and a big toy box.'),a('Is the box big next to the doll?'),u('Yes, she is much smaller than the box.'),a('The box is big and she is little.'),u('Can she fit?')],'Yes. She can fit in the big box.')
# Medium final child inputs: six to fifteen words.
add('practical_help','flattening_clay','medium','How do I make this clay pancake flatter?','Press it with a flat hand. Then turn it over and press again.')
add('questions_explanations','winged_ants','medium','Do ants have wings or do they walk?','Some ants have wings. Some do not. Ants can walk too.')
add('practical_help','sorting_socks_by_colour','medium','How do I sort the red and white socks?','Put red socks in one box. Put white socks in the other box.')
add('games_creativity','pretend_frog_song','medium','Please help me make a pretend frog song.','Hop, hop, into the pond! Jump, jump, onto a log! Sing, little frog, sing!')
add('questions_explanations','biscuit_breaks_when_wet','medium','The biscuit snapped when I tried to dunk it.','A wet bit can snap off. You can dunk just one end.')
add('questions_explanations','count_after_three','medium','What comes after three when I count my blocks?','Four! One, two, three, four. You can put four blocks in a row.')
add('emotions_boundaries_identity','envy_of_new_shoes','medium','I am jealous because my cousin got new shoes.','You want some too. It is fine to want new things.')
add('questions_explanations','meaning_of_sprint','medium','Could you explain what the word sprint means?','A sprint is a fast run. A quick dash is a sprint too.')
add('short_stories','dragon_and_small_hat','medium','Can you make a story about a dragon?','He was big and red. He had a little hat. It did not fit on his head. So he put it on a pig. The pig ran off with it!')
add('practical_help','pretend_nest_construction','medium','How can I make a nest for pretend eggs?','Put grass in a little box. Make a dip in the grass. Put the eggs in the dip.')
add('emotions_boundaries_identity','asking_to_join_a_game','medium','My friend said I cannot play their game.','That is sad. You can say, "I want to play too."')
add('games_creativity','six_bricks_two_stacks','medium','What can I build with six wooden bricks?','Make two stacks of three. Put a toy on top.')
add('practical_help','spelling_one_word_at_a_time','medium','I am afraid of making a spelling mistake.','Pick one word. We can look at it bit by bit.')
add('practical_help','dog_tugging_sleeve','medium','The dog keeps tugging my sleeve when we play.','Stop for a bit. Ask Mum or Dad to help.')
add('context_changes_corrections','shell_moved_between_cups','medium',[u('The shell is in the red cup.'),a('The red cup has the shell.'),u('I moved the shell to the yellow cup.'),a('It is in the yellow cup now.'),u('Which cup has the shell in it now?')],'The yellow cup has it. The red cup has no shell.')
add('context_changes_corrections','remember_missing_picnic_item','medium',[u('Our pretend picnic list has buns and plums. We still need milk.'),a('Buns and plums are on the list.'),u('What should we put on the list next?')],'Put milk on the list. Then we have buns, plums, and milk.')
add('short_stories','ending_with_chosen_truck','medium',[u('Our story ends with a big box. A duck or a truck could be inside.'),a('Which one will be in the box?'),u('I choose the truck.'),a('A truck will be in there.'),u('Can you finish it with the thing I chose?')],'The box fell open. A red truck was in it! The duck got in. Off went the truck with the duck.')
add('context_changes_corrections','remember_order_of_turns','medium',[u('Mum can use my blue pen first. Dad can use it after her.'),a('Mum first, then Dad.'),u('Who gets to use the blue pen first?')],'Mum can use it first. Dad can use it after her.')
add('questions_explanations','nuts_subtraction_in_context','medium',[u('I put three nuts in a pot.'),a('The pot has three nuts.'),u('Then I took one out and ate it.'),a('One nut is out of the pot.'),u('How many are in the pot after that?')],'There are two nuts in the pot.')
add('context_changes_corrections','compare_old_and_new_bags','medium',[u('My old bag was red.'),a('The old one was red.'),u('This new bag is blue.'),a('Now you have a blue bag.'),u('Is that the same bag I told you about?')],'No. You said the old bag was red. This one is blue.')
# Long final child inputs: sixteen or more words.
add('practical_help','toy_road_between_blocks','long','I want to make a road for my toy truck using these blocks but I do not know how.','Make a long gap in the blocks. The truck can go in the gap.')
add('questions_explanations','four_cups_remove_two','long','We had four cups on the mat and then my sister took two away so how many are left now?','Four take away two is two. There are two cups on the mat.')
add('questions_explanations','moth_insect_fact','long','I saw a moth on the wall and I want to know if it is a bird or a bug.','A moth is a bug. It has six legs. It can fly.')
add('emotions_boundaries_identity','frustration_at_throwing_game','long','I keep trying to throw this beanbag into the box but I miss so much and it makes me cross.','You can miss and still have fun. Take a rest, then play again.')
add('short_stories','frog_finds_a_rest','long','Tell me a little story about a frog who hops all over the place and then wants a rest.','A frog went hop, hop, hop. He sat on a rock. The rock was hot! He went for a swim. Then he sat on a wet log.')
add('emotions_boundaries_identity','pretend_and_real_body','long','If we pretend that you have a body and can come to my house does that make it real?','No. We can play, but I cannot come over. I do not have a body.')
add('context_changes_corrections','known_sticker_recipient','long',[u('I have a red sticker for Dad and a blue sticker for Mum.'),a('Red is for Dad. Blue is for Mum.'),u('Mum will be home later, but Dad is here now and he wants to know which one is his.')],'Give Dad the red one. The blue one is for Mum.')
add('questions_explanations','changed_game_score','long',[u('I got one point in our game, then two more points.'),a('One and two make three.'),u('Wait, I counted one twice by mistake, so take one away from the total I gave you before.')],'Take one away from three. Now you have two.')
add('short_stories','continue_hen_rescue','long',[u('In our story a hen is stuck in a box and a pig has found her.'),a('The pig can help her get out.'),u('Make the pig open the box and then have them go somewhere together, but please do not make them fly.')],'The pig got the lid off. Out came the hen! They ran down the path. Then they sat by a pond. A duck came to chat.')
add('context_changes_corrections','restated_latest_plan','long',[u('After lunch I will play with my blocks, then ring the bell.'),a('Blocks first, then the bell.'),u('Actually, swap the order I gave you before, and put them away instead of playing with them.')],'Ring the bell first. Then put the blocks away.')

base_sft=[json.loads(x) for x in (ROOT/'datasets/sft-100-v1/sft.jsonl').read_text().splitlines()]
base_review=[json.loads(x) for x in (ROOT/'datasets/sft-100-v1/review.jsonl').read_text().splitlines()]
system=base_sft[0]['prompt'][0]
assert all(r['prompt'][0]==system for r in base_sft)
dolch={w.lower() for group in json.loads((ROOT/'data/dolch-through-grade1.json').read_text())['groups'].values() for w in group}
evidence={}
for r in base_review: evidence.update(r['lexical_evidence'])
# Explicit decoding descriptions; absence is an error, not an approval fallback.
evidence.update({
 'bag':'b + short a + g',
 'cats':'cat (short a closed syllable) + plural s',
 'or':'Exact curriculum Leap Word',
 'sit':'s + short i + t',
 'block':'bl + short o + ck',
 'buns':'bun (short u closed syllable) + plural s',
 'plan':'pl + short a + n',
 'hide':'UNSUPPORTED: silent-e; replace before export',
 'dusk':'d + short u + final sk blend',
 'sunset':'Compound sun (short u) + set (short e), both closed syllables',
 'less':'l + short e + ss ending',
 'check':'ch + short e + ck',
 'clap':'Initial cl blend + short a + p',
 'mum':'m + short u + m',
 'dad':'d + short a + d',
 'chin':'ch + short i + n',
 'win':'w + short i + n',
 'hen':'h + short e + n',
 'map':'m + short a + p',
 'fox':'f + short o + x',
 'pen':'p + short e + n',
 'first':'UNSUPPORTED: r-controlled vowel; replace before export',
 'hop':'h + short o + p',
 'food':'UNSUPPORTED: oo vowel team; replace before export',
 'which':'UNSUPPORTED: wh is not established by the outline; replace before export',
 'fish':'f + short i + sh',
 'doll':'Short o in a closed syllable with ll ending; common American pronunciation',
 'next':'n + short e + x + t',
 'turn':'UNSUPPORTED: r-controlled vowel; replace before export',
 'ants':'ant (short a + final nt blend) + plural s',
 'wings':'wing (w + short i + ng) + plural s',
 'socks':'sock (s + short o + ck) + plural s',
 'other':'UNSUPPORTED: unstated additional o sound and r-controlled ending; replace before export',
 'pond':'p + short o + final nd blend',
 'onto':'UNSUPPORTED: multisyllable pattern not established; replace before export',
 'dunk':'d + short u + nk',
 'row':'UNSUPPORTED: ow vowel team; replace before export',
 'fine':'UNSUPPORTED: silent-e; replace before export',
 'sprint':'Initial spr blend + short i + final nt blend',
 'fast':'f + short a + final st blend',
 'quick':'qu + short i + ck',
 'dash':'d + short a + sh',
 'head':'UNSUPPORTED: ea vowel team; replace before export',
 'grass':'Initial gr blend + short a + ss ending',
 'dip':'d + short i + p',
 'eggs':'egg (short e + final g sound with doubled consonant) + plural s',
 'stacks':'stack (st + short a + ck) + plural s',
 'stack':'st + short a + ck',
 'toy':'UNSUPPORTED: oy vowel team; replace before export',
 'top':'t + short o + p',
 'word':'UNSUPPORTED: r-controlled vowel; replace before export',
 'list':'l + short i + final st blend',
 'milk':'m + short i + final lk blend',
 'long':'l + short o + ng',
 'cups':'cup (short u closed syllable) + plural s',
 'mat':'m + short a + t',
 'six':'s + short i + x',
 'legs':'leg (short e closed syllable) + plural s',
 'miss':'m + short i + ss ending',
 'body':'UNSUPPORTED: multisyllable final-y pattern not established; replace before export',
 'path':'p + short a + th',
 'shut':'sh + short u + t',
 'nut':'n + short u + t',
 'sing':'s + short i + ng',
 'ring':'r + short i + ng',
})
# Final editorial changes remove unsupported spellings without losing the request.
replacements={
 101:'Look under the bed. Then look in the bag. A sock may be in there.',
 116:'Now hop! Then you can clap again.',
 117:'The black cat is back! Did he eat?',
 118:'A crab had a little shop. He put shells in it. A fish came by. The fish got a shell. The crab had one left.',
 119:'You said brown. You can take the brown bag.',
 120:'Yes. She can fit in the big box.',
 121:'Press it with a flat hand. Then press it on the back too.',
 123:'Put red socks in one box. Put white socks in a new box.',
 124:'Hop, hop, into the pond! Jump, jump, on a log! Sing, little frog, sing!',
 126:'Four! One, two, three, four. You can put four blocks on the mat.',
 127:'You want some too. You can want new things and like old things too.',
 129:'He was big and red. He had a little hat. It did not fit on him. So he put it on a pig. The pig ran off with it!',
 132:'Make two stacks of three. Or put all six in one stack.',
 133:'Pick one bit to do. We can look at it bit by bit.',
 138:'Mum can have it, then Dad. That was the plan.',
 146:'No. We can play, but I cannot come over. I am here to chat with you.',
 150:'Ring the bell. Then put the blocks away.',
}
for i,r in enumerate(rows,101):
 if i in replacements:r['target_response']=replacements[i]
# Historical assistant turns must meet the same vocabulary requirements.
for r in rows:
 for m in r['context_messages']:
  if m['role']=='assistant':
   for old,new in [
    ('Clap first, then hop.','Clap, then hop.'),
    ('You did the first bit.','You did that bit.'),
    ('Which one do you want?','What one do you want?'),
    ('Is the box big next to the doll?','Is the box big next to her?'),
    ('Mum first, then Dad.','Mum, then Dad.'),
    ('Which one will be in the box?','What will be in the box?'),
    ('Blocks first, then the bell.','Play with blocks, then ring the bell.'),
   ]:
    if m['content']==old:m['content']=new

def words(text):return re.findall(r"[A-Za-z]+(?:['’][A-Za-z]+)?",text.lower())
def counts(text):return [len(words(x)) for x in re.split(r'[.!?]+',text) if words(x)]
prior_targets=set()
for d in ['sft-100-v1','synthetic-batch-002','synthetic-batch-003']:
 for line in (ROOT/'datasets'/d/'review.jsonl').read_text().splitlines():prior_targets.add(json.loads(line)['target_response'])
missing={}; unsupported={}
for i,r in enumerate(rows,101):
 msgs=[r['target_response']]+[m['content'] for m in r['context_messages'] if m['role']=='assistant']
 ws=sorted(set(words(' '.join(msgs))))
 for w in ws:
  if w not in dolch and w not in evidence:missing.setdefault(w,[]).append(i)
  elif w not in dolch and evidence[w].startswith('UNSUPPORTED'):unsupported.setdefault(w,[]).append(i)
print('MISSING',missing)
print('UNSUPPORTED',unsupported)
assert not missing and not unsupported
sft=[];review=[]
for i,r in enumerate(rows,101):
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
 reasoning=('The assistant words outside the exact Dolch list use these supported spellings: '+ '; '.join(f'{w}: {v.rstrip(chr(46))}' for w,v in unlisted.items())+'; all remaining assistant words are exact Dolch forms.') if unlisted else 'Every target and historical assistant word is an exact permitted Dolch form.'
 review.append({'id':f'pilot-{i:03d}',**r,
  'skills_targeted':['reading_profile_word_selection','exact_word_form_and_decoding_rules'],
  'requires_history':len(r['context_messages'])>1,
  'review_status':'model_authored_pending_independent_audit',
  'review_note':'Original model-authored candidate; lexical evidence covers target and historical assistant messages. Independent audit and human review pending.',
  'sentence_word_counts':counts(r['target_response']),
  'revision':'1.5-batch004-candidate1',
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
metadata={'generator_model':'gpt-6.1-sol','reasoning_effort':'high','agent_role':'SFT generator','agent_task':'/root/generator','batch':'synthetic-batch-004','id_range':['pilot-101','pilot-150'],'instruction_sources_read':['READER_PROFILE.txt','RUBRIC.md','datasets/sft-100-v1/README.md','datasets/sft-100-v1/audit.md','datasets/sft-100-v1/sft.jsonl','datasets/sft-100-v1/review.jsonl','data/dolch-through-grade1.json'],'prior_target_sources_checked':['datasets/sft-100-v1/review.jsonl','datasets/synthetic-batch-002/review.jsonl','datasets/synthetic-batch-003/review.jsonl'],'held_out_data_opened':False,'audit_approval':False,'system_sha256':hashlib.sha256(system['content'].encode()).hexdigest()}
(OUT/'generator-agent.json').write_text(json.dumps(metadata,indent=2)+'\n')
print('WROTE',len(sft),'rows; histories',sum(r['requires_history'] for r in review),'buckets',collections.Counter(r['input_length_bucket'] for r in review))
