"""Input-only history annotations. Never rewrites approved SFT bytes."""
import json,sys
from pathlib import Path
import build_corpus as b
A=Path(__file__).resolve().parent
SUPPORTED={
'claps':'clap (cl + short a + p) + s ending, lesson42',
'crabs':'crab (cr + short a + b) + s ending, lesson42',
'hint':'h + short i + final nt blend',
'kid':'k + short i + d',
'kids':'kid (k + short i + d) + s ending, lesson42',
'king':'k + short i + ng digraph, lesson36',
'lands':'land (l + short a + final nd blend) + s ending, lesson42',
'nest':'n + short e + final st blend',
'plant':'initial pl blend + short a + final nt blend',
'rad':'r + short a + d',
'sack':'s + short a + ck, lesson34',
'ship':'sh + short i + p',
'slick':'initial sl blend + short i + ck, lesson34',
'such':'s + short u + first ch sound',
'taps':'tap (t + short a + p) + s ending, lesson42',
'tells':'tell (t + short e + ll, lesson29) + s ending, lesson42',
'ten':'t + short e + n',
'test':'t + short e + final st blend',
'than':'voiced th + short a + n',
'tub':'t + short u + b',
'boxes':'box (b + short o + x /ks/) + es ending, lesson42',
'gifts':'gift (g + short i + final ft blend) + s ending, lesson42',
'helps':'help (h + short e + final lp blend) + s ending, lesson42',
'maps':'map (m + short a + p) + s ending, lesson42',
'shelf':'sh + short e + final lf blend',
'track':'initial tr blend + short a + ck, lesson34',
}
REASONS={}
def group(ws,reason):
 for w in ws.split():
  assert w not in REASONS,w
  REASONS[w]=reason

group('6','Numeral: no exact word-form or supported decoding evidence is supplied for this digit in this benchmark.')
group('beach bee been boat coat clue easy each equal feel food freezing groups grown hear keep key loud mouth need plain room screen sheet show sound sounds straight teacher true year','Untaught vowel-team or vowel-sequence spelling; no exact Dolch entry for this form.')
group('car farm first floor form hard heard heart hurt jar letters mark more number order other others part person short sore sort story turn word words work worries your','R-controlled spelling or r-controlled unstressed syllable not established by the supplied outline; exact form is not listed.')
group('alive alone blame board choice choose drove five game gave hide home leave line made note page place pose role rule same scare scene shapes size space taste those tile time use','Silent-e, complex vowel spelling, or additional consonant sound not established for this unlisted exact form.')
group('asked building changed clapped counting downed feelings funnier going guessing happened looking moved planned taller','Unlisted ed/ing/ier/er inflection or derivative; the benchmark does not grant these suffix rules from an allowed base.')
group('changes comes does gives goes knows leaves likes says sees stays uses wants','Exact unlisted derivative or irregular form; a listed-only irregular base does not automatically license this form. No separate taught-pattern evidence is established here.')
group('about across always another answer anyone anything baby before birds bottom boy carry change charge claim clear correct cousin crown different doing done door dragon edit exact example fall fingers flew folders full gone happens kind listen many mean meaning means meant middle mind never nobody people piano postpone pretend question real school secret sentence set sign simple someone stay talk their touch toy truth unplug usual way whole would write wrong','Specific unsupported pattern; replaced below with word-specific explanation.')
# Word-specific findings, including forms for which the supplied outline is insufficient.
REASONS.update({
'before':'Unlisted multisyllable form with unstressed initial vowel and ore/r-controlled spelling; no whole-form taught-pattern evidence.',
'about':'Initial unstressed vowel plus ou spelling; not an explicitly supported compound or exact list form.',
'across':'Unlisted multisyllable form with unstressed initial vowel; no clear taught-pattern evidence for the whole spelling.',
'always':'ay vowel team plus complex multisyllable form is not established; exact form is not listed.',
'another':'Unstressed vowels plus er ending in a multisyllable form; exact form is not listed.',
'answer':'Silent w and er ending are not established; exact form is not listed.',
'anyone':'Complex unlisted compound built from exceptional listed forms; no independent taught-pattern proof for this whole exact spelling.',
'anything':'Complex unlisted compound with exceptional any; no independent taught-pattern proof for this whole exact spelling.',
'baby':'Multisyllable word with final y=/ee/, not established by the unenumerated additional-y heading.',
'birds':'ir r-controlled vowel; s does not establish unsupported bird spelling.',
'bottom':'Unlisted multisyllable form with unstressed second vowel; no explicit taught-pattern evidence for the whole form.',
'boy':'oy vowel team is not established; exact form is not listed.',
'carry':'ar sound in a multisyllable form plus final y=/ee/; no exact list entry.',
'change':'Silent-e spelling and soft g are not established by the supported first-sound patterns; no exact list entry.',
'charge':'ar spelling plus soft g/silent e; no exact list entry.',
'claim':'ai vowel team not established; exact form is not listed.',
'clear':'ea/ear spelling not established; exact form is not listed.',
'correct':'Unstressed initial vowel in an unlisted multisyllable form; no explicit whole-form decoding evidence.',
'cousin':'ou irregular vowel and unstressed second syllable; no exact list entry.',
'crown':'ow vowel spelling not established; exact form is not listed.',
'different':'Unlisted complex multisyllable form and unstressed vowels; no explicit whole-form decoding evidence.',
'doing':'Unlisted ing derivative of listed do, not covered by supported s/es endings.',
'done':'o vowel exception and silent-e spelling; no exact list entry.',
'door':'oo/r vowel spelling not established; exact form is not listed.',
'dragon':'Unlisted multisyllable form with unstressed second vowel; no explicit whole-form decoding evidence.',
'edit':'Unlisted multisyllable form without explicit whole-word taught-pattern evidence; simple closed-syllable heading is not blanket permission.',
'exact':'Initial unstressed vowel and x=/gz/ in a multisyllable word are not explicitly established.',
'example':'Initial unstressed vowel, x=/gz/, and unstressed final syllable are not explicitly established.',
'fall':'al vowel sound is not established by the unenumerated additional-a heading; all exact exception does not license fall.',
'fingers':'Unlisted multisyllable base with er ending; s does not establish its unsupported spelling.',
'flew':'ew vowel spelling not established; exact form is not listed.',
'folders':'Unestablished long-o closed syllable plus er ending; s does not establish the base.',
'full':'Unlisted /oo/ sound of u is not established by the unenumerated additional-u heading.',
'gone':'Unlisted o/silent-e spelling; go exact entry does not grant this changed form.',
'happens':'Unlisted multisyllable base with unstressed vowel; s does not supply whole-base decoding evidence.',
'kind':'Long i in a closed syllable is not established; exact form is not listed.',
'listen':'Silent t and unstressed final syllable; no exact list entry.',
'many':'Unlisted additional-a vowel and final y sound; no explicit whole-form evidence.',
'mean':'ea vowel team not established; exact form is not listed.',
'meaning':'ea vowel team plus unlisted ing derivative.',
'means':'ea vowel team; s does not establish the unsupported base.',
'meant':'Irregular ea vowel spelling not established; exact form is not listed.',
'middle':'Unlisted unstressed final le syllable, not covered by simple closed/open syllables.',
'mind':'Long i in a closed syllable is not established; exact form is not listed.',
'never':'Unlisted multisyllable form with er ending; no whole-form taught-pattern evidence.',
'nobody':'Unlisted multisyllable compound with final y and unstressed vowel; no whole-form evidence.',
'people':'eo vowel spelling plus unstressed final le syllable; no exact list entry.',
'piano':'Complex multisyllable vowel sequence and stress are not established; no exact list entry.',
'postpone':'Unlisted long-o closed/silent-e multisyllable form; no explicit taught-pattern evidence.',
'pretend':'Unlisted multisyllable form with unstressed first vowel; no explicit whole-form evidence.',
'question':'qu is supported, but the remaining complex tion spelling is not established; no exact list entry.',
'real':'ea vowel sequence not established; exact form is not listed.',
'school':'ch=/k/ plus oo vowel team is not explicitly established; no exact list entry.',
'secret':'Unlisted multisyllable form with unstressed second vowel; no explicit whole-form evidence.',
'sentence':'Soft c, silent e, and unstressed multisyllable form are not explicitly established.',
'set':'s + short e + t; independently decodable. Corrected to supported evidence below.',
'sign':'Silent g and long i in closed syllable not established; exact form is not listed.',
'simple':'Unlisted unstressed final le syllable; no explicit whole-form evidence.',
'someone':'Unlisted complex compound made from exceptional listed forms; no independent whole-form taught-pattern evidence.',
'stay':'ay vowel team not established; exact form is not listed.',
'talk':'al vowel sound and silent l are not established; exact form is not listed.',
'their':'eir vowel/r-controlled spelling not established; exact form is not listed.',
'touch':'ou irregular vowel spelling not established; exact form is not listed.',
'toy':'oy vowel team not established; exact form is not listed.',
'truth':'Unlisted long-u closed-syllable spelling is not established by the supplied outline.',
'unplug':'Unlisted prefixed multisyllable form; prefix un- is not a listed curriculum rule or a compound of standalone supported words.',
'usual':'Complex multisyllable vowels and s=/zh/ are not established; exact form is not listed.',
'way':'ay vowel team not established; exact form is not listed.',
'whole':'Silent w/wh plus silent e spelling not established; exact form is not listed.',
'would':'Silent l and irregular ou vowel spelling not established; exact form is not listed.',
'write':'Silent w and silent-e long-i spelling not established; exact form is not listed.',
'wrong':'Silent w spelling not established; exact form is not listed.',
})
REASONS.update({'both':'Long o in a closed syllable is not established; exact form is not listed.','buzz':'Final zz spelling is not explicitly established by ff/ll/ss rules; no exact list entry or separate supplied taught-pattern evidence.','call':'Unlisted al vowel sound not established by unenumerated additional-a heading.','cold':'Long o in a closed syllable is not established; exact form is not listed.','hold':'Long o in a closed syllable is not established; exact form is not listed.','should':'Silent l and irregular ou spelling not established; exact form is not listed.','try':'Final y long-i sound is not established by the unenumerated additional-y heading; no exact list entry.'})
SUPPORTED['set']='s + short e + t'
REASONS.pop('set')

def create():
 ev=b.evidence_map()|b.EXTRA_EVIDENCE|SUPPORTED
 unknown=set()
 for n in range(1,7):
  for line in(A/f'batch-{n:02d}/sft.jsonl').read_text().splitlines():
   for m in json.loads(line)['prompt'][1:]:
    if m['role']=='assistant': unknown.update(b.words(m['content'])-ev.keys())
 assert not unknown-REASONS.keys(), sorted(unknown-REASONS.keys())
 lexicon={w:{'status':'supported','evidence':ev[w]}if w in ev else {'status':'unsupported_by_benchmark','evidence':REASONS[w]}for w in sorted(set(SUPPORTED)|unknown)}
 out=[]
 for n in range(1,7):
  data=[json.loads(l)for l in(A/f'batch-{n:02d}/sft.jsonl').read_text().splitlines()]
  meta=[json.loads(l)for l in(A/f'batch-{n:02d}/review.jsonl').read_text().splitlines()]
  for row,review in zip(data,meta):
   checks=[];flaws=[]
   seeded=review['flawed_history_indices']
   for i,m in enumerate(row['prompt'][1:],1):
    if m['role']!='assistant':continue
    issues={w:REASONS[w]for w in sorted(b.words(m['content'])-ev.keys())}
    checks.append({'message_index':i,'content':m['content'],'supported_words':{w:ev[w]for w in sorted(b.words(m['content'])&ev.keys())},'unsupported_words':issues})
    if issues:flaws.append({'message_index':i,'kind':'reading_profile','word_findings':issues,'loss_scope':'input_only_no_completion_loss'})
    if i in seeded:flaws.append({'message_index':i,'kind':'meaning_or_response_quality','description':'Intentional incorrect or unresponsive prior assistant turn. Independent full-history review confirms the final completion recovers from or supersedes it.','loss_scope':'input_only_no_completion_loss'})
   out.append({'id':review['id'],'batch':n,'approved_sft_sha256':b.sha(A/f'batch-{n:02d}/sft.jsonl'),'context_index_convention':'1-based messages excluding system','intentional_semantic_flawed_history_indices':seeded,'flawed_history_indices':sorted({x['message_index']for x in flaws}),'historical_flaws':flaws,'historical_assistant_lexical_checks':checks,'supervision':'final_completion_only','human_approved':False})
 b.write_jsonl(A/'history-flaws.jsonl',out)
 (A/'history-lexicon.json').write_text(json.dumps(lexicon,indent=2,ensure_ascii=False)+'\n')
 print('Sidecar',b.sha(A/'history-flaws.jsonl'),'lexicon',b.sha(A/'history-lexicon.json'),'rows',len(out),'flawed',sum(bool(x['flawed_history_indices'])for x in out),'lexicalwordtypes',len(unknown))
if __name__=='__main__':create()
