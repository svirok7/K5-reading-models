# Qwen SFT v1 development comparison

Prepared locally on 2026-10-30. No model generation, GPU evaluation, evaluator request, paid call, training, held-out access, or Reading Lab database mutation was performed by this preparation.

## Frozen baseline reference

`baseline-reference/manifest.json` SHA-256:

```
9215dc370204863e1ff58383d6e6083e709a883af54e74f80f9d7a54c82b89b6
```

Absolute reference: `/Users/viroksharma/Desktop/Personal/Projects for Fun/Reading-Model/stage1/evaluation-sft-v1/baseline-reference/manifest.json`.

This is a logical snapshot of all 16 saved Qwen base-model records from Reading Lab's `runs/conversation-results.sqlite3`, read through SQLite `mode=ro`, `PRAGMA query_only=ON`, and one transaction. Other models' records were not exported. Each original JSON body is preserved verbatim inside `source-bodies.jsonl`; `baseline-records.jsonl` preserves the complete parsed records, including responses, prompts, histories, rubric/profile snapshots, evaluator judgments/metadata, manual decisions, and edit histories. Original body hashes and all four snapshot file hashes are bound by the manifest. Files are read-only; the exporter refuses an existing output directory. The manifest hash above anchors the reference independently of its own file map.

`groups.json` keeps model metadata, prompt condition/hash, rubric hash/version, and archive state separate. The expanded reader profile is extracted from each saved rubric, not reconstructed from today's editable files. `development-inputs.jsonl` contains 13 no-thinking final-turn requests; final saved responses and scorer notes are excluded from generation inputs. Required earlier assistant turns remain in fixed histories.

| Saved template/settings group | Condition | Records | Saved evaluator verdicts | Saved manual decisions |
| --- | --- | ---: | ---: | ---: |
| v1, no thinking, 128 tokens, temp 0.7 / top-p 0.8 / top-k 20 | A | 1 | 0 | 0 |
| v1, no thinking, same decoding | B | 11 | 11 not acceptable | 11 not acceptable |
| v2, thinking, 2048 tokens, temp 0.6 / top-p 0.95 / top-k 20 | B | 3 | 2 not acceptable | 1 not acceptable |
| v3, no thinking, 128 tokens, temp 0.7 / top-p 0.8 / top-k 20 | B | 1 | 0 | 0 |

All 16 explicitly record `Qwen/Qwen3-1.7B`, revision `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`, MPS float16 inference, no adapter, and rubric v1.5/hash `d889cbab30562a67eb42e50f876fec3fc5f5280673f053d624d5460a8d711576`. Thus revision and inference precision are known for this baseline. Saved RNG seeds, dependencies, tokenizer artifact hashes, exact tokenized inputs, and historical encoder implementations are unknown. The template label alone cannot establish v1/v3 equivalence. Do not pool thinking-enabled v2 with no-thinking results. One v2 output was incomplete.

The sole current-template record is `d874e7c6-083c-4dc4-b7fa-8d603e0afdd0`. Its saved response can be reused as a small, explicitly limited comparison if revision/device/precision/decoding match. One unscored casual greeting does not establish an acceptance rate or general improvement. A fresh base control is necessary if using legacy v1 inputs under today's encoder, changing hardware/precision, or requiring seeded matched generations. Preserve all saved responses when adding that control.

The local snapshot and generated results are Git-ignored because they contain conversation data. Do not include them in training kits or publish them. Scripts and this procedure are separate, reviewable files.

## Verify and choose the comparison before generation

Run commands from `stage1`:

```sh
python3 evaluation-sft-v1/prepare_reference.py --verify evaluation-sft-v1/baseline-reference
python3 evaluation-sft-v1/replay_development.py
python3 evaluation-sft-v1/replay_development.py --selection all-no-thinking
```

These commands verify integrity and print plans without loading a model or importing model dependencies. The default selection is the one current-template case. `all-no-thinking` selects the 13 original prompts/histories while applying the current v3 encoder; use a fresh matched control for this selection. Retain the original A/B and rubric groups even when using the same new inference configuration. Multi-turn histories are fixed context and contain base-model answers; this is not a test of a self-generated SFT conversation. Multiple turns from the same conversation are correlated.

Before running an adapter, retain its completed `run-record.json`, pinned base revision, approved dataset/template hashes, final weight hashes, training mode, smoke report, and successful reload evidence. The replay script verifies model/revision/status/no-thinking and every adapter artifact hash in that record, and verifies the training template against the pinned inference tokenizer. It refuses a changed reference or existing output directory. No synthetic adapter or success result should be created while training remains incomplete.

## Generate only after the actual adapter exists

The following are templates, not executed commands. Replace the two absolute adapter/run-record placeholders with verified real export paths. A fresh result directory is required each time. The current local baseline used MPS float16; if running on CUDA or CPU, explicitly pass identical device/precision options to both runs and report that the comparator is a new control.

For a matched 13-input development experiment (necessary for the legacy v1 inputs):

```sh
python3 evaluation-sft-v1/replay_development.py --selection all-no-thinking --device mps --precision float16 --run --out evaluation-sft-v1/results/matched-base-001
python3 evaluation-sft-v1/replay_development.py --selection all-no-thinking --device mps --precision float16 --adapter /ABSOLUTE/REAL/EXPORT/adapter --run-record /ABSOLUTE/REAL/EXPORT/run-record.json --run --out evaluation-sft-v1/results/sft-001
python3 evaluation-sft-v1/compare_development.py --base evaluation-sft-v1/results/matched-base-001 --sft evaluation-sft-v1/results/sft-001 --out evaluation-sft-v1/results/comparison-001
```

For the sole current-template saved response, run the adapter with `--selection current-only` (the default), then omit `--base` when preparing its comparison. The script refuses legacy, device, precision, revision, or decoding mismatches. Even an accepted saved-baseline comparison retains the missing-seed/dependency/tokenizer limitations. Add a fresh control only to resolve a concrete mismatch or stochastic comparability need; do not rerun old baselines merely to complete a checklist.

`--run` is the explicit generation gate; it may download pinned public weights, but never calls an API evaluator. The runner uses ordinary nonquantized pinned base weights for both variants, independent of the training mode, with identical saved system prompts/histories and generation settings. It resets a reproducible per-case seed for each variant, runs an identical excluded warm-up, and records template/rendered-input/token hashes, effective generation configuration, parameter dtypes, software/hardware, output token IDs, truncation and latency. It never substitutes adapter responses into another case's context. Floating-point behavior can remain nondeterministic despite equal seeds. Any failure is saved and raised; there is no silent retry/resume or precision fallback. Preserve partial outputs and choose a fresh run directory after resolving it.

## Blind manual review and reporting

`compare_development.py` verifies complete hashed runs and matching settings/input hashes before creating `review.jsonl`, a separate `identity-key.json`, and a comparison manifest. Keep the key closed while scoring; the deterministic label order hides labels but is not proof that a reviewer cannot infer identity. Review against the exact saved group rubric/profile in `baseline-reference/groups.json`.

Copy `review.jsonl` to a new `ratings.jsonl`. For each X/Y response, fill `scores.word_types`, `scores.length`, and `scores.rhythm` as integers 0–4; use null for unscored fields. Every word must be eligible for `word_types >= 3`; identify unsupported words and exact spelling patterns in `unsupported_words` and `evidence`. Accept reading only when all three scores are at least 3, unless a human supplies `manual_decision` plus evidence. Record meaningful, relevant, accurate answers separately with `meaningful: true/false`, judging the final child's request and fixed history. A generic easy response that ignores the request fails meaningfulness. Note repetition, awkward rhythm, lost information, safety failures, and other regressions in `repetition_or_regression`. Do not change response texts, IDs, groups, or histories.

```sh
python3 evaluation-sft-v1/compare_development.py --comparison evaluation-sft-v1/results/comparison-001 --ratings evaluation-sft-v1/results/comparison-001/ratings.jsonl > evaluation-sft-v1/results/comparison-001/report.json
```

The report retains configuration/history groups, response and scored counts, reading decisions, three score means with denominators, separate meaningfulness, fail-to-pass and pass-to-fail paired counts, and every paired response/evidence. Generation manifests report errors/truncations and completed latency p50/p95 by group; blank ratings remain unscored. For the written conclusion show both improved and regressed pairs, eligible-word results, meaning/relevance, length/rhythm/repetition, and sampling/precision/template limitations. No numerical improvement target was set in advance. Training loss is not quality evidence. Existing model-judge ratings are uncalibrated and preserved as historical annotations; the scripts do not call them or overwrite them. Any new paid evaluator batch requires explicit authorization and an independently saved rubric/settings group.

## Reading Lab integration once the adapter exists

1. Preserve the existing `qwen` base option and this snapshot. Validate the real adapter's PEFT base ID, pinned revision, tokenizer/template, weight hashes, and full run record; complete reload inference first.
2. Set only the existing `qwen_sft.adapter` entry in `models.json` to the verified absolute local adapter path; its backend stays `qwen`. Mark its pending flag false after verification. Do not point Sarvam SFT to a Qwen adapter.
3. The coordinator updated `QwenEngine.base_revision` to the experiment's pinned revision for model and tokenizer loading; Qwen adapters with a different or missing revision are rejected. Mocked offline checks verify both loader revision arguments, recorded revision, and mismatch rejection. GPU/local real adapter inference remains a separate required check. Registry revision fields are not used to select a different revision. Record matching precision/device/template/decoding metadata for any comparison.
4. The live UI automatically requests evaluator judgments after responses. Use this standalone replay workflow for the comparison unless paid judging is authorized or UI auto-evaluation is explicitly disabled. Selecting an SFT label is not evidence a trained adapter exists.
5. Test that switching between base/SFT starts fresh conversations, reloads the actual selected model/adapter, records distinct adapter hashes, and leaves all saved baseline rows intact. Preserve the unmerged base; no model-registry or engine edits were made by this preparation.

Keep all held-out material untouched until the checkpoint, prompts, decoding, rubric and human review/evaluator calibration procedure are fixed. No held-out examples or contents were read or copied into these artifacts. Any eventual held-out run is separate from this development procedure.
