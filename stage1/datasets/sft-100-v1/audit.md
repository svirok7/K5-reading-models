# Audit of all 100 examples

## Findings and corrections

- No clear unsupported assistant word found under profile v1.5 after checking all targets and 132 historical assistant messages. This is a model linguistic review against the specification, not independent human verification.
- could (first grade), yellow (preprimer), and white (primer) are exact list exceptions. Their irregular spellings do not disqualify them and do not authorize derivatives.
- 010: clarified n + ch in crunch rather than describing nch as a single taught unit.
- 031: clarified the long-i open syllable in hi.
- 068: replaced awkward “Take a bit” with “We can stop for a bit.”
- 085: replaced an opening “It” with an explicit bug referent.
- 086: named the goat Rex in the child input and used Rex in the reply to distinguish it from the pig. Rex is permitted by short e + x, not by an automatic name allowance.

These are word-reasoning and basic correctness fixes; no conversational preference-training objective was added. Child language remains unrestricted. Prior versions are archived, source batches and combined exports agree, and old authoring builders are disabled to prevent silently undoing corrections.

## Checks

100 stable IDs and 100 distinct targets; 40 short / 40 medium / 20 long final inputs; 33 contextual examples. Every SFT row contains only prompt and completion; all system profiles are identical and expanded; roles alternate; final completion matches its review target; no reasoning is present in completions. Every assistant word has exact-list or decoding evidence, and each exact-list claim was checked against the source JSON. Sentence lengths <=12 words and <=1 question per target. Hashes refreshed.

## Limits

Evidence coverage is not an independent phonics validator. No held-out examples were opened or semantic overlap checked against them. No learning, memorization or generalization claim can be made from this audit. Tokenizer-level completion masks, context truncation and model training remain untested. Some replies are intentionally sparse because this dataset targets word selection, not conversational richness. Narrow vocabulary creates repeated phrasing even though full targets are distinct. The named character should be checked for pronunciation by the eventual human reviewer.
