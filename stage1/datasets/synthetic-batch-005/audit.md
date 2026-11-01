# Independent audit — batch 005, round 1

Result: **50 pass, zero open findings.**

Per the user’s requested focus, this audit primarily checks word eligibility and word-choice evidence. I read all 50 targets, all 19 historical assistant turns, every lexical evidence entry, and every external word-choice rationale. The current SFT prompts/completions agree with their review rows, and all system messages match the frozen system.

## Word eligibility review

- Reviewed all **198 distinct assistant word forms** through the independent exact-list or decoding routes.
- Cross-checked all **386 “Exact Dolch entry” claims** against the frozen JSON. No false exact-form claim found. Listed irregular forms were accepted as exact exceptions without generalizing their spelling patterns.
- Independently checked all **103 non-Dolch forms**, including the explicitly permitted curriculum Leap Word `or`. The remaining forms use defensible closed syllables, consonant blends, taught digraphs and endings, supported compounds, s inflections, or the taught open-syllable form `hi`. Coverage checks were not treated as phonics verification.
- Checked names and family labels by spelling: `Gran` is gr + short a + n; `Mum` and `Dad` are regular closed syllables. No automatic name allowance was used.
- Checked actual inflections such as `bends`, `fins`, `ducks`, `flags`, `pens`, `stamps`, and `strings` from their supported bases. No contraction or unsupported ed/ing suffix was introduced.
- Checked pronunciation-sensitive evidence: `wind` denotes moving air and uses short i; `doll` has a defensible short-o pronunciation in common American English.

No clear unsupported target/history spelling or false decoding rationale found.

## Brief secondary checks

No clear material relevance, fact, safety, contextual-use, length, or question-count failure found. All 16 marked history cases use prior information. The input mix remains 20 short, 20 medium, and 10 long. The longest target sentence has 10 words; each target has at most one question. Targets are distinct from earlier accepted targets.

## Exact reviewed bytes

- Frozen manifest SHA-256: `abe144fa530582a8dccf231cf99a8a59715bf2e64402f78c3851eebb49ab3819`
- SFT SHA-256: `a5fe96aba85131b180b3814bce7771b06a8737fc9a0fcd055be67cf54a303385`
- Review SHA-256: `5cc2df3595362e0a70f968caaa85c24dceb16a9d3c89a6c034c8a66fe4964156`
- Auditor: `/root/auditor`, declared model `gpt-6.1-sol`, reasoning effort `high`.

## Limits

This is independent model linguistic review, not human approval. No held-out examples or archived test material were opened. No claim of learning, individual reading mastery, or generalization is made. Any subsequent edit requires independent re-audit and new exact-file hashes.
