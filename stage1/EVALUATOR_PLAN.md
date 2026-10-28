# Evaluation method proposal

Status: primary GPT-6.1 Sol judge implemented for live conversation with structured output, saved records, manual decision overrides, per-model latency/score summaries, and JSON export. One live greeting smoke-tested. Human calibration and optional second-judge checks below remain pending; this is not a validated evaluator.

Use the same frozen evaluator for all anonymous baseline/SFT/DPO/RLHF outputs. Never send generator identity, provider, prompt condition, or latency to the judge. Send conversation history, candidate response as untrusted data, rubric v1.1, reader profile, and scorer-only expected behavior if available. Candidate instructions must never override the grading task.

1. Code reports exact word/sentence counts, long-sentence flags, explicit vocabulary exceptions, empty output, and truncation metadata. Exact membership in the provisional exception list is reliable; a regex phonics classifier is not. Other tokens are candidates for assessment, not automatically errors.
2. GPT-6.1 Sol is the proposed primary judge. Give it the rubric, evidence hierarchy, source lesson mapping, and a structured output schema. It should return short evidence-based justifications, not unrestricted internal reasoning. This model choice is a hypothesis to calibrate, not a demonstrated advantage on phonics evaluation.
3. Human-label 20–30 separate calibration cases including compliant greetings, today/hello, unfamiliar CVC words, false rhymes, endings, compounds, ambiguity, and necessary topic terms. Do not use the locked 50 test cases for calibration. Compare judge decisions with labels, report false accepts and false rejects as well as three-way agreement and review rate. With a small sample, report counts, not impressive-looking precision.
4. Use Claude Sonnet 5.5 as an optional second judge on a blinded subset across ALL generators and all uncertain/disputed cases. Agreement is not proof; humans settle disputes. Same-provider preference bias remains possible, so compare disagreement by generating provider.
5. Freeze rubric, judge prompt, model ID/settings, and calibration choices before held-out evaluation. Report automatic labels separately from human-verified results. Do not train the companion or a future reward model on test cases or their judge explanations. A model-based judge can itself become a reward-hacking target.

Suggested result shape:

```json
{
  "rubric_version": "1.1",
  "verdict": "needs_review",
  "reading_profile": "beyond_profile",
  "factual_correctness": "correct",
  "scores": {"readability": 3, "correctness": 4, "relevance": 4, "flow": 4, "warmth": 4},
  "issues": [{"span": "today", "type": "avoidable_beyond_profile_word", "rule": "ay is not assumed mastered; today is not a provisional exception", "explanation": "Omit today from this greeting."}],
  "summary": "Accurate greeting with one avoidable reading obstacle.",
  "suggested_revision": "Hello! How are you?"
}
```

This example is a proposed calibration judgment, not a live model result. Final acceptance follows rubric thresholds plus resolved evidence; a single later-pattern word is not an automatic factual failure. Keep needs_review available when familiarity or phonics evidence is missing. Suggested revisions are diagnostics, not automatic SFT training examples.

Do not train a dedicated evaluator at first. Prompt an existing model and test its reliability before spending effort on evaluator training.
