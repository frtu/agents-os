# /specs/data-model.md

# Data Model

## Planning

Workspace

```
id

name

createdAt
```

---

Epic

```
id

workspaceId

title

description

status
```

---

Story

```
id

epicId

title

description

priority

status
```

---

Task

```
id

storyId

title

description

status

order
```

---

Dependency

```
taskId

dependsOnTaskId
```

---

AcceptanceCriteria

```
id

storyId

description
```

---

## Runtime

StoryExecution

```
id

storyId

status

startedAt

completedAt
```

---

TaskExecution

```
id

storyExecutionId

taskId

status
```

---

AgentExecution

```
id

taskExecutionId

agentType

status
```

---

HumanRequest

```
id

executionId

type

status

createdAt
```

---

Decision

```
id

humanRequestId

decision

comment

user

createdAt
```

---

Artifact

```
id

executionId

type

location

version
```

---

TimelineEvent

```
id

executionId

type

payload

createdAt
```

Timeline becomes the immutable audit log.
