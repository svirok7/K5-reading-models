# Batch 002 audit and corrections

All 30 final assistant replies and all 40 assistant-history replies were reviewed for word eligibility under profile v1.5. Child speech is unrestricted. No clear unsupported assistant word remains under the supplied profile. This is model linguistic review plus deterministic evidence/list checks, not independent human verification.

## Could and yellow

- could: exact first-grade Dolch entry; allowed despite its irregular spelling and silent l.
- yellow: exact preprimer Dolch entry; allowed despite requiring spellings beyond simple short-vowel decoding.

The rule is supported decoding OR exact allowed-list membership. A listed exception does not authorize other words with the same spelling pattern, derivatives, or contractions. Inclusion in this experiment does not establish an individual child's mastery.

## Corrections

- 040: replaced “A big bang!” with “Do you want it to stop?” because a loud sound need not be a bang; no unsupported replacement word was added.
- 042 history: replaced “You could get wet” with “You could slip” to match the ice context. Could remains valid by exact list membership; slip uses sl + short i + p.
- 048: changed ambiguous “where is the other” to “and the lid”; unchanged eligible target.
- 058: changed ambiguous “before or after” to “nap before or after”; unchanged eligible target.
- Made several decoding-evidence descriptions more precise (including ck, x, and open-syllable i).

The previous artifacts are preserved in archive-before-audit/. Both SFT and review outputs were regenerated from the corrected authoring script. IDs, category quotas, 12/12/6 input-length mix and 10 contextual examples remain valid. Every SFT completion matches its review target, and every assistant word has evidence with exact Dolch membership checked against the source JSON. No tokenizer/mask run or model training was performed.
