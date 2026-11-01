# 100-example SFT candidate dataset

Exactly 100 examples in stable order: pilot-001 through pilot-100. sft.jsonl contains only conversational prompt/completion fields. review.jsonl is line-aligned and contains IDs, one-sentence word-choice reasoning and audit metadata; never feed that metadata to normal SFT.

Use completion_only_loss=True and the Qwen3 native chat template with enable_thinking=False. The full v1.5 system profile is included in every prompt. Only the final assistant completion is a target; historical assistant turns are prompt context. Avoid silent truncation; verify sequence lengths and masks using the selected training runtime before training.

All examples are model-authored and self-reviewed, pending human review. This export is not proof of independent lexical validation or training success. No held-out data was opened. Earlier batches were retained as authored; this task checked new targets/history and export alignment. No new eligibility Q&A training task was added: reasoning stays outside the completion.
