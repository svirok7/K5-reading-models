Coordinator completion note (after independent review): the export has now been downloaded and every artifact hash verified. Reading Lab's actual Qwen engine loaded it locally on MPS. The 13-case development replay and coordinator-model review are complete; see evaluation-sft-v1/results/comparison-001/REPORT.md. These behavioral ratings were not independently or human reviewed. Earlier retrieval/comparison-pending statements below describe the review-time state.

# Independent SFT implementation review

Reviewed 2026-10-30 against the supplied LoRA-first execution plan. Review scope: `sft_train.py`, `test_sft_train.py`, and the executable logic in `sft_colab.ipynb`. No implementation files were edited by the reviewer. No held-out content was opened and no Colab/GPU operation was performed.

**Current outcome: ordinary LoRA full training completed and the final adapter passed reload/inference verification in Colab.** The independently inspected run record confirms all 300 approved rows exactly once, 38 applied optimizer updates, zero skips, 38 finite/nonzero gradient checks, and 47.3007% memory headroom. Local adapter retrieval and the baseline-versus-SFT development comparison remain pending; no behavioral improvement is claimed. The earlier stop and subsequent user-authorized allocator experiment are preserved below as history.

Reviewed helper SHA-256 after the allocator follow-up: `777e78d03b131e03ff12a125153d692afe85e092ea307297914bd4f8a9252275`.
Reviewed tests SHA-256 after the allocator follow-up: `03a933fe6e4e1011f1806277f7516f252b788287251e26a4dab24cb5f3bad085`.
Notebook SHA-256 after allocator setup and workflow documentation: `d09c8e85fc8dc28c6f6364b90142f48e9c6f72375148d059511cbd8bee8655a7`.

## Evidence

- Independently ran the final 23 offline unit tests: all passed. Loader tests mock weight loading and CUDA support; they verify branch construction, not real device execution.
- Independently ran the new tiny CPU adapter-attachment preflight using a real 2-by-2 Linear layer and pinned PEFT. Adapter attachment succeeded entirely on CPU, without model downloads or optimizer steps. Scoped notebook tests cover absent, incompatible, previously imported incompatible, and compatible optional torchao branches.
- Independently compiled all 11 notebook code cells. `RUN_SMOKE` and `RUN_TRAINING` remain false, every execution count is null, and no cell contains saved outputs.
- Rechecked the trusted training artifact with the cached pinned tokenizer: 300 unique token sequences, 4,683 supervised tokens, maximum length 1,825. The longest row is `pilot-022`, which contains assistant history. No training content or audit reasoning was copied into this report.
- Independently exercised the real custom Trainer and PEFT adapters on a one-layer randomly initialized CPU Qwen3 with synthetic token IDs. One epoch consumed all 300 synthetic rows exactly once, reached 38 optimizer steps, passed 38 finite/nonzero gradient checks, and changed adapter weights. No pretrained weights were downloaded or trained.
- Independently exercised real Trainer checkpoint save/resume on the same tiny synthetic CPU setup with dropout enabled. Resume from checkpoint 30 consumed the remaining 60 rows over eight updates, reached step 38, and produced the exact same adapter fingerprint as uninterrupted training.
- Independently compared actual custom-Trainer gradient accumulation against a combined batch using a tiny random CPU Qwen3/PEFT model, eight synthetic microbatches, varying target lengths, and dropout disabled. Maximum adapter-gradient difference was `1.49e-08`. Runtime configuration was `model_accepts_loss_kwargs=True` and Accelerator accumulation one, confirming that the existing sum-CE/group-target-token normalization does not need another division by eight.
- Independently iterated the actual prepared full Trainer DataLoader on the approved features without model forwards. Its first eight row IDs exactly match the strengthened smoke's first accumulation group: `pilot-043`, `pilot-062`, `pilot-287`, `pilot-161`, `pilot-031`, `pilot-266`, `pilot-173`, `pilot-206`.
- Inspected the installed pinned Trainer/PEFT source: the gradient callback runs after Accelerate unscales/clips gradients, adapter dtype promotion is supported, and optimizer/RNG resume requires PyTorch 2.6 or newer. The implementation now checks the latter before changing resume metadata.

## Findings resolved during review

| Severity | Finding | Resolution inspected |
| --- | --- | --- |
| P1 | Original smoke sampled two rows from the first eight, omitted the longest row, and used accumulation one instead of eight. A later longest/history-only smoke missed a numerically harder first full-training group. | Sequential smoke uses 16 microbatches at unchanged accumulation eight: the first group matches the seeded full-run first eight rows, and the second alternates longest/history rows. Actual observed row IDs must match. |
| P1 | Original full run marked training complete without reloading its final adapter or testing generation. | Completion now follows exact adapter fingerprint verification, finite reloaded loss, and successful generation on the pinned base. |
| P1 | Coordinator's actual T4 preflight exposed that PyTorch's default BF16 query includes emulation and reported BF16 on a GPU without native BF16. The initial review had not distinguished native support from emulation. | A single helper explicitly queries `including_emulation=False`; environment reporting, weight loading, Trainer flags, and reload autocast all use it. Regression mocks simulate emulated-only support and assert the exact native-only keyword at every site. T4 therefore selects FP16, with FP32 adapters. No GPU optimization preceded the correction. |
| P1 | Coordinator's first real LoRA load reached adapter construction, where preinstalled torchao 0.10.0 triggered PEFT's minimum-0.16 optional-dispatch guard. No optimizer step occurred. | Dependency setup removes only incompatible optional torchao before imports, records the action, clears availability caches, and requires restart when an imported torchao could remain live. A real tiny CPU adapter-attachment probe now checks dispatch before the base model is downloaded. This is a dependency repair and does not permit QLoRA fallback. |
| P1 | The default FP16 scale 65,536 overflowed during the fresh full run's first accumulation group, although forward losses were finite and the earlier smoke passed. Standard dynamic-scaler skipping would consume rows without applying their update. | Controlled zero-update GPU replay confirmed scale-induced overflow. Initial scale 1,024 is now explicit in configuration, mode/run/adapter identities, and notebook setup; it is applied through the scaler's public state API identically before smoke/full training. Checkpoint scaler restoration happens later. Finite-gradient checks remain strict, and actual applied-update counters reject skipped steps. |
| P2 | Existing experiment metadata could be overwritten before old run directories were rejected. | New notebook attempts require a fresh experiment root; explicit matching resume preserves setup records. |
| P2 | Combining sampled driver free memory with peak allocator reservation could overstate headroom when non-allocator GPU memory was also in use. | Headroom additionally subtracts initial non-allocator use from the peak reservation estimate. The 15% gate applies to training and reload evidence. |
| P2 | PyTorch 2.4/2.5 was permitted even though pinned Transformers cannot safely load optimizer/RNG state on those versions. | Resume rejects versions below 2.6 before mutating run state. Fresh runs retain the documented 2.4 minimum. |
| P2 | A disconnect after final training but before reload left a status that could not use explicit checkpoint recovery. | `trained_pending_reload` is accepted for metadata-validated checkpoint replay. Completed runs remain rejected. |
| P2 | Re-saving an existing checkpoint included the previous resume manifest's self-hash, making the rewritten checkpoint fail validation. | The resume manifest excludes itself from the file checksum map. |

## Requirements checked

Final-completion labels use the exact inference prefix and assert token-boundary stability. System/user text, historical assistant turns, the disabled-thinking prefix, and padding are masked. The final completion and end-of-message suffix remain supervised, including when padding and EOS share an ID. Every actual model batch is checked against approved feature IDs and labels.

Ordinary LoRA loads the pinned unquantized base, freezes it, enables non-reentrant checkpointing, and retains FP32 trainable adapters with native BF16 where available or FP16 mixed precision otherwise. That branch neither constructs quantization settings nor calls k-bit preparation. QLoRA remains an explicit NF4 branch. Notebook fallback requires recorded LoRA OOM or insufficient-headroom evidence; unrelated errors do not qualify.

Smoke and full-run identities bind mode, settings, data/manifest hashes, native template, helper source, and run context. Fresh full training reinitializes from the seed and verifies the pre-smoke fingerprint. Checkpoints bind adapter, optimizer, scheduler, RNG, Trainer state, and FP16 scaler where applicable; resume checks ownership, hashes, settings, package versions, and precision. Mode is present in both run and exported adapter records.

## Remaining execution limits

### Completed full run and remaining handoff

The reviewer independently inspected `runs/qwen-sft300-v2-lora-allocator-20261030-008/run-record.json` (local file SHA-256 `243be7918e7765d345d7af2c3a323264fb866505fb0a5d54f03f0f9b2504ba44`). It reports `status=training_completed`, epoch one, ordinary LoRA on the pinned Qwen revision, and the unchanged approved data/configuration. Its identity exactly matches the passing allocator smoke identity.

The actual row list contains 300 unique IDs and exactly equals `pilot-001` through `pilot-300`. There are 38 checked gradient steps, 38 applied optimizer updates, zero skipped updates, and starting global step zero. FP16 scale stays at 1,024, with growth tracker advancing from zero to 38. Actual batch masks are verified. The final adapter fingerprint differs from both the fresh initialization and diagnostic smoke adapter.

Training and reload-inclusive memory records both pass the 15% gate with margin `0.4730074642816729` (47.3007%). Peak allocated memory is 7,307,073,536 bytes and peak reserved memory is 8,090,812,416 bytes. The run took approximately 766.9 seconds and recorded aggregate training loss `2.368481435273823`; that is an engineering measurement, not a quality result.

The final reload record confirms exact saved/reloaded adapter-weight fingerprint equality, finite forward loss `0.5303304195404053`, and successful generated-token inference. The adapter fingerprint is `9b02b42128440a635c0f7ca2b4bc8ed8c8344fcfc97790eda09a74f34239b51c`; the recorded adapter safetensors file SHA-256 is `81514bffcb7ae1ee5ce60d48357afaeaa05313b80c42318b406f2d94846f12aa`. These are verified execution-record observations; the reviewer has not independently loaded the final adapter locally.

The coordinator reports that the export bundle exists and was hash-verified in Drive. Automatic local download did not produce a usable local adapter artifact after two attempts, and manual user download was requested. Local artifact retrieval, Reading Lab integration, and the reproducible baseline-versus-SFT development comparison remain outstanding. No held-out evaluation was performed, and `quality_improvement_verified` remains false.

### User-authorized allocator follow-up

After the earlier stop, the user explicitly authorized a narrow allocator experiment. The reviewed notebook sets `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` before importing torch, rejects an already-imported torch or a conflicting primary allocator variable, and binds the setting into run context. Runtime records retain both allocator environment variables and the actual allocator backend. The model, approved data, precision, seed, LoRA settings, batch/accumulation, and required 15% margin remain unchanged. Enabling full training after smoke uses a separate flag-setting cell because the initial allocator configuration cell deliberately requires a fresh kernel.

The reviewer independently inspected the actual `sft-diagnostics/lora-allocator-008-smoke-report.json`. It binds the current reviewed helper hash and kit SHA-256 `84df1923ca4101eaefb4548687c27ff5c5737405eb388bbe11b935ef50bec939`. Recorded runtime allocator state is primary variable absent, CUDA alias `expandable_segments:True`, backend `native`.

Run `-008` passes: all 16 smoke microbatches retain their approved masks; both optimizer updates apply with zero skips; both gradient checks are finite/nonzero; adapters change while the base stays frozen; exact saved/reloaded adapter weights match and inference succeeds. FP16 scaler state remains at 1,024. Peak allocated memory is 7,307,075,072 bytes and peak reserved memory is 8,489,271,296 bytes. Training and reload-inclusive reports both give free-memory margin `0.44752580646513246` (44.7526%), exceeding the unchanged 15% target.

This actual measured result cleared the smoke gate for the fresh ordinary-LoRA full run subsequently completed above. No quality improvement is inferred from smoke or training losses.

### Historical stop before allocator authorization

The reviewer independently inspected the locally preserved actual reports for clean LoRA run `qwen-sft300-v2-lora-20261030-006` and QLoRA run `qwen-sft300-v2-qlora-20261030-007` under `sft-diagnostics/colab-20261030/`. Both reports bind the reviewed helper hash and the unchanged approved experiment settings, including FP16 initial scale 1,024. Both ran on a Tesla T4 with 15,637,086,208 bytes VRAM, PyTorch `2.11.0+cu130`, and CUDA 13.0; QLoRA used bitsandbytes `0.49.2`.

| Final clean attempt | Applied updates / skipped | Finite nonzero gradient checks | Exact adapter reload / inference | Measured free-memory margin | Result |
| --- | --- | --- | --- | --- | --- |
| LoRA `-006` | 2 / 0 | 2 | Pass / pass | 6.248% | Insufficient headroom |
| QLoRA `-007` | 2 / 0 | 2 | Pass / pass | 10.701% | Insufficient headroom |

Each attempt audited all 16 actual smoke microbatches, changed only adapters, kept the base frozen, and preserved scaler scale 1,024 across both applied updates. Their training and reload-inclusive memory reports agree on failure of the 15% gate. Peak reserved memory was 14,510,194,688 bytes for LoRA and 13,813,940,224 bytes for QLoRA. The explicit QLoRA fallback was justified by the clean LoRA headroom failure; neither attempt failed a precision, gradient, masking, or reload check.

**At that point, stopping and preserving the reports was the correct plan-compliant action.** Both reports have `passed=false`, `status=insufficient_headroom`, and `failure_kind=insufficient_headroom`; neither run has a full-run directory in the preserved evidence. The subsequent user authorization and passing allocator experiment above reopened the execution path. Smoke adapters remain diagnostic artifacts and must not be presented as the one-epoch final adapter. The reviewer did not open held-out content or operate Colab.

### Earlier diagnostic history

Coordinator-reported GPU evidence: LoRA run `-003` passed two optimizer updates, adapter save/reload/inference, and approximately 47% memory headroom. Its subsequent fresh full run stopped at global step zero with finite accumulated loss `7.057175636291504` and GradScaler `found_inf=1`; no full-run optimizer update or checkpoint occurred. The persisted gradient summary was inspected independently. Post-clipping nonfinite gradients can reflect contamination from a smaller set of raw overflows, so the 392 post-clipping tensors do not establish 392 independent overflow sources.

Coordinator then ran the reviewed reconstruction diagnostic on the same eight approved rows and fresh initial adapter fingerprint. Scale 65,536 produced 2,523,152 nonfinite elements in 58 raw gradient tensors. Scales 1,024 and 256 produced finite, nonzero gradients in all 392 tensors, with norms `26.67669356691012` and `26.676295835124666` respectively (about `1.49e-05` relative difference). Forward losses matched between trials, adapter fingerprints remained unchanged, and optimizer steps were zero. Each trial used the same reset RNG stream; its equivalence to the original failed Trainer's dropout stream was not established. These results support the explicit scale repair without changing the loss objective, data, learning rate, or accumulation.

The updated scale configuration and strengthened smoke were subsequently exercised in the attempts above. Real LoRA and QLoRA/bitsandbytes smoke execution is verified. The allocator experiment then met the memory gate in ordinary LoRA and enabled the completed full run. Local artifact retrieval and its quality comparison remain pending. Driver free memory is sampled and the conservative allocator estimate uses initial non-allocator consumption; external changes between samples can be missed and this limit is recorded in the report itself.

On a resumed invocation, Transformers' aggregate `training_loss` is not necessarily directly comparable to the aggregate from an uninterrupted run. Use recorded per-step loss/gradient logs and resume history for interpretation. No quality improvement is inferred from any training-loss value.
