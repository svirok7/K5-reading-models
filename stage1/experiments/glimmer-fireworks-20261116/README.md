# Muse Glimmer SFT experiment

User scope: fine-tune Meta Muse Glimmer 30B on the exact existing `sft-600-v1` dataset, then evaluate through Reading Lab's existing testing UI, reading rubric and manual decisions. No new benchmark set. Use Sol agents. Total additional provider spend must be $0.

## Monitoring

- Local progress: http://localhost:8766/
- Existing testing UI: http://127.0.0.1:8765/
- Fireworks training: https://app.fireworks.ai/dashboard/fine-tuning

`STATUS.md` and each component report record preparation and execution separately. A successful local check is not a completed training run.

## Components

- `data/`: lossless conversion of all 600 approved examples and actual tokenizer/loss-mask proofs. Historical assistant replies remain context only.
- `training/`: pinned official Fireworks serverless SFT recipe, three-epoch rank-16 LoRA, checkpoints and resume. No generation-based evaluation, sampling or dedicated resources.
- `evaluation/`: read-only export of existing UI records and offline replay plans; no new prompts and no billable execution.
- Reading Lab: Fireworks model/deployment support plus a default $0 guard that blocks API inference and the OpenAI evaluator before any outbound call. Local models and manual reading decisions remain available.

The logged-in Fireworks create-run page explicitly advertises free serverless Muse Glimmer SFT through November 30, 2026. Inference and dedicated training are separately billed. Free training does not establish a free route to evaluating the tuned model; serving must be resolved within the $0 constraint before generating Glimmer evaluation replies.

## Credentials

The existing ignored project `.env` supplies `FIREWORKS_API_KEY`. Credentials must never appear in reports, browser URLs, source files or logs.
