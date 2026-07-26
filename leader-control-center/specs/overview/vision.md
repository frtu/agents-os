# Vision

## Problem Statement

Modern AI agents can execute work that spans minutes, hours, or days. Unlike
conversational assistants, these workflows frequently pause to request
clarification, approvals, permissions, or missing information before they can
continue.

Today this creates a poor experience for the people responsible for the work:

- Leaders constantly context-switch between dozens of conversations.
- Long-running work loses visibility once a chat scrolls away.
- Approvals interrupt focus and arrive without operational context.
- There is no single operational view across many concurrent AI initiatives.

Existing Kanban tools manage **human** work.
Existing AI chat interfaces manage **individual conversations**.
Neither provides **supervision over many durable AI workflows at once**.

---

## Vision

Leader Control Center is a **human-in-the-loop control plane for durable AI
workflows**.

Today's AI interfaces are conversation-centric.
Leader Control Center is **execution-centric**.

Instead of managing one AI conversation at a time, leaders supervise multiple
concurrent **Initiatives** through a single operational console — planning work,
launching executions, responding to human requests, reviewing artifacts, and
auditing history without losing context.

The application is **not** a workflow engine.
It is a **Meta Orchestration Control Plane** built on top of durable workflow
engines.

---

## What the Leader Can Do

From one console, a leader can:

- Plan work as business Initiatives
- Launch AI executions
- Monitor progress across all Initiatives
- Respond to human requests (approve, clarify, choose, permit)
- Review generated artifacts
- Continue, retry, or cancel execution
- Audit complete execution history

---

## Goals

Leader Control Center aims to become the operational console for durable AI
execution. It should allow leaders to:

- supervise multiple concurrent AI initiatives
- organize work around business outcomes
- reduce interruption fatigue
- maintain human strategic control
- support long-running execution
- provide complete execution history
- progressively automate execution over time
- remain independent of any specific workflow engine or AI provider

---

## Non Goals

Leader Control Center is **not**:

- a workflow engine
- a chat application
- a project management replacement
- an LLM framework
- an MCP server
- an AI coding IDE

It **coordinates** these systems rather than replacing them.

---

## Primary User

A **leader** — an engineering manager, staff+ engineer, founder, or operator —
who is accountable for multiple concurrent outcomes and delegates execution to
AI while retaining strategic control. The leader values *supervision speed*:
answering "what's running, what needs me, what's done, where are we blocked?"
in seconds.

See [glossary.md](./glossary.md) for the ubiquitous language and
[principles.md](./principles.md) for the product principles that constrain every
design decision.
