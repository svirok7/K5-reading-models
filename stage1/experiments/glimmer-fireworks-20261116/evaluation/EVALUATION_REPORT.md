# Existing testing UI evaluation — preparation only

The user's revised scope uses the existing testing UI and its saved conversations, reading evaluator, and manual decisions. A subsequent hard limit requires **$0 spend**. No fresh benchmark, independent joint-quality rubric, new 34-case evaluation, paid judge run, or Glimmer generation was performed. The briefly drafted fresh inputs and their authoring script were deleted before use. Existing held-out and archived test contents were not inspected.

The four intended model conditions remain Qwen3-1.7B base, the deployed Qwen 600-example/three-epoch adapter, Glimmer base, and a future Glimmer SFT artifact. Glimmer results are pending. Existing UI results do not establish a four-way controlled comparison.

## Current evidence

`existing-ui-baseline/` is a read-only SQLite export of **151 active UI records**, including original histories, responses, model metadata, saved prompt/rubric snapshots, evaluator decisions, and manual decision history. It contains 146 existing evaluator ratings and 142 existing manual decisions. No archived record bodies were loaded into Python. Exporting did not call a model, evaluator, or provider API and did not modify the UI database.

The export manifest SHA256 is `5779ee65a6da973d56df6684a42ab39cb809200471e239b34b0d2d60647cb565`. Its file hashes bind the raw records and summary. The snapshot is historical evidence; later UI decisions require a new export directory.

The exact deployed Qwen 600/three-epoch UI group has:

| Existing UI measure | Value |
|---|---:|
| Saved responses | 46 |
| Unique exact prompt/rubric/history inputs | 44 |
| Effective acceptable decisions | 35 |
| Effective not acceptable decisions | 9 |
| Pending decisions | 2 |
| Existing evaluator ratings | 44 |
| Existing manual decisions | 43 |
| Completed response latency p50 / p95 | 3.21 / 4.72 seconds |

These are descriptive counts using `records.effective()` and `records.summaries()` unchanged. Manual decisions take precedence over evaluator verdicts, while evaluator score means remain the original evaluator scores. The acceptance fraction is 35/44 decided responses; the two pending responses are not counted as failures or successes. Repeated histories are not independent new inputs.

That adapter's saved UI artifact hash is `bfe9b369c6605a8814fe36933680244fd9da7016ce738806fa0033f97f35ce38`; the adapter path identifies `qwen-sft600-v1-epoch3-20261101/adapter`. This UI artifact hash is different in meaning from the old training resume-record SHA256. The older 300-example adapter has a separate UI group (25 records) and is never pooled with the deployed 600-example adapter. Qwen base Prompt B records span three different saved configuration groups. Different model/settings, prompt hashes, and rubric hashes remain separate as in the UI.

`existing-qwen600-fireworks-offline-plan.jsonl` contains **44 deduplicated existing UI histories**, sourced from those 46 deployed-Qwen records. Each plan row binds source record IDs, exact history/prompt/rubric hash, and the export manifest hash. It is an offline convenience file, with `execution_permitted=false` and `spend_limit_usd=0`; it has no model outputs. Plan SHA256: `a27d06c0ae39821ced02e8d9552e89e71c033eb85b844876fccd7387bff710b1`.

## Same UI procedure

1. Open the existing Reading Model UI and Review results. Existing judgments remain available without any API request.
2. Keep the same prompt condition and exact saved history when comparing a response. Use saved model metadata to distinguish base, 300-example SFT, and deployed 600-example SFT records. The offline plan identifies reusable 600-example histories; it does not generate them or add development cases.
3. Apply the existing reading rubric: word types, length, and rhythm, each 0–4. A rubric pass requires all three at least 3. The reader profile is unchanged: end of AAR Level 1 plus the explicit cumulative Dolch list through first grade. The child's spoken vocabulary does not expand the allowed response vocabulary.
4. In $0 mode, inspect the response and save the normal UI Acceptable/Not acceptable manual decision, optionally with a reason. A manual override continues to take precedence. No new semantic, truthfulness, safety, or joint-success score is introduced by this preparation.
5. Refresh/export the UI's saved results. Preserve raw responses, generation status, prompt/rubric snapshots, metadata, and manual history. Report exact shared-input coverage before calling any comparison paired. Existing natural conversations have different histories and repeat counts; raw acceptance-rate differences are not controlled model improvements.

`evaluator.py` is unchanged and remains the standard reading-only judge. It is an uncalibrated model judge, not a human assessment. It deliberately excludes generator identity and latency from judge input, and evaluates the final visible companion text. No alternate blinded-review pipeline was added. Saved evaluator ratings remain historical evidence, but running that evaluator now would spend OpenAI credit and is blocked.

## $0 enforcement

`server.py` defaults to `ZERO_COST_MODE=True`. Under that default:

- `/api/chat` rejects OpenAI, Claude, and Fireworks before constructing a provider engine or making an outbound call.
- `/api/evaluate` rejects before accessing the requested record or calling the paid OpenAI judge.
- Local Qwen/Sarvam inference and existing manual review remain available.
- `/api/config` exposes `zero_cost_mode`; the UI displays the constraint, disables API Send, skips automatic evaluation after local generation, and provides manual reading review controls without a Retry button for the paid judge.

Only an explicit future server launch with `READING_MODEL_ALLOW_PAID_APIS=1` changes that default. It is not enabled by this work, by a saved API key, or by selecting a model. Preparing API settings does not call the provider. No deployment or inference request was used for verification.

`ui_evaluation.py` has only `export` and `plan` commands. It contains no HTTP client, generation command, or evaluator invocation. `export` opens the database using SQLite `mode=ro` and `PRAGMA query_only=ON`, excluding archived rows in SQL. Existing directories/files are never overwritten. `plan` accepts only existing exported inputs and registered UI model keys, checks that the saved prompt/rubric still match the current UI, and deduplicates exact histories.

Example offline commands, from this evaluation directory:

```sh
python3 ui_evaluation.py export --backend qwen --adapter present \
  --adapter-hash bfe9b369c6605a8814fe36933680244fd9da7016ce738806fa0033f97f35ce38 \
  --condition B --rubric-version 1.5 --out qwen600-ui-export

python3 ui_evaluation.py plan --source qwen600-ui-export \
  --manifest-sha SHA256_PRINTED_BY_EXPORT --model fireworks \
  --out existing-history-offline-plan.jsonl
```

These commands perform no inference. Provider token usage and cost are not inferred from character counts or historical local Qwen latencies. No new Glimmer latency, token, cost-per-response, or quality result is available.

## Verification and integration review

- Six helper tests pass: read-only export/archive exclusion, standard UI manual precedence, repeat/overlap accounting, immutable snapshots, existing-history-only offline plans, and changed rubric rejection. All inputs are temporary mechanical fixtures, not evaluation cases.
- Four $0 guard tests pass: each paid backend blocked before construction/outbound, paid judge blocked before record access/outbound, local generation plus manual decisions work, and the future explicit opt-in path retains the original evaluator behavior under mocks.
- Three Fireworks transport tests pass using mocked responses only. The review corrected whitespace-only output being labeled completed and retained final text separately from provider reasoning, raw provider JSON, usage, model ID, request ID, finish status, and latency.
- The integration review corrected Fireworks model-field synchronization when changing the API dropdown and preserving the entered Fireworks model while forgetting a key. No key is written to export metadata.
- `node --check ui/app.js` and Python compilation pass. No API/model request or deployment was made by these tests.

The historical completed `reading-compliance-20261031-002` evaluation logic and primary/final reports were read to understand provenance and the selected adapter. Its independent joint-quality selection procedure and 34-case results are not reused as this UI evaluation's protocol or Glimmer evidence.
