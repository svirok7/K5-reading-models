<div align="center">

# Reading Model

### Small models. Simple words. Better reading companions.

An experiment in teaching a language model to write replies a beginning reader can read independently.

**Qwen3 · LoRA fine-tuning · 600 training examples · Local model playground**

[Get started](#run-the-playground) · [Results](#what-we-found) · [Training](#how-it-works) · [Experiment report](stage1/experiments/reading-compliance-20261031-002/FINAL_REPORT.md)

</div>

---

A conversational model can answer a child's question correctly and still use words the child cannot read. This project explores a narrower question: **can a small model learn to give useful replies within an explicit reading profile?**

It combines a local chat playground, a versioned reading rubric, audited synthetic training examples, and controlled fine-tuning comparisons. The current local model is **Qwen3-1.7B with a LoRA adapter trained on 600 examples for three epochs**.

> Research prototype and adult evaluation workbench. Reading accessibility and conversation quality are measured separately; this is not a validated child-facing product.

## The reading target

The current benchmark is **end of All About Reading Level 1, plus the cumulative Dolch preprimer, primer and first-grade word list**.

A response word is eligible when either:

- Its spelling is supported by the saved decoding profile.
- Its exact form appears in the permitted high-frequency list or curriculum Leap Words.

For example, **want** and **make** are allowed through exact list membership. That does not automatically allow every related word form.

The child's spoken input is unrestricted. The reading constraints apply to the model's written reply. Replies also aim for short sentences and natural phrasing; repetition and rhyme are optional.

[Reader profile](stage1/READER_PROFILE.txt) · [Exact word list](stage1/data/dolch-through-grade1.json) · [Scoring rubric](stage1/RUBRIC.md)

## What we found

### Controlled development comparison

The models below answered the **same 34 frozen inputs**: 16 single-turn cases and 18 fixed conversation histories.

| Adapter | Reading passes | Joint quality passes |
|:--|--:|--:|
| Historical 300-example, one-epoch adapter | 9/34 · **26.5%** | 6/34 · **17.6%** |
| Fresh 300-example, three-epoch adapter | 17/34 · **50.0%** | 14/34 · **41.2%** |
| **600-example, three-epoch adapter** | **22/34 · 64.7%** | **18/34 · 52.9%** |

**Reading passes** require acceptable word types, length and rhythm. **Joint quality passes** additionally require relevance, truthfulness, safety, appropriate correction/repetition handling and complete generation.

The selected adapter improved joint success by **35.3 percentage points** over the historical adapter. Two additional generation seeds sustained the improvement, with 17/34 joint successes each. Those repeats reuse the same inputs; they are not independent new test cases.

These are development results. The comparison changed data coverage and training exposure, and does not isolate their individual effects. Human approval remains pending.

[Full report and limitations](stage1/experiments/reading-compliance-20261031-002/FINAL_REPORT.md) · [Per-variant results](stage1/experiments/reading-compliance-20261031-002/primary-quality.csv)

### Exploratory live testing

A saved live-testing snapshot reached **35/44 reading passes (79.5%)**. This uses different inputs and a narrower metric than joint quality, so it is not directly comparable to the controlled results.

An overlap check against the exact training dataset found:

- **0** matching full conversation inputs after normalizing case and punctuation.
- **1** matching final user message: “Then what happened?”, in a different history.
- **0** evaluated replies matching complete training targets after the same normalization.

This provides evidence beyond exact-example replay. It does not rule out memorized patterns, semantic overlap or overfitting. Some easy-to-read replies were repetitive or unhelpful, and the live judge deliberately does not score those weaknesses.

[Overlap analysis](stage1/analysis/ui-training-overlap-20261101/overlap.json) · [Analysis script](stage1/analysis/ui-training-overlap-20261101/check.py)

## How it works

```text
Versioned reading profile + conversation
                  │
                  ▼
        Qwen3-1.7B + LoRA adapter
                  │
                  ▼
             Model reply
                  │
                  ▼
      Saved locally before evaluation
                  │
                  ▼
     Reading judge → adult review / override
```

The base model stays frozen. Fine-tuning updates **17,432,576 adapter parameters**, approximately **1%** of the base model's parameter count.

| Training setting | Selected run |
|:--|:--|
| Base model | Qwen/Qwen3-1.7B, pinned revision |
| Method | Ordinary LoRA, all linear layers |
| LoRA rank / alpha / dropout | 16 / 32 / 0.05 |
| Training examples | 600 |
| Epochs / example exposures | 3 / 1,800 |
| Optimizer updates | 225 |
| Initial learning rate | 0.0001, linear decay |
| Loss supervision | Final assistant completion only |
| Thinking | Disabled |

The dataset includes single-turn and conversation-history examples, with corrections and recovery cases. Training predicts the next target token; the reading score is an evaluation metric, not the training loss. The full reading instructions are still supplied at inference time.

[Training report](stage1/experiments/reading-compliance-20261031-002/TRAINING_REPORT.md) · [Dataset documentation](stage1/datasets/sft-600-v1/README.md) · [Training implementation](stage1/sft_train.py)

## Run the playground

### 1. Clone and start

```sh
git clone https://github.com/svirok7/K5-reading-models.git
cd K5-reading-models/stage1
python3 server.py
```

Open **http://127.0.0.1:8765/**. The server binds to localhost. The UI and API-backed engines use Python's standard library.

Choose an API-backed companion and configure its key in **Settings**, or install the optional local-model dependencies below. Keys entered in Settings stay in server memory and disappear when the server stops.

To load keys from an existing environment file instead:

```sh
python3 server.py --env-file /path/to/existing/.env.local
```

The server reads only the supported API keys and model IDs from that file. Do not commit credentials.

### 2. Enable local Qwen or Sarvam

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-model.txt
python server.py
```

First use downloads the base model. Local inference supports Apple Silicon MPS, CPU, and the configured CUDA path. CUDA quantization additionally requires `bitsandbytes`; it is not used on a Mac. Model weights require substantial disk space and memory.

**Adapter setup:** trained weights are not included in Git. The checked-in `qwen_sft` entry in `stage1/models.json` records the original workstation's adapter path. To use SFT on another machine, obtain the matching adapter and update that entry to its absolute local path. Until then, select the Qwen baseline or an API-backed model.

### 3. Evaluate and review

Each new reply is saved locally, then sent to a separate OpenAI reading judge. **Automatic evaluation requires an OpenAI API key even when the companion runs locally or uses Claude.** API generation and evaluation incur provider charges.

The judge scores word types, length and rhythm. An adult can retry a failed evaluation or save a manual decision. Manual decisions take precedence while preserving the original judgment and edit history.

Conversation records live in `stage1/runs/conversation-results.sqlite3`, which is ignored by Git. The committed live-testing overlap report contains a separate analysis snapshot.

## Explore the repository

| Path | What it contains |
|:--|:--|
| [`stage1/server.py`](stage1/server.py), [`ui/`](stage1/ui/) | Local chat and review interface |
| [`stage1/engine.py`](stage1/engine.py) | Local and API-backed inference |
| [`stage1/evaluator.py`](stage1/evaluator.py) | Structured reading-accessibility judge |
| [`stage1/prompts/`](stage1/prompts/) | Short-instruction and full-profile prompt variants |
| [`stage1/datasets/`](stage1/datasets/) | Versioned training data, audits and manifests |
| [`stage1/sft_train.py`](stage1/sft_train.py), [`sft_colab.ipynb`](stage1/sft_colab.ipynb) | Training helper and initial Colab workflow |
| [`stage1/experiments/`](stage1/experiments/) | Experiment-specific workflows, frozen inputs and results |
| [`stage1/evaluation-sft-v1/`](stage1/evaluation-sft-v1/) | Earlier replay and comparison tooling |
| [`stage1/analysis/`](stage1/analysis/) | Exploratory analysis of live testing |

The experiment's [own notebook and instructions](stage1/experiments/reading-compliance-20261031-002/README.md) describe the 600-example comparison. Earlier stage documents preserve historical plans; use the final experiment report for completed results.

## Validation

The last pre-push check passed **53 offline tests**: 29 training tests, 5 earlier evaluation tests, and 19 experiment evaluation/selection/execution tests.

From `stage1/`, with the model environment installed:

```sh
.venv/bin/python -m unittest test_sft_train
(cd evaluation-sft-v1 && ../.venv/bin/python -m unittest test_evaluation)
(cd experiments/reading-compliance-20261031-002 && ../../.venv/bin/python -m unittest test_evaluate test_selection test_execution)
```

Some training checks require the pinned Qwen tokenizer to be cached locally. These tests cover masking, updates, integrity checks, resume behavior and evaluation logic; they do not establish broad conversational quality.

## What still needs work

- **Context handling:** replies can ignore corrections or become repetitive.
- **Useful answers:** a short, readable reply can still fail the request.
- **Remaining reading errors:** unsupported names, spellings and word forms still appear.
- **Identity and truthfulness:** controlled testing still found fabricated personal experiences.
- **Evaluation confidence:** the live judge is uncalibrated, and the controlled suite is small, reused development material.

The next useful milestone is a fresh unseen evaluation that measures reading accessibility and conversation quality separately, with human review.
