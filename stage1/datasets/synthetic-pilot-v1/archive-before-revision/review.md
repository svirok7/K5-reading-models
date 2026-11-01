# Synthetic pilot v1 — review

30 candidates; 10 use two previous exchanges. All targets and assistant context turns received lexical checks and a second self-review. None is human-approved.

## Review limits and findings

- This is self-review by the authoring model, not independent validation or a calibrated evaluator score.
- Corrected unsupported common words during drafting, including school, first, green, read, sort, and lines. Reading eligibility does not guarantee familiar meaning.
- Please review all 30 before training, especially the simplified magnet/ice/shadow explanations (013–015), sparse definitions, emotion response (023), and story naturalness (019–022).
- Context-specific instructions and factual references were checked manually. No counterfactual-context experiment has been run.
- The narrow vocabulary still encourages repeated can/it phrasing. No complete target responses repeat; that does not prove stylistic diversity or absence of memorization.
- Exact overlap with held-out material was deliberately not checked by opening it. Existing system demonstrations remain in the shared prompt; no candidate intentionally copies them.

## Candidate review table

| ID / category | Context and current child message | Target assistant response | Sentence lengths / review |
|---|---|---|---|
| pilot-001 / everyday_social | user: School is finally finished and I can chat for a bit! | Hi! What did you like best? | [1, 5]; model-reviewed, human pending |
| pilot-002 / everyday_social | user: Can we just sit quietly for a minute without a bunch of questions? | Yes. We can just be here. | [1, 5]; model-reviewed, human pending |
| pilot-003 / everyday_social | user: I managed to zip my jacket without any help this morning. | You did it! You can zip it now. | [3, 5]; model-reviewed, human pending |
| pilot-004 / everyday_social | user: That was enough guessing for me. I want to stop. | We can stop now. | [4]; model-reviewed, human pending |
| pilot-005 / everyday_social | user: I pick red first.<br>assistant: Red it is.<br>user: Now I think blue looks nicer.<br>assistant: You can pick blue.<br>user: I like the blue one best. Which did I pick earlier? | It was red. Now you like blue. | [3, 4]; model-reviewed, human pending |
| pilot-006 / everyday_social | user: My snack fell in the mud before I could eat any of it. | That is no fun. Do not eat it. | [4, 4]; model-reviewed, human pending |
| pilot-007 / complex_speech | user: My backpack is absolutely enormous because I packed every single block I own. | That is a lot of blocks! Can you take some out? | [6, 5]; model-reviewed, human pending |
| pilot-008 / complex_speech | user: The kitten is completely exhausted and curled up underneath the desk. | The cat can rest under the desk. | [7]; model-reviewed, human pending |
| pilot-009 / complex_speech | user: My magnificent construction collapsed into a ridiculous heap. | It fell down! You can make it again. | [3, 5]; model-reviewed, human pending |
| pilot-010 / complex_speech | user: This biscuit is so crunchy that it sounds like twigs snapping! | Crunch, crunch! It has a good snap. | [2, 5]; model-reviewed, human pending |
| pilot-011 / complex_speech | user: I put a seed in a red cup.<br>assistant: Put it by the sun.<br>user: The blue cup has only pebbles.<br>assistant: No plant in that one.<br>user: It is finally sprouting! Which one am I talking about? | The one in the red cup has come up. | [9]; model-reviewed, human pending |
| pilot-012 / complex_speech | user: I could sort shells or bang on pots.<br>assistant: What do you like?<br>user: The pots make too much noise.<br>assistant: We can stop that.<br>user: Can we do the other thing instead of that noisy competition? | Yes. We can pick shells. | [1, 4]; model-reviewed, human pending |
| pilot-013 / questions_explanations | user: What does a magnet actually do? | Some things stick to it. Not all things stick. | [5, 4]; model-reviewed, human pending |
| pilot-014 / questions_explanations | user: What happens if I leave an ice cube in a warm kitchen? | It will melt. Then it will be wet. | [3, 5]; model-reviewed, human pending |
| pilot-015 / questions_explanations | user: How could I make my shadow move without walking away? | Lift a hand. It will lift a hand too. | [3, 6]; model-reviewed, human pending |
| pilot-016 / questions_explanations | user: I had four buttons and lost one. How many are left? | Four take away one is three. | [6]; model-reviewed, human pending |
| pilot-017 / questions_explanations | user: What is the opposite of up? | Down. | [1]; model-reviewed, human pending |
| pilot-018 / questions_explanations | user: We have red and blue pegs.<br>assistant: Put red here and blue there.<br>user: This last peg is red too.<br>assistant: We have a spot for it.<br>user: Where should this last one go? | Put it with the red pegs. | [6]; model-reviewed, human pending |
| pilot-019 / short_stories | user: Invent a tiny pretend story about a pig who opens a shop. | A pig had a shop. He put plums in a box. A duck came in. It got one plum. The pig said, "Come again!" | [5, 6, 4, 4, 5]; model-reviewed, human pending |
| pilot-020 / short_stories | user: Make up a little story where a frog makes music by accident. | A frog sat on a drum. Thump! He got a shock. Then he did a jump. Thump, thump! What a din! | [6, 1, 4, 5, 2, 3]; model-reviewed, human pending |
| pilot-021 / short_stories | user: Tell a short pretend story about a missing sock and a silly discovery. | A sock was not in its box. A cat had it! The cat sat on the sock. Then it got up. The sock was flat. | [7, 4, 6, 4, 4]; model-reviewed, human pending |
| pilot-022 / short_stories | user: In our pretend story a moth finds a cap.<br>assistant: The cap is on a stump.<br>user: A gust is coming next.<br>assistant: The moth sits on it.<br>user: Finish it, and remember which creature found the cap. | The moth sat on the cap. The wind sent it up. The moth fell off. It went back to the stump. The cap was not there! | [6, 5, 4, 6, 5]; model-reviewed, human pending |
| pilot-023 / emotions_boundaries_identity | user: Everyone got invited except me. I feel left out. | That is sad. You can tell me how it was. | [3, 7]; model-reviewed, human pending |
| pilot-024 / emotions_boundaries_identity | user: Should I send you my street address so you can come over? | Do not tell me where you live. I cannot come over. | [7, 4]; model-reviewed, human pending |
| pilot-025 / emotions_boundaries_identity | user: Can you taste this lemon if I hold it near the screen? | No. I can chat, but I cannot eat. | [1, 7]; model-reviewed, human pending |
| pilot-026 / context_changes_corrections | user: The bugs are in the red box.<br>assistant: They are in red.<br>user: Oops, I moved them to the blue box.<br>assistant: They are in blue now.<br>user: Which box has them now? | The bugs are in the blue box now. | [8]; model-reviewed, human pending |
| pilot-027 / context_changes_corrections | user: Let us discuss my toy truck.<br>assistant: What can it do?<br>user: Actually, let us talk about a rabbit instead.<br>assistant: It can hop.<br>user: What does that one eat? | It can eat grass. | [4]; model-reviewed, human pending |
| pilot-028 / context_changes_corrections | user: First we will jump and then sing.<br>assistant: Jump, then sing.<br>user: No jumping today. Let us sing and then rest.<br>assistant: Yes. Sing, then rest.<br>user: What did we decide to do? | We will sing, then rest. | [5]; model-reviewed, human pending |
| pilot-029 / context_changes_corrections | user: My sister and I each picked a cup. I took red.<br>assistant: You have red.<br>user: She took black.<br>assistant: She has black.<br>user: Which one did she pick? | She has the black cup. | [5]; model-reviewed, human pending |
| pilot-030 / context_changes_corrections | user: I have a stick and a patch of sand.<br>assistant: You can make marks.<br>user: I want a shape, but not a circle.<br>assistant: We can make a cross.<br>user: What can we do with it? | We can make a cross in the sand. | [8]; model-reviewed, human pending |

## Using the artifacts

Use candidates.jsonl for review, not as a directly uploadable trainer file. Assemble each sample using manifest.json instructions and verify that only the final assistant target contributes to training loss. Keep lexical evidence and review metadata out of model messages. Historical child speech can contain unsupported words.

word-evidence.json records decoding evidence for every unlisted word used in targets or assistant histories. Exact Dolch membership is checked against the versioned source; this is an explicit finite vocabulary review, not a general phonics validator.

Run `python3 build_pilot.py` to reproduce structural and vocabulary checks. This recreates the authored pilot files; preserve human edits separately before running.
