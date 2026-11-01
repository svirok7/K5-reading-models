# Fresh independent audit of the original 300 examples

**Lexical result: all 300 pass. Overall: 296 pass; four secondary corrections required.**

Reviewed all 300 target responses and all 144 historical assistant turns against frozen profile v1.5 and the exact Dolch list. The dataset has 371 distinct assistant forms: 125 exact Dolch forms and 246 forms supported by phonics or explicit curriculum Leap Word allowance. All 2,289 exact-list evidence claims match the frozen JSON. Every evidence statement and external rationale was checked.

The review distinguishes actual word forms from automatic derivatives, contractions, names, or blanket spelling allowances. Examples checked directly include Meg/Ben/Jill/Rex/Gran, plural s and es, supported compounds, th/sh/ch/qu/x, ck/ng/nk, ff/ll/ss, and long i in hi. Independent notes for broad evidence wording appear in the JSON lexical inventory. No clear unsupported assistant word, false exact-list claim, or false word-choice rationale was found.

## Findings

- **FULL300-F1, pilot-057:** The final input names rain, so “It can get you wet” does not need earlier history despite `requires_history=true`. Make the final input refer back without restating the topic.
- **FULL300-F2, pilot-065:** The final input says “the cold one,” so “Not hot, then” is independently derivable. Make earlier warm/cold alternatives necessary.
- **FULL300-F3, pilot-096:** The final input names cheese, so “You can eat it” does not need the earlier topic switch. Refer back without restating cheese.
- **FULL300-F4, pilot-186:** “You put it there” invents a placement event. History only gives marble locations. Remove or replace that sentence with grounded wording.

All four are medium-severity open findings; no original row was edited. The first three need child-input corrections only and should preserve their short-input buckets. No other clear material relevance, factual, safety, history, or length defect was found in the fresh pass.

## Exact original bytes

- Frozen manifest SHA-256: `bb34c2e66a9dbbe2684e574790f5d120ede4aa58174cf2d030b0837c75d9c760`
- Original SFT SHA-256: `b10b797e6951ca8dacf81da3956ada6094b5c9393dbfb06dcff5438ff1c327f3`
- Original review SHA-256: `b5b661afb9f3973121cb1366442b79cca5fffe949b9b591dad0500e8c9f7cf1b`

The JSON report contains all 300 per-ID verdicts, four checks per row, precise findings, exact original line hashes, and the full lexical inventory. All contexts and targets were read; repeated evidence and templated rationale statements were checked against the independently reviewed word forms, with only punctuation normalized for template comparisons.

Auditor: `/root/auditor`, declared model `gpt-6.1-sol`, reasoning effort `high`. No held-out, test, or archive material was opened. This is model linguistic review, not human approval or evidence of learning/generalization. A corrected dataset needs independent re-audit and new exact-file hashes. Tokenizer/template/loss-mask training checks are separate and have not been established by this linguistic report.
