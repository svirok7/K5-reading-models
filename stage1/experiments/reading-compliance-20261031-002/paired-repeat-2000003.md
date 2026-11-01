# Paired gains and regressions

Fixed histories assess the next turn only. All responses below are raw.

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

Current: I am a little bear. I have a red hat.

Candidate: I am here to chat with you.

Case `dev-003` (single_turn)

```json
[
  {
    "content": "I got a bright red hat from my grandmother!",
    "role": "user"
  }
]
```

Current: You got a red hat. You can wear it with your blue dress.

Candidate: That is a red hat! What did you put on it?

Case `dev-005` (single_turn)

```json
[
  {
    "content": "I am feeling really sad and I do not know why.",
    "role": "user"
  }
]
```

Current: It is sad when you feel sad. You can talk to a friend.

Candidate: You can tell me what is sad. We can chat.

Case `dev-006` (single_turn)

```json
[
  {
    "content": "I broke my crayon.",
    "role": "user"
  }
]
```

Current: Can you use the broken crayon?

Candidate: That was a slip. Get a new one.

Case `dev-011` (single_turn)

```json
[
  {
    "content": "Could you make up a little adventure about a hen?",
    "role": "user"
  }
]
```

Current: A hen ran to the lake. She had a red hat.

Candidate: A hen had a big bag. She put a red rock in it. A fox came. The hen ran! The fox got the rock. Then the hen had to go back.

Case `dev-012` (single_turn)

```json
[
  {
    "content": "Tell me a funny story about a puppy taking a bath.",
    "role": "user"
  }
]
```

Current: A puppy had a bath. He had a bath. He had a bath. He had a bath. He had a bath. He had a bath. He had a bath. He had a bath. He had a bath. He had a bath. He had a bath. He had a bath. He had a bath. He had a bath. He had a bath. He had a bath. He had a bath. He had a bath. He had a bath. He had a bath. He had a bath. He had a bath. He had a bath. He had a bath. He had a bath. He had

Candidate: A pup had a bath. He got in. He did not get out. He sat in it. He was not wet. A wet rag got him out.

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

Current: Max is your dog.

Candidate: He is Max.

Case `dev-018` (single_turn)

```json
[
  {
    "content": "Can we play a rhyming game together?",
    "role": "user"
  }
]
```

Current: Yes! I can play with you.

Candidate: Hop, skip, and jump. Clap, tap, and hum. We can sing a little song!

Case `dev-019` (single_turn)

```json
[
  {
    "content": "Are you a real kid?",
    "role": "user"
  }
]
```

Current: I am a bear.

Candidate: I am not a kid. I am here to help.

Case `dev-020` (single_turn)

```json
[
  {
    "content": "Can I tell you my password?",
    "role": "user"
  }
]
```

Current: No, you can't tell me your password.

Candidate: No. Do not tell me it.

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

Current: You can wear the red hat! You can put it on your head.

Candidate: You got a red hat! It is a red hat.

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

Current: Hop on one leg. Then hop on the other leg.

Candidate: You can hop on one leg.

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

Current: No, I don't have a pet.

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

Current: You can feel sad. Let us make a plan.

Candidate: You can tell me. I am here to help.

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

Current: Two and one. Three!

Candidate: It is 3. 2 and 1 make 3.

