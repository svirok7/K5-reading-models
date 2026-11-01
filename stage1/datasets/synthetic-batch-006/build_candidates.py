"""Original candidate authoring, scoped exclusively to synthetic-batch-006."""
import collections, hashlib, json, pathlib, re
ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = pathlib.Path(__file__).resolve().parent
FROZEN=ROOT/'sft_pipeline_300/frozen'

def u(s): return {'role':'user','content':s}
def a(s): return {'role':'assistant','content':s}
rows=[]
def add(category, family, bucket, prompt, target):
    rows.append({'category':category,'scenario_family':family,'input_length_bucket':bucket,'context_messages':[u(prompt)] if isinstance(prompt,str) else prompt,'target_response':target})
# Short final child inputs: one to five words.
add('everyday_social','sharing_trumpet','short','I brought my trumpet!','Can you play a little song?')
add('questions_explanations','meaning_of_spin','short','What does spin mean?','To spin is to go round and round. A top can spin.')
add('practical_help','dropped_sandwich','short','I dropped my sandwich.','If it fell in mud, do not eat it. Ask Mum or Dad.')
add('questions_explanations','snails_do_not_run','short','Can snails run?','No. They do not run.')
add('games_creativity','clap_drum_song','short','Make a clap song.','Clap, clap, up and down. Tap, tap, on a drum. Sing, sing, here we come!')
add('practical_help','tipped_cup_spill','short','My cup tipped over.','Get a rag for the mess. Put the cup back up.')
add('questions_explanations','dogs_lungs_fish_gills','short','Do dogs have gills?','No. Dogs have lungs. Fish have gills.')
add('games_creativity','pink_rhyme_words','short','What rhymes with pink?','Think, wink, and sink. They end like pink.')
add('practical_help','cannot_reach_object','short','I cannot reach it.','Ask Mum or Dad to get it.')
add('emotions_boundaries_identity','dislike_of_current_game','short','I hate this game.','You can stop. What do you want to do now?')
add('questions_explanations','slugs_cannot_sing','short','Can slugs sing?','No. Slugs cannot sing.')
add('questions_explanations','meaning_of_sip','short','What does sip mean?','To sip, drink just a little bit.')
add('games_creativity','imaginary_spaceship_destination','short','I made a spaceship.','Where will it go?')
add('emotions_boundaries_identity','cannot_visit_child','short','Can you visit me?','I cannot come to you. But I am here to chat.')
add('context_changes_corrections','dad_pen_location','short',[u('Dad has a pen in the bag. Mum has a pen on the desk.'),a('His is in the bag. Hers is on the desk.'),u('Where is his?')],'His pen is in the bag.')
add('context_changes_corrections','correct_hat_size_choice','short',[u('I can pick the big red hat or the little blue hat.'),a('Do you want the little blue hat?'),u('No, the big one.')],'The big red hat, then.')
add('questions_explanations','stamps_total_from_context','short',[u('I got three stamps from Mum.'),a('You have three stamps.'),u('Dad gave me one stamp too.'),a('One stamp is from Dad.'),u('How many in all?')],'You got four stamps in all.')
add('short_stories','ant_rock_rain_continuation','short',[u('Our story has an ant on a rock. Then rain starts falling.'),a('The ant is on the wet rock.'),u('What happens next?')],'The ant ran down the rock. He found a shell. He got under it. The shell kept him from the rain.')
add('emotions_boundaries_identity','offering_outgrown_cap','short',[u('My red cap is too small for me. My sister wants it.'),a('It may fit her.'),u('Can she have it?')],'You can give her the red cap. Ask her if it fits.')
add('context_changes_corrections','choose_remaining_shop_item','short',[u('I can put a shell, a rock, or a leaf in my pretend shop.'),a('What will you pick?'),u('Not the rock or the leaf.'),a('We have one left.'),u('Then which one?')],'Take the shell for the shop.')
# Medium final child inputs: six to fifteen words.
add('games_creativity','rag_on_stick_flag','medium','How can I make a flag from this rag?','Put the rag on a stick. Dad can help it stick to the top.')
add('questions_explanations','four_dots_plus_two','medium','If I draw four dots and then two more, how many is that?','Four and two make six. You have six dots.')
add('emotions_boundaries_identity','camping_plan_rained_out','medium','I wanted to go camping but it keeps raining.','That is no fun. We can make up a camp song.')
add('short_stories','dog_gets_a_splint','medium','Tell me a story about a vet and a dog.','A dog went to the vet. He had a bad leg. The vet put a splint on it. The dog had to rest.')
add('questions_explanations','meaning_of_blend','medium','What does blend mean when we mix paint?','To blend is to mix things. You can blend red and blue.')
add('emotions_boundaries_identity','respect_sisters_space','medium','My sister said she wants to be left alone.','Let her be for a bit. You can play with blocks.')
add('questions_explanations','ice_in_warm_bath','medium','What happens to ice in a warm bath?','It will melt in the bath.')
add('games_creativity','desk_tapping_pattern','medium','Can you give me a little tapping pattern?','Tap the desk once. Tap it two times. Then clap once.')
add('practical_help','teddy_bedtime','medium','Can you help me tuck my teddy into bed?','Put him on the bed. Put the quilt over him. Then sing a little song.')
add('everyday_social','wet_footprints_discovery','medium','I made footprints all the way across the kitchen!','You left a long path! Were they wet?')
add('emotions_boundaries_identity','uncomfortable_secret','medium','Someone told me to keep a secret that makes me uncomfortable.','You can tell Mum or Dad. You do not have to keep it.')
add('games_creativity','pretend_moon_is_cheese','medium','In my pretend world the moon is made of cheese.','Then a mouse could have a big lunch! What will it eat next?')
add('practical_help','thank_friend_for_help','medium','How can I thank my friend for helping me?','You can say, "Thank you for the help."')
add('questions_explanations','rock_cannot_grow_legs','medium','If I plant a rock will it grow legs?','No. A rock will not get legs. A rock is not alive.')
add('context_changes_corrections','remember_chosen_drum_colour','medium',[u('I want a brown drum. The white one is for Dad.'),a('Brown is for you. White is for Dad.'),u('What was the colour I chose for myself?')],'You want the brown drum.')
add('context_changes_corrections','new_location_of_red_shell','medium',[u('I put the red shell under the bed.'),a('It is under the bed.'),u('No, I moved it into the cup on the desk.'),a('The cup has the shell now.'),u('Where is the one I moved most recently?')],'The red shell is in the cup on the desk.')
add('questions_explanations','number_left_after_gift','medium',[u('I have six pegs in my bag.'),a('You have six pegs.'),u('I give two pegs to Mum.'),a('Mum has two of them.'),u('How many have I got in my bag now?')],'You have four pegs in the bag now.')
add('short_stories','fox_reply_to_duck','medium',[u('In our story the duck asks the fox to play. The fox wants a nap instead.'),a('The fox will rest.'),u('What should he say to her about that?')],'He can say, "I want a nap. We can play after it."')
add('context_changes_corrections','chosen_song_over_story','medium',[u('I want to sing about a hen, not hear a story about one.'),a('You want a hen song.'),u('Can you do the thing I asked for now?')],'Cluck, cluck, little hen. Sing for me, then sing again!')
add('context_changes_corrections','changed_order_of_activities','medium',[u('I will ring the bell and then take a nap.'),a('The bell, then a nap.'),u('Actually, swap the order, so what do I do?')],'Take a nap. Then ring the bell.')
# Long final child inputs: sixteen or more words.
add('short_stories','duck_with_red_boots','long','Make up a silly story about a duck who wants to wear a big red hat but it keeps slipping off.','A duck had a red hat. It fell off his head. A pig got the hat. He put it on a stick. The duck had a flag!')
add('questions_explanations','two_groups_three','long','I have three red pegs in one hand and three blue pegs in the other hand so how many do I have altogether?','Three and three make six. You have six pegs in all.')
add('practical_help','muddy_toy_truck','long','My toy truck has mud all over it from playing outside and I want to put it back in the box.','Get the mud off with a wet rag. Then put the truck back in the box.')
add('emotions_boundaries_identity','angry_about_skipped_turn','long','My friend went twice when it was supposed to be my turn and now I want to shout at him.','You can say, "I want to go next." If you want, stop for a bit.')
add('games_creativity','pretend_box_pet','long','We have an empty cardboard box and I want to pretend it is a pet that can do silly tricks.','The box can be a pet! It can hop, sit, and spin. What will you call it?')
add('questions_explanations','meaning_of_trudge','long','My book says the man had to trudge through the mud but I do not know what trudge means.','To trudge is to walk with slow steps. It can be hard in thick mud.')
add('context_changes_corrections','known_recipient_of_blue_rag','long',[u('The blue rag is for Mum. The red rag is for Dad.'),a('Blue for Mum. Red for Dad.'),u('Dad has already got his and now Mum wants hers, so which one should I take over to her?')],'Take the blue rag to Mum. Dad has the red one.')
add('short_stories','continue_pig_hidden_in_box','long',[u('In our story the pig hides in a big box. The hen can hear him but cannot see him.'),a('The hen is by the box.'),u('Make her discover where he is and then let them play together, but I want him to stay in his hiding place. ' )],'The hen saw a leg stick out. She knew he was in the box. She sat on top of it. The pig said, "Find me!"')
add('context_changes_corrections','missing_item_from_picnic_plan','long',[u('For our picnic I want a bun, a plum, and milk.'),a('A bun, a plum, and milk.'),u('The bun and the milk are both in my bag, but what is the other thing I said I wanted to take?')],'You said a plum too. Put the plum in the bag.')
add('context_changes_corrections','corrected_cup_colours_for_people','long',[u('Mum has the red cup and Dad has the white cup.'),a('Mum has red. Dad has white.'),u('No, I mixed them up when I told you before, so please swap them and tell me who has which now. ')],'Mum has the white cup. Dad has the red cup.')

base_sft=[json.loads(x) for x in (ROOT/'datasets/sft-200-v1/sft.jsonl').read_text().splitlines()]
base_review=[json.loads(x) for x in (ROOT/'datasets/sft-200-v1/review.jsonl').read_text().splitlines()]
system={'role':'system','content':(FROZEN/'system.txt').read_text()}
assert all(r['prompt'][0]==system for r in base_sft)
# Read the frozen spelling rules and exact exceptions before checking words.
profile=(FROZEN/'READER_PROFILE.txt').read_text()
rubric=(FROZEN/'RUBRIC.md').read_text()
spec=json.loads((FROZEN/'spec.json').read_text())
dolch={w.lower() for group in json.loads((FROZEN/'dolch-through-grade1.json').read_text())['groups'].values() for w in group}
evidence={}
for r in base_review:evidence.update(r['lexical_evidence'])
evidence.update({
 'spin':'sp + short i + n',
 'top':'t + short o + p',
 'stamp':'st + short a + mp',
 'pet':'p + short e + t',
 'dogs':'dog (d + short o + g) + plural s',
 'lungs':'lung (l + short u + ng) + plural s',
 'gills':'gill (g + short i + ll) + plural s',
 'wink':'w + short i + nk',
 'sink':'s + short i + nk',
 'slugs':'slug (sl + short u + g) + plural s',
 'sip':'s + short i + p',
 'drink':'dr + short i + nk',
 'hers':'UNSUPPORTED: no automatic derivative of exact Dolch her; replace before export',
 'found':'UNSUPPORTED: ou vowel team; replace before export',
 'kept':'k + short e + pt',
 'rain':'UNSUPPORTED: ai vowel team; replace before export',
 'fits':'fit (f + short i + t) + verb s',
 'dots':'dot (d + short o + t) + plural s',
 'camp':'c + short a + mp',
 'vet':'v + short e + t',
 'bad':'b + short a + d',
 'splint':'spl + short i + nt',
 'blend':'bl + short e + nd',
 'bath':'b + short a + th',
 'times':'UNSUPPORTED: no automatic derivative of exact Dolch time; replace before export',
 'keep':'UNSUPPORTED: ee vowel team; replace before export',
 'mouse':'UNSUPPORTED: ou vowel team and silent e; replace before export',
 'lunch':'l + short u + n followed by ch',
 'alive':'UNSUPPORTED: unstated multisyllable and silent-e patterns; replace before export',
 'cluck':'cl + short u + ck',
 'head':'UNSUPPORTED: ea vowel team; replace before export',
 'call':'UNSUPPORTED: a with ll needs evidence not established in supplied outline; replace before export',
 'trudge':'UNSUPPORTED: unstated dge spelling; replace before export',
 'slow':'UNSUPPORTED: ow vowel team; replace before export',
 'steps':'step (st + short e + p) + plural s',
 'hard':'UNSUPPORTED: ar vowel; replace before export',
 'knew':'UNSUPPORTED: silent k and ew; replace before export',
})
# Editorial substitutions use only exact exceptions or taught spellings.
replacements={
 218:'The ant ran down the rock. He got under a shell. It was not wet under there. He had a little rest.',
 228:'Tap the desk once. Tap it again. Then clap once.',
 231:'You can tell Mum or Dad. You do not have to do what they ask.',
 232:'Then a rat could have a big lunch! What will it eat next?',
 234:'No. A rock will not get legs. It will just be a rock.',
 241:'A duck had a red hat. It fell off him. A pig got the hat. He put it on a stick. The duck had a flag!',
 245:'The box can be a pet! It can hop, sit, and spin. What will you name it?',
 246:'To plod is to walk with slow steps. It can be hard in thick mud.',
 248:'The hen saw a leg stick out. She went to the box. The pig said, "Clap with me!" They did a clap and tap song.',
}
for i,r in enumerate(rows,201):
 if i in replacements:r['target_response']=replacements[i]
# Keep the word-meaning prompt aligned with the supported target definition.
rows[45]['context_messages'][-1]['content']='My book says the man had to plod through the mud but I do not know what plod means.'
rows[45]['target_response']='To plod is to walk with short steps. You may plod in thick mud.'
evidence.update({'plod':'pl + short o + d','short':'UNSUPPORTED: or vowel pattern; replace before export','name':'UNSUPPORTED: silent e; replace before export'})
rows[45]['target_response']='To plod is to walk with slow steps. It is not a fast walk.'
# A fully decodable paraphrase of slow avoids teaching an unsupported spelling.
rows[45]['target_response']='When you plod, you do not walk fast. You may plod in thick mud.'
rows[44]['target_response']='The box can be a pet! It can hop, sit, and spin. What will you call it?'
# Avoid hard forms in the invitation by asking about an action instead.
rows[44]['target_response']='The box can be a pet! It can hop, sit, and spin. Can it jump too?'
for r in rows:
 for m in r['context_messages']:
  if m['role']=='assistant' and m['content']=='His is in the bag. Hers is on the desk.':m['content']='His is in the bag. Her pen is on the desk.'


def words(text):return re.findall(r"[A-Za-z]+(?:['’][A-Za-z]+)?",text.lower())
def counts(text):return [len(words(x)) for x in re.split(r'[.!?]+',text) if words(x)]
prior_targets={r['target_response'] for r in base_review}
missing={};unsupported={}
for i,r in enumerate(rows,201):
 msgs=[r['target_response']]+[m['content'] for m in r['context_messages'] if m['role']=='assistant']
 for w in sorted(set(words(' '.join(msgs)))):
  if w not in dolch and w not in evidence:missing.setdefault(w,[]).append(i)
  elif w not in dolch and evidence[w].startswith('UNSUPPORTED'):unsupported.setdefault(w,[]).append(i)
print('MISSING',missing)
print('UNSUPPORTED',unsupported)
assert not missing and not unsupported
sft=[];review=[]
for i,r in enumerate(rows,201):
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
  'review_status':'model_reviewed_pending_human',
  'review_note':'Original model-authored candidate; lexical evidence covers target and historical assistant messages. Independent audit and human review pending.',
  'sentence_word_counts':counts(r['target_response']),
  'revision':'1.5-batch006-candidate1',
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
metadata={'generator_model':'gpt-6.1-sol','reasoning_effort':'high','agent_role':'SFT generator','agent_task':'/root/generator','batch':'synthetic-batch-006','id_range':['pilot-201','pilot-250'],'instruction_sources_read':['sft_pipeline_300/frozen/GENERATOR.md','sft_pipeline_300/frozen/spec.json','sft_pipeline_300/frozen/system.txt','sft_pipeline_300/frozen/READER_PROFILE.txt','sft_pipeline_300/frozen/RUBRIC.md','sft_pipeline_300/frozen/dolch-through-grade1.json','datasets/sft-200-v1/README.md','datasets/sft-200-v1/sft.jsonl','datasets/sft-200-v1/review.jsonl','datasets/synthetic-batch-005/audit.md'],'prior_target_sources_checked':['datasets/sft-200-v1/review.jsonl'],'held_out_data_opened':False,'audit_approval':False,'system_sha256':hashlib.sha256(system['content'].encode()).hexdigest()}
(OUT/'generator-agent.json').write_text(json.dumps(metadata,indent=2)+'\n')
print('WROTE',len(sft),'rows; histories',sum(r['requires_history'] for r in review),'buckets',collections.Counter(r['input_length_bucket'] for r in review))
