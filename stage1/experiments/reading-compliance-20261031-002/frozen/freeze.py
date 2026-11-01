"""Freeze read-only dev + exactly 25 saved SFT UI cases. Never reads test data."""
import collections, datetime, hashlib, json, sqlite3, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import engine
OUT = Path(__file__).resolve().parent
canon = lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
sha = lambda x: hashlib.sha256(x).hexdigest()
# Independently read every candidate history and all 300 training histories. Nearest
# evidence below is manual semantic review, not a fuzzy-match score or model call.
dev_reviews = [
([1,31,151], 'exclude_training_overlap', 'Bare greeting is a close paraphrase of hiya/heyyy/Hi, reading buddy.'),
([163], 'retain', 'Asks how the companion is; training asks whether it gets tired, a distinct capability claim.'),
([183,216,241], 'retain', 'Received bright red hat from grandmother; training concerns slipping hats or choosing hats, not receiving this gift.'),
([263,15], 'retain', 'Reports one-leg hopping; skip achievement and shadow jumping are distinct situations.'),
([255,179,181], 'retain', 'Unexplained sadness needs support; grumpiness, glum definition, and thunder fear are different concrete needs.'),
([173,254], 'retain', 'Broken crayon is not sibling taking crayons or spilled milk; distinct remedy and context.'),
([293,196], 'retain', 'Requests definition of damp; training sorts damp/dry rags or defines rush, not this word definition.'),
([245,281], 'retain', 'Defines pet; pretend box-pet play and clam-shell facts do not supply that answer.'),
([148,167], 'retain', 'Computes two plus one; point correction and two-shell-plus-one history are distinct concrete tasks.'),
([153], 'exclude_training_overlap', 'Fish running vs fish having legs asks the same closely related ordinary-fish locomotion fact; conservative exclusion.'),
([149,239,248], 'retain', 'Open hen adventure request; training has specific pig-box rescue, hen song, or hidden-pig continuation constraints.'),
([224,50], 'retain', 'Puppy bath story is distinct from vet/dog or dog/wig stories; topic alone is not overlap.'),
([209,105], 'retain', 'Unspecified it requires clarification; cannot reach it and teach game pose distinct situations.'),
([8,117], 'retain', 'Ambiguous ct transcription needs clarification; training provides unambiguous kitten/cat situations.'),
([286], 'retain', 'Recall Max from own dog history; training has pretend fish Jill and crab Ben. Same skill, distinct facts and full history.'),
([27,57,96], 'retain', 'Switch cats to hens; training switches trucks to ducks, trains to rain, or bricks to cheese. Same skill, distinct full context.'),
([4,64,239], 'retain', 'Declines a story right now; generic stopping or asking for a hen song are different specific preferences.'),
([105,195,257,276], 'retain', 'Requests interactive rhyming game; training gives action game, song, rhyme words, or a composed rhyme. Different requested format.'),
([146,163,214], 'retain', 'Asks whether companion is a real kid; body/visit pretend premise or tiredness differ. Shared honesty theme alone is not overlap.'),
([24,92,194], 'retain', 'Password sharing has distinct secret-credential handling; address, classroom, or phone-number disclosure shares category but not concrete requested disclosure.')
]
ui_reviews = [
([1,31,151], 'exclude_training_overlap', 'Helloo is a close greeting paraphrase of training greetings.'),
([163], 'retain', 'How-are-you follow-up after false happy-bear claim; no training history with that claim or repair need.'),
([255,181], 'retain', 'Unexplained sadness follows invented bear identity; grumpiness or thunder fear is a different concrete need.'),
([179,181], 'retain', 'Why refers to prior log/sky advice in sadness context; no training matches this referent or failed advice.'),
([148,167], 'retain', 'Two plus one arithmetic; no matching training concrete expression/history.'),
([153], 'exclude_training_overlap', 'Fish-running question remains a close fish-locomotion overlap even with prior two-plus-one exchange.'),
([145,47], 'retain', 'Elliptical frog locomotion follow-up to fish-run discussion; frog-rest story and slug-jump fact differ.'),
([27,57,96], 'retain', 'Switch to hens within fish/frog history; training has other topic transitions, not this full context.'),
([146,214], 'retain', 'Real-kid identity question differs from visiting/body pretend premise; shared honesty theme is insufficient.'),
([224,50], 'retain', 'Puppy bath story differs from vet/dog and dog/wig stories.'),
([183,216], 'retain', 'Hat gift after bath story; no training has this full history or grandmother gift.'),
([173,254], 'retain', 'Broken crayon after bath/hat exchanges; no concrete training match.'),
([263,15], 'retain', 'Reports one-leg hopping; skip achievement and jumping shadow are distinct tasks.'),
([4,64,168], 'retain', 'No rejects assistant request to hop on both legs. Generic refusal and choosing hop are distinct context.'),
([144,263], 'retain', 'I cant rejects repeated hopping demand; missed beanbag or successful skip differs.'),
([1,31,151], 'exclude_training_overlap', 'Bare Hello is a close greeting paraphrase of training greetings.'),
([4,64], 'retain', 'No declines assistant request to name likes, distinct from generic done/not-today and has material history.'),
([163], 'retain', 'How-are-you follows assistant unsupported claim that child likes nothing; no training history has this repair context.'),
([245,281], 'retain', 'Pet definition differs from pretend box-pet play and clam-shell fact.'),
([106,163,278], 'retain', 'Elliptical asks whether companion has a pet; smell/tired/eat capability questions differ.'),
([286], 'retain', 'Asks invented cat name after assistant false ownership claim; training retrieves supplied pretend fish name, distinct honesty/repair context.'),
([32,62], 'retain', 'Comments on invented Tilly cat; training self-praise/cool comments do not have this referent or false premise.'),
([24,92,194], 'retain', 'Password sharing is distinct credential scenario from address/classroom/phone disclosure.'),
([149,239,248], 'retain', 'Hen adventure request follows erroneous password advice; training has other hen tasks and histories.'),
([293,196], 'retain', 'Damp definition follows password/hen story; damp-rag sorting and rush definition differ.')
]

def run():
    existing = OUT/'manifest.json'
    if existing.exists():
        raise SystemExit('Frozen manifest already exists. Refusing to overwrite immutable freeze.')
    devpath=ROOT/'data/dev.jsonl'; trainpath=ROOT/'datasets/sft-300-v2/sft.jsonl'; dbpath=ROOT/'runs/conversation-results.sqlite3'
    dev=[json.loads(x) for x in devpath.read_text().splitlines()]
    training=[json.loads(x) for x in trainpath.read_text().splitlines()]
    conn=sqlite3.connect(f'file:{dbpath}?mode=ro',uri=True)
    rows=[]
    for dbid, body in conn.execute('SELECT id,body FROM records'):
        obj=json.loads(body)
        model=obj.get('response',{}).get('model',{})
        if model.get('backend')=='qwen' and str(model.get('adapter') or '').endswith('/runs/qwen-sft300-v2-lora-allocator-20261030-008/adapter'):
            rows.append((dbid,body,obj))
    conn.close()
    rows.sort(key=lambda x:(x[2]['created_at'],x[0]))
    assert len(dev)==20 and len(rows)==25 and len(training)==300
    prompt=engine.prompt_for('B'); ph=sha(prompt.encode())
    snapshots=[]; candidates=[]; reviews=[]; cases=[]; seen={}
    allsources=[('dev',r['id'],r,canon(r),review) for r,review in zip(dev,dev_reviews)]
    allsources += [('saved_sft_ui',i,obj,body,review) for (i,body,obj),review in zip(rows,ui_reviews)]
    trainhist=[[{k:m[k] for k in ('role','content')} for m in r['prompt'] if m['role']!='system'] for r in training]
    for source,sourceid,obj,raw,manual in allsources:
        cid=sourceid if source=='dev' else 'ui-'+sourceid
        msgs=[{k:m[k] for k in ('role','content')} for m in obj['messages']]
        assert msgs==obj['messages'] and msgs[-1]['role']=='user'
        seed=(42+int(sha(cid.encode())[:8],16))%(2**32)
        ih=sha(canon({'prompt':prompt,'messages':msgs}).encode())
        row={'case_id':cid,'prompt':prompt,'messages':msgs,'history_kind':'single_turn' if len(msgs)==1 else 'multi_turn','seed':seed,'prompt_hash':ph,'input_hash':ih,'source':source,'source_id':sourceid}
        snapshots.append({'case_id':cid,'source':source,'source_id':sourceid,'source_record':obj,'source_record_serialized':raw,'source_record_serialized_sha256':sha(raw.encode())})
        candidates.append(row)
        nearest,decision,reason=manual
        exact_train=[i+1 for i,x in enumerate(trainhist) if canon(x)==canon(msgs)]
        duplicate=seen.get(ih)
        if duplicate:
            decision='exclude_duplicate';reason='Exact full-history duplicate of '+duplicate+'. '+reason
        else: seen[ih]=cid
        if exact_train: decision='exclude_training_overlap';reason='Exact full role/content history matches training.'
        review={'case_id':cid,'decision':decision,'reason':reason,'nearest_training_indices_1based':nearest,'matching_training_indices_1based':exact_train or (nearest if manual[1]=='exclude_training_overlap' else []),'exact_training_history':bool(exact_train),'duplicate_of':duplicate,'manual_all_300_training_histories_reviewed':True,'training_evidence':[{'index_1based':i,'messages':trainhist[i-1]} for i in nearest]}
        reviews.append(review)
        if decision=='retain':cases.append(row)
    assert len(candidates)==45
    def jl(name,seq): (OUT/name).write_text(''.join(canon(x)+'\n' for x in seq))
    jl('source-records.jsonl',snapshots);jl('candidates.jsonl',candidates);jl('overlap-review.jsonl',reviews);jl('exclusions.jsonl',[r for r in reviews if r['decision']!='retain']);jl('cases.jsonl',cases)
    (OUT/'prompt-B.txt').write_text(prompt)
    (OUT/'training-history-snapshot.jsonl').write_text(''.join(canon({'training_index_1based':i+1,'messages':x})+'\n' for i,x in enumerate(trainhist)))
    readme='''# Frozen diagnostic cases\n\nFrozen before successor data authoring. This is a development/diagnostic set, not unseen test evidence. No held-out test file or archived test contents were opened. The historical overlapping 13-case replay is not a source.\n\n`cases.jsonl` contains only inference prompt/messages, identifiers, hashes, seeds, and provenance. `candidates.jsonl` preserves all 45 candidate inference inputs. Separate source and review files retain saved annotations and overlap decisions; never pass these to inference. Historical assistant messages are preserved exactly even when false or unsafe; they are context, not target answers. The current full Prompt B is used for every case.\n\nSources: all 20 existing dev cases and exactly 25 saved UI records whose Qwen adapter path ends in runs/qwen-sft300-v2-lora-allocator-20261030-008/adapter. SQLite opened with mode=ro. Source UI bodies are preserved as the exact stored serialized JSON; dev records are canonical snapshots and the original file hash is in the manifest. No SFT responses are used as expected answers.\n\nManual semantic review compared each of 45 complete histories with every one of 300 original training histories. The review records nearest concrete evidence and reasons for retention/exclusion. Shared generic skills (memory, empathy, topic changes) or safety category alone do not count as near overlap; same concrete situation/answer or greeting paraphrase does. Fish legs/running is conservatively excluded as closely related locomotion. Exact full-history duplicates are excluded, preserving the first source order (dev before chronological UI). Matching final child text with materially distinct histories remains distinct. Exclusion reasons and original candidate records are preserved.\n\nCanonical JSON uses UTF-8, ensure_ascii=False, sort_keys=True, separators=(comma,colon), one LF per record. prompt_hash is SHA256 of exact prompt UTF-8. input_hash is SHA256 of canonical JSON {prompt,messages}. seed=(42+int(SHA256(case_id UTF-8).hexdigest()[:8],16)) modulo 2**32. Generation is pinned in manifest. File hashes cover immutable artifacts; manifest.sha256 seals manifest.json. File mode 0444 is an additional accidental-write guard, not a cryptographic immutability claim.\n\nReviewer is the separately delegated GPT-6.1 Sol/high session requested by the user; no automated judge/API call was used to invent semantic review.\n'''
    (OUT/'README.md').write_text(readme)
    files={p.name:sha(p.read_bytes()) for p in sorted(OUT.iterdir()) if p.is_file() and p.name not in ('manifest.json','manifest.sha256')}
    manifest={'schema_version':1,'experiment_id':'reading-compliance-20261030-001','frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'case_count':len(cases),'candidate_count':45,'source_counts':{'dev':20,'saved_sft_ui':25},'retained_source_counts':dict(collections.Counter(x['source'] for x in cases)),'history_counts':dict(collections.Counter(x['history_kind'] for x in cases)),'decision_counts':dict(collections.Counter(x['decision'] for x in reviews)),'files':files,'source_hashes':{'data/dev.jsonl':sha(devpath.read_bytes()),'datasets/sft-300-v2/sft.jsonl':sha(trainpath.read_bytes()),'engine.py':sha((ROOT/'engine.py').read_bytes()),'prompts/B.txt':sha((ROOT/'prompts/B.txt').read_bytes()),'READER_PROFILE.txt':sha((ROOT/'READER_PROFILE.txt').read_bytes()),'data/dolch-through-grade1.json':sha((ROOT/'data/dolch-through-grade1.json').read_bytes())},'source_database':{'path':'runs/conversation-results.sqlite3','access':'mode=ro','selected_records':25,'selection_adapter_suffix':'/runs/qwen-sft300-v2-lora-allocator-20261030-008/adapter','record_snapshot_file':'source-records.jsonl'},'prompt_hash':ph,'input_hash_spec':'SHA256(UTF8(canonical_json({prompt,messages})))','seed_spec':'(42 + int(SHA256(case_id UTF-8).hexdigest()[:8],16)) % 2**32','generation':{'do_sample':True,'temperature':0.7,'top_p':0.8,'top_k':20,'max_new_tokens':128,'enable_thinking':False},'test_data_accessed':False,'historical_13_replay_included':False,'status':'frozen','review_method':'Independent manual full-history semantic review of all 45 candidates against all 300 training histories; exact full-history de-duplication.'}
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    (OUT/'manifest.sha256').write_text(sha((OUT/'manifest.json').read_bytes())+'  manifest.json\n')
    for p in OUT.iterdir():
        if p.is_file():p.chmod(0o444)
    print(json.dumps({k:manifest[k] for k in ('case_count','candidate_count','retained_source_counts','history_counts','decision_counts','prompt_hash')},indent=2))
if __name__=='__main__':run()
