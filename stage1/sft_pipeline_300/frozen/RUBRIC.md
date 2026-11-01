# Reading accessibility rubric v1.5

Benchmark: end of All About Reading Level 1 (through lesson 53), plus cumulative Dolch preprimer, primer, and first-grade words. This is an experimental reading target, not an individual assessment or a universal standard for six-year-olds.

## Shared specification

READER_PROFILE.txt specifies decoding rules and boundaries. data/dolch-through-grade1.json stores the exact permitted high-frequency forms, source URL, and selection. engine.reader_profile() expands both into Prompt B and each saved evaluation rubric snapshot. Neither model receives the original PDFs. Prompt A stays a short baseline instruction.

Allow a word when its spelling is supported by the end-of-Level-1 skills OR it is an exact entry on the selected list (or a curriculum Leap Word). Neither route requires the other. Do not assume all speech vocabulary, names, contractions, or derivatives are supported. Any unsupported word makes word_types at most 2. Necessary hard words may still be needed for an accurate or safe response, but remain reading failures for this benchmark.

Examples of word eligibility, not full response scoring: good/you/too/me pass via the list; tell passes via ll. Wrong/right/why are not supported. Earlier Dolch membership is sufficient, but later-grade list placement does not disqualify an independently decodable word. The previous suggested sentence containing wrong was erroneous.

## Scores and decisions

Evaluate ONLY the companion response for word_types, length, and rhythm. Child inputs represent speech and may be complex. Score each 0–4: 4 excellent; 3 acceptable with minor issues; 2 material difficulty; 1 very difficult; 0 unusable. Accept only if all three are at least 3. Give a binary verdict and one concise evidence-based explanation. Do not score factual correctness, relevance, warmth, or enjoyment. Network failures are errors, not verdicts.

Length targets and scoring thresholds are project heuristics, not PDF findings. Rhythm means natural phrasing, not mandatory rhyme. Understanding and familiarity are distinct from decoding eligibility.

## Sources and limits

- Supplied AAR-L1-Scope-and-Sequence.pdf, PDF pages 1–2: blends and short vowels; th/sh/ch/qu/x; ff/ll/ss (29); ck (34); ng (36); nk (38); compounds (40); s/es (42); additional phonogram sounds (44–48); open/closed syllables and long vowels (52). Where the outline does not enumerate a correspondence, do not invent it or blanket-approve harder patterns.
- Supplied Run Bug Run, The Runt Pig, and Cobweb the Cat samples inform short clauses, repetition, and natural rhythm. They are selected excerpts; adult-facing promotional copy is not evidence of student word mastery. No passages are copied into prompt demonstrations or datasets.
- Canonical exact word list: https://www.readwritethink.org/sites/default/files/resources/lesson_images/lesson301/dolchwordlist.pdf — 40 preprimer + 52 primer + 41 first-grade entries (133 distinct words), excludes later grades and the noun list. This source uses giving; some other versions use going.
- Cross-reference: https://uurc.utah.edu/charts/dolch.php — its published first-grade groups have small differences, including a repeated where and omission of were in the end group. We use the canonical list above consistently, not an undocumented union of versions.
- https://ufli.education.ufl.edu/resources/teaching-resources/instructional-activities/irregular-and-high-frequency-words/ explains why high-frequency words may need explicit teaching. List inclusion is an assumption of familiarity for this experiment.

All previous records retain their saved rubric/prompt. Summaries keep different prompt and rubric hashes separate; do not pool v1.4 and v1.5 for improvement claims.
