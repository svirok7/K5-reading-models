# Verified training execution

Both fresh Qwen3-1.7B all-linear rank-16 LoRA runs completed on T4/FP16 with the sealed configuration. The 600-row run resumed from epoch-two checkpoint 150 after a Colab usage-limit interruption. Updates 151–185 from the abandoned segment remain preserved separately; the completed trajectory uses the resumed final epoch. Small FP16 replay differences are recorded in resume-replay-observation.json.

| Run | Epochs | Optimizer updates | Row exposures | Operational memory headroom |
|---|---:|---:|---:|---:|
| same300 | 3 | 114 | 900 | 47.29% |
| expanded600 | 3 | 225 | 1800 | 43.68% |

The expanded-run memory figure covers the resumed final-epoch invocation and reload checks; it is not a continuous memory trace across the interrupted earlier runtime. Its original configuration smoke passed with46.35%headroom. Each epoch checkpoint passed weight reload and inference checks. Every approved row was consumed exactly once per epoch. The resumed 75-update segment had zero skipped updates, finite nonzero gradients, and restored scaler progress from150 to225. The pre-resume epoch ledgers and metadata remain preserved.

The fresh 300-row epoch-one checkpoint follows a 114-update learning-rate schedule, unlike the historical 38-update adapter. The expanded run changes data coverage and optimization exposure together, so this is not a pure data-size ablation.

Both loss CSVs match every saved per-update loss and learning-rate record. Plotting in Colab additionally verified the final retained checkpoint and ledger. Lower training loss alone does not establish quality improvement.

All seven response groups contain34 cases (238responses). Tokenized input hashes, seeds, model/tokenizer artifact hash aggregate, and inference environment match. The current comparator has one preserved incomplete generation; all six candidate groups are complete. Quality ratings and selection are separate pending artifacts.
