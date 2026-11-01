# First SFT experiment — training and development comparison complete

Ordinary LoRA completed one epoch on all 300 examples with 38 applied optimizer updates and zero skips. The allocator fix, set before PyTorch import, produced 44.75% smoke headroom and 47.30% full-training headroom against the unchanged 15% target. Final adapter weights reloaded identically and inference passed. The downloaded export and every adapter file match their saved hashes.

Reading Lab now has the local adapter configured under Qwen SFT, while the base option remains available. All 13 matched development responses completed without truncation. Provisional coordinator-model review found three reading passes versus zero base passes, but also an irrelevant dog-identity answer and exact history repetition. Human review is pending; this is not a broad quality claim. Detailed grouped counts, paired examples, limitations and annotations: `evaluation-sft-v1/results/comparison-001/REPORT.md`.

All 23 training tests and 5 evaluation tests pass. The notebook remains LoRA-first with execution gates off. Baseline material is preserved and held-out content remains untouched. Local run artifacts: `runs/qwen-sft300-v2-lora-allocator-20261030-008/`. Export SHA256: `6db5dd5f7da748b1fdba8c135084d47702fe23de8ba24b30dbbcfdf2ec936558`.

## Execution history (historical entries below)

# Allocator fix succeeded — training and final reload complete

Run `qwen-sft300-v2-lora-allocator-20261030-008` completed one epoch on all300examples,38applied optimizerupdates,0skips, with finite nonzero gradients on everyupdate. Fulltraining/reload measured47.30%headroom, above15%required. Finaladapter reloaded against pinnedbase with identicalweights and verifiedinference. The allocator setting `expandable_segments:True` was set before torchimport and bound in runcontext/environment. All23trainingtests pass; independentreview approved. The distributednotebook remains LoRA-first with executiongatesoff.

Verified export in Drive: `MyDrive/Reading-Model/sft/qwen-sft300-v2-lora-allocator-20261030-008/adapter-export.zip`. SHA256 `6db5dd5f7da748b1fdba8c135084d47702fe23de8ba24b30dbbcfdf2ec936558`.

Actual runrecord saved locally at `runs/qwen-sft300-v2-lora-allocator-20261030-008/run-record.json`. Smoke report: `sft-diagnostics/lora-allocator-008-smoke-report.json`. No behavioral improvement claim yet: ReadingLab installation and developmentcomparison await localexport transfer. Two in-appbrowserdownload attempts returned no localartifact; manualdownload requested. Baseline matchedcontrol is ready and heldout content remains untouched.

## Earlier execution history

# Allocator experiment — full training running

User authorized the allocator change. New run008 sets expandable_segments:True before torch import, recording it in run identity and environment. Real LoRA smoke passed with44.75%headroom (peakallocated7,307,075,072bytes; peakreserved8,489,271,296bytes),2appliedupdates/0skips, finitegradients, exactsave/reload andinference. All23offline trainingtests pass; independentreview approved. Fresh full training is running; no finaladapter or SFTcomparison confirmed yet. See sft-diagnostics/lora-allocator-008-smoke-report.json.

## Prior execution history

# First SFT experiment — stopped at memory gate

Updated 2026-10-30, Asia/Kolkata. The requested execution reached the plan's explicit stop condition: both ordinary LoRA and QLoRA missed the required 15% free-memory margin on the available Tesla T4. No final trained adapter or baseline-versus-SFT comparison exists.

| Clean smoke run | Mode | Peak allocated bytes | Peak reserved bytes | Free-memory margin | Result |
| --- | --- | ---: | ---: | ---: | --- |
| 006 | LoRA | 7,311,627,776 | 14,510,194,688 | 6.25% | Insufficient headroom |
| 007 | QLoRA | 6,675,388,928 | 13,813,940,224 | 10.70% | Insufficient headroom |

Both final smoke runs passed all-row actual collator checks (300 examples, 4,683 supervised tokens, maximum sequence 1,825), finite nonzero gradients, frozen base, changing adapter weights, two applied optimizer updates with zero skips, exact adapter save/reload and inference. Smoke weights were discarded. The memory target measures operational driver free memory and allocator reservation, rather than live allocated tensors alone. Clean LoRA began with zero allocated/reserved CUDA memory. QLoRA was selected explicitly after LoRA failed headroom, with unchanged data and experiment settings. Neither mode qualifies for the full run.

The distributed notebook defaults to ordinary LoRA with execution gates off. All 23 training and 5 evaluation offline tests pass. Kit SHA256: `53516179b02f2b63a4040461bbcb0fdae38f6d3cec9b17dc3c5e92a564f719c0`. Notebook SHA256: `81d1e88e0954a1d1774a528ab37ebe28a16c0ae8e164b7ea90fdb355cd9a16d8`. The kit has five files and excludes evaluation and audit reasoning. The independent review covers masking, precision, gradient/update guards, smoke isolation, resume metadata and reload checks.

Earlier failures are preserved: native BF16 detection was corrected for the T4; incompatible optional torchao was removed from the disposable runtime. Historical full run003 stopped before its first optimizer update due to FP16 overflow at initial scale65536. A zero-update replay on identical initialized weights and the exact failed eight rows established finite gradients at scales1024/256; the helper now explicitly records scale1024 and rejects skipped optimizer updates. Fresh final smoke runs passed this stricter numerical gate. The old root `sft-gpu-smoke-report.json` is historical run003 evidence, not a final passing gate.

The saved16 baseline records remain untouched in an immutable hash-bound snapshot, separated into four settings groups. A matched13-prompt no-thinking base control completed in `evaluation-sft-v1/results/matched-base-001`; historical templates were not assumed equivalent. No SFT responses or quality claims were produced. Human dataset review remains pending. Held-out content remains untouched.

Diagnostics: `sft-diagnostics/colab-20261030/` contains actual run configs, environments and smoke/failure reports. The verified archive `sft-diagnostics/sft-execution-diagnostics-20261030.zip` has SHA256 `395dbb0fc9a6c8795b9d7e631a6d06407475616292bea1c141ad49fcb0f73875`. Earlier loss-scale replay evidence is retained separately in `sft-diagnostics/fp16-scale-replay.json`.

Execution notebook: https://colab.research.google.com/drive/1GC5ijOkkXFBZeMnLO6PDmWrVB5DSjroJ?authuser=1

To continue beyond this stop requires a revised plan: for example, use a larger GPU or explicitly review allocator/memory changes and rerun both gates. No purchases, subscription changes, publication, baseline overwrite or final full training occurred.
