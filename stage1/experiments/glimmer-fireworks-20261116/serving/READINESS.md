# Muse Glimmer checkpoint evaluation worker

Verified 2026-11-18. Use the completed step 114 sampler through the serverless
Training API. It bills tokens and creates no GPU deployment or training run.
The promoted model is READY, rank 16, base Muse Glimmer 30B; its model metadata
reports no deployed references and supportsServerless=false. READY alone does
not make its model ID callable through chat completions.

Official docs explicitly support a fresh sampling client after the run ends.
This route is for evaluation/non-production workloads with variable shared-pool
latency, which fits an experimental Reading Lab evaluation mode.

## Protocol

1. POST https://api.fireworks.ai/training/v1/serverless/api/v1/create_sampling_route
   with `{ "training_run": "accounts/svirok123/trainingRuns/run-4b603d583d83427fa832495d3974576c" }`.
2. POST https://api.fireworks.ai/training/v1/serverless/inference/v1/completions
   with fixed model
   `accounts/svirok123/trainingSamplers/checkpoints/svirok123/run-4b603d583d83427fa832495d3974576c/step-114-5490cecd`,
   native prompt token IDs, n=1, max_tokens<=128, raw_output=true, stop=["<|eot|>"].

The final 5490cecd suffix is part of the sampler snapshot name: SDK
qualify_snapshot_name appends the session suffix before the save. The shorter
step-114 names the training checkpoint and must not be used for sampling.
Control plane GET confirmed the inference LoRA checkpoint
run-4b603d583d83427fa832495d3974576c-step-114-5490cecd exists and is promotable.
The exact standalone route has not been sampled yet; a budget-reserved smoke
request must confirm the exported public path resolves before marking live.

## Host integration

Run `training/.venv/bin/python serving/worker.py`, send one JSON on stdin.
Prepare: `{ "mode":"prepare", "instructions":"...", "messages":[{"role":"user","content":"..."}] }`.
Offline prepare hash-checks the pinned tokenizer, uses the pinned native
muse_glimmer renderer, and adds native ` to=user<|message|>` assistant prefill.
Returns status=prepared, token_ids, input_count/input_tokens, max_output_tokens,
and fixed model/checkpoint identity. It requires no key or network.

Reserve the maximum token cost in the host app, then generate:
`{ "mode":"generate", "token_ids":[...], "max_tokens":128, "temperature":0.7, "top_p":0.8, "top_k":20 }`.
Pass FIREWORKS_API_KEY in environment. Returns status, text, raw_text, truncated,
finish_reason, usage.input_tokens/output_tokens, raw_response, response_id,
request_id, latency_s, fixed identity, and generation_attempted. Provider usage
is explicitly marked provider_usage=true/usage_source=provider; absent or invalid
provider counters return null normalized usage with usage_source=missing. Failed or missing provider
usage must be accounted conservatively by the host reservation ledger. No
provider/model overrides are accepted. Native markup is not rewritten.

Curl uses IPv4, zero retries, a 15-second connect timeout, and a 180-second total
timeout for each of the route and completion calls. Credentials enter curl via
stdin config, absent from command argv and files. No network inference was run
while preparing this worker.

Current official Muse Glimmer Training API rates are $1.96/M prompt,
$0.39/M cached prompt, $4.88/M sampled tokens. Reserve at the uncached prompt
rate. 8064 input + 128 output costs at most $0.01643008 at those token rates.

## Evidence

- https://docs.fireworks.ai/fine-tuning/training-api/serverless.md#sampling-without-a-training-client
- https://docs.fireworks.ai/fine-tuning/evaluating-fine-tuned-models.md#serverless-checkpoint-sampling
- https://fireworks.ai/pricing
- Pinned SDK fireworks/training/sdk/client.py: qualify_snapshot_name;
  _standalone_checkpoint_sampling_model_name; _bind_standalone_sampler_route;
  _create_sampling_client. Pinned sampler wire payload:
  fireworks/training/sdk/sampling.py async_completions_stream.
- Offline native prepare smoke passed; three mocked tests verify fixed model,
  one sample, caps, and route failure stops before sampling.
