# Improve reading compliance and meaning: execution plan for GPT-6 Sol, medium

## Goal and fixed constraints

Improve the Qwen3-1.7B reading companion substantially while preserving meaning, truthfulness, and safety.

Workspace: `/Users/viroksharma/Desktop/Personal/Projects for Fun/Reading-Model/stage1`

Current baseline:

- Dataset: `datasets/sft-300-v2`, 300 examples.
- Adapter: `runs/qwen-sft300-v2-lora-allocator-20261030-008/adapter`.
- Training: one epoch, 38 optimizer updates, rank 16, alpha 32, dropout 0.05, all-linear adapters, learning rate `1e-4`, gradient accumulation 8.
- Loss decreased sharply and then flattened. Existing UI results suggest simpler vocabulary but persistent meaning and identity failures.

Execute two bounded training experiments: existing data for more epochs, and improved data with broader coverage. Prepare the improved data while conducting the first experiment.

**Non-negotiable constraints**

- Evaluate raw responses; no inference-time checker, rewriting, or constrained decoding.
- Reuse existing development inputs. Do not create a new development suite.
- Never inspect `data/test.jsonl` or archived test contents.
- Preserve existing datasets, adapters, UI records, and comparison artifacts.
- No rank sweep, learning-rate sweep, full fine-tuning, RL, paid evaluator calls, or compute purchases during this cycle.

## 1. Coordination and frozen evaluation

The new chat’s executor is **GPT-6 Sol, medium**. It coordinates implementation and execution.

Use explicitly configured **GPT-6.1 Sol/high** subagents for data authoring and independent review, as previously requested. Spawn with `fork_turns="none"` and provide complete briefs. At most three workers run alongside the coordinator; agents own separate files.

Create a fresh experiment directory with a manifest and resumable status record. Record data, prompt, code, model, tokenizer, adapter, and environment hashes. Never overwrite a completed experiment.

Build the evaluation set from:

- The existing 20 development cases.
- The 25 saved SFT UI cases, including their exact histories.

Exclude exact duplicate prompt/history combinations and cases overlapping training by exact match or close semantic duplication. Preserve all exclusions and reasons. Keep distinct histories even when final user text matches. Freeze the resulting cases before reviewing new training examples.

Do not add the overlapping 13-case replay as another independent sample. Retain its historical report for context.

Generate a current-adapter reference on the frozen inputs. Reuse an existing response only when input, model, template, decoding, and seed metadata match; otherwise generate a fresh response. New base-model runs are unnecessary for this cycle—the primary comparator is the current SFT adapter.

Use the current full reading-profile prompt, pinned model revision, no-thinking mode, identical inference hardware/precision, and existing decoding settings: temperature 0.7, top-p 0.8, top-k 20, maximum 128 new tokens. Freeze reproducible per-case seeds.

## 2. Implement and run the same-data epoch experiment

Extend `sft_train.py` to support integer multi-epoch runs safely. The current helper hardcodes one epoch, 38 updates, and each row appearing once; update these assertions rather than bypassing them.

Required changes:

- Validate dataset size against its manifest.
- Verify every approved row is consumed once per epoch.
- Log training loss at each optimizer update.
- Save reloadable adapters and resumable training state at each epoch.
- Retain all epoch checkpoints.
- Extend replay verification to accept hash-bound intermediate checkpoints.
- Preserve existing masking, finite-gradient, zero-skipped-update, allocator, and reload safeguards.

Run a fresh three-epoch experiment on the unchanged 300 examples. Keep rank, learning rate, batch settings, and other training settings fixed. Use linear learning-rate decay across the entire run and seed 42.

Expect 114 optimizer updates after confirming epoch-boundary accumulation behavior with a test. Do not improvise continuation from the historical completed adapter.

The new epoch-one checkpoint has a different learning-rate trajectory from the historical one-epoch run. Document this; do not attribute every difference solely to epoch count.

Evaluate each epoch checkpoint on the frozen development inputs. Do not add validation-loss targets or a separate reference-answer authoring project.

## 3. Improve data in parallel, then run the expanded-data experiment

The data author reviews the existing training corpus for examples that encourage repetition, weak relevance, or invented experience. Preserve the source dataset; corrections belong in a versioned successor with explicit before/after records.

Create **300 new training examples**, with 50 assigned to each primary category:

1. Meaning-preserving simplification and explanations.
2. Exact word forms, contractions, and lexical boundaries.
3. Corrections, refusals, and topic changes.
4. Honest identity and personal-experience responses.
5. Emotional support and safe, relevant help.
6. Longer conversation tracking and recovery from imperfect history.

Across the new examples:

- Exactly 150 require preceding conversation.
- At least 100 contain three to five prior assistant turns.
- At least 50 contain a flawed prior assistant response requiring recovery.
- Child vocabulary remains unrestricted.
- Target responses must be eligible, meaningful, accurate, and natural.
- Reference examples from the evaluation set must not be copied or closely paraphrased into training.

Keep review rationale and word-level eligibility evidence outside the SFT messages. Imperfect historical assistant replies must be explicitly annotated and excluded from completion loss.

Use six batches of 50. An independent agent audits every example and any corrections to the original corpus. Structural checks do not substitute for semantic or linguistic review. Allow three correction rounds per batch, then report unresolved findings rather than weakening requirements.

Export a new 600-example dataset with immutable manifests. Mark approval accurately as independent agent review, pending human review where applicable.

Train one fresh three-epoch run on this dataset using the same model, rank, learning rate, scheduler policy, and batch settings as the 300-example experiment. Save and evaluate each epoch checkpoint.

Report both epoch and update counts: this experiment changes data coverage and total optimization exposure, so it is not a pure data-size ablation.

## 4. Review and select using joint quality

Randomize candidate labels and conceal identities from the reviewing agent. Score:

- Reading rubric: word eligibility, length, rhythm.
- Meaning preservation and relevance.
- Truthfulness and safety.
- Repetition and response to corrections.

**Joint success** requires reading acceptance plus meaningful, truthful, safe content. Record serious failures individually; they cannot be compensated for by a higher reading score.

Choose the checkpoint with the most joint successes; break ties in favor of the earlier checkpoint. Keep single-turn and fixed-history results separately visible. Fixed histories measure next-turn performance, not complete autonomous conversations.

The target for a substantial gain is **at least +20 percentage points in joint success over the current adapter**, with no new serious safety or identity failures on paired cases. This is an experimental decision threshold, not a guaranteed outcome.

If a candidate meets that target, compare it with the current adapter using two additional generation seeds on the same frozen cases. Require positive joint-success improvement in both repeats and no new serious failures before recommending adoption. Do not treat repeated seeds as independent cases.

If no candidate qualifies, retain the current adapter as the reference and explain whether the next investment should be better data, a larger base model, or a bounded rank/preference-training experiment. Do not launch those follow-ups automatically.

## 5. Verification, execution gates, and deliverables

Before GPU execution, test:

- Multi-epoch row consumption and update accounting, including partial batches.
- Completion masking, especially imperfect assistant histories.
- Epoch checkpoint retention and exact reload.
- Resume integrity for optimizer, scheduler, scaler, and RNG state.
- Evaluation exclusion of targets and reviewer notes.
- Dataset separation and immutable hashes.

Use the existing Colab/T4 workflow. Each changed training configuration must pass its smoke test and the existing 15% memory-headroom gate. Stop on numerical, integrity, or memory failure; preserve diagnostics. Do not silently switch precision or purchase hardware.

If GPU access is unavailable, complete code, tests, audited data, and the executable notebook, then report the exact access blocker.

Deliver:

- Versioned training data and independent audit records.
- Tested training/evaluation code and execution notebook.
- Training-loss curves and per-epoch quality results.
- Paired examples showing both gains and regressions.
- A concise adoption recommendation, including limitations and remaining human-review needs.

No automatic replacement of the live UI adapter. Provide the selected artifact and evidence for the user’s adoption decision.
