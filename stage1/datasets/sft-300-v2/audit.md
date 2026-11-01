# Independent full-corpus audit — sft-300-v2

**300 pass; zero open findings. All four original findings are resolved.**

The fresh original audit reviewed every word in all 300 target responses and all 144 historical assistant turns, every lexical evidence entry, and every external word-choice rationale. All 371 distinct assistant forms qualify through the frozen exact Dolch list or defensible supported decoding, including the explicit curriculum Leap Word allowance. The current dataset has 2,285 exact-Dolch claims, all checked against the frozen JSON. Names, actual s/es inflections, phonograms, blends, closed syllables, compounds, and pronunciation-sensitive forms were checked independently. No clear unsupported assistant word or false lexical rationale was found.

## Verified corrections

- **057:** “what does it do” now needs the earlier changed rain topic.
- **065:** “the other one” now needs the warm/cold alternatives and rejection of warm milk.
- **096:** “and what about that” now needs the earlier change to cheese.
- **186:** The target is now “Look under the mat.” The invented claim that the child placed the marble was removed; counts, evidence, and rationale were independently rechecked.

I reread all four complete changed SFT/review rows. The remaining 296 rows are byte-identical to the fully audited originals in both files, proved by exact JSONL line hashes. Only the expected four IDs changed; original v1 data files remain unchanged. The JSON report includes all 300 current verdicts, resolved finding provenance, current/source row hashes, and the full lexical inventory.

## Current data checks

SFT/review alignment, exact frozen system, alternating roles, evidence coverage, every exact-list claim, supplied sentence counts, one-question bound, and target uniqueness pass. All 97 marked history rows now use prior information. Actual final-input whitespace counts are **121 short, 121 medium, 58 long**; the corrections preserve the original buckets. These actual counts should be used instead of assuming 120/120/60. Maximum target sentence length is 11 easy words.

## Exact approved bytes

- Frozen manifest SHA-256: `bb34c2e66a9dbbe2684e574790f5d120ede4aa58174cf2d030b0837c75d9c760`
- SFT SHA-256: `42aea06f60ce82af7e276440c3318220efa751cc4fd3c111208176366bb419b3`
- Review SHA-256: `4bea6c4aaf5ecde8218d6a998c4d7435ee217faa75dddd63b719cc79815e445b`
- Auditor: `/root/auditor`, declared model `gpt-6.1-sol`, reasoning effort `high`.

## Limits

Status: **independently_reviewed_pending_human**. This is independent model linguistic review, not human approval or proof of reading mastery, learning, or generalization. No held-out, test, or archive material was opened. Tokenizer/chat-template/loss-mask readiness must be checked separately for the selected training setup. Any subsequent data edit invalidates these exact hashes and requires independent re-audit.
