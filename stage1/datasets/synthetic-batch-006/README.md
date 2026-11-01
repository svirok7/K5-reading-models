# Synthetic batch 006: candidates pending independent audit

50 original candidates, pilot-201 through pilot-250, authored by the SFT generator agent using gpt-6.1-sol with high reasoning effort. Independent audit and human review remain pending. generator-agent.json records the role and instruction sources read.

sft.jsonl contains only prompt and completion. The expanded system message uses sft_pipeline_300/frozen/system.txt exactly, matching the accepted 200-row baseline. Only the final assistant completion is a training target. review.jsonl is line-aligned and supplies full context, target, concise word-choice reasoning, and spelling evidence for every distinct target and historical assistant word. Review metadata must not be fed to normal SFT.

Final child inputs comprise exactly 20 short inputs (1–5 whitespace-separated words), 20 medium inputs (6–15), and 10 long inputs (16+). Exactly 16 records contain historical assistant context and genuinely require prior information; the other 34 have no assistant history. Every assistant sentence has at most 12 words; targets contain at most one question. The generator checked spelling-evidence coverage, exact Dolch forms, schema alignment, the identical system profile, within-batch unique targets, and absence of exact target duplication against the accepted 200 rows. These are generator checks, not independent phonics verification.

The lexical objective remains primary. New closed-syllable forms, blends, taught digraphs/endings, and s inflections have specific evidence. Listed irregular words are treated as exact exceptions; no automatic derivatives or contractions are introduced. Contextual cases recover prior people, choices, locations, totals, objects, or sequence information.

Child speech is unrestricted. No held-out test data or test archives were opened, no training was run, and the accepted baseline and earlier batches were preserved. build_candidates.py is the authoring source; do not rerun it over audit corrections without incorporating those corrections first.
