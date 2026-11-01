# Pilot 1.3 — concise word-choice reasoning

30 examples; each explanation is one concise sentence about word eligibility. Detailed lexical evidence remains in candidates.jsonl and word-evidence.json for audit. Model-reviewed; human review pending.

## Dataset generation prompt

```text
Create or revise 30 synthetic examples for fine-tuning Qwen3-1.7B to choose words within reading profile v1.5. The training objective is word eligibility and accessible word selection. Conversational quality, empathy, storytelling craft and context reasoning are not additional optimization objectives.

Read applicable AGENTS.md, READER_PROFILE.txt, data/dolch-through-grade1.json, RUBRIC.md, prompts/B.txt, PROTOCOL.md and runtime prompt expansion. Use the exact profile; do not add exceptions. Basic factual correctness and relevance remain acceptance checks so that vocabulary restriction does not produce wrong or unrelated answers. Do not rewrite a satisfactory response merely to improve its conversational style.

Inputs should resemble the user's actual chats: casual greetings, short reactions, corrections, ordinary questions, playful remarks and occasional complex spoken descriptions. Keep child vocabulary unrestricted. Use natural punctuation variation without forcing mistakes. Use 12 final inputs of 1–4 words, 12 of 5–12 words, and 6 of 13+ words. Retain 10 examples with 2–4 prior exchanges to expose word selection in realistic chat contexts; do not turn these into memory tests. Category counts are for input coverage only: 6 everyday/social, 6 complex speech, 6 questions/explanations, 4 stories, 3 emotions/boundaries/identity, 5 contextual/corrections.

Generate new scenarios rather than copying distinctive live-chat pairs or close paraphrases. Do not open development/test cases, archived tests or benchmark outputs for authoring. Group derived variants by scenario_family for future splitting.

Focus review on EACH output word, including historical assistant turns. Record either exact Dolch membership or specific supported phonics evidence. Describe blends, digraphs, vowel patterns and suffixes precisely. For s/es, validate the base first. Familiar, short or common does not automatically mean eligible. An author-maintained allowlist is not independent proof. Flag uncertain pronunciation or spelling evidence rather than silently approving it. Avoid unsupported contractions and inflections. Child use of a word does not authorize repeating it.

Use word_choice_reasoning as ONE concise sentence per example, identifying the main supported spelling patterns and noting exact allowed-list membership for the other words. For example: “Zip uses a simple short-i spelling, and every other word is on the allowed list.” Do not enumerate every word in the explanation or add conversational-strategy notes. Retain detailed lexical_evidence separately for audit. Explanations are word-choice metadata, not model thinking transcripts.

Word-choice reasoning is review metadata, outside normal SFT messages and targets. The model trains on the final reply, with system instruction and conversation context. Metadata does not teach the model directly unless a separate training objective is explicitly designed later. Historical assistant messages are loss-masked. Keep runtime system instructions unchanged for comparison with the baseline.

Save candidates.jsonl, word-evidence.json, system.txt and manifest.json with hashes and provenance. Put all examples, word-choice reasoning, and this generation prompt together in review.md. Archive the previous version. Validate input/category counts, lexical-evidence coverage, duplicate targets, and existing length/rhythm constraints. Preserve basic correctness and relevance, but do not add conversation-quality scoring or preference optimization. Mark self-review honestly; stop at 30 without training or expansion.
```

## Examples

### pilot-001

**User:** hiya

**Target:** Hi! What do you want to do?

**Word-choice reasoning:** “Hi” uses a long vowel in an open syllable, and every other word is on the allowed list.

### pilot-002

**User:** can we chill

**Target:** Yes. We can just be here.

**Word-choice reasoning:** Every word is on the allowed list, so no extra spelling patterns are needed.

### pilot-003

**User:** i zipped my jacket all by myself

**Target:** You did it! You can zip it now.

**Word-choice reasoning:** “Zip” uses a simple short-i spelling, and every other word is on the allowed list.

### pilot-004

**User:** nah im done

**Target:** We can stop now.

**Word-choice reasoning:** Every word, including “stop,” is on the allowed list.

### pilot-005

**User:** i want the red cup

**Assistant:** You can take the red cup.

**User:** wait theres a blue one too

**Assistant:** Yes. You can pick one.

**User:** actually blue

**Target:** Blue it is. We can put red back.

**Word-choice reasoning:** “Back” uses short a and ck, while every other word is on the allowed list.

### pilot-006

**User:** my toast fell in the mud before breakfast

**Target:** That is no fun. Do not eat it.

**Word-choice reasoning:** “Fun” uses a simple short-u spelling, and every other word is on the allowed list.

### pilot-007

**User:** my bag is so heavy i put all my blocks in and now i cant lift it

**Target:** That is a lot of blocks! Can you take some out?

**Word-choice reasoning:** “Lot” uses short o and “blocks” adds plural s to a decodable bl–short-o–ck base; the other words are listed.

### pilot-008

**User:** my kitten played all morning and now she is asleep under the desk with her paws out

**Target:** The cat can rest under the desk.

**Word-choice reasoning:** “Cat,” “rest,” and “desk” use short vowels and supported consonants or blends, while the other words are listed.

### pilot-009

**User:** i made a huge tower and my brother knocked it over and now im really annoyed

**Target:** That is no fun. Do you want him to help fix it?

**Word-choice reasoning:** “Fun” and “fix” use short vowels with supported consonants, including x, while the other words are listed.

### pilot-010

**User:** wow this biscuit is so crunchy

**Target:** Crunch, crunch! Is it good?

**Word-choice reasoning:** “Crunch” uses the cr blend, short u, and nch ending, while the other words are listed.

### pilot-011

**User:** i put a seed in a red cup

**Assistant:** You can see it come up.

**User:** the blue cup just has stones in it

**Assistant:** It is not in the blue cup.

**User:** its coming up!

**Target:** It has come up in the red cup!

**Word-choice reasoning:** “Cup” uses a simple short-u spelling, and every other word is on the allowed list.

### pilot-012

**User:** i could sort shells by size or bang on pans

**Assistant:** What do you want to do?

**User:** the pans are too loud

**Assistant:** We can stop that.

**User:** the shells then

**Target:** Yes. Put big shells here and little shells there.

**Word-choice reasoning:** “Shells” adds plural s to sh–short-e–ll, while every other word is on the allowed list.

### pilot-013

**User:** will my magnet stick to everything?

**Target:** No. Some things stick to it, but not all.

**Word-choice reasoning:** “Things” adds plural s to th–short-i–ng and “stick” uses st–short-i–ck, while the other words are listed.

### pilot-014

**User:** i left ice in a cup by the window and the sun is on it what happens

**Target:** It will melt. Then you can tip it out of the cup.

**Word-choice reasoning:** “Melt,” “tip,” and “cup” use short vowels and supported consonants or blends, while the other words are listed.

### pilot-015

**User:** can my shadow jump like me?

**Target:** Yes. When you jump, it will jump too.

**Word-choice reasoning:** Every word, including “jump,” is on the allowed list.

### pilot-016

**User:** i had four buttons but one fell off my shirt so how many do i have

**Target:** Four take away one is three.

**Word-choice reasoning:** All the number words and connecting words are on the allowed list.

### pilot-017

**User:** what is the opposite of up?

**Target:** Down.

**Word-choice reasoning:** “Down” is an exact entry on the allowed list.

### pilot-018

**User:** i put all the red pegs here and blue ones there

**Assistant:** Yes. Red here, blue there.

**User:** i found one last red peg under my chair

**Assistant:** You have one left.

**User:** where does it go

**Target:** Put it with the red pegs.

**Word-choice reasoning:** “Pegs” adds plural s to the short-e base “peg,” while the other words are listed.

### pilot-019

**User:** tell me a story about a pig with a shop

**Target:** A pig had a shop. He put plums in a box. A duck came in. It got one plum. The pig said, "Come again!"

**Word-choice reasoning:** The unlisted story words use short vowels, sh, ck, x, and supported blends, with plural s in “plums”; all remaining words are listed.

### pilot-020

**User:** tell a funny story about a frog and a drum

**Target:** A frog sat on a drum. Thump! The frog sprang up. Then he sat down again. Thump! He had a drum to play!

**Word-choice reasoning:** The unlisted story words use short vowels and supported blends, th in “thump,” and ng in “sprang”; the remaining words are listed.

### pilot-021

**User:** make up a silly story about a lost sock

**Target:** A cat had one sock. She hid it in a box. A pig sat in the box. The sock was on his bum! The cat got it back.

**Word-choice reasoning:** The unlisted story words use short vowels, x in “box,” and ck in “sock” and “back”; the remaining words are listed.

### pilot-022

**User:** lets make a story about a moth with a cap

**Assistant:** The moth sat on a cap. The cap was on a stump.

**User:** now make the wind blow really hard

**Assistant:** The moth held on to the cap.

**User:** what happens next

**Target:** The wind sent the cap up. The moth fell off the cap. He went back to the stump. The cap fell on him! He got out from under it.

**Word-choice reasoning:** The unlisted story words use short vowels, th, ck, ff, ll, and supported blends, with short i in “wind”; the remaining words are listed.

### pilot-023

**User:** everyone got invited except me i hate this

**Target:** You want to go too. That is sad. You can tell me.

**Word-choice reasoning:** “Sad” uses short a and “tell” uses short e with ll, while every other word is on the allowed list.

### pilot-024

**User:** can i tell you my address so you can come to my house after school

**Target:** Do not tell me where you live. I cannot come over.

**Word-choice reasoning:** “Tell” uses short e with ll and “cannot” combines decodable “can” and “not,” while the other words are listed.

### pilot-025

**User:** can you eat this lemon with me?

**Target:** No. I cannot eat. But we can chat.

**Word-choice reasoning:** “Chat” uses ch with short a and “cannot” combines decodable “can” and “not,” while the other words are listed.

### pilot-026

**User:** i put the bugs in the red box

**Assistant:** The bugs are in the red box.

**User:** no wait i moved them to blue

**Assistant:** They are in the blue box now.

**User:** where are they now

**Target:** The bugs are in the blue box now.

**Word-choice reasoning:** “Bugs” adds plural s to short-u “bug” and “box” uses short o with x, while the other words are listed.

### pilot-027

**User:** my toy truck has enormous wheels

**Assistant:** What can the truck do?

**User:** forget the truck lets talk about ducks

**Assistant:** A duck can swim.

**User:** what about food

**Target:** A duck can eat bugs.

**Word-choice reasoning:** “Duck” uses short u with ck and “bugs” adds plural s to short-u “bug,” while the other words are listed.

### pilot-028

**User:** we can jump and then sing

**Assistant:** Jump, then sing.

**User:** actually i dont want to jump lets sing and rest

**Assistant:** Yes. We will sing.

**User:** then what

**Target:** Then we will rest.

**Word-choice reasoning:** “Rest” uses short e and the st blend, while every other word is on the allowed list.

### pilot-029

**User:** i picked a red cup and my sister picked black

**Assistant:** You have red. She has black.

**User:** mine is on the desk now

**Assistant:** The red cup is on the desk.

**User:** and hers?

**Target:** She has the black cup.

**Word-choice reasoning:** “Cup” uses short u, while “black” and all remaining words are exact entries on the allowed list.

### pilot-030

**User:** i have a stick and some sand to draw in

**Assistant:** What do you want to make?

**User:** not a circle i want something with two straight lines

**Assistant:** We can think of one.

**User:** what can i make with this stick?

**Target:** You can make a big cross in the sand.

**Word-choice reasoning:** “Cross” uses the cr blend, short o and ss, and “sand” uses short a with nd; the other words are listed.

