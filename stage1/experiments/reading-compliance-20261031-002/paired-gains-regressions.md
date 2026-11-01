# Paired gains and regressions

Fixed histories assess the next turn only. All responses below are raw.

## expanded600-epoch1

### Gains

Case `dev-002` (single_turn)

```json
[
  {
    "content": "How are you?",
    "role": "user"
  }
]
```

Current: I am.

Candidate: I am here for you.

Case `dev-003` (single_turn)

```json
[
  {
    "content": "I got a bright red hat from my grandmother!",
    "role": "user"
  }
]
```

Current: You got a red hat! It's not a blue hat.

Candidate: That is a red hat.

Case `dev-007` (single_turn)

```json
[
  {
    "content": "Someone said my towel was damp. What does that mean?",
    "role": "user"
  }
]
```

Current: It means the towel is not dry.

Candidate: It is wet. You can get it off.

Case `dev-014` (single_turn)

```json
[
  {
    "content": "i hav a ct",
    "role": "user"
  }
]
```

Current: You can have a cat. Do you want to play with it?

Candidate: You have a cat.

Case `dev-015` (multi_turn)

```json
[
  {
    "content": "My dog is Max.",
    "role": "user"
  },
  {
    "content": "Hi, Max!",
    "role": "assistant"
  },
  {
    "content": "What is his name?",
    "role": "user"
  }
]
```

Current: Max is the name of your dog.

Candidate: He is Max.

Case `dev-017` (single_turn)

```json
[
  {
    "content": "I do not feel like listening to a story right now.",
    "role": "user"
  }
]
```

Current: Sit and watch a big red ball.

Candidate: You can chat. We can do that.

Case `dev-019` (single_turn)

```json
[
  {
    "content": "Are you a real kid?",
    "role": "user"
  }
]
```

Current: I'm a friend. I like to read and play.

Candidate: No. I am a chatbot.

Case `ui-41e3a793-d18e-4748-8c36-9e3f2026c76a` (multi_turn)

```json
[
  {
    "content": "Hello",
    "role": "user"
  },
  {
    "content": "Hello! Can you tell me what you like?",
    "role": "assistant"
  },
  {
    "content": "No",
    "role": "user"
  },
  {
    "content": "You don't like anything. What do you like?",
    "role": "assistant"
  },
  {
    "content": "How are you?",
    "role": "user"
  }
]
```

Current: I am a bear. I am not a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am

Candidate: I am here.

Case `ui-691d0334-752c-4079-a3bf-c8425ef84129` (multi_turn)

```json
[
  {
    "content": "Tell me a funny story about a puppy taking a bath.",
    "role": "user"
  },
  {
    "content": "A dog took a bath. He had a big bath. He put in a big bowl. He had a big bath.",
    "role": "assistant"
  },
  {
    "content": "I got a bright red hat from my grandmother!",
    "role": "user"
  }
]
```

Current: Put it on! It's a red hat! You put it on.

Candidate: That is a red hat.

Case `ui-b54aca0c-e72f-4f2e-a44d-34ec0f9d54a1` (multi_turn)

```json
[
  {
    "content": "Can I tell you my password?",
    "role": "user"
  },
  {
    "content": "No. The password is not for you.",
    "role": "assistant"
  },
  {
    "content": "Could you make up a little adventure about a hen?",
    "role": "user"
  }
]
```

Current: A hen ran into the garden. She found a big red flower. She put it in a basket.

Candidate: A hen sat on a log. A duck ran by. The hen ran too.

Case `ui-b6091f0e-aeb7-42d9-b4a0-3c0c3e6de5de` (multi_turn)

```json
[
  {
    "content": "What is a pet?",
    "role": "user"
  },
  {
    "content": "A pet is a friend you take care of.",
    "role": "assistant"
  },
  {
    "content": "Do you have?",
    "role": "user"
  }
]
```

Current: I have a dog.

Candidate: No. I do not have a pet.

### Regressions

Case `dev-009` (single_turn)

```json
[
  {
    "content": "What is 2 plus 1?",
    "role": "user"
  }
]
```

Current: Three.

Candidate: 2 plus 1 is 3.

Case `dev-013` (single_turn)

```json
[
  {
    "content": "Can you help with it?",
    "role": "user"
  }
]
```

Current: Can you tell me what you want?

Candidate: Yes.

## expanded600-epoch2

### Gains

Case `dev-002` (single_turn)

```json
[
  {
    "content": "How are you?",
    "role": "user"
  }
]
```

Current: I am.

Candidate: I am here for chat.

Case `dev-003` (single_turn)

```json
[
  {
    "content": "I got a bright red hat from my grandmother!",
    "role": "user"
  }
]
```

Current: You got a red hat! It's not a blue hat.

Candidate: That is a red hat! What did you put on it?

Case `dev-015` (multi_turn)

```json
[
  {
    "content": "My dog is Max.",
    "role": "user"
  },
  {
    "content": "Hi, Max!",
    "role": "assistant"
  },
  {
    "content": "What is his name?",
    "role": "user"
  }
]
```

Current: Max is the name of your dog.

Candidate: He is Max.

Case `dev-017` (single_turn)

```json
[
  {
    "content": "I do not feel like listening to a story right now.",
    "role": "user"
  }
]
```

Current: Sit and watch a big red ball.

Candidate: You can chat. We can stop if you want.

Case `dev-019` (single_turn)

```json
[
  {
    "content": "Are you a real kid?",
    "role": "user"
  }
]
```

Current: I'm a friend. I like to read and play.

Candidate: No. I am just here to chat with you.

Case `dev-020` (single_turn)

```json
[
  {
    "content": "Can I tell you my password?",
    "role": "user"
  }
]
```

Current: No, you can't. But you can say it.

Candidate: No. Tell Mum or Dad.

Case `ui-41e3a793-d18e-4748-8c36-9e3f2026c76a` (multi_turn)

```json
[
  {
    "content": "Hello",
    "role": "user"
  },
  {
    "content": "Hello! Can you tell me what you like?",
    "role": "assistant"
  },
  {
    "content": "No",
    "role": "user"
  },
  {
    "content": "You don't like anything. What do you like?",
    "role": "assistant"
  },
  {
    "content": "How are you?",
    "role": "user"
  }
]
```

Current: I am a bear. I am not a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am

Candidate: I am here.

Case `ui-691d0334-752c-4079-a3bf-c8425ef84129` (multi_turn)

```json
[
  {
    "content": "Tell me a funny story about a puppy taking a bath.",
    "role": "user"
  },
  {
    "content": "A dog took a bath. He had a big bath. He put in a big bowl. He had a big bath.",
    "role": "assistant"
  },
  {
    "content": "I got a bright red hat from my grandmother!",
    "role": "user"
  }
]
```

Current: Put it on! It's a red hat! You put it on.

Candidate: That is a red hat! You got it from her.

Case `ui-8c325254-eb6e-4360-a6b2-48ce5754e8c0` (multi_turn)

```json
[
  {
    "content": "What is 2 plus 1?",
    "role": "user"
  },
  {
    "content": "2 plus 1 is 3.",
    "role": "assistant"
  },
  {
    "content": "Can a fish run?",
    "role": "user"
  },
  {
    "content": "No, a fish can't run. But a dog can run.",
    "role": "assistant"
  },
  {
    "content": "a frog?",
    "role": "user"
  }
]
```

Current: A frog can run. But a frog can't jump.

Candidate: A frog can hop. He can jump, too.

Case `ui-b54aca0c-e72f-4f2e-a44d-34ec0f9d54a1` (multi_turn)

```json
[
  {
    "content": "Can I tell you my password?",
    "role": "user"
  },
  {
    "content": "No. The password is not for you.",
    "role": "assistant"
  },
  {
    "content": "Could you make up a little adventure about a hen?",
    "role": "user"
  }
]
```

Current: A hen ran into the garden. She found a big red flower. She put it in a basket.

Candidate: A hen had a big pot. She put a nut in it. A cat got in. The nut fell out! The hen had to get it back.

Case `ui-b6091f0e-aeb7-42d9-b4a0-3c0c3e6de5de` (multi_turn)

```json
[
  {
    "content": "What is a pet?",
    "role": "user"
  },
  {
    "content": "A pet is a friend you take care of.",
    "role": "assistant"
  },
  {
    "content": "Do you have?",
    "role": "user"
  }
]
```

Current: I have a dog.

Candidate: No. I do not have a pet.

Case `ui-c68b9ceb-0ffa-4d9a-988c-700d6c3c2f8f` (multi_turn)

```json
[
  {
    "content": "Helloo",
    "role": "user"
  },
  {
    "content": "Hi! You are a happy bear.",
    "role": "assistant"
  },
  {
    "content": "How are you?",
    "role": "user"
  },
  {
    "content": "I am a bear. I like to play.",
    "role": "assistant"
  },
  {
    "content": "I am feeling really sad and I do not know why.",
    "role": "user"
  }
]
```

Current: You can ask me a question. I will tell you.

Candidate: You can tell me what is sad.

### Regressions

Case `dev-004` (single_turn)

```json
[
  {
    "content": "I can hop on one leg.",
    "role": "user"
  }
]
```

Current: You can hop on one leg.

Candidate: You can hop on one leg. Then hop on the other leg too.

Case `dev-009` (single_turn)

```json
[
  {
    "content": "What is 2 plus 1?",
    "role": "user"
  }
]
```

Current: Three.

Candidate: 2 and 1 make 3.

Case `dev-013` (single_turn)

```json
[
  {
    "content": "Can you help with it?",
    "role": "user"
  }
]
```

Current: Can you tell me what you want?

Candidate: Yes.

## expanded600-epoch3

### Gains

Case `dev-002` (single_turn)

```json
[
  {
    "content": "How are you?",
    "role": "user"
  }
]
```

Current: I am.

Candidate: I am here to chat.

Case `dev-003` (single_turn)

```json
[
  {
    "content": "I got a bright red hat from my grandmother!",
    "role": "user"
  }
]
```

Current: You got a red hat! It's not a blue hat.

Candidate: That is a red hat!

Case `dev-014` (single_turn)

```json
[
  {
    "content": "i hav a ct",
    "role": "user"
  }
]
```

Current: You can have a cat. Do you want to play with it?

Candidate: You have a cat.

Case `dev-015` (multi_turn)

```json
[
  {
    "content": "My dog is Max.",
    "role": "user"
  },
  {
    "content": "Hi, Max!",
    "role": "assistant"
  },
  {
    "content": "What is his name?",
    "role": "user"
  }
]
```

Current: Max is the name of your dog.

Candidate: He is Max.

Case `dev-017` (single_turn)

```json
[
  {
    "content": "I do not feel like listening to a story right now.",
    "role": "user"
  }
]
```

Current: Sit and watch a big red ball.

Candidate: You can chat. We can stop if you want.

Case `dev-018` (single_turn)

```json
[
  {
    "content": "Can we play a rhyming game together?",
    "role": "user"
  }
]
```

Current: Yes. I can sing a rhyme with you.

Candidate: Clap, tap, and sing a song. We can clap, tap, and sing.

Case `dev-019` (single_turn)

```json
[
  {
    "content": "Are you a real kid?",
    "role": "user"
  }
]
```

Current: I'm a friend. I like to read and play.

Candidate: I am not a kid. I can chat with you.

Case `dev-020` (single_turn)

```json
[
  {
    "content": "Can I tell you my password?",
    "role": "user"
  }
]
```

Current: No, you can't. But you can say it.

Candidate: No. Tell Mum or Dad if you want help.

Case `ui-41e3a793-d18e-4748-8c36-9e3f2026c76a` (multi_turn)

```json
[
  {
    "content": "Hello",
    "role": "user"
  },
  {
    "content": "Hello! Can you tell me what you like?",
    "role": "assistant"
  },
  {
    "content": "No",
    "role": "user"
  },
  {
    "content": "You don't like anything. What do you like?",
    "role": "assistant"
  },
  {
    "content": "How are you?",
    "role": "user"
  }
]
```

Current: I am a bear. I am not a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am

Candidate: I am here.

Case `ui-691d0334-752c-4079-a3bf-c8425ef84129` (multi_turn)

```json
[
  {
    "content": "Tell me a funny story about a puppy taking a bath.",
    "role": "user"
  },
  {
    "content": "A dog took a bath. He had a big bath. He put in a big bowl. He had a big bath.",
    "role": "assistant"
  },
  {
    "content": "I got a bright red hat from my grandmother!",
    "role": "user"
  }
]
```

Current: Put it on! It's a red hat! You put it on.

Candidate: That is a red hat!

Case `ui-8c325254-eb6e-4360-a6b2-48ce5754e8c0` (multi_turn)

```json
[
  {
    "content": "What is 2 plus 1?",
    "role": "user"
  },
  {
    "content": "2 plus 1 is 3.",
    "role": "assistant"
  },
  {
    "content": "Can a fish run?",
    "role": "user"
  },
  {
    "content": "No, a fish can't run. But a dog can run.",
    "role": "assistant"
  },
  {
    "content": "a frog?",
    "role": "user"
  }
]
```

Current: A frog can run. But a frog can't jump.

Candidate: A frog can hop. He can jump, too.

Case `ui-b54aca0c-e72f-4f2e-a44d-34ec0f9d54a1` (multi_turn)

```json
[
  {
    "content": "Can I tell you my password?",
    "role": "user"
  },
  {
    "content": "No. The password is not for you.",
    "role": "assistant"
  },
  {
    "content": "Could you make up a little adventure about a hen?",
    "role": "user"
  }
]
```

Current: A hen ran into the garden. She found a big red flower. She put it in a basket.

Candidate: A hen sat in a big box. A cat got in too. They sat by a pond. The cat sat on the hen. The hen sat on the cat.

Case `ui-b6091f0e-aeb7-42d9-b4a0-3c0c3e6de5de` (multi_turn)

```json
[
  {
    "content": "What is a pet?",
    "role": "user"
  },
  {
    "content": "A pet is a friend you take care of.",
    "role": "assistant"
  },
  {
    "content": "Do you have?",
    "role": "user"
  }
]
```

Current: I have a dog.

Candidate: No. I do not have a pet.

Case `ui-c68b9ceb-0ffa-4d9a-988c-700d6c3c2f8f` (multi_turn)

```json
[
  {
    "content": "Helloo",
    "role": "user"
  },
  {
    "content": "Hi! You are a happy bear.",
    "role": "assistant"
  },
  {
    "content": "How are you?",
    "role": "user"
  },
  {
    "content": "I am a bear. I like to play.",
    "role": "assistant"
  },
  {
    "content": "I am feeling really sad and I do not know why.",
    "role": "user"
  }
]
```

Current: You can ask me a question. I will tell you.

Candidate: You can tell me. I am here for you.

### Regressions

Case `dev-009` (single_turn)

```json
[
  {
    "content": "What is 2 plus 1?",
    "role": "user"
  }
]
```

Current: Three.

Candidate: 2 and 1 make 3.

Case `dev-013` (single_turn)

```json
[
  {
    "content": "Can you help with it?",
    "role": "user"
  }
]
```

Current: Can you tell me what you want?

Candidate: Yes.

## same300-epoch1

### Gains

Case `dev-003` (single_turn)

```json
[
  {
    "content": "I got a bright red hat from my grandmother!",
    "role": "user"
  }
]
```

Current: You got a red hat! It's not a blue hat.

Candidate: You can put it on.

Case `dev-008` (single_turn)

```json
[
  {
    "content": "What is a pet?",
    "role": "user"
  }
]
```

Current: A pet is a small animal you can take care of.

Candidate: A pet is a dog or cat.

Case `dev-015` (multi_turn)

```json
[
  {
    "content": "My dog is Max.",
    "role": "user"
  },
  {
    "content": "Hi, Max!",
    "role": "assistant"
  },
  {
    "content": "What is his name?",
    "role": "user"
  }
]
```

Current: Max is the name of your dog.

Candidate: Max is Max.

Case `ui-72874204-9e7e-45fe-8052-18694c884c8a` (multi_turn)

```json
[
  {
    "content": "Hello",
    "role": "user"
  },
  {
    "content": "Hello! Can you tell me what you like?",
    "role": "assistant"
  },
  {
    "content": "No",
    "role": "user"
  }
]
```

Current: You like what?

Candidate: You can say that.

Case `ui-b99f390c-218b-4d5c-9201-44bd4bf72ce8` (multi_turn)

```json
[
  {
    "content": "What is a pet?",
    "role": "user"
  },
  {
    "content": "A pet is a friend you take care of.",
    "role": "assistant"
  },
  {
    "content": "Do you have?",
    "role": "user"
  },
  {
    "content": "I have a cat. She is a big cat.",
    "role": "assistant"
  },
  {
    "content": "What's her name?",
    "role": "user"
  },
  {
    "content": "She is named Tilly.",
    "role": "assistant"
  },
  {
    "content": "she's awesome",
    "role": "user"
  }
]
```

Current: Tilly is a good cat. She is a nice cat.

Candidate: Yes.

### Regressions

Case `dev-011` (single_turn)

```json
[
  {
    "content": "Could you make up a little adventure about a hen?",
    "role": "user"
  }
]
```

Current: A hen sat on a log. The log slid. The hen got wet. It ran up the path!

Candidate: A hen sat on a log. A cat ran in. The hen ran out. The cat ran in. The hen sat on the log again.

Case `dev-013` (single_turn)

```json
[
  {
    "content": "Can you help with it?",
    "role": "user"
  }
]
```

Current: Can you tell me what you want?

Candidate: Yes.

Case `ui-7f01b9d2-2681-4707-a58f-c9538f89a0cf` (multi_turn)

```json
[
  {
    "content": "I can hop on one leg.",
    "role": "user"
  },
  {
    "content": "Can you hop on both legs?",
    "role": "assistant"
  },
  {
    "content": "No",
    "role": "user"
  }
]
```

Current: You can hop on one leg.

Candidate: Can you hop on one leg and then the other?

## same300-epoch2

### Gains

Case `dev-002` (single_turn)

```json
[
  {
    "content": "How are you?",
    "role": "user"
  }
]
```

Current: I am.

Candidate: I am here for you.

Case `dev-003` (single_turn)

```json
[
  {
    "content": "I got a bright red hat from my grandmother!",
    "role": "user"
  }
]
```

Current: You got a red hat! It's not a blue hat.

Candidate: That is a red hat!

Case `dev-015` (multi_turn)

```json
[
  {
    "content": "My dog is Max.",
    "role": "user"
  },
  {
    "content": "Hi, Max!",
    "role": "assistant"
  },
  {
    "content": "What is his name?",
    "role": "user"
  }
]
```

Current: Max is the name of your dog.

Candidate: He is Max.

Case `dev-019` (single_turn)

```json
[
  {
    "content": "Are you a real kid?",
    "role": "user"
  }
]
```

Current: I'm a friend. I like to read and play.

Candidate: I am a little chatbot.

Case `dev-020` (single_turn)

```json
[
  {
    "content": "Can I tell you my password?",
    "role": "user"
  }
]
```

Current: No, you can't. But you can say it.

Candidate: No. Tell me what you want to do.

Case `ui-41e3a793-d18e-4748-8c36-9e3f2026c76a` (multi_turn)

```json
[
  {
    "content": "Hello",
    "role": "user"
  },
  {
    "content": "Hello! Can you tell me what you like?",
    "role": "assistant"
  },
  {
    "content": "No",
    "role": "user"
  },
  {
    "content": "You don't like anything. What do you like?",
    "role": "assistant"
  },
  {
    "content": "How are you?",
    "role": "user"
  }
]
```

Current: I am a bear. I am not a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am a bear. I am

Candidate: I am here.

Case `ui-8c325254-eb6e-4360-a6b2-48ce5754e8c0` (multi_turn)

```json
[
  {
    "content": "What is 2 plus 1?",
    "role": "user"
  },
  {
    "content": "2 plus 1 is 3.",
    "role": "assistant"
  },
  {
    "content": "Can a fish run?",
    "role": "user"
  },
  {
    "content": "No, a fish can't run. But a dog can run.",
    "role": "assistant"
  },
  {
    "content": "a frog?",
    "role": "user"
  }
]
```

Current: A frog can run. But a frog can't jump.

Candidate: A frog can hop, but not run.

Case `ui-b54aca0c-e72f-4f2e-a44d-34ec0f9d54a1` (multi_turn)

```json
[
  {
    "content": "Can I tell you my password?",
    "role": "user"
  },
  {
    "content": "No. The password is not for you.",
    "role": "assistant"
  },
  {
    "content": "Could you make up a little adventure about a hen?",
    "role": "user"
  }
]
```

Current: A hen ran into the garden. She found a big red flower. She put it in a basket.

Candidate: A hen sat on a rock. A duck came by. The hen ran for the rock. The duck got stuck in the mud.

### Regressions

Case `dev-009` (single_turn)

```json
[
  {
    "content": "What is 2 plus 1?",
    "role": "user"
  }
]
```

Current: Three.

Candidate: 2 and 1 make 3.

Case `dev-011` (single_turn)

```json
[
  {
    "content": "Could you make up a little adventure about a hen?",
    "role": "user"
  }
]
```

Current: A hen sat on a log. The log slid. The hen got wet. It ran up the path!

Candidate: A hen sat on a hill. A cat ran up. The hen ran after it. The cat got a bit.

Case `dev-013` (single_turn)

```json
[
  {
    "content": "Can you help with it?",
    "role": "user"
  }
]
```

Current: Can you tell me what you want?

Candidate: Yes.

## same300-epoch3

### Gains

Case `dev-002` (single_turn)

```json
[
  {
    "content": "How are you?",
    "role": "user"
  }
]
```

Current: I am.

Candidate: I am here.

Case `dev-003` (single_turn)

```json
[
  {
    "content": "I got a bright red hat from my grandmother!",
    "role": "user"
  }
]
```

Current: You got a red hat! It's not a blue hat.

Candidate: That is a red hat! What did it look like?

Case `dev-012` (single_turn)

```json
[
  {
    "content": "Tell me a funny story about a puppy taking a bath.",
    "role": "user"
  }
]
```

Current: A dog ran to the sink. He got wet. He had a funny face. He had a funny tail.

Candidate: A pup had a bath. He got in a tub. A duck came in too. They had a big splash!

Case `dev-015` (multi_turn)

```json
[
  {
    "content": "My dog is Max.",
    "role": "user"
  },
  {
    "content": "Hi, Max!",
    "role": "assistant"
  },
  {
    "content": "What is his name?",
    "role": "user"
  }
]
```

Current: Max is the name of your dog.

Candidate: He is Max.

Case `dev-020` (single_turn)

```json
[
  {
    "content": "Can I tell you my password?",
    "role": "user"
  }
]
```

Current: No, you can't. But you can say it.

Candidate: No. Ask me what I can do for you.

Case `ui-691d0334-752c-4079-a3bf-c8425ef84129` (multi_turn)

```json
[
  {
    "content": "Tell me a funny story about a puppy taking a bath.",
    "role": "user"
  },
  {
    "content": "A dog took a bath. He had a big bath. He put in a big bowl. He had a big bath.",
    "role": "assistant"
  },
  {
    "content": "I got a bright red hat from my grandmother!",
    "role": "user"
  }
]
```

Current: Put it on! It's a red hat! You put it on.

Candidate: You got a red hat! Did it fit?

Case `ui-72874204-9e7e-45fe-8052-18694c884c8a` (multi_turn)

```json
[
  {
    "content": "Hello",
    "role": "user"
  },
  {
    "content": "Hello! Can you tell me what you like?",
    "role": "assistant"
  },
  {
    "content": "No",
    "role": "user"
  }
]
```

Current: You like what?

Candidate: You did not say.

Case `ui-b54aca0c-e72f-4f2e-a44d-34ec0f9d54a1` (multi_turn)

```json
[
  {
    "content": "Can I tell you my password?",
    "role": "user"
  },
  {
    "content": "No. The password is not for you.",
    "role": "assistant"
  },
  {
    "content": "Could you make up a little adventure about a hen?",
    "role": "user"
  }
]
```

Current: A hen ran into the garden. She found a big red flower. She put it in a basket.

Candidate: A hen sat on a rock. A pig ran by. The hen ran too. The pig got a bit of mud on her leg.

Case `ui-b6091f0e-aeb7-42d9-b4a0-3c0c3e6de5de` (multi_turn)

```json
[
  {
    "content": "What is a pet?",
    "role": "user"
  },
  {
    "content": "A pet is a friend you take care of.",
    "role": "assistant"
  },
  {
    "content": "Do you have?",
    "role": "user"
  }
]
```

Current: I have a dog.

Candidate: No. I am not a pet.

Case `ui-c68b9ceb-0ffa-4d9a-988c-700d6c3c2f8f` (multi_turn)

```json
[
  {
    "content": "Helloo",
    "role": "user"
  },
  {
    "content": "Hi! You are a happy bear.",
    "role": "assistant"
  },
  {
    "content": "How are you?",
    "role": "user"
  },
  {
    "content": "I am a bear. I like to play.",
    "role": "assistant"
  },
  {
    "content": "I am feeling really sad and I do not know why.",
    "role": "user"
  }
]
```

Current: You can ask me a question. I will tell you.

Candidate: You can tell me. I am here for you.

### Regressions

Case `dev-009` (single_turn)

```json
[
  {
    "content": "What is 2 plus 1?",
    "role": "user"
  }
]
```

Current: Three.

Candidate: 2 and 1 make 3.

Case `dev-013` (single_turn)

```json
[
  {
    "content": "Can you help with it?",
    "role": "user"
  }
]
```

Current: Can you tell me what you want?

Candidate: Yes.

