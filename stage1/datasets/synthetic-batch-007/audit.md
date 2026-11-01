# Independent audit — batch 007, round 1

Result: **50 pass, zero open findings.**

The primary focus was exhaustive word eligibility, as requested by the user and frozen instructions. I read all 50 targets, all 16 historical assistant turns, every lexical evidence entry, and every external word-choice rationale. All 198 distinct assistant forms were reviewed against profile v1.5.

## Lexical checks

- Cross-checked all 380 “Exact Dolch entry” claims against the frozen exact list. Listed exceptions were accepted only as exact forms, without automatic derivatives.
- Independently checked all 110 non-Dolch forms, including explicit curriculum Leap Word `or`, through supported spelling routes. Evidence coverage was not treated as phonics verification.
- Checked the new names directly: `Meg` is m + short e + g; `Ben` is b + short e + n; `Jill` is j + short i + ll. No automatic name exemption was used.
- Checked actual s/es inflections such as `dishes`, `drops`, `bells`, `drums`, `sticks`, `cups`, `buns`, `rags`, `plums`, `things`, and `blocks` from supported bases.
- Checked blends and phonograms including `branch` (br + short a + n + ch), `brisk` (br + short i + sk), `trim` (tr + short i + m), `trunk` (tr + short u + nk), and `shock` (sh + short o + ck). `Add` and `egg` retain regular short vowels and their final consonant sound despite doubled letters. `Cannot` uses supported can + not parts.

No clear unsupported assistant word, false exact-form claim, or false word-choice rationale found. No unsupported contraction or ed/ing suffix was introduced.

## Brief secondary checks

No clear material relevance, fact, safety, history-use, length, or question-count defect found. All 16 marked history cases use prior information; the other 34 have no assistant history. The final-input mix is 20 short, 20 medium, and 10 long. The longest target sentence has 11 easy words, within the occasional 9–12-word allowance. Each target has at most one question. Current SFT prompts/completions match review rows; all system messages match the frozen system. No exact target duplicate occurs among the accepted250.

## Exact reviewed bytes

- Frozen manifest SHA-256: `bb34c2e66a9dbbe2684e574790f5d120ede4aa58174cf2d030b0837c75d9c760`
- SFT SHA-256: `2d139adbaf5f2dee2ef86af002465043ec0399d62d66701cf974c02517fc4b54`
- Review SHA-256: `3955157f7bc10c92ed7826b82d382ce64f08a57646a2de193c88be4bc7a2d39b`
- Auditor: `/root/auditor`, declared model `gpt-6.1-sol`, reasoning effort `high`.

## Limits

Independent model linguistic review is not human approval or evidence of reading mastery, learning, or generalization. No held-out examples or archived test material were opened. Any further edit requires independent re-audit and new exact-file hashes.
