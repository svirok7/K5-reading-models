# Resume this bounded Codex run

Read README.md, AUDIT_FOCUS.md and state.json, then run `workflow.py status`.
Use the frozen copies of GENERATOR.md and AUDITOR.md. Dispatch separate Codex
subagents with model `gpt-6.1-sol`, reasoning effort `high`, and separate contexts.
Retain the generator for corrections and the auditor for independent re-review.
Record their real agent identities; do not invent attestations.

For each incomplete batch, start the batch checkpoint before authoring. The
generator may read the baseline, all accepted batches, and past audit lessons.
The auditor receives the frozen specification and the candidate files. Neither
agent may read held-out test examples or test archives. Give each agent ownership
of its files: generator writes candidate JSONL; auditor writes audit reports.

Wait for the generator to explicitly freeze its files, then run validation. Only
release validated bytes for audit. Ingest the auditor's complete per-example
report through the CLI. If it fails, start a correction round, send the findings
to the generator, wait for freeze, validate again, and request independent review
on the new hashes. Never edit a failed audit to make it pass. The CLI allows at
most three correction rounds. Stop and report unresolved findings at that limit.

After a passing audit, accept through the CLI. Only then release the next batch
to the generator. After both batches are accepted, export and verify 200 aligned
rows, unchanged baseline prefix, and current manifest/checkpoint hashes. Report
the accepted count, actual corrections, tests, and pending human review status.

The Python CLI manages state and validates evidence coverage; semantic word
eligibility is performed by the auditor. This is a Codex-session workflow, not a
scheduled background service. If interrupted, continue from verified disk state
rather than assuming an agent's last chat message reflects current files.
