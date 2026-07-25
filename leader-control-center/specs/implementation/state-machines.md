# /specs/state-machines.md

# State Machines

## Story

```
Draft

↓

Todo

↓

Ready

↓

Executing

↓

Review

↓

Completed

↓

Archived
```

---

## Task

```
Draft

↓

Ready

↓

Running

↓

Waiting

↓

Blocked

↓

Completed

↓

Cancelled
```

---

## Story Execution

```
Created

↓

Running

↓

Waiting

↓

Completed

↓

Cancelled

↓

Failed
```

---

## Task Execution

```
Created

↓

Running

↓

WaitingDecision

↓

Running

↓

Completed

↓

Failed

↓

Cancelled
```

---

## Agent Execution

```
Queued

↓

Running

↓

WaitingTool

↓

WaitingDecision

↓

Completed

↓

Failed
```

---

# Decision Lifecycle

```
Requested

↓

Viewed

↓

Responded

↓

Applied

↓

Closed
```

---

# Human Request Lifecycle

```
Created

↓

Visible

↓

Acknowledged

↓

Resolved

↓

Closed
```
