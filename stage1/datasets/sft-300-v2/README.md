# sft-300-v2: independently audited 300-example SFT dataset

Version 2 preserves sft-300-v1 and fixes four findings from a fresh independent full-corpus model audit. The exact v2 data bytes have independent model approval: **300 pass, zero open findings**. Status is `independently_reviewed_pending_human`; human approval remains pending.

Three final child prompts (057, 065, 096) now genuinely require earlier context. Example 186 no longer invents a child-placement event; its counts, evidence, and external rationale were updated. All other 296 rows are byte-identical in both SFT and review files, independently verified with exact line hashes. Revision metadata was added only to the four changed review rows. CHANGELOG.md summarizes the edits; changes.jsonl preserves complete old/new objects and line strings.

The fresh linguistic audit covered all 300 targets, 144 historical assistant turns, 371 distinct assistant word forms, every evidence entry, and every external word-choice rationale. All assistant words have exact-list or defensible supported-decoding evidence under profile v1.5. Read audit.md for scope/limits and audit.json for all 300 per-ID verdicts, resolved findings, current/source row hashes, and the full lexical inventory. manifest.json binds the approval and report hashes to exact data bytes.

sft.jsonl contains only prompt and completion. Every system profile matches the frozen system. review.jsonl contains line-aligned external metadata and must not be fed to normal SFT. All IDs, history flags, historical assistant turns, and original input buckets are preserved. Actual final-user-input counts are **121 short, 121 medium, 58 long**, using whitespace word counts (short 1–5, medium 6–15, long 16+). There are 97 history-dependent examples and 300 distinct targets.

Alignment, alternating roles, lexical coverage, exact Dolch claims, sentence/question bounds, target uniqueness, unchanged rows, and unchanged source data hashes were checked. Scripts supplement independent linguistic judgment; they do not establish phonics by coverage alone.

Tokenizer/chat-template/completion-loss-mask verification remains separate and must use the intended model’s tokenizer and chat template. No training has been executed. No held-out, test, or archive material was opened. Independent model review is not human approval or evidence of learning/mastery/generalization. Any later data edit requires a new exact-hash independent audit.
