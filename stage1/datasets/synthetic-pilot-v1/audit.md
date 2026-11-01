# Pilot audit — 2026-10-28

Verdict: revise before training or expanding. Previous validation overstated lexical confidence: the script tests membership in an author-supplied evidence map, not independently established phonics eligibility. All entries remain pending human review.

## Input distribution

Compared with 74 unarchived v1.5 Prompt B live-chat records (including repeated inputs across models), the 30 final pilot inputs have median 11 words versus 5; zero inputs <=4 words versus 35/74; zero lowercase-start inputs versus 10/74. These are descriptive measurements, not independent sampled-population estimates.

Live inputs include greetings, brief reactions, contradictions, playful boasting, topic changes, football/player names, refusals, and spelling/punctuation variation. Pilot inputs are polished, frequently adult-authored requests, with conspicuous memory-test questions. Complex speech is valid, but overrepresented.

Revision target: 12 short inputs (1–4 words), 12 ordinary inputs (5–12), 6 longer inputs; retain 10 contextual examples and existing category counts. Short follow-ups must genuinely require context. Include social greetings, playful replies, corrections, disinterest, emotional disclosure, and ordinary questions. Match style without copying exact distinctive live-chat pairs. Avoid mechanical typos and arbitrary misspelling quotas.

## Word eligibility and meaning

- Blocking: marks in pilot-030 assistant history has r-controlled ar. Plural s does not make its base mark eligible. Replace the phrase, and correct word-evidence.json.
- Dialect-sensitive: grass (010 evidence map / targets 027) and plant (011 history) need a declared pronunciation assumption. Under some English accents these use the BATH vowel rather than a simple short a. Do not label these universally verified; clarify the benchmark pronunciation or choose unambiguous wording. (Grass occurs in target 027; its map entry is not tied to candidate 010.)
- Several evidence labels are vague or misleading: duck needs ck evidence, shells needs sh + short e + ll + s, things needs th + short i + ng + s, tell needs short e + ll, back needs short a + ck. Base-word evidence must be checked before allowing s/es.
- No additional clear unsupported target word identified under the profile's intended short-vowel readings, but this is a model audit, not a certified phonics assessment.
- Decodable is not equivalent to familiar or natural: din is avoidable, and 'did a jump' is stilted.
- Reading success cannot excuse lost meaning, unclear pronouns, or invented context.

## Per-example disposition

| ID | Finding / required change |
|---|---|
|001|Readable target; input is polished. Add genuine casual greeting coverage elsewhere.|
|002|Readable, respects preference; input sounds like an adult instruction.|
|003|Readable and relevant; simplify input style.|
|004|Readable, direct; plausible refusal, but polish down input.|
|005|Meaning retained; explicit recall question is overrepresented in pilot.|
|006|Plausible event, sensible target; retain as longer input.|
|007|Adult-like adjective stacking; preserve complex meaning with natural speech.|
|008|Overwritten input; target changes observation to permission but remains relevant.|
|009|Overwritten input; 'make it again' may push rebuilding before acknowledging frustration.|
|010|Readable target but unnatural 'good snap'; revise phrasing and input.|
|011|'Put it by the sun' is poor location advice. Replace history; resolve plant pronunciation. Explicit memory quiz is artificial.|
|012|Meaning failure: sorting shells becomes picking shells. 'Competition' has no setup. Rewrite scenario and target together.|
|013|Useful elementary description; 'stick' alone does not distinguish magnetism from glue. Review explanatory adequacy.|
|014|'Then it will be wet' is vague about melting; revise to convey liquid/change without overstating word eligibility.|
|015|Shadow movement answer is plausible but pronoun is imprecise; review wording.|
|016|Correct arithmetic, readable. Retain capability, make input more conversational.|
|017|Correct, concise; retain.|
|018|Context is usable; make final question conversational and remove redundant history hints.|
|019|Coherent simple story; request is overly engineered.|
|020|Awkward 'did a jump', uncommon din; revise naturalness.|
|021|Readable but weak payoff for requested silly discovery; improve story quality.|
|022|Multiple 'it' referents obscure cap/moth. Replace explicit instruction to remember with natural continuation.|
|023|'You can tell me how it was' is vague for exclusion; improve emotional specificity.|
|024|Relevant privacy and capability boundary; retain.|
|025|Cannot eat does not directly address inability to taste through screen; refine answer if feasible.|
|026|Target correct; assistant history 'in red' is clipped. Make correction/reply natural.|
|027|Topic-switch skill useful; input too formal; resolve grass pronunciation.|
|028|Latest plan tracked correctly; resembles benchmark memory quiz.|
|029|Referent resolved; 'She has black' is clipped. Improve history wording.|
|030|Unsupported marks in history. Assistant already supplies cross, so target repeats answer and tests little reasoning. Replace setup.|

## Rationale annotation

Add short author-facing annotations explaining communicative intent, essential meaning, evidence for word choices, context dependency, and why a tempting alternative fails. These are concise teaching/design notes, not hidden chain-of-thought transcripts.

Keep annotations out of ordinary SFT targets. Train on the final conversational reply with context and reader profile. Historical assistant turns remain loss-masked. The model learns statistical regularities from varied demonstrations; generalization is possible, not guaranteed. Test it on new scenarios and changed contexts. If needed later, use a separately marked rewrite task or preference pairs rather than teaching the child-facing assistant to print rationales.

## Next action

Revise this 30-example pilot before scaling. Preserve v1 and create a versioned revision with reviewed per-word evidence and input-style coverage. No candidate files were modified by this audit.
