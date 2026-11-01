# Independent audit — batch 006, round 1

Result: **50 pass, zero open findings.**

The primary focus was exhaustive word eligibility, as requested by the user and the frozen lexical-first instructions. I read all 50 targets, all 20 historical assistant turns, every lexical evidence entry, and every external word-choice rationale. All 191 distinct assistant forms were reviewed against profile v1.5.

## Lexical checks

- Cross-checked all 361 “Exact Dolch entry” claims against the frozen exact list. Listed exceptions are accepted as exact forms without extending their spelling allowance to derivatives.
- Independently checked all 96 non-Dolch forms, including the explicit curriculum Leap Word `or`, through supported spelling routes. Coverage scripts were not treated as phonics verification.
- Checked actual inflections including `dogs`, `gills`, `lungs`, `slugs`, `dots`, `fits`, `stamps`, `pegs`, `legs`, `things`, and `blocks` from supported bases.
- Checked blends and phonograms including `splint` (spl + short i + nt), `plod` (pl + short o + d), `drink` (dr + short i + nk), `lunch` (l + short u + n + ch), `cluck` (cl + short u + ck), and `quilt` (qu + short i + lt).
- `Mum` and `Dad` qualify by regular closed-syllable spelling, without an automatic name exception. `Cannot` uses supported can + not parts. `Bath` and `path` have defensible short-a pronunciations.

No clear unsupported assistant word, false exact-form claim, or false word-choice rationale found. No unsupported contraction or ed/ing suffix was introduced.

## Brief secondary checks

No material relevance, fact, safety, history-use, length, or question-count defect found. All 16 marked history cases use prior information; the other 34 have no assistant history. The final-input mix is 20 short, 20 medium, and 10 long. Maximum target sentence length is 10 words, with at most one question per target. Current SFT prompts/completions match their review rows; all system messages match the frozen system. Targets have no exact duplicate among the accepted200.

## Exact reviewed bytes

- Frozen manifest SHA-256: `bb34c2e66a9dbbe2684e574790f5d120ede4aa58174cf2d030b0837c75d9c760`
- SFT SHA-256: `a17dfffc89c5d0aad8711f8863ea7eba2066a4d3a05cb646b426a128bd72cbaf`
- Review SHA-256: `cc636820ab37e22e987e61163e149793e8927ada30a2a1697d5b57b3bc6ef989`
- Auditor: `/root/auditor`, declared model `gpt-6.1-sol`, reasoning effort `high`.

## Limits

Independent model linguistic review is not human approval or evidence of reading mastery, learning, or generalization. No held-out examples or archived test material were opened. Any further edit requires independent re-audit and new exact-file hashes.
