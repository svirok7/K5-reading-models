# Baseline protocol v2 — 50-case benchmark

## Active test set
Exactly 50 cases in data/test.jsonl: 10 natural conversations, 10 complex spoken inputs, 10 word-eligibility boundaries, 10 explanations/stories, 10 fixed-context conversations. Only the final response is generated and scored per case. For the 10 fixed-context cases, each model receives identical scripted history. This measures use of context, not an entire self-generated dialogue. Reset between cases. Report single-turn and fixed-context results separately.

Former test cases are preserved in data/archive as historical development/reference material. They are not loaded by the runner or counted in the active benchmark. Existing 20 development cases remain for tuning and smoke checks. Do not train on, copy demonstrations from, or tune against the new test set. The test file is frozen by SHA-256 in data/benchmark-v2-manifest.json; the runner verifies it before loading models. Freeze training/checkpoints, prompt choices, and evaluator settings on development material before the final comparison. If test results influence subsequent tuning, label later results exploratory rather than fresh held-out evidence.

## Comparison
Use the same 50 cases for every model and training stage. A and B each produce 50 responses (100 outputs per model, still 50 distinct cases). Freeze decoding options and output limits as far as provider support allows. Keep provider/hardware differences explicit. The runner requires --frozen for test runs and records case/prompt/profile/model fingerprints. Use a new output directory after configuration changes; resume only identical runs. Never send expected_behavior or meaningful_answer_check to the companion. These are scorer-only notes.

## Reading and meaningfulness
Use rubric v1.5: word_types, length, rhythm scored 0–4; acceptable requires all three >=3. Manual decisions override evaluator decisions. Record factual or irrelevant answers under a separate manual answered-meaningfully yes/no field using each case's check. A generic easy response that ignores the request fails this check even if reading scores pass. Do not fold it into the reading-only judge.

Calibrate the evaluator on development examples with human labels before accepting final benchmark scores; calibration is not yet complete. Check both allowed-but-irregular words and decodable words absent from the list, alongside genuinely unsupported spellings. Do not use final test response pairs as calibration or preference-training data.

Report reading acceptance rate, three score means, meaningful-answer rate, response count, errors/truncations, and companion latency p50/p95. Blank ratings are unscored, not zero. Compare each case with its baseline to show improvements AND regressions; report counts of fail→pass and pass→fail. Keep independent and fixed-context results separate and do not pool different rubric versions. Fifty cases support an initial experiment, not a production-quality claim.

## Review and persistence
Import generated JSONL into Review results > Colab results. Score before revealing identities. The meaningful-answer choice is exported with reviews. Export manual reviews before closing the browser. Keep raw results unchanged. Live chat results remain separately persisted in SQLite with prompt/rubric snapshots, evaluator scores, manual decisions, and latency.

No new benchmark runs or evaluator calibration have been completed merely by creating this set. Run development checks first, then use run_baseline.py --split test --frozen with a fresh output directory once settings are fixed.
