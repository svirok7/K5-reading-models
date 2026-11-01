# Completed: 200 to 300 examples

Added pilot-201 through pilot-300 in two sequential batches of 50. Both generator
and independent auditor used gpt-6.1-sol with high reasoning effort. Batch 006
was accepted before batch 007 began. Both passed their initial audit with zero
open findings and no correction rounds.

The auditor primarily checked word eligibility and accurate external evidence
for every target and historical assistant word: 100 targets and 36 historical
assistant messages. Batch 006 had 191 distinct assistant forms; batch 007 had
198. Exact-list forms, supported decoding, names, inflections and rationale were
reviewed. Secondary checks found no material defects.

Each new batch retains 20 short, 20 medium and 10 long final child inputs, with
16 history-dependent examples. datasets/sft-300-v1 contains 300 aligned rows
with unique sequential IDs. The previous 200 rows are preserved byte for byte
as the prefix of both SFT and review exports. Exact-hash audit reports and
checkpoints are saved; nine workflow tests pass, including configurable runs.

New examples are **model-generated and independently agent-reviewed, pending
human review**. No held-out examples were opened. No training or tokenizer-mask
verification was performed. Earlier datasets and approvals remain intact.
