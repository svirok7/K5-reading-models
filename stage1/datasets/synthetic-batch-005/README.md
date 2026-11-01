# Synthetic batch 005: candidates pending independent audit

50 original candidates, pilot-151 through pilot-200, authored by the SFT generator agent using gpt-6.1-sol with high reasoning effort. No independent audit or human approval is claimed. generator-agent.json records the role and instruction sources read.

sft.jsonl contains only prompt and completion. Its expanded system message is byte-identical to the frozen sft-100-v1 baseline. Only the final assistant completion is a training target. review.jsonl is line-aligned and provides the full context, final target, word-choice reasoning, and explicit lexical evidence for every target and historical assistant word. Review metadata must not be fed to normal SFT.

The final child inputs comprise exactly 20 short inputs (1–5 whitespace-separated words), 20 medium inputs (6–15), and 10 long inputs (16+). Exactly 16 records require earlier context. Assistant sentences contain at most 12 words; targets contain at most one question. The generator checked lexical evidence coverage, exact-list claims, unique new targets, absence of exact target duplication against baseline and prior batches 002–004, schema alignment, and the identical expanded system profile. These checks are not independent phonics verification.

The accepted batch 004 and its audit informed this batch: final turns in the 16 contextual cases refer to prior choices, numbers, places, objects, or plans without independently supplying the full answer. Lexical selection remains the training objective; familiar meanings and relevant, natural replies were also considered.

Child input vocabulary is unrestricted. The generator did not open held-out test data or test archives. Baseline and accepted batch 004 files were preserved. build_candidates.py is the original authoring source; do not rerun it over independent audit corrections without incorporating those corrections first.
