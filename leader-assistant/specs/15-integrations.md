---
id: 202608152112-15
title: External Integrations & Output Feedback
spec: 15-integrations
layer: moc
status: draft
lifecycle: draft
Category: spec
Tags: [integrations, external-pm, feedback-loop, jira, linear]
traceability:
  readme: ["§16 External Project Management Systems", "§26 Output → Knowledge Feedback"]
  references: ["_references_/10-internal-storage/wiki-architecture.md"]
related:
  - "[[00-product-vision]]"
  - "[[09-planning]]"
  - "[[13-api]]"
  - "[[16-workflows]]"
  - "[[014-workspace-mcp-servers]]"
Created: 2026-08-15
Last Updated: 2026-09-12
---

# External Integrations & Output Feedback

The external PM system is an **integration boundary**, invoked only on explicit user demand. The assistant does not continuously synchronize its Vault with a PM system.

## 1. On-Demand External Actions

Examples: "Create a new story for payment reconciliation." · "Update the acceptance criteria of story ABC-123." · "Create these tasks in Jira." · "Move this ticket to In Progress."

Procedure (README §16):
1. understand the request;
2. use knowledge and specifications;
3. generate a proposed action/plan ([[09-planning]]);
4. ask for clarification if needed;
5. invoke the external integration;
6. capture the resulting output/action;
7. optionally feed useful resulting knowledge back into the Vault.

The Integration Manager ([[12-assistant]]) owns these boundaries.

## 2. Boundary Rules (invariants)

- The Vault is **not** the PM system (Jira, Linear, Azure DevOps). See [[00-product-vision]].
- No autonomous execution of arbitrary external actions without user intent ([[01-principles]] Non-Goals).
- No continuous whole-Vault synchronization with any PM tool.

> Producing the artifacts themselves (meeting summaries, tickets, strategy, etc.) — reusing the externalized root `templates/` — is the secondary output capability specified in [[21-outputs]]. This doc covers pushing them to external systems and feeding results back.

## 3. Output → Knowledge Feedback (README §26)

Generated artifacts can become inputs to the knowledge system:

```text
Knowledge → Specification → Review → Feedback → Improved Knowledge
```

After generating an output, evaluate: which concepts were used; whether existing concepts needed correction; whether new concepts emerged; whether a contradiction was discovered; whether the spec exposed missing knowledge; whether concept usage should be recorded (`referenced-to`, [[05-zettelkasten]]).

## 4. Per-Workspace MCP Servers (feature [[014-workspace-mcp-servers]])

A distinct, narrower integration path than §1's on-demand external actions: attaching a live
**MCP server** (e.g. Atlassian at `https://mcp.atlassian.com/v1/mcp`) to a single workspace so
its tools become directly callable by the agent, rather than the assistant driving one-off
external actions itself.

- **Registration** is per-workspace, in `<workspace>/.mcp.json` (the schema the `claude` CLI
  already discovers) — an operator `list`/`add`/`remove`s servers, never the agent (default
  agent MCP blacklist). See [[03-workspace]] §4b for the storage layout.
- **Login** is captured once per workspace via a workspace-scoped `CLAUDE_CONFIG_DIR`
  (`<workspace>/.mcp-auth/`, git-ignored) so later agent runs reuse the token without a second
  login. The config dir is relocated only for workspaces that register a server, and only for
  the duration of a run ([[014-workspace-mcp-servers]] FR-10/FR-15/FR-16).
- Registered servers' tools are exposed to the agent as `mcp__<name>__*`, still subject to the
  existing PreToolUse risk gate ([[011-maker-checker-approval]]) — this is a tool surface, not a
  bypass of the gate that governs §1's on-demand actions.
- Isolation: a server + login on one workspace is invisible to another (Constitution P13).

## 5. Acceptance Criteria

- AC1: External PM actions occur only when explicitly requested by the user.
- AC2: Each external action is preceded by a proposed action/plan.
- AC3: Results of external actions are captured (and optionally fed back into the Vault).
- AC4: No background process synchronizes the whole Vault to an external PM tool.
- AC5: Generated outputs trigger an output→knowledge evaluation recording concept usage.
- AC6: An operator can add/list/remove a per-workspace external MCP server and capture its
  login once, reused by later agent runs without a second login ([[014-workspace-mcp-servers]]).
- AC7: The agent cannot itself add, remove, or log in to an external MCP server (operator-only).
