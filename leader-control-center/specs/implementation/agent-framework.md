# /specs/agent-framework.md

# Agent Framework

## Philosophy

Leader Control Center does not implement agents.

It manages and supervises them.

Agents are treated as executable capabilities.

---

# Agent Definition

Every Agent has

```
id

name

description

version

capabilities

supportedTools
```

Example

Resume Writer v2

Architecture Reviewer

Research Assistant

Diagram Generator

---

# Agent Execution

An Agent Definition may create many Agent Executions.

```
Resume Writer

↓

Execution 1

↓

Execution 2

↓

Execution 3
```

---

# Agent Capabilities

Examples

Research

Writing

Coding

Review

Diagram

Presentation

Search

Planning

Translation

---

# Agent Inputs

Prompt

Context

Artifacts

Memory

Tool Access

---

# Agent Outputs

Artifacts

Timeline Events

Human Requests

Logs

Metrics

---

# Versioning

Agents are immutable.

Changing prompts creates

Version 2

rather than modifying Version 1.

This guarantees reproducibility.
