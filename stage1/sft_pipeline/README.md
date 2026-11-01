# Checkpointed SFT expansion

Python 3 standard library workflow for preserving sft-100-v1 and accepting two sequential batches of 50 before exporting sft-200-v1. Run from any directory using the script's absolute path, or from stage1 as below. No benchmark/test files are read by this workflow.

The same CLI now supports independent bounded runs through `--work-dir`. Baseline/destination paths, counts, reserved batch labels and ID ranges, input buckets, and history counts come from each run's frozen spec. The next run is in ../sft_pipeline_300 with baseline sft-200-v1, batches 006/007, and destination sft-300-v1. From stage1 use `python3 sft_pipeline/workflow.py --work-dir sft_pipeline_300 status`. Its start commands additionally require `--generator-model gpt-6.1-sol --generator-reasoning high`; the earlier run remains compatible with its original commands. A separate directory preserves each run's frozen files, checkpoints, and state.

The Codex coordinator dispatches the generator and auditor subagents, both explicitly configured as `gpt-6.1-sol` with high reasoning effort. The CLI enforces the disk checkpoints; it does not launch models or run a background service. Resume in Codex by reading `state.json`, running `status`, and dispatching only the next incomplete step. Apply the user's lexical-first clarification in [AUDIT_FOCUS.md](AUDIT_FOCUS.md). The run is bounded to 200 total examples.

```sh
python3 sft_pipeline/workflow.py init
python3 sft_pipeline/workflow.py start --batch 004 --generator-agent /root/generator
# Generator authors datasets/synthetic-batch-004/{sft,review}.jsonl.
python3 sft_pipeline/workflow.py validate --batch 004
# Independent gpt-6.1-sol/high agent follows frozen/AUDITOR.md.
python3 sft_pipeline/workflow.py audit --batch 004 --audit-file /path/to/audit.json
python3 sft_pipeline/workflow.py accept --batch 004
python3 sft_pipeline/workflow.py start --batch 005 --generator-agent /root/generator
# Repeat authoring, validate, independent audit, accept for 005.
python3 sft_pipeline/workflow.py export
python3 sft_pipeline/workflow.py status
python3 -m unittest discover -s sft_pipeline -p 'test_*.py' -v
```

`init` freezes copies of the shared specification and instructions, profile, exact list, rubric, and baseline system text. frozen/manifest.json hashes those copies plus all existing baseline top-level files. state.json pins the manifest. A changed baseline or frozen file blocks all subsequent actions. Re-running init verifies the original freeze; it cannot silently establish a new baseline. The original baseline directory is never edited. Inspection uses only its named training/review artifacts, never nested archives.

States are started → validated → audited → accepted → exported. Validation failure and audit failure are durable blocked states; stale disk contents appear as effective_status=stale_files. status and every transition re-read disk bytes and verify the freeze. Each transition writes state atomically and keeps round validation and audit snapshots under checkpoints. Acceptance rechecks both structural validation and stored exact-hash audit; editing either data file invalidates approval. An unchanged accepted batch resumes without another generation or audit. Batch 005 cannot start, validate, audit, or accept until 004 is accepted at its current bytes.

For corrections, repair the generator files, then run `start --batch 004 --generator-agent /root/generator --correction`, validate, and request a fresh independent audit. Initial generation is round 0; at most 3 correction rounds follow. Every round keeps its own audit. A failed audit is not overwritten; another audit requires another round. Any open finding, fail verdict, or false per-example check blocks acceptance. Audit identities are explicit attestations; the script checks the required model/settings and distinct identity strings but cannot authenticate their truth or perform semantic review.

Structural checks enforce 50 aligned rows, reserved IDs/order, identical system, valid message roles, target/context alignment, metadata counts, length buckets, no exact duplicate target across accepted corpus, word-evidence coverage across targets and assistant history, and exact Dolch claims. They do not prove phonics eligibility, reasoning correctness, meaningfulness, safety, factual accuracy, naturalness, or true history dependence. The independent auditor must check those in full. See frozen/AUDITOR.md for the required per-example JSON schema. Child inputs are unrestricted. Review metadata is never part of SFT completion targets.

Export verifies both exact-hash approvals again and concatenates baseline bytes plus accepted 004 and 005 bytes, preserving the original 100 rows byte for byte. A fresh sibling staging directory is renamed atomically; an existing identical export is reusable, while different existing content is rejected. Interrupted `.tmp` export folders require inspection and removal before retry. Completed export artifacts have source/checkpoint hashes and pending-human-review status. Training, tokenizer masks, truncation checks, and held-out evaluation are outside this workflow. Export is not evidence of learning or generalization.

For isolated test fixtures, global `--root /stage1/path --work-dir /pipeline/path` must precede the command. Do not repoint a production work directory to another baseline. Back up the entire sft_pipeline directory, including frozen, checkpoints, and state.json, to resume on another machine. Absolute audit/report source paths are not needed after ingestion; checkpoint copies are authoritative.
