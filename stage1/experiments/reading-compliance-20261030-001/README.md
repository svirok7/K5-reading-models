# Reading compliance and meaning experiment

This is a sealed partial preparation, not a completed experiment. Colab refused a T4 connection with “You cannot currently connect to a GPU due to usage limits in Colab.” No new training, raw-response comparison, or adoption evidence exists. The configured GPT-6.1 Sol/high author and reviewer also hit an account usage limit. Of 300 planned new examples, 250 are saved and 150 independently approved. Batch 4 has one unresolved grounding issue, batch 5 needs linguistic/semantic review, and batch 6 is not authored. Original-corpus fixes are not materialized into a successor. The 600-example dataset has not been exported or approved. The live UI adapter remains the reference. See access-blocker.json and status.json for exact current state.

The frozen development set has34 cases:16 single-turn and18 fixed-history next turns. It derives only from the existing 20 development cases and 25 saved SFT UI records. Seven full prompt/history duplicates and four close training overlaps are excluded with evidence in frozen/. The overlapping historical 13-case replay is retained at its original location for context, never added to the denominator. Held-out test/archive contents were not read.

Fresh runs use Qwen/Qwen3-1.7B revision 70d244cc86ccca08cf5af4e1e306ecf908b1ad5e, no thinking, full profileB, LoRA all-linear rank 16 / alpha 32 / dropout 0.05, LR 1e-4, seed 42, microbatch 1 / accumulation 8, linear decay across three epochs. The unchanged 300-row run has 114 updates / 900 row exposures; the expanded 600-row run has 225 updates / 1800 exposures. Each saves a retained checkpoint and full resume state per epoch. The fresh epoch-one schedule differs from historical one-epoch training, so differences cannot be attributed solely to epoch count. Expanded data also increases optimization exposure; it is not a pure size ablation.

Inference is fixed to a single Colab T4 / FP16 for both comparator and candidates, with the same pinned tokenizer/template, temperature 0.7 / top-p 0.8 / top-k 20 / max 128 new tokens. Per-case seeds are frozen; no historical response is reused because the required full metadata does not match. The runner returns raw responses without rewriting or inference checks. The first fresh generation is the current adapter; no new base-model run is planned.

## Files and execution

- plan.json: immutable model/data/code/prompt/adapter/environment bindings. This partial plan includes only same300; expanded600 is explicitly blocked.
- reading_compliance_colab.ipynb and reading-compliance-colab.zip: executable notebook and sealed upload kit for the approved unchanged-data run only. The expanded-data run and adoption decision are blocked. delivery.json binds both.
- execute.py: the sealed plan’s approved bounded runs with smoke and 15% operational headroom gates; no automatic precision/hardware changes. Logs diagnostics and stops on failures.
- evaluate.py: verify frozen inputs, generate raw replies, conceal labels and score paired results after independent review.
- repeat_seeds.py: conditionally generate and blind only the qualifying selected/current checkpoint pair at two extra seed offsets.
- choose_checkpoint.py: joint-success selection and extra-seed adoption gate.
- plot_results.py: real update-loss plots and paired gain/regression excerpts after generation/review.
- code-review.md and delivery-code-review.md: independent implementation review with limits; audit/ contains independent linguistic/semantic data review.

Upload the new notebook to Colab and select the existing free T4. Upload only the sealed ZIP when requested, or use the Files sidebar. Its hash is embedded in the notebook. The code uses the historical adapter already in Drive at `MyDrive/Reading-Model/sft/qwen-sft300-v2-lora-allocator-20261030-008/full/adapter`, and writes a fresh experiment folder. All dependencies come from the existing pinned registry workflow; no purchase is allowed. If interrupted, set ONLY to the matching experiment name and RESUME to its exact latest complete epoch checkpoint. Completed runs are never continued from or overwritten.

The sealed partial notebook may generate same300 checkpoint evidence when GPU access returns. It must not yield an adoption decision until the expanded-data experiment also completes. Keep the sealed preparation unchanged; produce a new version after the missing authoring and independent review finish.

After generation, supply only `blind-review/review.jsonl`, full reading prompt/rubric, and REVIEW_PROTOCOL.md to the independent reviewing agent. Conceal identity-key.json and all checkpoint/run paths until ratings are sealed. Save one rating per opaque review ID. Use these commands with paths in your extracted kit and Drive output:

```sh
python evaluate.py summarize --review-dir OUTPUT/blind-review --ratings RATINGS.jsonl --reference-label current --out OUTPUT/primary-summary.json
python plot_results.py pairs --review OUTPUT/blind-review --summary OUTPUT/primary-summary.json --out OUTPUT/paired-examples.md
python choose_checkpoint.py --summary OUTPUT/primary-summary.json --metadata CHECKPOINT-METADATA.json --out OUTPUT/primary-decision.json
```

For the completed two-run study, CHECKPOINT-METADATA.json maps all six labels to explicit epoch/update counts, e.g. `{"same300-epoch1":{"epoch":1,"updates":38},...}`. Expanded epochs have 75 / 150 / 225 updates. Selection maximizes joint successes, then earlier epoch; equal epochs across datasets prefer fewer updates, then stable label. Keep16 single-turn and18 fixed-history results visible separately. Serious safety/identity failures are individually recorded and cannot be compensated for by reading scores.

Run `python repeat_seeds.py --output OUTPUT --current-adapter CURRENT_ADAPTER --primary-summary OUTPUT/primary-summary.json --primary-decision OUTPUT/primary-decision.json` only when primary-decision.json says pending_repeat_seeds. It enforces that gate before generating.

A ≥20 percentage point primary joint gain with no new serious paired failures triggers two additional generation offsets 1000003 and 2000003. Generate only current and selected checkpoint on the same frozen cases, with identical inference hardware/precision/environment; then blind and summarize each seed separately. Each repeat must have strictly positive gain and no new serious paired failures. Pass both repeat summaries to choose_checkpoint.py with `--repeats REPEAT1.json REPEAT2.json`. Repeated seeds are not independent cases. No automatic UI replacement occurs, even after a passing recommendation.

When no checkpoint qualifies, retain the current reference. Use observed failure types to recommend the next bounded investment in data, model capacity, or rank/preference training; do not launch it automatically. During the current GPU block there is no new evidence to choose among these investments.

## Local checks

From stage1, run `.venv/bin/python -m unittest discover -s . -p test_sft_train.py -v`, then `.venv/bin/python -m unittest discover -s experiments/reading-compliance-20261030-001 -p 'test_*.py' -v`. Tests use mechanical fixtures and tiny CPU models, not a new development set. GPU-scale masking, numerical gradients, reload and operational headroom still require the actual notebook smoke gate. Human data/quality review remains pending.

The current draft and exact hash-matched review states are in authoring-progress.json. Run validate_authoring.py --require-complete before any successor export; it currently rejects the incomplete corpus. Missing word evidence in batch 5 is recorded explicitly. Structural checks never stand in for the independent semantic audit. Resume authoring with the requested GPT-6.1 Sol/high workers after their usage limit resets; allow at most three correction rounds per batch.
