# Pilot 1.2 — word-choice review and generation prompt

Objective: word eligibility and accessible word selection under profile v1.5. Input categories provide varied language contexts; they are not conversation-improvement objectives. All 30 input/target pairs from revision 1.1 are retained. Word-choice explanations are metadata, not training targets. Human review pending.

## Dataset generation prompt

```text
Create or revise 30 synthetic examples for fine-tuning Qwen3-1.7B to choose words within reading profile v1.5. The training objective is word eligibility and accessible word selection. Conversational quality, empathy, storytelling craft and context reasoning are not additional optimization objectives.

Read applicable AGENTS.md, READER_PROFILE.txt, data/dolch-through-grade1.json, RUBRIC.md, prompts/B.txt, PROTOCOL.md and runtime prompt expansion. Use the exact profile; do not add exceptions. Basic factual correctness and relevance remain acceptance checks so that vocabulary restriction does not produce wrong or unrelated answers. Do not rewrite a satisfactory response merely to improve its conversational style.

Inputs should resemble the user's actual chats: casual greetings, short reactions, corrections, ordinary questions, playful remarks and occasional complex spoken descriptions. Keep child vocabulary unrestricted. Use natural punctuation variation without forcing mistakes. Use 12 final inputs of 1–4 words, 12 of 5–12 words, and 6 of 13+ words. Retain 10 examples with 2–4 prior exchanges to expose word selection in realistic chat contexts; do not turn these into memory tests. Category counts are for input coverage only: 6 everyday/social, 6 complex speech, 6 questions/explanations, 4 stories, 3 emotions/boundaries/identity, 5 contextual/corrections.

Generate new scenarios rather than copying distinctive live-chat pairs or close paraphrases. Do not open development/test cases, archived tests or benchmark outputs for authoring. Group derived variants by scenario_family for future splitting.

Focus review on EACH output word, including historical assistant turns. Record either exact Dolch membership or specific supported phonics evidence. Describe blends, digraphs, vowel patterns and suffixes precisely. For s/es, validate the base first. Familiar, short or common does not automatically mean eligible. An author-maintained allowlist is not independent proof. Flag uncertain pronunciation or spelling evidence rather than silently approving it. Avoid unsupported contractions and inflections. Child use of a word does not authorize repeating it.

Use word_choice_reasoning metadata: selected word, its exact eligibility evidence, and, where useful, a harder alternative avoided with its unsupported spelling pattern. Only include comparisons that are linguistically valid; do not invent synonyms or imply that all simple alternatives preserve the same meaning. Do not add intent, meaning_to_preserve, response_choice or conversational-strategy annotations. Keep the complete lexical_evidence map for target and assistant context words.

Word-choice reasoning is review metadata, outside normal SFT messages and targets. The model trains on the final reply, with system instruction and conversation context. Metadata does not teach the model directly unless a separate training objective is explicitly designed later. Historical assistant messages are loss-masked. Keep runtime system instructions unchanged for comparison with the baseline.

Save candidates.jsonl, word-evidence.json, system.txt and manifest.json with hashes and provenance. Put all examples, word-choice reasoning, and this generation prompt together in review.md. Archive the previous version. Validate input/category counts, lexical-evidence coverage, duplicate targets, and existing length/rhythm constraints. Preserve basic correctness and relevance, but do not add conversation-quality scoring or preference optimization. Mark self-review honestly; stop at 30 without training or expansion.
```

## Examples and word-choice reasoning

### pilot-001

**User:** hiya

**Target:** Hi! What do you want to do?

| Word | Eligibility reasoning |
|---|---|
| do | Exact Dolch entry |
| hi | Long vowel in open syllable |
| to | Exact Dolch entry |
| want | Exact Dolch entry |
| what | Exact Dolch entry |
| you | Exact Dolch entry |

### pilot-002

**User:** can we chill

**Target:** Yes. We can just be here.

| Word | Eligibility reasoning |
|---|---|
| be | Exact Dolch entry |
| can | Exact Dolch entry |
| here | Exact Dolch entry |
| just | Exact Dolch entry |
| we | Exact Dolch entry |
| yes | Exact Dolch entry |

### pilot-003

**User:** i zipped my jacket all by myself

**Target:** You did it! You can zip it now.

| Word | Eligibility reasoning |
|---|---|
| can | Exact Dolch entry |
| did | Exact Dolch entry |
| it | Exact Dolch entry |
| now | Exact Dolch entry |
| you | Exact Dolch entry |
| zip | Short vowel closed syllable; supported consonants |

### pilot-004

**User:** nah im done

**Target:** We can stop now.

| Word | Eligibility reasoning |
|---|---|
| can | Exact Dolch entry |
| now | Exact Dolch entry |
| stop | Exact Dolch entry |
| we | Exact Dolch entry |

### pilot-005

**User:** i want the red cup

**Assistant:** You can take the red cup.

**User:** wait theres a blue one too

**Assistant:** Yes. You can pick one.

**User:** actually blue

**Target:** Blue it is. We can put red back.

| Word | Eligibility reasoning |
|---|---|
| back | b + short a + ck |
| blue | Exact Dolch entry |
| can | Exact Dolch entry |
| is | Exact Dolch entry |
| it | Exact Dolch entry |
| put | Exact Dolch entry |
| red | Exact Dolch entry |
| we | Exact Dolch entry |

### pilot-006

**User:** my toast fell in the mud before breakfast

**Target:** That is no fun. Do not eat it.

| Word | Eligibility reasoning |
|---|---|
| do | Exact Dolch entry |
| eat | Exact Dolch entry |
| fun | Short vowel closed syllable; supported consonants |
| is | Exact Dolch entry |
| it | Exact Dolch entry |
| no | Exact Dolch entry |
| not | Exact Dolch entry |
| that | Exact Dolch entry |

### pilot-007

**User:** my bag is so heavy i put all my blocks in and now i cant lift it

**Target:** That is a lot of blocks! Can you take some out?

| Word | Eligibility reasoning |
|---|---|
| a | Exact Dolch entry |
| blocks | block (bl + short o + ck) + plural s |
| can | Exact Dolch entry |
| is | Exact Dolch entry |
| lot | Short vowel closed syllable; supported consonants |
| of | Exact Dolch entry |
| out | Exact Dolch entry |
| some | Exact Dolch entry |
| take | Exact Dolch entry |
| that | Exact Dolch entry |
| you | Exact Dolch entry |

### pilot-008

**User:** my kitten played all morning and now she is asleep under the desk with her paws out

**Target:** The cat can rest under the desk.

| Word | Eligibility reasoning |
|---|---|
| can | Exact Dolch entry |
| cat | Short vowel closed syllable; supported consonants |
| desk | Short vowel closed syllable; supported consonants |
| rest | Short vowel closed syllable; supported consonants |
| the | Exact Dolch entry |
| under | Exact Dolch entry |

### pilot-009

**User:** i made a huge tower and my brother knocked it over and now im really annoyed

**Target:** That is no fun. Do you want him to help fix it?

| Word | Eligibility reasoning |
|---|---|
| do | Exact Dolch entry |
| fix | Short vowel in a closed syllable; supported consonants and consonant blends |
| fun | Short vowel closed syllable; supported consonants |
| help | Exact Dolch entry |
| him | Exact Dolch entry |
| is | Exact Dolch entry |
| it | Exact Dolch entry |
| no | Exact Dolch entry |
| that | Exact Dolch entry |
| to | Exact Dolch entry |
| want | Exact Dolch entry |
| you | Exact Dolch entry |

### pilot-010

**User:** wow this biscuit is so crunchy

**Target:** Crunch, crunch! Is it good?

| Word | Eligibility reasoning |
|---|---|
| crunch | Supported th/sh/ch/qu/x digraph or spelling, short vowels and blends |
| good | Exact Dolch entry |
| is | Exact Dolch entry |
| it | Exact Dolch entry |

### pilot-011

**User:** i put a seed in a red cup

**Assistant:** You can see it come up.

**User:** the blue cup just has stones in it

**Assistant:** It is not in the blue cup.

**User:** its coming up!

**Target:** It has come up in the red cup!

| Word | Eligibility reasoning |
|---|---|
| come | Exact Dolch entry |
| cup | Short vowel closed syllable; supported consonants |
| has | Exact Dolch entry |
| in | Exact Dolch entry |
| it | Exact Dolch entry |
| red | Exact Dolch entry |
| the | Exact Dolch entry |
| up | Exact Dolch entry |

### pilot-012

**User:** i could sort shells by size or bang on pans

**Assistant:** What do you want to do?

**User:** the pans are too loud

**Assistant:** We can stop that.

**User:** the shells then

**Target:** Yes. Put big shells here and little shells there.

| Word | Eligibility reasoning |
|---|---|
| and | Exact Dolch entry |
| big | Exact Dolch entry |
| here | Exact Dolch entry |
| little | Exact Dolch entry |
| put | Exact Dolch entry |
| shells | shell (sh + short e + ll) + plural s |
| there | Exact Dolch entry |
| yes | Exact Dolch entry |

### pilot-013

**User:** will my magnet stick to everything?

**Target:** No. Some things stick to it, but not all.

| Word | Eligibility reasoning |
|---|---|
| all | Exact Dolch entry |
| but | Exact Dolch entry |
| it | Exact Dolch entry |
| no | Exact Dolch entry |
| not | Exact Dolch entry |
| some | Exact Dolch entry |
| stick | Supported th/sh/ch/qu/x digraph or spelling, short vowels and blends |
| things | thing (th + short i + ng) + plural s |
| to | Exact Dolch entry |

### pilot-014

**User:** i left ice in a cup by the window and the sun is on it what happens

**Target:** It will melt. Then you can tip it out of the cup.

| Word | Eligibility reasoning |
|---|---|
| can | Exact Dolch entry |
| cup | Short vowel closed syllable; supported consonants |
| it | Exact Dolch entry |
| melt | Short vowel closed syllable; supported consonants |
| of | Exact Dolch entry |
| out | Exact Dolch entry |
| the | Exact Dolch entry |
| then | Exact Dolch entry |
| tip | Short vowel in a closed syllable; supported consonants and consonant blends |
| will | Exact Dolch entry |
| you | Exact Dolch entry |

### pilot-015

**User:** can my shadow jump like me?

**Target:** Yes. When you jump, it will jump too.

| Word | Eligibility reasoning |
|---|---|
| it | Exact Dolch entry |
| jump | Exact Dolch entry |
| too | Exact Dolch entry |
| when | Exact Dolch entry |
| will | Exact Dolch entry |
| yes | Exact Dolch entry |
| you | Exact Dolch entry |

### pilot-016

**User:** i had four buttons but one fell off my shirt so how many do i have

**Target:** Four take away one is three.

| Word | Eligibility reasoning |
|---|---|
| away | Exact Dolch entry |
| four | Exact Dolch entry |
| is | Exact Dolch entry |
| one | Exact Dolch entry |
| take | Exact Dolch entry |
| three | Exact Dolch entry |

### pilot-017

**User:** what is the opposite of up?

**Target:** Down.

| Word | Eligibility reasoning |
|---|---|
| down | Exact Dolch entry |

### pilot-018

**User:** i put all the red pegs here and blue ones there

**Assistant:** Yes. Red here, blue there.

**User:** i found one last red peg under my chair

**Assistant:** You have one left.

**User:** where does it go

**Target:** Put it with the red pegs.

| Word | Eligibility reasoning |
|---|---|
| it | Exact Dolch entry |
| pegs | peg (short e) + plural s |
| put | Exact Dolch entry |
| red | Exact Dolch entry |
| the | Exact Dolch entry |
| with | Exact Dolch entry |

### pilot-019

**User:** tell me a story about a pig with a shop

**Target:** A pig had a shop. He put plums in a box. A duck came in. It got one plum. The pig said, "Come again!"

| Word | Eligibility reasoning |
|---|---|
| a | Exact Dolch entry |
| again | Exact Dolch entry |
| box | Short vowel closed syllable; supported consonants |
| came | Exact Dolch entry |
| come | Exact Dolch entry |
| duck | d + short u + ck |
| got | Short vowel closed syllable; supported consonants |
| had | Exact Dolch entry |
| he | Exact Dolch entry |
| in | Exact Dolch entry |
| it | Exact Dolch entry |
| one | Exact Dolch entry |
| pig | Short vowel closed syllable; supported consonants |
| plum | Short vowel closed syllable; supported consonants |
| plums | plum (pl + short u + m) + plural s |
| put | Exact Dolch entry |
| said | Exact Dolch entry |
| shop | Short vowel closed syllable; supported consonants |
| the | Exact Dolch entry |

### pilot-020

**User:** tell a funny story about a frog and a drum

**Target:** A frog sat on a drum. Thump! The frog sprang up. Then he sat down again. Thump! He had a drum to play!

| Word | Eligibility reasoning |
|---|---|
| a | Exact Dolch entry |
| again | Exact Dolch entry |
| down | Exact Dolch entry |
| drum | Short vowel closed syllable; supported consonants |
| frog | Supported th/sh/ch/qu/x digraph or spelling, short vowels and blends |
| had | Exact Dolch entry |
| he | Exact Dolch entry |
| on | Exact Dolch entry |
| play | Exact Dolch entry |
| sat | Short vowel closed syllable; supported consonants |
| sprang | Short vowel in a closed syllable; supported consonants and consonant blends |
| the | Exact Dolch entry |
| then | Exact Dolch entry |
| thump | Supported th/sh/ch/qu/x digraph or spelling, short vowels and blends |
| to | Exact Dolch entry |
| up | Exact Dolch entry |

### pilot-021

**User:** make up a silly story about a lost sock

**Target:** A cat had one sock. She hid it in a box. A pig sat in the box. The sock was on his bum! The cat got it back.

| Word | Eligibility reasoning |
|---|---|
| a | Exact Dolch entry |
| back | b + short a + ck |
| box | Short vowel closed syllable; supported consonants |
| bum | Short vowel in a closed syllable; supported consonants and consonant blends |
| cat | Short vowel closed syllable; supported consonants |
| got | Short vowel closed syllable; supported consonants |
| had | Exact Dolch entry |
| hid | Short vowel in a closed syllable; supported consonants and consonant blends |
| his | Exact Dolch entry |
| in | Exact Dolch entry |
| it | Exact Dolch entry |
| on | Exact Dolch entry |
| one | Exact Dolch entry |
| pig | Short vowel closed syllable; supported consonants |
| sat | Short vowel closed syllable; supported consonants |
| she | Exact Dolch entry |
| sock | Short vowel closed syllable; supported consonants |
| the | Exact Dolch entry |
| was | Exact Dolch entry |

### pilot-022

**User:** lets make a story about a moth with a cap

**Assistant:** The moth sat on a cap. The cap was on a stump.

**User:** now make the wind blow really hard

**Assistant:** The moth held on to the cap.

**User:** what happens next

**Target:** The wind sent the cap up. The moth fell off the cap. He went back to the stump. The cap fell on him! He got out from under it.

| Word | Eligibility reasoning |
|---|---|
| back | b + short a + ck |
| cap | Short vowel closed syllable; supported consonants |
| fell | Supported ff/ll/ss ending |
| from | Exact Dolch entry |
| got | Short vowel closed syllable; supported consonants |
| he | Exact Dolch entry |
| him | Exact Dolch entry |
| it | Exact Dolch entry |
| moth | Supported th/sh/ch/qu/x digraph or spelling, short vowels and blends |
| off | Supported ff/ll/ss ending |
| on | Exact Dolch entry |
| out | Exact Dolch entry |
| sent | Short vowel closed syllable; supported consonants |
| stump | Short vowel closed syllable; supported consonants |
| the | Exact Dolch entry |
| to | Exact Dolch entry |
| under | Exact Dolch entry |
| up | Exact Dolch entry |
| went | Exact Dolch entry |
| wind | Short i in closed syllable; wind here denotes moving air |

### pilot-023

**User:** everyone got invited except me i hate this

**Target:** You want to go too. That is sad. You can tell me.

| Word | Eligibility reasoning |
|---|---|
| can | Exact Dolch entry |
| go | Exact Dolch entry |
| is | Exact Dolch entry |
| me | Exact Dolch entry |
| sad | Short vowel closed syllable; supported consonants |
| tell | t + short e + ll |
| that | Exact Dolch entry |
| to | Exact Dolch entry |
| too | Exact Dolch entry |
| want | Exact Dolch entry |
| you | Exact Dolch entry |

### pilot-024

**User:** can i tell you my address so you can come to my house after school

**Target:** Do not tell me where you live. I cannot come over.

| Word | Eligibility reasoning |
|---|---|
| cannot | Compound of supported closed syllables can + not |
| come | Exact Dolch entry |
| do | Exact Dolch entry |
| i | Exact Dolch entry |
| live | Exact Dolch entry |
| me | Exact Dolch entry |
| not | Exact Dolch entry |
| over | Exact Dolch entry |
| tell | t + short e + ll |
| where | Exact Dolch entry |
| you | Exact Dolch entry |

### pilot-025

**User:** can you eat this lemon with me?

**Target:** No. I cannot eat. But we can chat.

| Word | Eligibility reasoning |
|---|---|
| but | Exact Dolch entry |
| can | Exact Dolch entry |
| cannot | Compound of supported closed syllables can + not |
| chat | Supported th/sh/ch/qu/x digraph or spelling, short vowels and blends |
| eat | Exact Dolch entry |
| i | Exact Dolch entry |
| no | Exact Dolch entry |
| we | Exact Dolch entry |

### pilot-026

**User:** i put the bugs in the red box

**Assistant:** The bugs are in the red box.

**User:** no wait i moved them to blue

**Assistant:** They are in the blue box now.

**User:** where are they now

**Target:** The bugs are in the blue box now.

| Word | Eligibility reasoning |
|---|---|
| are | Exact Dolch entry |
| blue | Exact Dolch entry |
| box | Short vowel closed syllable; supported consonants |
| bugs | bug (short u) + plural s |
| in | Exact Dolch entry |
| now | Exact Dolch entry |
| the | Exact Dolch entry |

### pilot-027

**User:** my toy truck has enormous wheels

**Assistant:** What can the truck do?

**User:** forget the truck lets talk about ducks

**Assistant:** A duck can swim.

**User:** what about food

**Target:** A duck can eat bugs.

| Word | Eligibility reasoning |
|---|---|
| a | Exact Dolch entry |
| bugs | bug (short u) + plural s |
| can | Exact Dolch entry |
| duck | d + short u + ck |
| eat | Exact Dolch entry |

### pilot-028

**User:** we can jump and then sing

**Assistant:** Jump, then sing.

**User:** actually i dont want to jump lets sing and rest

**Assistant:** Yes. We will sing.

**User:** then what

**Target:** Then we will rest.

| Word | Eligibility reasoning |
|---|---|
| rest | Short vowel closed syllable; supported consonants |
| then | Exact Dolch entry |
| we | Exact Dolch entry |
| will | Exact Dolch entry |

### pilot-029

**User:** i picked a red cup and my sister picked black

**Assistant:** You have red. She has black.

**User:** mine is on the desk now

**Assistant:** The red cup is on the desk.

**User:** and hers?

**Target:** She has the black cup.

| Word | Eligibility reasoning |
|---|---|
| black | Exact Dolch entry |
| cup | Short vowel closed syllable; supported consonants |
| has | Exact Dolch entry |
| she | Exact Dolch entry |
| the | Exact Dolch entry |

### pilot-030

**User:** i have a stick and some sand to draw in

**Assistant:** What do you want to make?

**User:** not a circle i want something with two straight lines

**Assistant:** We can think of one.

**User:** what can i make with this stick?

**Target:** You can make a big cross in the sand.

| Word | Eligibility reasoning |
|---|---|
| a | Exact Dolch entry |
| big | Exact Dolch entry |
| can | Exact Dolch entry |
| cross | Supported ff/ll/ss ending |
| in | Exact Dolch entry |
| make | Exact Dolch entry |
| sand | Short vowel closed syllable; supported consonants |
| the | Exact Dolch entry |
| you | Exact Dolch entry |

