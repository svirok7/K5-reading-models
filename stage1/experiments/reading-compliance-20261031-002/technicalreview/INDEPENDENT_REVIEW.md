# Runtime review and experiment 002 verification

Reviewed on 2026-10-31 by the GPT-6.1 Sol / high training worker. The worker reviewed the coordinator's sealed experiment 001 and delivery builder independently, then authored the explicitly authorized experiment 002 execution hardening. Tests of those authored changes are implementation verification, not a separate independent review of the worker's own code. The original training helper and all sealed 001 source artifacts were preserved.

No unresolved blocking issue was found in the final sealed 002 package under the reviewed execution paths. Actual Qwen/T4 numerical behavior, headroom, training, and behavioral quality remain unmeasured by this review.

## Verified corrections in 002

The original repeat command could accept a primary summary containing only one experiment's checkpoints, because it checked the selected label's qualification without requiring the complete six-checkpoint study. Selection now derives the six labels and exact epoch/update metadata from the sealed two-experiment plan. Both the selection CLI and repeat command require current plus all six candidates, correct paired counts/gains, the frozen case count, and the original current-adapter record. Partial `--only` execution is explicitly marked as incomplete and cannot authorize selection.

The primary decision is now bound to the exact primary-summary SHA256 and recomputed from that summary and the full metadata. Repeat generation verifies both completed runs, their retained checkpoint inventories, all seven completed primary evaluations, and the primary blinded-review packet before proceeding. Only the deterministically selected checkpoint and current adapter are generated, using exactly offsets 1000003 and 2000003.

Inference parity is checked before allocating model weights and again against the loaded model's actual record. T4/FP16, pinned base/revision, no-thinking template, decoding, CUDA/runtime/Python/package group, actual parameter dtype counts, attention implementation, and model/tokenizer artifact aggregate must match. The prepared artifact map is verified against actual downloaded bytes before loading the model and checked again after loading. Optional provenance-only `source`/`source_id` fields in frozen cases are accepted but never included in the rendered model input; target or scorer-note fields remain rejected.

Repeat continuation verifies and reuses completed current/candidate generations and existing blinded packets, rather than creating more samples. A mechanical interruption after the first completed generation is recoverable: successful generation occurs exactly once for each of the two labels at each of the two offsets, even after continuing twice. Already-created partial/failed generation artifacts are preserved and cause a stop; they are not silently overwritten or treated as completed.

The optional reuse API supports explicitly hash-bound completed training/evaluation references without changing their original context or source plan. Source run-record and checkpoint-index hashes, exact configuration/helper/data identity, successful reload/headroom evidence, all checkpoint bytes, evaluation manifests, response bytes, frozen inputs, seeds, and comparison group are verified. Relative reference paths resolve against the new output root. The final 002 plan uses empty optional reuse maps, so the tested normal path performs both approved fresh runs.

## Checkpoint and runtime assessment

The training helper remains byte-identical to the previously tested helper: SHA256 `1d19f350b8cbc7b38106c4795a28186a944bd39e60265f9837deac1d8df22ecb`. Its 29 tests pass again. Actual CPU Trainer loops establish 114 updates for 300 rows over three epochs and 225 for 600 rows, including correct final partial accumulation. The tiny real PEFT/dropout fixture retains and reloads every epoch and reproduces uninterrupted final weights, row order, losses, and scheduler behavior after resume.

Source inspection of the pinned Trainer integration confirms that epoch publication runs after the completed epoch ledger and per-update log are ready. Complete optimizer/scheduler/RNG state and FP16 scaler state are required before a checkpoint is indexed. Every epoch's adapter is reloaded against the pinned base after live training state is released; its exact fingerprint and inference are checked. Reload verification rechecks the bound files afterward. A run is not marked completed before these checks and the unchanged 15% headroom gate pass. These are runtime guards, not proof of a successful T4 run.

The execution path generates a fresh current comparator on the same T4/FP16 path as new checkpoints. The two fresh training runs initialize from the pinned base and seed 42, not from the current comparator or smoke adapter. The actual current-adapter record and its original weights remain bound separately. No baseline-model inference sweep, precision fallback, purchase, or live adapter replacement was introduced.

## Local evidence

- All 29 training-helper tests pass.
- All 19 evaluation/selection/execution tests pass: the original 11 mechanical tests plus eight execution/provenance tests.
- The fresh-run orchestration fixture performs exactly two fresh training calls (300 then 600), two smoke calls, and seven evaluation calls. It does not run a GPU or create measured model outputs.
- The reuse orchestration fixture performs only the 600-row training call, uses all four explicitly bound source evaluations, and leaves the source bytes unchanged.
- Fixtures reject changed/missing prepared model bytes, altered generation manifests/responses, wrong inference group/seed, incomplete primary coverage, changed metadata/gain, changed decision or summary hash, changed source context/index, and changed repeat environment before generation.
- All nine cached pinned base/tokenizer artifacts were streamed through SHA256 and match the prepared record. No model was loaded for this check. Detailed evidence: `prepared-model-hash-verification.json`.
- All eight code cells in the original sealed notebook and the newly generated 002 notebook compile. The reviewed dependency cell still installs/checks the pinned packages, performs the scoped optional-torchao preflight, and exercises CPU PEFT dispatch. The pinned tokenizer is downloaded before local-only mask tests. No notebook execution or build was performed by this worker.

Commands:

```text
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest test_sft_train -q
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s experiments/reading-compliance-20261031-002 -p 'test_*.py' -q
```

## Final sealed artifact checks

Every current code file matches its hash in the sealed 002 plan and its packaged bytes. The ZIP inventory is unique, relative, traversal-free, and exactly matches its kit manifest; every packaged file hash and the packaged plan hash passes. Frozen development inputs are byte-identical between 001 and 002. Every original source artifact tracked before this review, including the 001 plan, notebook, archive, and training helper/tests, is unchanged.

| Artifact | SHA256 |
| --- | --- |
| 002 ZIP | `24be38ca94a924e635e6f06c7086cef1db1b41f0803e8d3ec411482d230424fb` |
| 002 plan | `9277deeec7d2c6c628e3b2254fa6b499401f51bd789c57ec97b63c8ab4c9704a` |
| 002 notebook | `9dd7bcaf8f563b80a4464db28aaecb6e7c10a10bda2d1bcec4c820e419659c74` |
| `evaluate.py` | `179e8b1dbfa7d11a9122438b93febdc3a9175c1cb5da862826cf4bc1a5ba72c4` |
| `execute.py` | `367212e866b3dec3188480497cd1ba089959ff32f745143c5fbcd8fa4e5e2aaa` |
| `choose_checkpoint.py` | `0dc183842b49386370bbda9f86b6b91b201b4ca34ff924484fcc70f06e1a4c28` |
| `repeat_seeds.py` | `7ab4e110e51b2c11502901af767a236bb90b84997d0fe5d4f2ec357ef86f2e4f` |
| `test_execution.py` | `dd82c77c750f879f0a6310090e8b108e0b6a0bf788ffca70693a553c52626d2b` |

Machine-readable source, package, and verification hashes are retained alongside this report. No code or packaged artifact was edited after sealing.

## Limits

The coordinator reported that T4 access returned, but upload approval remained pending; this worker made no upload, GPU, purchase, or external egress attempt. No actual loss curve, new adapter, response comparison, or adoption evidence exists from this review. Dataset semantics and independent approval are owned by the separate author/reviewer workflow. Independent blinded ratings and both extra paired seeds remain required before recommending adoption. Neither active held-out test contents nor archived test contents were opened.
