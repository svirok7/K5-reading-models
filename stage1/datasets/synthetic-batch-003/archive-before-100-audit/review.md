# Batch 003 — examples 61–100

40 examples: 16 short, 16 medium, 8 long inputs; 13 with prior exchanges. Objective: reading-profile word selection. Model-authored and self-reviewed; pending human review. Word explanations are excluded from SFT completions. Detailed evidence includes assistant history. No benchmark/development data was opened.

Completion-only training: conversational prompt/completion JSONL, completion_only_loss=True, native Qwen3 chat template with enable_thinking=False; verify label masks, template and sequence lengths before training. No training or tokenizer verification performed.

## Examples

### pilot-061

**User:** morninggg

**Target:** Hi! Did you just get up?

**Word-choice reasoning:** “Hi” uses long i in an open syllable, while the other words are listed.

### pilot-062

**User:** thats so cool

**Target:** You like it!

**Word-choice reasoning:** Every word is an exact allowed-list entry, avoiding the unsupported oo spelling in “cool.”

### pilot-063

**User:** i put all my socks away

**Target:** You put them all away!

**Word-choice reasoning:** Every word is an exact entry on the allowed list.

### pilot-064

**User:** nope not today

**Target:** We do not have to.

**Word-choice reasoning:** Every word is on the allowed list, avoiding the unsupported spelling in “today.”

### pilot-065

**User:** i can have warm milk or cold milk

**Assistant:** You can pick.

**User:** i dont like warm milk

**Assistant:** What do you want?

**User:** the cold one

**Target:** Not hot, then.

**Word-choice reasoning:** “Hot” uses short o, while “not” and “then” are listed.

### pilot-066

**User:** my aunt came to visit yesterday

**Target:** Did you have fun with her?

**Word-choice reasoning:** “Fun” uses short u, and every other word is on the allowed list.

### pilot-067

**User:** i dropped my spoon in my soup

**Target:** Can you get it out?

**Word-choice reasoning:** Every word is on the allowed list, avoiding the unsupported vowel spellings in “spoon” and “soup.”

### pilot-068

**User:** wait a sec

**Target:** Take a bit.

**Word-choice reasoning:** “Bit” uses short i, while “take” and “a” are listed.

### pilot-069

**User:** my umbrella turned inside out in the wind and now its all bent and funny looking

**Target:** The wind bent it! Can you fix it?

**Word-choice reasoning:** “Wind,” “bent,” and “fix” use short vowels and supported consonants or blends; the other words are listed.

### pilot-070

**User:** all squishy

**Target:** Can you press it flat?

**Word-choice reasoning:** “Press” uses pr, short e and ss, and “flat” uses fl with short a; the other words are listed.

### pilot-071

**User:** we tried making bread but the dough stuck to absolutely everything including my fingers and sleeves

**Target:** What a mess! Did it stick to the pan too?

**Word-choice reasoning:** “Mess,” “stick,” and “pan” use short vowels with ss or ck where needed; the other words are listed.

### pilot-072

**User:** my dad made an enormous pile of laundry and i disappeared behind it when i crouched down

**Target:** Did he see you? You could be under it!

**Word-choice reasoning:** Every word is listed, including the irregular exact entry “could.”

### pilot-073

**User:** i thought this pretend gem was a real stone

**Assistant:** Is it a rock?

**User:** no its from my toy treasure box

**Assistant:** It may not be a rock.

**User:** its plastic actually

**Target:** It is not a rock, then.

**Word-choice reasoning:** “Rock” uses short o with ck, while every other word is listed.

### pilot-074

**User:** my toy rocket is ready

**Assistant:** What can it do?

**User:** i pressed the button and it flew straight up

**Assistant:** Did it go up a lot?

**User:** it went miles

**Target:** It went up and up!

**Word-choice reasoning:** Every word is an exact allowed-list entry, avoiding the unsupported spelling in “miles.”

### pilot-075

**User:** the enormous tractor had wheels taller than me

**Target:** That is big! Did you get on it?

**Word-choice reasoning:** Every word is on the allowed list, avoiding the unsupported spellings in “tractor” and “wheels.”

### pilot-076

**User:** my ribbon got tangled around the chair legs and now i cant pull it free at all

**Target:** It is stuck. Ask for help with it.

**Word-choice reasoning:** “Stuck” uses st, short u and ck, while all remaining words are listed.

### pilot-077

**User:** what does thin mean when you say a thin stick

**Target:** A thin stick is not thick.

**Word-choice reasoning:** “Thin,” “stick,” and “thick” use short vowels with th or ck, while the other words are listed.

### pilot-078

**User:** if i push this toy truck gently across the kitchen floor will it move away from me

**Target:** Yes. You can make it go.

**Word-choice reasoning:** Every word is an exact entry on the allowed list.

### pilot-079

**User:** does a duck have a beak

**Target:** Yes. A duck has a bill.

**Word-choice reasoning:** “Duck” uses short u with ck and “bill” uses short i with ll; the other words are listed.

### pilot-080

**User:** i had three stickers and my cousin gave me one more so how many have i got

**Target:** Three and one make four.

**Word-choice reasoning:** Every word, including each number, is an exact allowed-list entry.

### pilot-081

**User:** i have three cups

**Assistant:** You have three.

**User:** i gave two to my friends

**Assistant:** Two are with them.

**User:** how many left

**Target:** You have one left.

**Word-choice reasoning:** “Left” uses short e with ft, while the other words are listed.

### pilot-082

**User:** i have a tiny pin next to my drum

**Assistant:** A pin and a drum.

**User:** the drum is nearly as big as my chair

**Assistant:** That is a big drum.

**User:** which is bigger

**Target:** The drum is big. The pin is little.

**Word-choice reasoning:** “Drum” and “pin” use short vowels with supported consonants or blends, while the other words are listed.

### pilot-083

**User:** is snow white or is it blue

**Target:** It can look white.

**Word-choice reasoning:** Every word, including “white,” is an exact allowed-list entry.

### pilot-084

**User:** what can i do with a bucket

**Target:** You can put things in it.

**Word-choice reasoning:** “Things” adds plural s to th–short-i–ng, while the other words are listed.

### pilot-085

**User:** tell me a story with a bug and a log

**Target:** It sat on a log. A bug came by. The bug got on the log too. Then the log slid down. Off they went!

**Word-choice reasoning:** “Sat,” “log,” “bug,” and “slid” use short vowels and supported blends, “off” uses ff, and the other words are listed.

### pilot-086

**User:** make up a silly story where a goat loses its hat and then gets it back again

**Target:** It had a red hat. The hat fell in a bin. A pig got it out. Then the pig put it on! It had to ask for it back. Then it got the hat back.

**Word-choice reasoning:** “Hat,” “bin,” “pig,” “got,” and “back” use short vowels with ck in “back,” and “fell” uses ll; the other words are listed.

### pilot-087

**User:** tell a story about a crab in a cup

**Target:** A crab hid in a cup. A gull saw it. The gull put a stick in. Snap! The crab held on.

**Word-choice reasoning:** “Crab,” “hid,” “cup,” “gull,” “stick,” “snap,” and “held” use short vowels with supported blends, ll and ck; the other words are listed.

### pilot-088

**User:** tell a story about a dog ringing a bell

**Target:** A dog sat by a bell. He hit it. Ring, ring! A cat ran in. The dog did it again.

**Word-choice reasoning:** “Dog,” “sat,” “bell,” “hit,” “ring,” and “cat” use short vowels, with ll and ng where needed; the rest are listed.

### pilot-089

**User:** our pretend toy boat went into a cave

**Assistant:** It went in.

**User:** the cave is full of sand and shells

**Assistant:** What could be in there?

**User:** what was inside

**Target:** It saw a big shell. A crab was in it. The crab got out. Then it hid in the sand.

**Word-choice reasoning:** “Shell” uses sh and ll, and “crab,” “got,” “hid,” and “sand” use short vowels and supported blends; the rest are listed.

### pilot-090

**User:** a mouse is hiding from a cat in our story

**Assistant:** The cat can see him.

**User:** the mouse is much smaller than the cat

**Assistant:** He can fit in a little gap.

**User:** how did he get away then

**Target:** He ran under the bed. The cat did not fit. He sat still. Then the cat went away.

**Word-choice reasoning:** “Ran” is listed, while “bed,” “cat,” “fit,” “sat,” and “still” use short vowels with supported blends or ll; the remaining words are listed.

### pilot-091

**User:** i wanted to go out but its raining

**Target:** You want to go out. That is no fun.

**Word-choice reasoning:** “Fun” uses short u, while every other word is on the allowed list.

### pilot-092

**User:** should i tell you the name of my school and exactly where my classroom is so you know

**Target:** No. Do not tell me where it is.

**Word-choice reasoning:** Every word is on the allowed list, avoiding the unsupported spellings in “school” and “classroom.”

### pilot-093

**User:** can you smell the popcorn i made

**Target:** No. I cannot smell it.

**Word-choice reasoning:** “Smell” uses sm, short e and ll, and “cannot” combines decodable “can” and “not”; the other words are listed.

### pilot-094

**User:** im scared ill get it all wrong

**Target:** You can ask for help.

**Word-choice reasoning:** Every word is listed, avoiding the silent-w spelling in “wrong.”

### pilot-095

**User:** my sock is on the desk

**Assistant:** You can get it.

**User:** oops it fell and i kicked it under the desk

**Assistant:** It fell down.

**User:** its under now

**Target:** The sock is under the desk now.

**Word-choice reasoning:** “Sock” uses short o with ck and “desk” uses short e with sk, while the other words are listed.

### pilot-096

**User:** i was talking about toy bricks

**Assistant:** What do you make?

**User:** now i want to talk about cheese

**Assistant:** What do you want to ask?

**User:** and what about cheese

**Target:** You can eat it.

**Word-choice reasoning:** Every word is listed, avoiding the unsupported ee spelling in “cheese.”

### pilot-097

**User:** i have three little bells

**Assistant:** You have three.

**User:** wait i found one more under the sofa

**Assistant:** One was under it.

**User:** how many then

**Target:** You have four now.

**Word-choice reasoning:** Every word is on the allowed list.

### pilot-098

**User:** i gave the cap to my mum

**Assistant:** She has the cap.

**User:** my dad has my gloves instead

**Assistant:** He has them.

**User:** who has it

**Target:** She has the cap.

**Word-choice reasoning:** “Cap” uses short a, while every other word is listed.

### pilot-099

**User:** i want white paper for my picture

**Assistant:** You want white.

**User:** the red paper is for my brother

**Assistant:** He can have red.

**User:** which colour again

**Target:** You want white.

**Word-choice reasoning:** Every word, including the exact primer entry “white,” is on the allowed list.

### pilot-100

**User:** i want to put this box on the shelf

**Assistant:** Can you lift it?

**User:** no the shelf is too high for me

**Assistant:** You do not have to lift it.

**User:** i meant put it down not up

**Target:** Put the box down, then.

**Word-choice reasoning:** “Box” uses short o with x, while the other words are listed.

