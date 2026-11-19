# Muse Glimmer SFT experiment — 2026-11-16

Status: free serverless SFT is attached and loading the verified dataset. Current session `accounts/svirok123/trainingSessions/ts-512a9f5c54024e0a8a053da25e600dcb`, run `run-377e9d98791149d29d1ad8dfafc164a2`. No inference calls or dedicated deployments are configured. All96 locked dependencies and local recipe Config/import checks passed.

## Authorized zero-dollar run

Training budget is exactly **$0**. The user subsequently authorized a separate narrowly bounded inference/evaluation run for less than$5 total; the evaluation runner owns that budget. Only the advertised free Muse Glimmer serverless LoRA SFT will run. All inference, generation evaluation, automatic holdout, loss evaluation calls, dedicated training, and dedicated deployments are disabled. There is no paid fallback switch. The same existing testing UI will be used later, through separately budgeted Training API sampling.

[Official pricing](https://fireworks.ai/pricing) and [compatible models](https://docs.fireworks.ai/fine-tuning/models) advertise free Muse Glimmer SFT through November 30, 2026 without a credit card. Root verified the same free Training API offer on the logged-in account's fine-tuning creation page. Read-only account GET authenticated the single-account key for `accounts/svirok123`; key values never appeared in logs or reports.

The [official Muse cookbook](https://docs.fireworks.ai/fine-tuning/training-api/cookbook/muse-glimmer.md) explicitly defines the deadline as jobs started before `2026-12-01T00:00:00-08:00` (08:00 UTC). In-session sampling is billed separately, so this experiment deliberately uses `sft_loop` directly with no sampling.

## Configuration and reproducibility

- Base: `accounts/fireworks/models/muse-glimmer-30b`.
- Tokenizer: `meta-models/Muse-Glimmer-30B` revision `a4e59da52a7bc87ae7251dd5545c0dd437c44b68`; renderer `muse_glimmer`.
- All 600 original examples, final assistant completion only: `train_on_what="last_assistant_message"` (the upstream default would include previous assistant turns).
- LoRA rank 16, alpha 32, 3 epochs, batch 16, 114 expected optimizer steps (38 per epoch including the final 8-row batch).
- Learning rate `5e-5`, 6-step linear warmup then constant; Adam beta2 0.999, weight decay 0.01, clip norm 1.0. The rate is the lower end of Fireworks' documented SFT range (5e-5 to1.5e-4), conservative for three passes over 600 short-response tutoring examples.
- Maximum length 8192; no input truncation or row dropping allowed by preflight. Actual mask report must certify all rows fit.
- Resumable checkpoint every10 steps plus final checkpoint; local cursor preserved in `run/dataloader.json`. One operation pair in flight simplifies checkpoint recovery.
- No W&B export or automatic evaluation split. Final adapter promotion creates a model artifact without an inference deployment.

[Managed SFT/DPO no longer accepts new jobs after November9](https://docs.fireworks.ai/fine-tuning/migrate-from-managed-training). This uses `serverless=True` in the supported Training API recipe.

Official cookbook pinned to `74e103ab4249d508912ccf264793e655980eead0` (package2026.11.13.1). `sources.json` records SHA256 of the recipe, pyproject, complete `uv.lock`, checkpoint implementation, and serverless implementation. `bootstrap.sh` installs the full frozen official lock into ignored `.venv/`. Ignored `vendor/` contains the source checkout; the two critical upstream source files are also retained in `source-snapshot/`.

## Commands

Run from this `training/` directory:

```sh
./bootstrap.sh
.venv/bin/python train.py plan
.venv/bin/python train.py account-check
.venv/bin/python train.py preflight
.venv/bin/python train.py launch
.venv/bin/python train.py status
.venv/bin/python train.py resume
```

`launch` requires the validated dataset hash, all600 zero-context-loss mask proofs, matching tokenizer revision, pinned source integrity, a valid single-account authentication record, and an active promotional window. It rejects duplicate fresh launches. `resume` uses the newest committed cursor checkpoint and the logged account/run identifier; an explicit `--checkpoint ACCOUNT/run-HEX/step-N` is also accepted. Keep the host awake and preserve this directory: the Python process drives training remotely.

## Validation so far

Five local launch-safety tests pass: rejecting paid/dedicated/sampling settings; stale dataset hashes; wrong tokenizer revisions; any context-loss positions, drops, or truncation; promotion deadline correctness; pinned source integrity; and preventing credential values in plan output. Actual tokenizer/data mask verification passed all600 examples, matching the pinned Hugging Face template exactly:1727–1879 tokens each,1,059,725 sequence tokens and9,104 supervised final-output tokens per epoch, zero context-loss positions, zero splits/drops/truncations. The trained final output includes the native assistant routing delimiters plus exact completion content and end-of-turn token.

## Serving and export

No paid inference has been requested. Public training-API rates for sampling Muse Glimmer are $1.96/1M prefill, $0.39/1M cached prefill, and $4.88/1M sampled tokens. These calls are disabled. Dedicated GPU list prices start at $8/hour for H100/H200, $13/hour forB200; no shape or GPU count is assumed and no deployment will be created under this budget. [Pricing](https://fireworks.ai/pricing).

A possible zero-platform-cost route is to download the adapter using `firectl model download`, then use the matching base locally. Fireworks warns the base must match its exact vendor checkpoint; equivalence to public HF weights must be confirmed. [Export documentation](https://docs.fireworks.ai/fine-tuning/deploying-loras.md#downloading-model-weights).

Meta publishes a16.8GB Q4_K_M GGUF and documents llama.cpp build b10353 or newer with Apple Metal support. This establishes local base-model feasibility, not proven compatibility of this future trained adapter with that quantization. Adapter conversion or BF16 merge followed by quantization still needs validation. This Mac is arm64 with56GiB free disk; this Mac has16GiB unified RAM. The16.8GB quantized base already exceeds physical RAM before KV cache, so local inference is likely to swap heavily and is not a practical immediate fallback. No large base-model weights have been downloaded. [Official GGUF model card](https://huggingface.co/meta-models/Muse-Glimmer-30B-GGUF).

## Network recovery

The first attempt created a remote adapter but stalled before loading data because Python preferred unreachable IPv6 routes for api.fireworks.ai. A host-specific IPv4 resolver fixed the read-only SDK metadata request (HTTP200 in0.5seconds) while preserving TLS verification. A retry exposed the account's actual single concurrent-run limit. Both unused zero-step sessions were explicitly deleted (HTTP200), and the occupied session was confirmed EXPIRED before the clean current run launched. Prior attempt logs and bindings are preserved under `attempts/`; cleanup responses are in `session-cleanup.json`. No forward/backward, optimizer, or inference calls occurred in those attempts.

## Continued execution

Coordinator fixed the missing pinned processor configuration and reran all600 actual production renderer proofs and full recipe preflight. The local preflight originally assumed a list return; it now correctly checks the recipe single Datum result. The failed missing-processor session was deleted with HTTP200 and archived under attempts/missing-processor-zero-step.

Current run: run-472bd65f3b79447e93f3bb80605c91f1; session ts-f47aadaccb304ec7ba2bed2263687331. Optimizer steps1 and2 completed with finite losses1.55997 and1.42845.114steps total are planned. Training is ongoing, not completed. Provider inference and judge spend remains$0. User now permits inference/evaluation below$5; no dedicated deployment has been created.

## Recovery after expired session

Provider GET reports EXPIRED/DEADLINE_EXCEEDED: training session expired after10m without active runs. Remote list confirms MANAGED_DURABLE step50 despite local save future failing. Restored step50 cursor792 from exact batch/epoch math, corroborated by792 preserved render records. Local preflight compares all600 complete token and loss-weight hashes against the original proof. Renderer date is pinned to2026-11-16; render_workers0 prevents spawned workers losing the override. Five launch safety tests pass. New free run run-c703375d1ac146598306ab68b612c3e9 is restoring the checkpoint. Full evidence is in cursor-recovery.json and recovery-inspection.json.

## Keepalive transport correction

The next resume stopped after52steps with repeated async heartbeat timeouts and an unloaded adapter. The text-only IPv4 workaround did not cover byte hostnames; corrected handling is now tested. More decisively, active heartbeat POST timed out with async HTTPX but curl returned HTTP200 in0.49s. The SDK heartbeat coroutine now uses that tested curl transport every10seconds, retaining TLS verification and keeping credentials out of command-line args. Heartbeat results are recorded without secrets in run/heartbeat.json. Seven tests pass.

New run run-4b603d583d83427fa832495d3974576c, session ts-1d40ac90c5c749c1a282ca89cb697a82, restored original step50 in24seconds. Repeated live heartbeats succeed. Training remains free; inference spend0.
