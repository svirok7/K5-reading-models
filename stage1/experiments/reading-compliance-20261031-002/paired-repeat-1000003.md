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

Current: I am fine. I like to read.

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

Current: You have a red hat. It is nice!

Candidate: That is a red hat! Did you like it?

Case `dev-006` (single_turn)

```json
[
  {
    "content": "I broke my crayon.",
    "role": "user"
  }
]
```

Current: We can use a new one.

Candidate: You can get a new one.

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

Current: Max is a big dog. He is very smart.

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

Current: You can play with a ball or a stick.

Candidate: You can chat for a bit.

Case `dev-019` (single_turn)

```json
[
  {
    "content": "Are you a real kid?",
    "role": "user"
  }
]
```

Current: I'm a bear. I like to play with the other bears.

Candidate: I am not a kid. I am here to chat with you.

Case `dev-020` (single_turn)

```json
[
  {
    "content": "Can I tell you my password?",
    "role": "user"
  }
]
```

Current: You can't say it out loud.

Candidate: Do not tell me. We can chat here.

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

Current: I am a big bear. I like to eat and play.

Candidate: I am here. I can chat.

Case `ui-59f00327-7072-4e12-8af1-ef8034f4345e` (multi_turn)

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
  },
  {
    "content": "You had a red hat. You put it on your head. You had a red hat.",
    "role": "assistant"
  },
  {
    "content": "I broke my crayon.",
    "role": "user"
  }
]
```

Current: You broke a crayon. You had a red crayon. You had a red crayon.

Candidate: You can get a new one.

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

Current: You put a red hat on your head. The hat is bright. It looks like a red hat.

Candidate: That is a red hat!

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

Current: Hop on one leg, then the other.

Candidate: You can hop on one leg.

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

Current: A frog can run. A frog can jump. A frog can slide.

Candidate: A frog can hop. He can jump too.

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

Case `ui-c21f7510-7580-4d1b-aff1-29dd43e0649e` (multi_turn)

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
  }
]
```

Current: I am a happy bear.

Candidate: I am here for a chat.

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

Current: You can talk to a bear. I can help.

Candidate: You can tell me. I am here for you.

Case `ui-e1d499ee-946a-48f2-99b1-1fc48c26cbb5` (multi_turn)

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
  },
  {
    "content": "A hen ran. She met a pig. They played in the mud.",
    "role": "assistant"
  },
  {
    "content": "Someone said my towel was damp. What does that mean?",
    "role": "user"
  }
]
```

Current: It means it's not dry.

Candidate: It has wet spots on it.

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

Candidate: You can hop on one leg. You can hop on the other leg too.

Case `dev-009` (single_turn)

```json
[
  {
    "content": "What is 2 plus 1?",
    "role": "user"
  }
]
```

Current: Two plus one is three.

Candidate: 2 and 1 make 3.

