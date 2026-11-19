# Trained Glimmer is ready for UI testing

Added dedicated Muse Glimmer30B SFT600examples/3epochs choice in Reading Lab. It samples the final trained checkpoint through Fireworks Serverless Training API without a GPU deployment. Model, saved checkpoint, tokenizer and native final-response prefix are fixed. Generation is capped128tokens with no automatic retry.

The existing reading evaluator, rubric and manual decisions are preserved. A single durable3.99USD ledger caps combined generation+judge spend; each request reserves its maximum before any paid call. Only provider-reported complete usage releases a reservation. Judge explicitly uses Standard service tier. Other paidAPI routes remain disabled. UI displays used/held/remaining budget.

Verified live through the UI: Hi! What can a cat do? => A cat can sit, nap, and purr. The same Sol reading judge scored it not_acceptable because purr is out of profile. This establishes working inference and scoring, not general quality. See serving/UI_VERIFICATION.json for record identity and budget.29offline tests pass, plus worker mocked tests and native tokenizer preparation.

The existing Start Reading Model.command now loads Fireworks credentials from the ignored project.env fallback, while retaining its original existing OpenAI key source. No new training or deployment was created.
