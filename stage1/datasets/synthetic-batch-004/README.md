# Synthetic batch 004: candidates pending independent audit

50 original candidates, pilot-101 through pilot-150, authored by the SFT generator agent using gpt-6.1-sol with high reasoning effort. No independent audit or human approval is claimed. generator-agent.json records the generator role and instruction sources read.

sft.jsonl contains only prompt and completion. Its expanded system message is byte-identical to the frozen sft-100-v1 baseline; only the final assistant completion is a training target. review.jsonl is line-aligned and includes the final target, full context, word-choice reasoning, and lexical evidence for every target and historical assistant word. Review metadata must not be fed to normal SFT.

The final child inputs comprise exactly 20 short inputs (1–5 whitespace-separated words), 20 medium inputs (6–15), and 10 long inputs (16+). Exactly 16 records have historical assistant context. All assistant sentences contain at most 12 words; targets contain at most one question. The generator checked lexical evidence coverage and exact-list claims, unique new targets, absence of exact target duplication against the frozen baseline and existing batches 002 and 003, schema alignment, and the identical expanded system profile. These checks do not constitute independent phonics verification.

Child input vocabulary is unrestricted. The generator did not open held-out test data or test archives. Baseline files were preserved. build_candidates.py is the original authoring source; do not rerun it over independent audit corrections without incorporating those corrections first.
