# Bounded expansion from 200 to 300 examples

This run freezes datasets/sft-200-v1 and adds batch 006 (pilot-201..250), then batch 007 (pilot-251..300). Both contain 50 rows: 20 short (1–5 final-user whitespace words), 20 medium (6–15), 10 long (16+), 16 requiring assistant history. Lexical eligibility is primary; independent semantic and phonics review remains necessary. Generator and auditor use gpt-6.1-sol/high with distinct identities. The earlier run, frozen state, and exports remain intact.

From stage1:

```sh
python3 sft_pipeline/workflow.py --work-dir sft_pipeline_300 init
python3 sft_pipeline/workflow.py --work-dir sft_pipeline_300 start --batch 006 --generator-agent /root/generator --generator-model gpt-6.1-sol --generator-reasoning high
python3 sft_pipeline/workflow.py --work-dir sft_pipeline_300 validate --batch 006
python3 sft_pipeline/workflow.py --work-dir sft_pipeline_300 audit --batch 006 --audit-file /path/to/independent-audit.json
python3 sft_pipeline/workflow.py --work-dir sft_pipeline_300 accept --batch 006
# Start 007 only after 006 acceptance; repeat validate/audit/accept.
python3 sft_pipeline/workflow.py --work-dir sft_pipeline_300 export
python3 sft_pipeline/workflow.py --work-dir sft_pipeline_300 status
```

Use the same start command with --correction after repairs. Initial generation is round 0; at most 3 correction rounds. Every edit needs fresh exact-hash validation and a new independent audit. Audit schema is in frozen/AUDITOR.md. Spec hash is the SHA-256 of frozen/manifest.json. Any open finding, failed check, or fail verdict blocks acceptance. Resume reads disk hashes; edited approvals and frozen inputs are rejected. Export preserves baseline bytes as prefix and writes datasets/sft-300-v1 only when both batches pass. Structural checks do not establish semantic correctness or prove eligibility; the independent agent must review every example in full.

Never open data/test.jsonl or archived test material. No training, tokenizer verification, held-out evaluation, learning, or generalization claims are part of this run. All examples remain pending human review. For workflow details and tests see ../sft_pipeline/README.md and test_workflow.py. Configuration is frozen at initialization; use a new work directory for each bounded expansion.
