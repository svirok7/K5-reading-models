# Independent delivery and plotting review

Reviewed on 2026-10-30 by the GPT-6.1 Sol / high training agent. The coordinator authored the reviewed scripts. The reviewer did not invoke `build()` or read/use an unapproved 600-row manifest.

## Findings sent to the coordinator

All six findings below were reported to the coordinator, corrected, and reinspected. No unresolved blocking finding remains in the reviewed source. The actual delivery package still requires the approved successor manifest and a real build; GPU execution remains blocked.

1. **Fresh-Colab tokenizer prerequisite:** the notebook runs `test_sft_train.py` before downloading the pinned tokenizer. Both the collator class setup and flawed-history test require the exact cached Hugging Face snapshot with `local_files_only=True`. A fresh runtime must prefetch the pinned tokenizer before running these tests.
2. **Missing notebook fixture:** `NotebookPreflightTests` reads `STAGE/sft_colab.ipynb`, but the payload omits it. Package the existing notebook as a hash-bound read-only fixture, or provide an equivalent explicit fixture and update the test accordingly.
3. **Known optional dependency startup guard:** the generated startup omits the previously vetted incompatible optional `torchao` cleanup. That can recreate the documented PEFT import failure in affected Colab environments. Reuse the scoped preflight, record its result, and obey its restart requirement before importing PEFT.
4. **Unbound paired-example reports:** `paired_examples` does not verify `review.jsonl` or `identity-key.json` against their manifest, or establish that the supplied summary belongs to those review inputs. A mechanical fixture confirmed that it emits altered unbound candidate text when supplied a summary declaring another frozen run. Verify the review hashes and matching frozen inputs, checkpoint record hashes, seed offset, and inference group before reporting paired gains/regressions.
5. **Unverified plotted loss values:** `loss_plot` verifies the number/step labels, but not finite losses or agreement with the saved training ledger / final hash-bound checkpoint state. Validate those sources before plotting, so stale or altered logs cannot become claimed real metrics. Source inspection established this gap. The fix is exercised below with mocked rendering because Matplotlib is absent from the local virtual environment.
6. **Missing documented instructions:** the generated notebook refers to experiment `README.md`, which is not included in its package. Include the instructions required for summarizing, repeat-seed evaluation, and checkpoint selection.


## Resolution verification

The payload now includes the original `sft_colab.ipynb` in the code-file hash binding and includes the experiment README. Generated setup executes only the original notebook's reviewed dependency cell 4, with explicit LoRA mode. That cell pins and checks dependencies, performs the scoped optional-torchao cleanup, records restart requirements, and tests CPU PEFT dispatch. The new notebook prefetches the exact pinned tokenizer before local-only tests. Source inspection found no additional external variable required by that dependency cell.

All eight newly generated code cells compile after these changes. An AST inspection of the dependency-diagnostic `write_text` suffix confirms it is exactly one newline character; it is neither an unterminated string nor a literal backslash plus `n`. Setup diagnostics are preserved in the Drive output. Execution now preserves the original environment and appends invocation environments, rejecting changed package versions, GPU, compute dtype, or allocator settings.

Loss plotting now verifies the final checkpoint against the run's record-hash binding, compares its loss points against the saved `trainer_state.json` log history, checks all loss/LR values are finite, and requires agreement with the audited per-update ledger. Paired reports now verify both review file hashes and the summary's review-manifest, frozen-input, candidate-record, seed, and comparison-group bindings.

Tiny temporary mechanical fixtures accept correctly bound loss and paired-report inputs and reject altered review text, a summary from another frozen run, a changed logged loss, and a NaN loss. Loss rendering was mocked; no fabricated fixture values were delivered as measured results or a real chart. The extraction tests were repeated after the setup changes and still pass. All 11 evaluation/selection tests also pass again.

Reviewed final source hashes:

| File | SHA256 |
| --- | --- |
| `build_delivery.py` | `15f47c5bcb974d4be0a6ab740451211b62f08a705f08bdb2d4b6684a346167f7` |
| `plot_results.py` | `a714fc2bc91c6a41b4129c0386e5202bf91f2432c83e5cfa23173d1e5d6db135` |
| `execute.py` | `525690ef760822554aa90cecbeea4ab2e625db4224eff5bef1cb21eeba4a247e` |
| `evaluate.py` | `5949109b09c0785607508de08fafd2147b99c97eabedafe2223ba8e1ceb627fb` |

## Checks completed without building

The eight generated Python code cells were extracted by evaluating only the AST expression that constructs the notebook cells, with a placeholder kit hash. Every code cell compiles. The build function was never called, no real plan/package was sealed, and no GPU or network operation was executed.

The generated extraction cell was run against small temporary mechanical archives. It accepts a correctly bound kit and rejects all five tested changes: `..` traversal, absolute paths, duplicate entries, symlink entries, and an incorrect whole-archive SHA256. Successful extraction also verifies the exact archive inventory, per-file hashes, and packaged plan hash. Using `archive.namelist()` after the context manager closes the archive works in this fixture; it does not require an open file handle.

Source review confirms that the zip includes only explicit code/training files, selected frozen development inputs, rubric/profile instructions, and the current adapter record. Historical adapter weights are supplied separately from Drive and checked against the bound record. The builder preserves existing sealed plans, archives, notebooks, and delivery records. Archive contents are hashed before upload and compared byte-for-byte after construction.

All 11 evaluation/selection integrity tests pass locally:

```text
./.venv/bin/python -m unittest discover -s experiments/reading-compliance-20261030-001 -p 'test_*.py' -v
Ran 11 tests: OK
```

These tests and the extraction fixtures establish mechanical integrity, not Qwen training, behavioral quality, real Colab availability, or GPU memory headroom. The 600-row audit remains separate and is a prerequisite to building the real delivery artifact. No active held-out or archived test contents were read.
