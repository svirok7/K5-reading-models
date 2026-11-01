# Training implementation and independent execution-code review

Reviewed on 2026-10-30 by the GPT-6.1 Sol / high training agent. The agent authored `sft_train.py` and its tests, so the training section is implementation verification, not an independent review of its own work. Its review of the coordinator-authored `execute.py`, `evaluate.py`, and `choose_checkpoint.py` is independent.

## Findings and disposition

No unresolved blocking code findings were identified in the reviewed execution, generation, blinding, scoring, or selection paths. Two actionable findings were reported to the coordinator and the fixes were inspected:

1. A global resume checkpoint was being applied to both experiments, which could reject the completed first run or attempt to resume a fresh second run. Execution now requires `--only` with `--resume` and the training helper enforces membership in the matching run and the latest retained completed epoch.
2. The evaluation checkpoint branch originally skipped the pinned model/revision/no-thinking and adapter base/revision checks applied to the current adapter. Those checks now apply to intermediate checkpoints as well.

Checkpoint replay also now rejects a directory whose numeric suffix differs from its saved optimizer step and an index whose epoch/update entries differ from the bound record.

## Training safeguards verified

The baseline remains bound to its original training and manifest SHA256 values. A 600-row successor requires explicit experiment-plan hashes and matching immutable manifest, count, dataset version, completed independent audit, and zero open findings. A manifest cannot approve itself merely by declaring an artifact hash. The successor test uses synthetic mechanical bytes; it is not an audit of the real successor dataset.

Epochs must be positive integers. The existing seed 42, sequence limit 2048, rank 16, alpha 32, dropout 0.05, learning rate 1e-4, microbatch 1, and accumulation 8 remain fixed. Training uses one linear schedule over the complete configured run, with the existing 3% warmup. It logs a finite loss and learning rate on every optimizer update.

Actual model-input labels remain completion-only, including when an assistant history contains false identity claims or instruction-like text. Each full-run epoch records every approved row exactly once. The last four-row accumulation group at 300 rows receives correct normalization; it is not dropped or divided as if it contained eight rows.

All epoch checkpoints are retained with optimizer, scheduler, RNG, and precision state. FP16 additionally requires scaler state; its public-state restoration tests remain in the suite. Each checkpoint includes a cumulative row/loss ledger, adapter identity, adapter fingerprint, and hashes of every saved file. An external checkpoint index binds the resume-record SHA256. Full training verifies the retained inventory and loads every saved epoch adapter for exact-fingerprint/inference checks after releasing the live training model. Replay verification checks the file inventory, all hashes, identity, complete-epoch accounting, and every per-update loss record.

The two-update fresh-model smoke, finite/nonzero gradients, no skipped optimizer updates, smoke-weight disposal, explicit precision/mode choice, and unchanged 15% memory target remain enforced. No sweeps or automatic precision fallback were introduced.

## Local evidence

`./.venv/bin/python -m unittest test_sft_train -q` passes all 29 tests. This includes the original 23 tests and six multi-epoch/integrity tests. Actual CPU Trainer loops consume 300 rows for three epochs with 114 optimizer updates, and 600 rows for three epochs with 225 updates. Gradient assertions verify the partial accumulation group rather than checking only the step-count formula.

A real tiny PEFT/GPT2 fixture with dropout saves all three epoch checkpoints and reloads each to the exact recorded adapter fingerprint without changing retained files. Resuming after epoch one reproduces the uninterrupted final fingerprint, row order, per-update loss records, and learning rates. The final scheduler step is six with zero remaining learning rate. Tampering with adapter weights, optimizer, scheduler, RNG, ledger, or the frozen record hash is rejected. Rebinding a duplicated-row ledger still fails the epoch-exposure check.

`./.venv/bin/python -m unittest discover -s experiments/reading-compliance-20261030-001 -p 'test_*.py' -v` passes all seven coordinator evaluation tests. These cover frozen input integrity, exclusion of targets/notes, blind-review fields, inference-group parity, complete unique ratings, joint success, serious failure by type, and unsupported-word failures.

Five additional mechanical selection assertions exercised earlier-epoch ties, the pending-repeat state, successful paired repeats, rejection after a new serious failure, and duplicate repeat-seed rejection. They used invented mechanical counts only, not model generations or new behavioral evaluation cases.

Local versions: torch 2.14.1; transformers 4.57.6; peft 0.21.2; accelerate 1.15.0.

## Limits and execution status

This review does not establish GPU memory headroom, actual Qwen FP16 numerical behavior, real 600-row data quality, or behavioral improvement. No Qwen weights were loaded or trained in these local tests. GPU execution remains deferred by the separately recorded Colab access/usage blocker. The actual runtime must pass fresh smoke, memory, numerical, checkpoint, and reload gates before any trained run is accepted. Blinded independent behavioral review and the two additional paired seed comparisons remain required before recommending adoption. No live configuration was changed, no baseline artifacts were overwritten, and neither the active held-out test contents nor archived test contents were read.

Reviewed content hashes:

| File | SHA256 |
| --- | --- |
| `sft_train.py` | `1d19f350b8cbc7b38106c4795a28186a944bd39e60265f9837deac1d8df22ecb` |
| `test_sft_train.py` | `198ec5c357dfdd9f89a5b5477efe29b639db1b18f6b34448766a8f9eb4a8c686` |
| `execute.py` | `8b93f5603848743a4883445783bc5f6f9d56a5e88d18565c2ce30a85695d3c78` |
| `evaluate.py` | `a695467e7833a7dc6b9961fcbe08ed1fd88584c5adbcfdb2c1d02db265cd9bf5` |
| `choose_checkpoint.py` | `65861c851315b44cf5f61aafef331811723fdb7a8a2440828f35015d64f1bde4` |
