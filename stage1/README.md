# Reading Lab — Stage 1

A localhost model playground and a controlled baseline evaluation kit for a reading companion. Target: a six-year-old midway through Level 1; operationally lessons 1–28 plus a provisional familiar conversational vocabulary.

**Prepared:** rubric, good/bad examples, A/B prompts, 20 development cases, 50 held-out cases, local UI, and Colab baseline notebook.
**Pending:** actual model generations, human ratings, and the baseline findings report. No measured model-quality or latency results are included.

## Open the local UI

From this folder:

```sh
python3 server.py
```

Open http://127.0.0.1:8765. The UI and OpenAI backend use Python's standard library; no package installation is needed. Keep the server running. Stop with Ctrl-C. A different port can be set with READING_MODEL_PORT.

- **Conversation:** choose Qwen, Sarvam, OpenAI, or Claude and prompt A/B. Switching models or prompts starts a new conversation, so one model's answers do not silently contaminate another's context.
- **OpenAI:** enter an accessible API model ID and key in the connection card. The key is kept in server memory only, not browser storage or project files. It can also come from the OPENAI_API_KEY environment variable. Never paste a key into chat, commit it, or put it in the notebook source. Requests are billable to your API account. No key validation request is made when saving settings.
- **Qwen:** Qwen3-1.7B uses its native chat template with a system message and thinking disabled. Sampling uses temperature 0.7, top-p 0.8, top-k 20, with a 128-token reply limit. Settings are recorded with latency and scores, separately from earlier thinking runs. It runs locally without an API key and requires the model dependencies below. First use downloads weights. Qwen SFT/DPO/RLHF entries stay disabled until real adapters are configured.
- **Sarvam:** live chat uses this machine's compute. First use downloads model weights; model loading is excluded from displayed response latency. MPS uses float16, CPU float32, CUDA 4-bit NF4. Local feasibility depends on available RAM; this machine's memory could not be inspected during preparation. No model weights were downloaded during preparation.
- **Future variants:** SFT, DPO, and RLHF are disabled until you train them. Put the absolute local adapter directory in the corresponding `adapter` field in models.json. Sarvam entries require adapters trained on `sarvamai/sarvam-1`; Qwen entries require adapters trained on `Qwen/Qwen3-1.7B`. Use the same conversation template as engine.py when preparing SFT data, or explicitly update and version the template for all comparisons. The UI reloads the adapter when you select it. The same precision/device must be used for fair checkpoint comparisons.
- **Blind review:** import real JSONL outputs from the notebook/runner. Multiple files are merged; the latest retry for a case/condition/run replaces the earlier record. Answer order is randomized per case for this browser session. Score 0–4, add notes/flags, and record pair preferences. Reveal identities after rating. Export reviews before closing; scores are not persisted automatically. Export includes the identity mapping and raw results, so do not show it to blinded raters before completion.

This is an adult experiment workbench, not a deployed child-facing service. The server binds only to loopback. It provides no public hosting or remote GPU tunnel.

## Enable live Qwen or Sarvam locally (optional)

Use a separate environment so the UI's basic operation stays lightweight:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-model.txt
# NVIDIA CUDA only (including Colab):
# python -m pip install bitsandbytes
python server.py
```

PyTorch and model weights are substantial downloads. On a Mac, bitsandbytes is not used. CPU inference may be slow. If memory is insufficient, do the generation run on Colab and import its outputs for review here. Colab is not kept running as a public inference server.

Dependency ranges are intentionally broad for initial setup. The baseline runner records actual installed versions; freeze the successful environment before comparing later checkpoints. The Colab/local model paths have been statically checked but require a real runtime smoke test.

## Colab baseline run

Open `baseline_colab.ipynb` in Google Colab and choose a GPU runtime. Upload `reading-lab-stage1.zip` when prompted. The notebook extracts the small evaluation kit, installs model dependencies, mounts Drive for persistent results, and starts with two dev cases. Set your OpenAI model ID; the key is requested in a hidden input.

1. Smoke: 2 cases × 2 prompts × 2 backends = 8 generations (4 API calls).
2. Development: set LIMIT=0 and SPLIT='dev' for 80 generations (40 API calls).
3. Freeze rubric/prompts/settings. Set SPLIT='test', LIMIT=0, FROZEN=True in a new run folder for 200 generations (100 API calls).
4. Download both JSONL result files from Drive. Import them into the localhost review UI.
5. Score and export reviews; write a findings report. Stage 1 ends here, not at notebook creation.

Use a new run directory whenever configuration, prompt, rubric, case subset, hardware, or dependencies change. Resume after disconnection with the exact same configuration. Completed/error records are skipped unless explicit retry is requested. Persistent outputs prevent accidental repeated spending; a crash after an API response but before its save can still require a repeated billable call.

## Files to read first

- `RUBRIC.md`: word categories, sentence-length targets, rhythm, scoring anchors.
- `EXAMPLES.md`: 12 original good/bad pairs and worked scoring examples.
- `PROTOCOL.md`: fairness, leakage, latency, execution, and completion criteria.
- `prompts/A.txt` and `prompts/B.txt`: actual runtime instructions.
- `data/dev.jsonl`: practice cases and scorer notes.
- `data/test.jsonl`: held-out cases; do not use for prompt tuning or training.

The source PDFs remain unchanged in the parent folder. Their teaching instructions were treated as source evidence, not instructions to this coding agent. All model prompts, examples, and cases are original adaptations of the desired style, not copied book text.

## CLI alternative

```sh
python run_baseline.py --backend sarvam --split dev --limit 2 --out runs/smoke
python run_baseline.py --backend openai --model YOUR_MODEL_ID --split dev --limit 2 --out runs/smoke
```

The OpenAI key is requested privately when absent from the environment. Supported overrides can be supplied with `--options '{"temperature":0}'` only if that model supports them. No unsupported defaults are silently retried. The API output cap includes any reasoning tokens; if your selected model returns incomplete/no visible output, adjust its documented reasoning settings or the cap on dev before freezing.

## Validation status

Local checks cover data/schema counts, distinct dev/test messages, prompt separation, transcript building, API response parsing with a mock, notebook syntax, and local UI interactions. These checks do not demonstrate Sarvam GPU/MPS compatibility or real API model access. Actual performance is pending your Colab/API run.

## Claude and existing project keys

Claude is also available in the picker and baseline CLI (`--backend claude --model YOUR_CLAUDE_MODEL_ID`). The API connection panel switches between providers. Supply your accessible model ID for each provider.

To reuse keys without copying them, start the server with `python3 server.py --env-file /path/to/existing/.env.local`. Only OPENAI_API_KEY, ANTHROPIC_API_KEY, OPENAI_MODEL, and ANTHROPIC_MODEL are read; key values remain in server memory. An existing key is present, not necessarily valid or funded. No live API requests were made during this change.

Adding Claude A/B creates two additional conditions: six total (300 test generations, including 200 paid API calls for OpenAI + Claude). The original notebook runs Sarvam/OpenAI by default; the optional Claude cell below is explicit.

Agreed API defaults: `gpt-6-luna` (reasoning effort none for UI/default notebook) and `claude-haiku-5-5`. The dropdown also offers stronger reference models and GPT-5. Choices are fixed IDs, never silently advanced to future versions. Model changes auto-save in server memory and reset the conversation. Availability is subject to account access.

## Conversation evaluations and manual overrides

New companion responses are saved before evaluation. GPT-6.1 Sol automatically evaluates them using the exact rubric snapshot and a structured schema. This adds one OpenAI API call per new response, even when the companion is Claude or Sarvam. The judge is experimental and uncalibrated. Its latency is separate from companion latency. Failures leave the response saved and manually judgeable; retry is explicit.

Select a manual decision, add an optional reason, and click Save decision. Manual takes precedence over the evaluator. Choose Use evaluator and save to remove the override. The original evaluator judgment and manual edit history are preserved. Resetting conversation never deletes saved records.

Records persist in `runs/conversation-results.sqlite3` (ignored by Git). Saved conversation results → Load results retrieves them after refresh/restart; Export results downloads JSON including messages, companion model/settings, condition/prompt, rubric snapshot/hash, evaluator judgment/metadata, manual edit history, effective decision, and source. Existing pre-feature conversations cannot be reconstructed automatically. Casual conversation results remain separate from held-out baseline test runs and blind review ratings. Do not include the runs directory in shared packages.

Saved-result summaries report sample counts, median/p95 completed companion latency, five mean evaluator scores, and effective decision counts per model/settings, prompt condition, and rubric hash. Manual decisions override acceptance labels, not numeric evaluator scores; those remain explicitly labelled evaluator scores. JSON export also contains evaluator latency separately. One live greeting was used for interface verification; it is casual development data, not held-out baseline evidence.


Current UI: grouped model picker, binary reading-accessibility evaluation (word types, length, rhythm), Save & continue, and automatically loaded conversation results under Review results. Rubric v1.2 records remain separate from historical v1.1 results. Manual decisions override evaluator verdicts; latency and scores are retained.

Run a Qwen development smoke batch from the model environment:

```sh
python run_baseline.py --backend qwen --split dev --limit 2 --out runs/qwen-smoke
```

Use the same Qwen chat template, thinking setting, and generation settings for baseline and trained adapter comparisons. The baseline notebook still defaults to its original Sarvam/OpenAI runs; Qwen can be run with the CLI above.


Current benchmark (v1.5): end of AAR Level 1 plus the explicit cumulative Dolch preprimer/primer/first-grade list in data/dolch-through-grade1.json. Spoken child input is unrestricted. Expanded profiles and exact prompts are saved per response. New Prompt A and B hashes require new comparison runs. Do not pool older profiles with v1.5 results.

## First 300-example SFT experiment

`sft_colab.ipynb` now defaults to ordinary LoRA on the pinned Qwen3-1.7B revision, with an explicit NF4 QLoRA fallback only after a recorded memory failure. The distributed notebook keeps both GPU execution switches off. The minimal `reading-sft-colab-v2.zip` contains training text, its original manifest, the helper, requirements, and a file-hash manifest; run `python3 build_sft_kit.py` after implementation edits to rebuild it and refresh the notebook's ZIP pin.

The helper checks final-completion labels on all 300 examples and in actual forward batches, freezes the base, uses FP32 adapters with mixed precision, verifies two representative optimizer updates and a 15% operational memory margin, then starts a fresh one-epoch adapter. Completion requires final adapter reload and generation. Checkpoint resume is explicit and bound to configuration, hashes, dependencies, precision, and optimizer/RNG state. `SFT_INDEPENDENT_REVIEW.md` records the independent implementation review; `sft-colab-validation.json` distinguishes offline checks, runtime preflight, and real model execution.

`evaluation-sft-v1/PROCEDURE.md` documents the frozen saved Qwen reference and development replay/comparison tools. Its conversation snapshot stays local and outside the training kit. Template, rubric, settings, and hardware groups remain separate. A real trained adapter and completed run record are required before adapter replay or enabling the existing Qwen SFT option. Held-out content remains untouched.


For this workstation, the existing shared key source is Orbi's `.env.local`. Start Reading Lab with:

```sh
.venv/bin/python server.py --env-file /Users/viroksharma/Desktop/Orbi/mvp-v2/.env.local
```

Keys entered in Settings are memory-only and disappear when the server stops. Restart with the command above to reload them without copying credentials into this project.
