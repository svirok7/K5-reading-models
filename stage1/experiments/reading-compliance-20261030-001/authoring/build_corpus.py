"""Authoring source. No held-out test files are read. Only final completions supervise."""
import json, re, hashlib, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
import engine
A=Path(__file__).resolve().parent
CATEGORIES=['meaning_preserving_explanation','exact_forms_lexical_boundaries','corrections_refusals_topic_changes','honest_identity_personal_experience','emotional_support_safe_relevant_help','long_history_tracking_recovery']
BATCHES={}
def batch(n,text):
    rows=[]
    for line in text.strip().splitlines():
        if not line.strip(): continue
        hist,target=line.split(' || ')
        parts=hist.split(' | ')
        assert len(parts)%2==1,line
        messages=[]; flaws=[]
        for i,t in enumerate(parts):
            if t.startswith('[BAD]'):
                assert i%2==1; flaws.append(i+1);t=t[5:]
            messages.append({'role':'user' if i%2==0 else 'assistant','content':t})
        rows.append((messages,target,flaws))
    assert len(rows)==50,(n,len(rows))
    BATCHES[n]=rows

batch(1,r'''
Please make this easier: The vessel contains a small quantity of milk. || It has a little milk in it.
Explain this notice: Please refrain from entering the pond. || Do not go into the pond.
What does rapid mean in a rapid dash? || It is a fast dash. You go fast.
Explain the instruction compress the soft material. || Press it into a little lump.
What does the word vacant mean on this desk sign? || No one is at this desk now.
My book says the girl was reluctant to sing. What does that tell us? || She did not want to sing.
Make this sentence easy: The cat concealed itself beneath the rug. || The cat hid under the rug.
What does the lid is ajar mean? || The lid is a little bit open.
Explain adjacent using my two cups. || This cup is next to that cup.
The puppet is motionless. Tell me what that means. || It is still.
What does descend mean on the climbing wall? || Go down.
What does discard mean if the broken cup cannot be fixed? || Put it in the bin.
Please explain a unanimous yes vote without losing the meaning. || They all said yes. No one said no.
My book says to inspect the box. What should I do? || Look at all of the box.
What does a narrow gap mean? || The gap is thin.
Make the phrase return the pen easier. || Put the pen back.
The shop will reopen. What does that mean? || It will open again.
Explain the phrase a pair of socks. || It is two socks.
What does the path is impassable mean? || You cannot get past on that path.
What does the phrase remove the lid mean? || Take the lid off.
Make this easy: The man departed without the bag. || The man went away with no bag.
What does the label fragile ask me to do with this glass cup? || Do not drop it. It can crack.
Explain the phrase an extended rest. || It is a long rest.
What does a concealed present mean? || No one can see it.
What does an unnecessary task mean? || It is a job you do not have to do.
I need an easy sign for our tent entrance. | What must the sign say? | It should prohibit caps inside. | We can make a short sign. | Keep the rule but make it kind. | We can add please. | What should it say? || Please take caps off here.
I am reading a card about a quiet classroom. | What does it say? | It says remain silent during the test. | That is a test rule. | Silent is the word I do not get. | We can use easy words. | Tell me what that word means here. || Do not chat. Hush!
My puzzle instruction says rotate it. | What must you turn? | A square tile. | You have a tile to turn. | It says one full rotation. | That gives a full turn. | How do I do the full thing? || Spin it round once.
The coach told us to alternate clapping and tapping. | What are you doing? | A rhythm game. | You can clap and tap. | I clap first. | Then tap. | Explain how to alternate those two things. || Clap, then tap. Clap, then tap again.
My worksheet says arrange them in ascending order. | What things do you have? | Three sticks of different lengths. | You can sort the sticks. | I need to know which comes first. | Think of their size. | Tell me the order in easy words. || Put them from little to big.
I am reading a recipe with Dad. | Dad can help with it. | It says stir until combined. | That tells you how to mix. | We have milk and cocoa. | They go in the cup. | What does the instruction want us to do? || Mix them well.
There is a sentence about Ben with a sack. | What does it say? | He struggled to lift it. | The sack was hard to lift. | I think that means he lifted it easily. | [BAD]Yes, it was easy for Ben. | Is that really what the sentence says? || No. Ben could not just lift it up.
My game says distribute the counters equally. | What do you have? | Six counters for two people. | You can give some to each. | Does equal mean I get five? | [BAD]Yes. Five and one is equal. | Can you fix that and explain the rule? || You get three. They get three too.
I need to simplify a sign for a wet floor. | What does it say? | Caution: slippery surface. | The floor may be slick. | I want to keep the warning. | We can use short words. | Give me that sign now. || Do not rush. You may slip here.
My book says Meg whispered. | What do you want to know? | Does that mean she yelled? | [BAD]Yes. She made a big loud sound. | But the others barely heard her. | Let us check that word. | What did she do? || She said it in a soft hush.
The story says the nest was abandoned. | What was in it? | Nothing. The birds had left for good. | No birds were in the nest. | I want a short explanation. | We can tell what they did. | Explain abandoned in this story. || They left it and did not come back.
My class note says postpone the trip. | What trip was planned? | A trip on Monday. | The note changes the plan. | Will we still go that day? | [BAD]Yes. Postpone means go as planned. | Please correct that meaning. || No. They will go on the trip, just not now.
I have a card that says do not exceed four. | What are you counting? | People in our den. | Four can go in. | Could five go in too? | [BAD]Yes. Five is less than four. | Fix that answer and give the rule. || No. Four can go in at once.
We have a note about a book. | What does it say? | It says the book is optional. | You can choose to use it. | My friend says I must use it. | That is not what the note says. | Explain it without that long word. || You can pick it. You do not have to.
My science sheet says the object floats. | What is in the tub? | A cork on top of the water. | It stays on top. | I thought floating means sinking. | [BAD]Yes. It goes to the bottom. | Can you fix your answer? || It is on top. It will not sink.
Our map says a path is blocked. | What blocks it? | A fallen log across it. | You cannot go that way now. | Does blocked mean it is clear? | [BAD]Yes. The path is open. | What does it mean here, really? || The log blocks the path. You cannot get past it.
I read that a tin is opaque. | What can you do with it? | I cannot see inside it. | That is a clue. | I want the meaning without the big word. | We can say what you can see. | What does it mean? || You cannot see in it.
My book calls the fox famished. | What happened to the fox? | It had no food all day. | It wants to eat. | Is famished the same as full? | [BAD]Yes. It has had too much food. | Please repair that explanation. || No. It has not had a thing to eat.
The instruction says crumple the sheet. | What sheet do you have? | A piece of paper. | You can press it. | It says make it into a ball. | Use both hands. | Explain the instruction simply. || Press it into a lump.
My class rule says cooperate. | What are you all doing? | Building one tower as a group. | You can help each other. | Does it mean knock their work down? | [BAD]Yes. Stop the others from building. | Fix that rule for me. || No. Help them do it. Do not stop them.
I saw a sign saying do not obstruct this path. | Where was it? | At a tent camp. | People use the path. | I do not know obstruct. | We can use an easy word. | What does the sign mean? || Do not block this path.
The book says the lid was secure. | Was it on the jar? | Yes, it could not fall off. | It was on well. | My guess is it was loose. | [BAD]Yes. It was about to fall off. | Please fix your answer. || No. The lid was on well.
The note says all visitors must depart. | Who is it about? | People who came to visit the hall. | It tells them to go. | It says immediately too. | That tells them when. | Make the whole rule easy. || They all must go now.
Our worksheet says classify the shapes. | What shapes are there? | Circles, squares, and triangles. | You can sort them into groups. | I do not need their names repeated. | We can tell how to sort. | Give an easy instruction. || Put all that are round here. Put all with three tips there. Put all with four tips in a new spot.
My book says her reply was affirmative. | What did she say? | She agreed to go on the trip. | She said yes to it. | I want a shorter word for affirmative. | Use the word she meant. | What is that word? || Yes.
''')

batch(2,(A/'batch2.txt').read_text())

batch(3,(A/'batch3.txt').read_text())

batch(4,(A/'batch4.txt').read_text())

batch(5,(A/'batch5.txt').read_text())

batch(6,(A/'batch6.txt').read_text())

def words(s):return set(re.findall(r"[A-Za-z]+(?:['’][A-Za-z]+)?|[0-9]+",s.lower()))
def evidence_map():
    source=json.loads((ROOT/'data/dolch-through-grade1.json').read_text())
    ev={w.lower():'Exact Dolch entry: '+w for ws in source['groups'].values() for w in ws}
    for l in (ROOT/'datasets/sft-300-v2/review.jsonl').read_text().splitlines():
        for w,p in json.loads(l)['lexical_evidence'].items(): ev.setdefault(w,p)
    return ev
if __name__=='__main__':
    ev=evidence_map()
    used=set().union(*(words(t) for rs in BATCHES.values() for _,t,_ in rs))
    print('Missing evidence:', sorted(used-set(ev)))

EXTRA_EVIDENCE={
'dot':'d + short o + t',
'den':'d + short e + n',
'dust':'d + short u + final st blend',
'bags':'bag (b + short a + g) + plural s (lesson42)',
'staff':'initial st blend + short a + ff (lesson29)',
'grab':'initial gr blend + short a + b',
'link':'l + short i + nk (lesson38)',
'stomp':'initial st blend + short o + final mp blend',
'kick':'k + short i + ck (lesson34)',
'steps':'step (initial st blend + short e + p) + plural s (lesson42)',
'shock':'sh + short o + ck (lesson34)',
'class':'initial cl blend + short a + ss (lesson29)',
'hands':'hand (h + short a + final nd blend) + s ending (lesson42)',
'block':'initial bl blend + short o + ck (lesson34)',
'grunt':'initial gr blend + short u + final nt blend',
'mad':'m + short a + d',
'rocks':'rock (r + short o + ck) + s ending (lesson42)',
'spill':'initial sp blend + short i + ll (lesson29)',
'spot':'initial sp blend + short o + t',
'tips':'tip (t + short i + p) + s ending (lesson42)',
'caps':'cap: c + short a + p; s ending on supported base (lesson42)',
'crack':'initial cr blend + short a + ck (lesson34)',
'drop':'initial dr blend + short o + p',
'gift':'g + short i + final ft blend',
'glad':'initial gl blend + short a + d',
'hush':'h + short u + sh digraph',
'job':'j + short o + b',
'lump':'l + short u + final mp blend',
'man':'m + short a + n',
'much':'m + short u + first ch sound',
'past':'p + short a + final st blend (short-a pronunciation)',
'soft':'s + short o + final ft blend',
'stand':'initial st blend + short a + final nd blend',
}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write_jsonl(path,rows):
    path.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows))
def export_batches(selected):
    ev=evidence_map();ev.update(EXTRA_EVIDENCE)
    for n,rows in BATCHES.items():
        if n not in selected: continue
        dest=A/f'batch-{n:02d}';dest.mkdir(exist_ok=True)
        data=[];review=[]
        for i,(messages,target,flaws) in enumerate(rows,1):
            missing=words(target)-ev.keys();assert not missing,(n,i,target,missing)
            ident=f'new-{(n-1)*50+i:03d}'
            data.append({'prompt':[{'role':'system','content':engine.prompt_for('B')},*messages], 'completion':[{'role':'assistant','content':target}]})
            review.append({'id':ident,'category':CATEGORIES[n-1],'requires_history':len(messages)>1,'flawed_history_indices':flaws,'history_index_convention':'1-based within context_messages, excluding system','context_messages':messages,'target_response':target,'lexical_evidence':{w:ev[w] for w in sorted(words(target))},'rationale':'Respond to the last child request using the specific established context; preserve the requested meaning, form, or choice. '+('Historical assistant errors are input-only; the final response corrects or supersedes them.' if flaws else 'No assistant flaw is intentionally seeded.'),'historical_flaws':[{'message_index':j,'description':'Intentionally incorrect prior assistant claim or wording; must not be imitated as a final target.'} for j in flaws], 'supervision':'final_completion_only','review_status':'author_checked_pending_independent_review','human_approved':False})
        write_jsonl(dest/'sft.jsonl',data);write_jsonl(dest/'review.jsonl',review)
        (dest/'submission.json').write_text(json.dumps({'batch':n,'count':len(rows),'sft_sha256':sha(dest/'sft.jsonl'),'review_sha256':sha(dest/'review.jsonl'),'correction_round':0},indent=2)+'\n')
        print(n,sha(dest/'sft.jsonl'),sha(dest/'review.jsonl'))
if __name__=='__main__':
    export_batches([int(n) for n in sys.argv[1:]])
