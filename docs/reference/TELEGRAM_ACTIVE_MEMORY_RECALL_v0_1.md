# Telegram Active Memory Recall v0.1

## Status

Stage 83P is implemented in the working tree and pending review.

It is not closed committed. It does not authorize staging or commit.

## Decision

83P adds deterministic active-memory recall to the Telegram runtime webhook.

It lets a Telegram MVP user ask what the robot remembers and see only approved active local memories for the resolved Telegram user and active robot.

It does not create memory.
It does not update memory.
It does not list pending proposals.
It does not list rejected proposals.
It does not list forgotten memories.
It does not list memories from other users or robots.

## Runtime path

83P targets only:

```text
POST /api/telegram/runtime/webhook
```

It does not change the legacy Telegram webhook:

```text
POST /api/telegram/webhook
```

## Intent precedence

The runtime memory branch uses this strict order:

```text
approval/rejection
  -> explicit memory proposal
  -> active memory recall
  -> generic conversation
```

Recall phrases never mutate memory state. Memory proposal matching does not catch recall phrases.

## Supported recall phrases

Spanish:

- `¿qué recuerdas de mí?`
- `que recuerdas de mi`
- `qué sabes de mí`
- `que sabes de mi`
- `muéstrame mis memorias`
- `lista mis memorias`

English:

- `what do you remember about me?`
- `what do you remember`
- `what do you know about me?`
- `show my memories`
- `list my memories`

Matching is deterministic and local. It does not use LLM-based intent classification.

## Active memory listing

When active approved memories exist, 83P lists memory content in the existing stable order returned by the local active-memory query.

Spanish response:

```text
Esto es lo que recuerdo de ti:

1. <memory text>
2. <memory text>
```

English response:

```text
Here is what I remember about you:

1. <memory text>
2. <memory text>
```

## Empty state

Spanish:

```text
Todavía no tengo memorias aprobadas sobre ti. Puedes decir "recuerda que ..." y te pediré aprobación antes de guardarlo.
```

English:

```text
I do not have any approved memories about you yet. You can say "remember that ..." and I will ask for approval before saving it.
```

## Boundary

83P builds only on the 82P approved-memory boundary.

82P remains responsible for proposal creation, approval, rejection, invalid ID handling, and finalized proposal handling.

83P only reads active approved memories through the existing local memory query. It does not introduce a new store, schema, migration, ranking algorithm, retrieval path, or context injection path.

## What is intentionally not implemented

- Context Scan
- retrieval
- connectors
- document or PDF handling
- caregiver runtime
- voice or audio
- proactive or background jobs
- scheduled jobs
- memory inference from normal conversation
- automatic memory creation
- memory editing
- memory deletion
- vector search
- embeddings
- LLM-based memory ranking
- LLM-based intent classification
- cross-chat memory merge
- 84P
- staging
- commit

## Non-claims

83P is not Memory Center UX.
83P is not full memory management.
83P is not a personalization engine.
83P is not a conversational continuity spine expansion.
83P is only active approved memory visibility over the Telegram runtime path.
