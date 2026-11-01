# Preparation complete where access allowed; experiment remains incomplete

Retain the current adapter as the reference. No new adapter was trained, no fresh reference responses were generated, and no adoption gain has been measured. The live Reading Lab configuration is unchanged. There are no new loss curves, quality scores, or paired gains/regressions to report.

Two external blockers stopped execution: Colab rejected the T4 connection because of GPU usage limits; the explicitly configured GPT-6.1 Sol/high author and reviewer then hit account usage limits. No hardware, credits, or subscriptions were purchased. The exact observed errors are preserved in access-blocker.json.

## Completed and verified

The immutable evaluation set contains 34 cases: 16 single-turn and 18 fixed histories. It reuses the existing 20 development inputs and 25 saved SFT UI records, preserving exact histories. Seven exact duplicates and four close training overlaps were excluded with reasons. The overlapping historical 13-case replay is not counted. Active and archived test contents were not inspected.

The training helper supports integer epochs, per-epoch row accounting, one loss log per optimizer update, retained epoch checkpoints, exact adapter reload, and hash-bound optimizer/scheduler/scaler/RNG resume. CPU tests confirm 114 updates for 300 rows and 225 for 600 over three epochs, including partial accumulation. Tiny PEFT tests check uninterrupted versus resumed weights, row order, losses, and learning rates. These tests do not establish T4 numerical stability or memory headroom.

All 40 offline tests pass from the extracted sealed kit: 29 training tests and 11 evaluation/selection tests. All eight notebook code cells compile. The package verifies code, data, prompt, tokenizer/model artifacts, adapter, and preparation-environment bindings. The actual T4 smoke and unchanged 15% headroom gate remain mandatory and unrun.

The 300 source rows and all 250 saved new draft rows pass actual pinned-tokenizer completion-mask checks locally. Their maximum lengths are 1,825 and 1,831 tokens respectively, below the 2,048 limit. Historical assistant replies, including deliberately flawed replies, are masked out of completion loss. This is a mechanical check, not approval of the draft content.

## Data and independent review

| Material | Saved | Independent status |
| --- | ---: | --- |
| Original source corpus | 300 | All reviewed; semantic fixes needed at rows 32, 45, 65; source preserved |
| New meaning/explanation batch | 50 | Approved after round 2 |
| New exact-form batch | 50 | Approved after round 2 |
| New correction/topic-change batch | 50 | Approved after round 2 |
| New identity/experience batch | 50 | Round 1: 49 pass; row 50 has an unresolved grounding claim |
| New emotional-support batch | 50 | Independent review pending; word evidence incomplete |
| New long-history/recovery batch | 0 | Not authored |

The immutable `datasets/reading-new150-reviewed-v1` contains only the 150 independently approved new examples and their audit records. It is explicitly a partial artifact, with human review pending, and cannot authorize the requested 600-row run. The full 600-row dataset was not exported. The complete saved authoring/audit state is preserved in `authoring-and-audit-snapshot-v1.zip`.

The current 250 draft additions include 125 history rows, 125 with three to five prior assistant turns, and 55 flawed-history recovery rows. To finish the specified quotas, the last batch must add exactly 25 history rows. Do not weaken the semantic or lexical requirements to complete the count. Original-corpus fixes still need exact before/after export records and independent hash binding.

## Executable delivery and remaining execution

`reading_compliance_colab.ipynb` and `reading-compliance-colab.zip` are sealed and tested as a **partial preparation**. Their plan authorizes only the unchanged 300-example, three-epoch experiment. It generates a fresh current-adapter reference and evaluates each retained epoch checkpoint when a free T4 is available. The 600-row run, extra-seed confirmation, and adoption selection are explicitly blocked by the incomplete corpus. Preserve this sealed version and prepare a new version after full data approval.

The complete planned experiments remain:

| Run | Epochs | Planned updates | Planned row exposures |
| --- | ---: | ---: | ---: |
| Unchanged 300 rows | 3 | 114 | 900 |
| Approved expanded 600 rows | 3 | 225 | 1,800 |

The fresh epoch-one checkpoint follows a different learning-rate trajectory from the historical one-epoch adapter. The expanded run changes both data coverage and optimization exposure, so it is not a pure data-size ablation.

Raw-response generation, concealed independent review, serious-failure accounting, paired reports, loss plotting, earlier-epoch selection, and two conditional repeat seeds are implemented. Initial independent code reviews and their exact reviewed hashes are preserved; final incremental hardening and partial-delivery changes received coordinator verification after the independent workers became unavailable.

The next action is to finish the configured author/reviewer work when their access returns, then run the notebook on an available free T4. Do not recommend a larger base model, rank change, or preference training from nonexistent new results. Any later adoption recommendation requires at least +20 percentage points in joint success, no new serious paired identity/safety failures, and positive gains on both additional paired seeds. Human review remains pending; no automatic UI replacement is permitted.

Exact continuation steps, batch findings, and preservation rules are in RESUME.md. Machine-readable state is in status.json; hashes are in manifest.json and delivery.json.
