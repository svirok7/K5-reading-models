"""Original candidate authoring, scoped exclusively to synthetic-batch-007."""
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
add('everyday_social','found_a_feather','short','I found a feather.','Was it big or little? You can tell me.')
add('questions_explanations','meaning_of_trim','short','What does trim mean?','To trim, cut a little bit off.')
add('questions_explanations','hens_and_eggs','short','Can hens lay eggs?','Yes. An egg has a shell.')
add('practical_help','milk_spill_cleanup','short','I spilled my milk.','Get a rag for the milk. It can help with the mess.')
add('emotions_boundaries_identity','grumpy_and_quiet','short','I am so grumpy.','You can sit for a bit. We do not have to chat.')
add('questions_explanations','cows_cannot_fly','short','Can cows fly?','No. They cannot fly.')
add('games_creativity','rug_rhyme_words','short','What rhymes with rug?','Bug, hug, and mug. You can put a mug on a rug!')
add('questions_explanations','fog_and_drops','short','Is fog wet?','Yes. Fog has little drops in it. They can get things wet.')
add('everyday_social','homemade_mask','short','I made a mask.','Is it a funny mask? You can tell me what is on it.')
add('games_creativity','duck_in_a_dress','short','Tell me something funny.','Think of a duck in a pink dress. She has a hat on her foot!')
add('emotions_boundaries_identity','request_for_a_hug','short','Can you hug me?','I cannot hug you. You can ask Mum or Dad for a hug.')
add('questions_explanations','meaning_of_mend','short','What does mend mean?','To mend is to fix. You can mend a rip.')
add('everyday_social','learned_to_skip','short','I can skip now!','You can skip! Now you can add a hop.')
add('emotions_boundaries_identity','asking_for_a_break','short','I want a break.','Stop for a bit. Come back when you want to.')
add('context_changes_corrections','recall_meg_destination','short',[u('Meg went to the pond. Ben went to the shop.'),a('They went out.'),u('Where did she go?')],'Meg went to the pond.')
add('context_changes_corrections','remember_cap_colour','short',[u('My cap was black. I left it on the bench.'),a('The cap is on the bench.'),u('What colour was it?')],'The cap was black.')
add('questions_explanations','plums_after_eating','short',[u('I had six plums and ate four.'),a('You ate four of them.'),u('And how many left?')],'Two plums are left.')
add('short_stories','ben_and_windblown_tent','short',[u('In our story Ben has a tent. A gust of wind lifts the tent.'),a('The wind sent the tent up.'),u('What happened to him?')],'Ben ran after the tent. It fell in the sand. He put it up again. Then he sat in it.')
add('context_changes_corrections','brown_bun_for_child','short',[u('Mum put a brown bun in my bag. She said that one was mine.'),a('There is a brown bun in the bag.'),u('Is it for me?')],'Yes. The brown bun is for you.')
add('short_stories','chosen_red_frog_story','short',[u('Can you make a story about a red frog or a blue bug?'),a('What one do you want?'),u('The red one now.')],'A red frog had a jam pot. He put the pot on a stump. A bug got in the jam. The frog got a big shock!')
# Medium final child inputs: six to fifteen words.
add('questions_explanations','meaning_of_twig','medium','Can you explain what a twig is?','A twig is a little branch. It can snap.')
add('practical_help','helping_with_dishes','medium','How can I help Dad with the dirty dishes?','Put the dishes in the sink. Ask Dad what you can do next.')
add('practical_help','kite_up_in_tree','medium','My kite is stuck really high in the tree.','Ask Mum or Dad to get it down. Do not go up after it.')
add('questions_explanations','dots_in_three_pairs','medium','I drew two dots three times so how many dots is that?','Two, two, and two make six. There are six dots in all.')
add('short_stories','meg_and_spilled_jam','medium','Please tell me a story about Meg and jam.','Meg had a pot of jam. She put it on a bun. The jam ran down her chin! She got a rag. Then she ate the bun.')
add('games_creativity','rat_cat_mat_rhyme','medium','Make up a rhyme about a cat and rat.','A rat sat on a mat. Up came a big black cat. The rat ran off with the mat!')
add('emotions_boundaries_identity','bedtime_darkness_worry','medium','I am scared of the dark at bedtime.','You can ask Mum or Dad to sit with you. Tell them what you think.')
add('emotions_boundaries_identity','companion_cannot_share_meal','medium','Will you eat some of my dinner with me?','I cannot eat with you. We can chat as you eat.')
add('questions_explanations','meaning_of_brisk','medium','What does brisk mean when someone says a brisk walk?','A brisk walk is a fast walk. You do not run.')
add('games_creativity','pretend_shop_plum_and_bun','medium','I have a plum and bun for my pretend shop.','Put the plum here and the bun there. Now the shop is open!')
add('questions_explanations','clam_and_shell','medium','Does a clam live inside a shell like this?','Yes. A clam has a shell. The shell can shut.')
add('everyday_social','dog_asleep_on_bag','medium','My dog fell asleep right on top of my bag.','He has a new bed! Is he snug on the bag?')
add('practical_help','hot_pan_boundary','medium','The pan is really hot but I want to move it.','Do not put a hand on it. Ask Mum or Dad to help.')
add('games_creativity','two_sticks_for_cross','medium','What can I make with just two sticks?','Put one stick over the other. You can make a cross.')
add('context_changes_corrections','known_box_for_bells','medium',[u('The bells go in the black box. The drums go in the brown box.'),a('Bells in black. Drums in brown.'),u('Where do I put the ones that ring?')],'Put the bells in the black box.')
add('context_changes_corrections','recall_named_fish','medium',[u('My pretend fish is called Jill. The pretend crab is called Ben.'),a('Jill is the fish. Ben is the crab.'),u('What was the name I gave the fish?')],'The fish is Jill. Ben is the crab.')
add('questions_explanations','one_group_removed_from_six','medium',[u('I have six cups. Two are red and four are white.'),a('Two red cups and four white cups.'),u('If I take away the white ones, how many are left?')],'The two red cups are left.')
add('short_stories','reply_about_lost_pin','medium',[u('In our story Meg lost a pin. Ben found it in a box.'),a('Ben has the pin now.'),u('What can he say to her about it?')],'He can say, "I have the pin. It was in the box."')
add('context_changes_corrections','remember_rest_before_song','medium',[u('Let us rest, then sing, then clap.'),a('Rest, sing, then clap.'),u('What did we say we would do before the song?')],'We will rest. Then we will sing.')
add('context_changes_corrections','correct_location_of_pink_hat','medium',[u('My pink hat was in the bag. Now I put it on the bed.'),a('The pink hat is on the bed now.'),u('Is the pink one still where it was before?')],'No. The pink hat is on the bed.')
# Long final child inputs: sixteen or more words.
add('short_stories','jill_and_big_quilt','long','Could you make up a little story about Jill who wants a nap but has to find her quilt first?','Jill went to her bed. Her quilt was not there. She found it in a big box. She got it out. Then she had a snug nap.')
add('questions_explanations','six_buns_share_four','long','I had six buns and gave one to each of four friends so how many buns do I still have?','Six take away four is two. You have two buns left.')
add('practical_help','sorting_damp_and_dry_rags','long','These cleaning rags are all mixed together and some are damp but some are dry so how can I sort them?','Put the damp rags in one box. Put the rags that are not wet in a new box.')
add('emotions_boundaries_identity','friend_wants_no_more_play','long','My friend says she does not want to play any more but I still want to keep playing with her.','Let her stop. You can play with a new thing. We can make up a song too.')
add('games_creativity','toy_bus_from_box','long','Can we pretend this big box is a bus and all my toy animals want to go for a ride?','Yes! Put them in the box. The bus can go to a shop. What will they get there?')
add('questions_explanations','meaning_of_trunk_for_packing','long','In the story they put all their clothes into a big trunk before the trip but what is a trunk?','A trunk is like a big box. You can put things in it for a trip.')
add('context_changes_corrections','known_recipient_of_pink_flag','long',[u('Meg wants the pink flag. Ben wants the black flag.'),a('Pink for Meg. Black for Ben.'),u('He has already got his one but she is still waiting for hers, so which one should I give her?')],'Give Meg the pink flag. Ben has the black one.')
add('short_stories','continue_duck_hidden_in_tent','long',[u('In our story a duck hides a shell in a tent. A pig comes to find the shell.'),a('The pig is by the tent.'),u('Please have him find the thing that she hid and then let them both make something with it together. ')],'The pig went into the tent. He saw the shell. The duck put sand in it. The pig put a flag in the sand. They had a little fort!')
add('context_changes_corrections','remember_order_after_first_task','long',[u('I will put the blocks away, ring the bell, and take a nap.'),a('Blocks away, then the bell, then a nap.'),u('I have done the first thing on the plan we made, so what are the two things I should do next?')],'Ring the bell. Then take a nap.')
add('context_changes_corrections','swap_drums_between_named_children','long',[u('Meg has a red drum and Ben has a blue drum.'),a('Meg has red. Ben has blue.'),u('Actually, they just swapped with each other after I told you that, so can you tell me which one she has now?')],'Meg has the blue drum now. Ben has the red drum.')

base_sft=[json.loads(x) for x in (ROOT/'datasets/sft-200-v1/sft.jsonl').read_text().splitlines()]
base_review=[json.loads(x) for x in (ROOT/'datasets/sft-200-v1/review.jsonl').read_text().splitlines()]
accepted006=[json.loads(x) for x in (ROOT/'datasets/synthetic-batch-006/review.jsonl').read_text().splitlines()]
system={'role':'system','content':(FROZEN/'system.txt').read_text()}
assert all(r['prompt'][0]==system for r in base_sft)
profile=(FROZEN/'READER_PROFILE.txt').read_text()
rubric=(FROZEN/'RUBRIC.md').read_text()
spec=json.loads((FROZEN/'spec.json').read_text())
dolch={w.lower() for group in json.loads((FROZEN/'dolch-through-grade1.json').read_text())['groups'].values() for w in group}
evidence={}
for r in base_review+accepted006:evidence.update(r['lexical_evidence'])
evidence.update({
 'trim':'tr + short i + m',
 'sticks':'stick (st + short i + ck) + plural s',
 'thing':'th + short i + ng',
 'cut':'c + short u + t',
 'hug':'h + short u + g',
 'fog':'f + short o + g',
 'drops':'drop (dr + short o + p) + plural s',
 'mask':'m + short a + sk',
 'dress':'dr + short e + ss',
 'foot':'UNSUPPORTED: oo vowel team; replace before export',
 'mend':'m + short e + nd',
 'rip':'r + short i + p',
 'skip':'sk + short i + p',
 'add':'Short a in a closed syllable with doubled final d',
 'meg':'m + short e + g; decodable name, not an automatic name exception',
 'ben':'b + short e + n; decodable name, not an automatic name exception',
 'jam':'j + short a + m',
 'shock':'sh + short o + ck',
 'branch':'br + short a + n followed by ch',
 'dishes':'dish (d + short i + sh) + plural es',
 'brisk':'br + short i + sk',
 'clam':'cl + short a + m',
 'other':'UNSUPPORTED: unstated additional o and r pattern; replace before export',
 'bells':'bell (b + short e + ll) + plural s',
 'drums':'drum (dr + short u + m) + plural s',
 'jill':'j + short i + ll; decodable name, not an automatic name exception',
 'found':'UNSUPPORTED: ou vowel team; replace before export',
 'damp':'d + short a + mp',
 'rags':'rag (r + short a + g) + plural s',
 'bus':'b + short u + s',
 'trip':'tr + short i + p',
 'trunk':'tr + short u + nk',
 'fort':'UNSUPPORTED: or vowel pattern; replace before export',
})
replacements={
 260:'Think of a duck in a pink dress. She has a hat on her leg!',
 284:'Put one stick on top of one more. You can make a cross.',
 291:'Jill went to her bed. Her quilt was not there. It was in a big box. She got it out. Then she had a snug nap.',
 298:'The pig went into the tent. He saw the shell. The duck put sand in it. The pig put a flag in the sand. They had a little sand pit!',
}
# Replace unlisted more with listed two and a concrete cross instruction.
replacements[284]='Put the two sticks in a cross. One can go on top.'
for i,r in enumerate(rows,251):
 if i in replacements:r['target_response']=replacements[i]

def words(text):return re.findall(r"[A-Za-z]+(?:['’][A-Za-z]+)?",text.lower())
def counts(text):return [len(words(x)) for x in re.split(r'[.!?]+',text) if words(x)]
prior_targets={r['target_response'] for r in base_review+accepted006}
missing={};unsupported={}
for i,r in enumerate(rows,251):
 msgs=[r['target_response']]+[m['content'] for m in r['context_messages'] if m['role']=='assistant']
 for w in sorted(set(words(' '.join(msgs)))):
  if w not in dolch and w not in evidence:missing.setdefault(w,[]).append(i)
  elif w not in dolch and evidence[w].startswith('UNSUPPORTED'):unsupported.setdefault(w,[]).append(i)
print('MISSING',missing)
print('UNSUPPORTED',unsupported)
assert not missing and not unsupported
sft=[];review=[]
for i,r in enumerate(rows,251):
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
  'revision':'1.5-batch007-candidate1',
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
metadata={'generator_model':'gpt-6.1-sol','reasoning_effort':'high','agent_role':'SFT generator','agent_task':'/root/generator','batch':'synthetic-batch-007','id_range':['pilot-251','pilot-300'],'instruction_sources_read':['sft_pipeline_300/frozen/GENERATOR.md','sft_pipeline_300/frozen/spec.json','sft_pipeline_300/frozen/system.txt','sft_pipeline_300/frozen/READER_PROFILE.txt','sft_pipeline_300/frozen/RUBRIC.md','sft_pipeline_300/frozen/dolch-through-grade1.json','datasets/sft-200-v1/README.md','datasets/sft-200-v1/sft.jsonl','datasets/sft-200-v1/review.jsonl','datasets/synthetic-batch-006/sft.jsonl','datasets/synthetic-batch-006/review.jsonl','datasets/synthetic-batch-006/audit.md'],'prior_target_sources_checked':['datasets/sft-200-v1/review.jsonl','datasets/synthetic-batch-006/review.jsonl'],'held_out_data_opened':False,'audit_approval':False,'system_sha256':hashlib.sha256(system['content'].encode()).hexdigest()}
(OUT/'generator-agent.json').write_text(json.dumps(metadata,indent=2)+'\n')
print('WROTE',len(sft),'rows; histories',sum(r['requires_history'] for r in review),'buckets',collections.Counter(r['input_length_bucket'] for r in review))
