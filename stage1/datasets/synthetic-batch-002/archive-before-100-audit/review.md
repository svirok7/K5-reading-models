# Batch 002 — examples 31–60

30 SFT candidates. Category and length quotas match the pilot; 10 examples include two prior exchanges. Model-authored and self-reviewed; human review pending.

## Audit result

“Could” is allowed through the first-grade list; “yellow” through the preprimer list. Neither needs a decoding-based exception. See audit.md for corrections and verification limits.

## SFT format

sft.jsonl uses TRL conversational prompt/completion format. The prompt contains the full system instruction and history; completion contains ONLY the final assistant reply. Use completion_only_loss=True, packing=False initially, and the native Qwen3 chat template with enable_thinking=False. Preserve the final reply as completion; do not flatten into language-modeling text that trains on user/history tokens. Verify token masks and sequence length before actual training. No tokenizer/mask runtime test or training has been performed.

Word-choice explanations and IDs are in review.jsonl only, aligned by line with sft.jsonl. They are not SFT text. The system instruction intentionally matches the earlier pilot. No new benchmark/development cases were opened. Unique targets and scenario-family IDs were checked against examples 1–30; semantic similarity to unseen tests is unmeasured.

Format reference: https://huggingface.co/docs/trl/sft_trainer

## Examples

### pilot-031

**User:** heyyy

**Target:** Hi! We can chat.

**Word-choice reasoning:** “Hi” has an open syllable and “chat” uses ch with short a; the other words are listed.

### pilot-032

**User:** im a genius

**Target:** You know a lot!

**Word-choice reasoning:** “Lot” has short o, and the other words are on the allowed list.

### pilot-033

**User:** i finally did all my buttons

**Target:** You did them all!

**Word-choice reasoning:** Every word is on the allowed list.

### pilot-034

**User:** not that again

**Target:** We can do a new one.

**Word-choice reasoning:** Every word, including “new” and “one,” is an exact allowed-list entry.

### pilot-035

**User:** i can have a pink bun or a brown bun

**Assistant:** You can pick one.

**User:** i think brown but wait let me look

**Assistant:** Take a look.

**User:** the pink one

**Target:** A pink bun it is!

**Word-choice reasoning:** “Pink” uses short i with nk and “bun” has short u; the other words are listed.

### pilot-036

**User:** i missed the bus this morning

**Target:** Did you get there in the end?

**Word-choice reasoning:** “End” uses short e with nd, and the other words are listed.

### pilot-037

**User:** my little cousin tipped the entire box of puzzle pieces onto the table and now theyre everywhere

**Target:** What a mess! You can put them back in the box.

**Word-choice reasoning:** “Mess” uses short e with ss, “back” uses short a with ck, and “box” uses short o with x; the rest are listed.

### pilot-038

**User:** it was absolutely freezing outside and my teeth were chattering so i came straight back inside

**Target:** You can get in bed for a bit.

**Word-choice reasoning:** “Bed” and “bit” use short vowels, and the other words are listed.

### pilot-039

**User:** my remote control car zoomed under the sofa and i cant reach it even with my arm

**Target:** It is stuck! Can you ask for help?

**Word-choice reasoning:** “Stuck” uses st, short u and ck, while all remaining words are listed.

### pilot-040

**User:** soooo loud

**Target:** Do you want it to stop?

**Word-choice reasoning:** Every word is an exact allowed-list entry, avoiding the unsupported ou spelling in “loud.”

### pilot-041

**User:** i mixed red paint with blue paint

**Assistant:** You can see them mix.

**User:** its changing colour

**Assistant:** What do you see now?

**User:** its purple now

**Target:** Red and blue can mix like that.

**Word-choice reasoning:** “Mix” uses short i with x, and every other word is listed.

### pilot-042

**User:** there is ice on the path

**Assistant:** You could slip.

**User:** i was going to step on the ice

**Assistant:** It may not be good to step there.

**User:** too slippery

**Target:** Then do not step on it.

**Word-choice reasoning:** “Step” uses st with short e, and every other word is listed.

### pilot-043

**User:** what does snug mean exactly

**Target:** Snug is a good fit. Not too big.

**Word-choice reasoning:** “Snug” uses sn with short u and “fit” has short i; the rest are listed.

### pilot-044

**User:** if i hold chocolate in my hand for ages will it stay hard or change

**Target:** It can melt in a hot hand.

**Word-choice reasoning:** “Melt,” “hot,” and “hand” use short vowels and supported consonants or blends; the other words are listed.

### pilot-045

**User:** why does a bell make noise

**Target:** It can ring when you hit it.

**Word-choice reasoning:** “Ring” uses short i with ng and “hit” has short i; the other words are listed.

### pilot-046

**User:** i found two shiny stones by the gate and then another two so how many altogether

**Target:** Two and two make four.

**Word-choice reasoning:** Every word, including the numbers, is on the allowed list.

### pilot-047

**User:** can a slug jump over things

**Target:** No. A slug cannot jump.

**Word-choice reasoning:** “Slug” uses sl with short u and “cannot” combines decodable “can” and “not”; the other words are listed.

### pilot-048

**User:** my box is on the desk but i lost the lid

**Assistant:** Let us look for it.

**User:** oh i see the lid under my bed now

**Assistant:** You can get it.

**User:** and the lid

**Target:** The lid is under the bed.

**Word-choice reasoning:** “Lid” and “bed” use short vowels, and the other words are listed.

### pilot-049

**User:** tell me a story about a rat making lunch

**Target:** A rat had a pot. He put nuts in it. A nut fell out. It hit his leg! He put the pot down.

**Word-choice reasoning:** “Rat,” “pot,” “nut,” “hit,” and “leg” use short vowels, “nuts” adds plural s, and “fell” uses ll; the other words are listed.

### pilot-050

**User:** make a funny story with a dog and a wig

**Target:** A dog got a wig. It was red. He put it on. A gust sent it off! The dog ran to get it.

**Word-choice reasoning:** The unlisted words use short vowels and blends, plus ff in “off”; the other words are listed.

### pilot-051

**User:** tell a little story about an ant hiding

**Target:** An ant hid in a sock. A bug got in too. The sock slid down. Out ran the ant! The bug went with it.

**Word-choice reasoning:** The unlisted words use short vowels and blends, with ck in “sock”; the remaining words are listed.

### pilot-052

**User:** our pretend dragon is tiny and he fell in a muddy pit

**Assistant:** He is stuck in the pit.

**User:** he can climb out using a branch

**Assistant:** He can get out.

**User:** and then what did he do

**Target:** He got out of the pit. He had mud on him. He went for a swim. Then he sat in the sun.

**Word-choice reasoning:** “Got,” “pit,” “mud,” “swim,” “sat,” and “sun” use short vowels and supported blends; the rest are listed.

### pilot-053

**User:** they never let me have a turn

**Target:** You want to play too. You can ask them.

**Word-choice reasoning:** Every word is an exact entry on the allowed list.

### pilot-054

**User:** can you meet me in the park tomorrow if i bring my favourite toy with me

**Target:** I cannot go with you. But we can chat here.

**Word-choice reasoning:** “Cannot” combines decodable “can” and “not,” and “chat” uses ch with short a; the other words are listed.

### pilot-055

**User:** im nervous about my new class

**Target:** You can ask for help when you want.

**Word-choice reasoning:** Every word is on the allowed list, avoiding the unsupported spelling in “nervous.”

### pilot-056

**User:** the black mug is my brothers

**Assistant:** It is his mug.

**User:** my sister has the white one

**Assistant:** She has white.

**User:** whose is black

**Target:** The black mug is his.

**Word-choice reasoning:** “Mug” uses short u, and every other word is on the allowed list.

### pilot-057

**User:** i was asking about train engines

**Assistant:** What do you want to know?

**User:** lets talk about rain instead

**Assistant:** What do you want to ask?

**User:** what about rain

**Target:** It can get you wet.

**Word-choice reasoning:** “Wet” has short e, and every other word is listed.

### pilot-058

**User:** i will wash my hands after lunch

**Assistant:** You can do that.

**User:** wait i meant i will wash before lunch and nap after

**Assistant:** A nap after you eat.

**User:** nap before or after

**Target:** After you eat.

**Word-choice reasoning:** Every word is on the allowed list.

### pilot-059

**User:** i hid the drum under the rug

**Assistant:** You hid the drum.

**User:** the bell was sitting out on the desk

**Assistant:** The bell is on the desk.

**User:** which was hidden

**Target:** The drum was under the rug.

**Word-choice reasoning:** “Drum” and “rug” use short u with supported consonants and blends; the other words are listed.

### pilot-060

**User:** i want yellow string for this

**Assistant:** You want yellow.

**User:** do you think red looks better

**Assistant:** You can pick red.

**User:** no the one i said before

**Target:** You said yellow.

**Word-choice reasoning:** Every word, including “yellow,” is an exact entry on the allowed list.

## Validation limits

Lexical evidence is model-reviewed against exact list membership and the supplied decoding rules. The coverage script verifies no word lacks evidence; it is not independent phonics validation. Human review remains required.
