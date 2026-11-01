# Training readiness — 2026-10-29

The corrected 300-row SFT candidate export, sft-300-v2, has passed offline tokenization and completion-boundary feasibility checks. Its exact revised bytes have also passed the finalized independent model audit: 300 pass, zero open findings, and four resolved findings. Status is independently reviewed, pending human review. An actual SFT training implementation, GPU smoke run, and trained adapter are still missing. This is enough data for a small first experiment, not evidence that the model will improve. All examples remain pending human review. No held-out material was opened for these checks, no weights were downloaded or loaded, and no training or new baseline generation was run.

## Dataset and offline checks completed

Use `stage1/datasets/sft-300-v2/sft.jsonl` as the current independently model-reviewed candidate. It contains exactly 300 conversational prompt/completion objects. Keep the aligned `review.jsonl` outside model inputs and loss targets; it holds IDs and word-choice reasoning. V2 corrects four findings from the subsequent full-corpus audit: three prompts now truly require prior context, and one reply drops an unsupported assertion about what the child did. The other 296 rows remain unchanged. The original v1 dataset, its baseline prefix, and earlier checkpoints remain preserved. The finalized v2 audit separately approves these changed bytes; its report is bound into the current manifest. Human review remains pending. Actual final-user whitespace counts are 121 short, 121 medium, and 58 long, with 97 history-dependent rows and 144 assistant-history turns; use these audited counts instead of assuming 120/120/60.

Export SHA-256 values:

- sft.jsonl: `42aea06f60ce82af7e276440c3318220efa751cc4fd3c111208176366bb419b3`
- review.jsonl: `4bea6c4aaf5ecde8218d6a998c4d7435ee217faa75dddd63b719cc79815e445b`

`offline_preflight.py --dataset datasets/sft-300-v2` checks all declared artifact hashes against the export manifest, loads only the locally cached Qwen tokenizer, and tokenizes every example with the same native template and `enable_thinking=False` used by `engine.py`. Its current reproducible evidence is `tokenization-preflight-v2.json`, bound to manifest SHA-256 `40d27ee7931fff21c9312a5820d5923d5ddf9cca6998482965abd13a078f4aa3`. The script also checks that the manifest/data did not change during measurement. The finalized preflight also verifies the independent audit JSON/Markdown artifact hashes; audit.json SHA-256 is `8f43f944dd91da7fddda7151199ad12fa34efd1a36da4849b645e5d2a39a1630`. The earlier `tokenization-preflight.json` remains the v1 record. Any later manifest or data edit requires a new exact-hash check. The cached tokenizer/config revision is `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e` for `Qwen/Qwen3-1.7B`.

| Actual offline measurement | Result |
| --- | --- |
| Full serialized sequence tokens | min 1,737; median 1,757.5; p95 1,800; max 1,825 |
| Prompt tokens, including final assistant generation prefix | min 1,729; median 1,738; max 1,795 |
| Final completion plus termination tokens | min 4; median 15; max 44; total 4,683 |
| Raw target text tokens | min 2; median 13; max 42; total 4,083 |
| Historical assistant turns, all excluded from proposed loss | 144 |
| Examples exceeding 1,024 tokens | 300/300 |
| Examples exceeding 2,048 tokens | 0/300 |
| Token prefix mismatches | 0/300 |

A 2,048-token sequence limit fits all current rows under this exact tokenizer and template. A 1,024-token trainer default would truncate every row and could remove all final-target supervision. Recheck the maximum after any dataset/template/tokenizer change; fail on overlength instead of silently truncating. The cached model config says 40,960 maximum positions while tokenizer metadata says 131,072; neither metadata value establishes the memory budget of the chosen training GPU.

For all 300 rows, separately tokenized inference-style prompt IDs exactly prefix the fully serialized conversation IDs. The remaining tokens decode to precisely the target text followed by `<|im_end|>` and a newline. The preflight constructs feasibility labels with `-100` for every prompt token, the final suffix IDs as labels, and `-100` for explicit right-padding. This proves a clean boundary is available. It does **not** verify the actual future trainer's preprocessing, data collator, packing, label shifting, gradients, or optimizer step. The export manifest correctly still has `tokenization_verified=false` and `training_executed=false`; it was not changed by this audit.

The cached native template has no `{% generation %}` spans. Prefer the existing conversational prompt/completion format with final-completion-only loss. Do not assume `assistant_only_loss=True` works with this unchanged template or that it would mask historical assistant turns as desired. The actual installed trainer may modify templates, so inspect its emitted IDs and labels directly. Hugging Face documents completion-only supervision separately from assistant-token masks in its [SFT trainer guide](https://huggingface.co/docs/trl/v0.25.0/en/sft_trainer).

## Current local code and environment

`baseline_colab.ipynb` is an inference/evaluation notebook. It installs model dependencies, mounts Drive, and runs Sarvam/OpenAI baseline generations, with an optional Claude cell. It is not an SFT notebook. Qwen inference is available through `run_baseline.py --backend qwen`; the notebook has not yet been adapted into a Qwen training workflow. No project trainer, LoRA setup, optimizer loop, or SFTTrainer use was found in the inspected Python/notebook code.

`engine.py` already uses `Qwen/Qwen3-1.7B`, native chat serialization, thinking disabled, and the base model plus an optional PEFT adapter. `models.json` has `qwen_sft` pending with `adapter:null`; there is no adapter configured for use. The runtime verifies the adapter's `base_model_name_or_path` equals `Qwen/Qwen3-1.7B`. Its base revision currently resolves from the Hub on load, so a reproducible first experiment also needs a pinned model/tokenizer revision for training and comparison rather than relying on a moving model name.

The system Python lacks the model packages. The project's `.venv/bin/python` has torch 2.14.1, transformers 4.57.6, accelerate 1.15.0, peft 0.21.2, tokenizers 0.22.2, huggingface_hub 0.36.2, and safetensors 0.8.0. It lacks TRL, datasets, and bitsandbytes. Its current execution environment reports CUDA unavailable and MPS unavailable. That is a runtime observation, not a claim about all hardware available to the user. The offline tokenizer check succeeds in this venv; GPU training compatibility has not been exercised.

## Suggested first experiment, not an executed configuration

Use a Google Colab GPU runtime for the first controlled run, saving adapters and checkpoints to Drive. Verify the assigned GPU and memory before selecting precision or batch size; no duration or free-runtime availability has been established. Use ordinary LoRA if the actual model/optimizer/activations fit, or 4-bit NF4 QLoRA when memory is tighter. For QLoRA, prepare the quantized model for k-bit training before attaching adapters, following the [PEFT quantization guide](https://huggingface.co/docs/peft/v0.18.0/developer_guides/quantization). The package versions and CUDA/PyTorch combination must be tested together and frozen after the smoke run; the current broad requirements file is not a training environment lock.

An intentionally small starting proposal is rank 16, alpha 32, dropout 0.05, `target_modules="all-linear"`, learning rate 1e-4, sequence length 2,048, microbatch 1, gradient accumulation 8, no packing, and one epoch with seed 42. These are proposed experiment settings, not tuned or demonstrated optimal values. With all 300 rows used once, that is about 38 optimizer updates; small data and only 4,683 supervised suffix tokens make overfitting a material limitation. Keep the long shared system prompt unchanged for the first comparison despite its computational overhead. BF16/FP16 choice must follow the assigned GPU's supported precision and the validated quantized compute configuration.

Before the complete epoch, the actual trainer must pass these checks:

1. Load the pinned base and tokenizer; record package versions, model revision, data hashes, full template text/hash, seed, hardware, precision, adapter settings, and training configuration in the run directory. Explicitly pass thinking-disabled template settings.
2. Inspect emitted training batches for a short reply, the longest example (`pilot-022`), and history-containing examples. Decode only non-`-100` labels and compare them with the expected final completion and intended terminator. Confirm all 144 historical assistant turns, system/user text, the empty thinking prefix, and padding receive no loss. Confirm every example retains nonempty supervision and no truncation.
3. Run a few forward/backward/optimizer steps; require finite loss, nonzero finite adapter gradients, frozen base parameters, and a successful save/reload of the adapter. Check the reloaded adapter is attached to the same base revision. This is the first actual training/runtime verification and remains outstanding.
4. Run an untrained Qwen development baseline in a fresh output directory with fixed decoding settings, then the adapter on the same development inputs/settings. Evaluate word eligibility, response length/rhythm, meaningful answers, and regressions using the existing review process. Do not count training loss or memorized training responses as quality evidence.
5. Freeze the selected checkpoint and comparison settings on development material before any later held-out evaluation. This readiness task neither opens nor runs held-out data. No new baseline score or learning claim follows from creating the dataset or this preflight.

For a first train-all-300 feasibility run, there is no internal validation set: state that explicitly and use the existing development benchmark for behavior checks. If checkpoint selection should instead use a synthetic validation split, create it by scenario family before training, record its IDs/hashes, and train on fewer than 300 rows; do not silently report both as a 300-row training run. Either choice leaves the held-out benchmark untouched.

After a successful run, retain the PEFT adapter with `adapter_config.json` and adapter weights plus the frozen run record. It can then be wired into `models.json`'s `qwen_sft` adapter path and compared through the existing UI/CLI. No such wiring or training was done here.

Reproduce the offline check from stage1 without network downloads:

```sh
.venv/bin/python sft_pipeline_300/offline_preflight.py --dataset datasets/sft-300-v2 --out sft_pipeline_300/tokenization-preflight-v2.json
```

Omitting `--dataset` retains the original v1 default; explicitly pass the dataset version used for training. Neither preflight report is an actual trainer/collator mask verification.
