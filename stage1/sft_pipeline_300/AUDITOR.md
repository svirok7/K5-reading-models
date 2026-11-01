# Independent auditor instructions

Use model gpt-6.1-sol at high reasoning. Review lexical eligibility first, including every target and historical assistant word, before considering conversational polish. The generator must also attest gpt-6.1-sol/high. You must be a different agent from the generator. Read the frozen spec, system, profile, exact word list, rubric, and the batch's current sft.jsonl and review.jsonl in full. Do not open data/test.jsonl or any archived test material. Hash the actual files you reviewed. Review only the reserved batch and compare earlier SFT targets if necessary for originality. The checkpoint verifies identity declarations and bytes; it cannot verify that a model identity is truthful or replace your linguistic judgment.

For every example, inspect every word in the target AND all historical assistant turns against the independent eligibility routes: exact permitted word form, or a supported decoding pattern with valid evidence. Check every lexical_evidence claim and external word_choice_reasoning for accuracy, including apparently easy words and non-Dolch names. Check that the final response answers the request meaningfully, makes sense factually, uses history when marked required, and needs that history rather than merely mentioning it. Flag unsupported spellings, false evidence, ambiguity, misleading facts, safety problems, excessive/awkward phrasing, and metadata mismatches. Do not treat a script's coverage pass or a generator's self-review as phonics verification. New training objective is word selection with external rationale, not eligibility Q&A.

Write UTF-8 JSON with the following exact top-level fields (summary optional). Obtain spec_sha256 from `validate` output; it is the frozen manifest SHA-256, not spec.json alone. Order examples exactly as the 50 review rows. Every check is a boolean, including history_use=true when an example correctly has no required history. A pass needs all four checks true and no open findings. All unresolved findings, regardless of severity, block acceptance. Resolved findings may be retained as provenance only after verifying fixes in the CURRENT bytes. On any edit, independently re-audit the final files and issue new hashes; never reuse a prior approval.

```json
{
  "batch": "006",
  "spec_sha256": "SHA256 of frozen/manifest.json",
  "sft_sha256": "SHA256 of batch sft.jsonl",
  "review_sha256": "SHA256 of batch review.jsonl",
  "auditor": {"agent_id": "/root/auditor", "model": "gpt-6.1-sol", "reasoning_effort": "high"},
  "examples": [
    {"id": "pilot-201", "verdict": "pass", "checks": {"word_eligibility": true, "reasoning_accuracy": true, "meaningfulness": true, "history_use": true}, "findings": []}
  ],
  "summary": "Review scope, concrete findings, and limits. All 50 actual rows required."
}
```

Each finding is `{"id":"F1","severity":"low|medium|high","status":"open|resolved","detail":"Exact word or passage, why it fails, and requested correction."}`. A fail verdict blocks even if findings are accidentally empty. Submit your report to coordinator, which runs audit then accept. Never edit the generator's examples as part of the audit; request corrections so they remain attributable. Independent model review does not imply human approval or demonstrated learning.
