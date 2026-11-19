# Exact sft-600-v1 data preparation

The original dataset remains unchanged. All 14 artifacts in its frozen manifest match their recorded SHA-256 values, and `manifest.sha256` matches the exact expected manifest digest:

- Source manifest: `932e287304906a7e8dbf1f293011d0592a2a847e9450837081e0324f31024df3`
- Source `sft.jsonl`: `844223c79402af7d93937c9485f182d7c5381434b4e2234381a989663466424e`
- Source `review.jsonl`: `07a4aced136602c4c88555e93bff7a9194ba9e2bb94bea4e46059efa17e6ca81`

`train.messages.jsonl` contains exactly the same 600 rows in the same order. Each row combines the original `prompt` and its single `completion` into `messages`; no roles, message strings, system prompts, final replies, punctuation, or whitespace inside strings change. JSON object key order and serialization are canonicalized. Every historical assistant message remains input. The source's review messages omit the system message; validation checks them against the original prompt after its system message.

247 rows contain a total of 601 historical assistant turns. The 143 rows with annotated history defects are preserved exactly. No heldout or archived evaluation set was read, edited, generated, or included. No account dataset was uploaded, and this work makes no inference, training, or paid API calls.

## Final-reply-only supervision

The export intentionally carries no `weight` fields. The loss policy is an explicit Training API recipe configuration:

```python
train_on_what = 'last_assistant_message'
renderer_name = 'muse_glimmer'
tokenizer_model = 'meta-models/Muse-Glimmer-30B'
tokenizer_revision = 'a4e59da52a7bc87ae7251dd5545c0dd437c44b68'
tokenizer_trust_remote_code = False
```

Do not use the recipe's default `all_assistant_messages`: it would supervise defective history. The per-row `message_loss_plan` is an audit declaration, not a field consumed by Fireworks. Only `messages` goes into the recipe. Training must use all 600 rows with no split, carveout, truncation, filtering, or skipped examples.

The [official recipe](https://github.com/fw-ai/cookbook/blob/74e103ab4249d508912ccf264793e655980eead0/training/recipes/sft_loop.py) and [render dispatcher](https://github.com/fw-ai/cookbook/blob/74e103ab4249d508912ccf264793e655980eead0/training/utils/supervised.py) are pinned to cookbook revision `74e103ab4249d508912ccf264793e655980eead0`. The [Muse renderer](https://github.com/fw-ai/cookbook/blob/74e103ab4249d508912ccf264793e655980eead0/training/renderer/muse_glimmer.py) identifies the tokenizer template revision above. Native Muse output includes routing syntax ` to=user<|message|>` before the exact reply and `<|eot|>` after it; these tokens are part of the final assistant output. The renderer also adds native system metadata. Those context tokens must have zero loss.

## Verification and blockers

`convert_dataset.py --verify-only` verifies every frozen source artifact, all 600 content identities, roles, ordering, review bindings, and declared message masks. Five focused tests also check preservation of flawed history, deterministic regeneration, rejection of unexpected completion/weight fields, and detection of target or mask tampering.

`verify_token_masks.py` is a separate hard gate. It uses the pinned official dispatcher and renderer with the real tokenizer to render every row, compares the model prompt prefix against zero-loss positions, checks the exact final output suffix, and verifies shifted `target_tokens`, model inputs, and loss weights. It rejects any row exceeding the configured context budget or producing multiple/no datums. It writes `token_mask_proofs.jsonl` and `token_mask_validation.json` only after all 600 rows pass.

**Completed:** all 600 rows passed real-tokenizer verification in the shared locked runtime (`fireworks-ai 1.2.32`, `torch 2.14.1`, `transformers 5.10.4`). Every full rendered sequence also matches the pinned Hugging Face chat template token for token. There are zero context loss positions and zero dropped, truncated, or split rows. Sequence lengths range from 1,727 to 1,879 tokens; `max_seq_len=4096` safely covers every example. One epoch contains 1,059,725 full-sequence tokens and 9,104 supervised final-output tokens. No data compatibility blocker remains.

`validation.json` describes the independent content/message-plan check; `token_mask_validation.json` records the actual token proof and binds the dataset and tokenizer digests. Launch must require its `status: passed`, 600 rows, matching dataset digest, zero context loss, zero dropped/truncated/split rows, and the exact renderer/tokenizer/cookbook configuration. The proof's per-row token/weight digests appear in `token_mask_proofs.jsonl`. Source metadata remains unchanged, including its historical approval/tokenization/training flags.

For execution, set `tokenizer_model` to the absolute path of this `data/tokenizer` snapshot, keep the pinned revision and explicit renderer above, and use local files. This uses the exact public tokenizer while avoiding a runtime download.

Reproduce the free local checks from the repository root:

```bash
python stage1/experiments/glimmer-fireworks-20261116/data/convert_dataset.py --verify-only
python -m unittest discover -s stage1/experiments/glimmer-fireworks-20261116/data -p test_dataset.py -v
python stage1/experiments/glimmer-fireworks-20261116/data/download_tokenizer.py
python stage1/experiments/glimmer-fireworks-20261116/data/verify_token_masks.py --local-files-only --max-seq-len 4096
```

Use `training/.venv/bin/python` for the final command; it requires the pinned cookbook runtime and verified local tokenizer snapshot. It creates no Fireworks client and needs no Fireworks API key.

Downloaded tokenizer files are ignored by Git; only their pinned snapshot manifest is retained. `download_tokenizer.py` restores and verifies the four public tokenizer/template files, without fetching model weights. Runtime verification also compares each rendered full sequence to the pinned Hugging Face chat template.

## Production preprocessing verification

The pinned processor_config.json was added to the local snapshot. All600 masks were rerun using populate_render_worker_state, matching the actual recipe including text-only processor initialization, and passed. Full recipe preflight also renders every row to a Datum before any session is created. No dataset messages changed.
