# Independent audit — batch 004, round 2

Result: **50 pass, zero open findings.**

Reviewed all 50 target responses, all 23 historical assistant turns, every lexical evidence entry, and every external word-choice rationale against the frozen profile and exact Dolch list. Checked relevance, facts, natural phrasing, sentence length, questions, and contextual use. Current SFT prompts/completions agree with review rows; all system messages match the frozen system.

## Resolved findings

- **B004-F1, pilot-148:** The final child input now refers to “the total I gave you before” without stating that total. The answer needs the earlier total of three and correctly removes one to give two.
- **B004-F2, pilot-150:** The final child input now asks to swap the earlier order and put “them” away instead of playing. The target needs the prior bell/blocks sequence and correctly rings the bell before putting the blocks away.

Both fixes were independently reviewed in the current bytes. All current contexts and targets were reread. Replacing only these two final-child-turn strings with their prior strings reproduces both prior reviewed file hashes exactly, verifying the rest of both files is unchanged. Thus every assistant word, evidence entry, and rationale remains the version reviewed in full.

No clear unsupported target or historical assistant word found. Exact-list claims match the frozen JSON. Regular closed-syllable/blend words, taught digraphs/endings, supported compounds, and s/es inflections were independently reviewed rather than inferred from coverage checks. The current pilot-132 uses exactly six bricks. All 16 marked history cases use relevant prior context after the corrections.

## Exact reviewed bytes

- Frozen manifest SHA-256: `abe144fa530582a8dccf231cf99a8a59715bf2e64402f78c3851eebb49ab3819`
- SFT SHA-256: `6b15a392b84c1171b9e10d1f3e9080b65b932ddafa1aa0a8ef3bc2828c5c6e01`
- Review SHA-256: `77a4dc94c6b02a40d692b00c7c728f01e0bf91e569659fdac996d1916c1b0d1a`
- Auditor: `/root/auditor`, declared model `gpt-6.1-sol`, reasoning effort `high`.

## Limits

This is independent model linguistic review, not human approval. No held-out examples or archived test material were opened. No claim of learning, individual reading mastery, or generalization is made. Any further edit requires re-audit of final bytes and new hashes.
