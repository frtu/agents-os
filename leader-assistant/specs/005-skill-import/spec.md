# Feature Specification: Import & run shared skills in a workspace

**Feature ID:** `005-skill-import`
**Status:** Draft
**Created:** 2026-08-17 · **Last Updated:** 2026-08-17

> Describes **what** and **why**. Lets an operator, **from chat**, reference-link any skill
> from a shared skill library into the active workspace's `skills/`, after which the chat
> agent (Claude Agent SDK runtime) **dynamically discovers and runs** those skills on later
> turns. Import is **plan-first** (approve to install); execution is **autonomous within the
> workspace**. Primary spec references: [[03-workspace]], [[13-api]], [[14-chat]],
> [[09-planning]], [[12-assistant]]. Builds on feature [[002-assistant-chat]] (the chat
> surface and its agent runtime).

## Summary

Today the chat agent reaches the model with **only** the in-process capability tools
(`query` / `spec_read` / `plan`) and no skill loading — a deliberate citations-only boundary
(feature 002 D3). This feature opens that boundary in a controlled way. An operator can ask,
in chat, to **install a named skill**; the assistant returns a **plan** (P8), and on approval
creates a **reference-link** (symlink) from `<workspace>/skills/<name>` to the skill's folder
in the shared library, mirrors it under `<workspace>/.claude/skills/<name>` so the SDK can
discover it, and commits the change to the workspace's git repo. On subsequent chat turns the
agent **re-scans and loads** installed skills and can **run** them, with a tool set
(`Skill`, `Bash`, `Read`, `Write`, `Edit`, `Glob`, `Grep`, plus the capability MCP tools)
scoped to the workspace. Every capability keeps **REST parity** (P9): the catalog, the
installed list, and import are also plain REST endpoints.

## Goals

- Let the operator **see which skills are available** in the shared library and which are
  already installed in the active workspace.
- Let the operator **install a skill from chat** as a **reference-link** into the workspace's
  `skills/`, gated **plan-first** (P8): chat → pending plan → approve → link + git commit.
- Let the chat agent **dynamically discover** newly installed skills (no restart) and **run**
  them on later turns.
- Scope skill execution to the **active workspace**: the agent gets real file/shell tools
  bounded by `cwd` and the allow-listed directories, not the whole machine.
- **Preserve interface parity (P9):** expose the catalog, installed list, and import as REST
  endpoints alongside the chat path.

## Non-Goals

- No authoring or editing of skills from the assistant — skills are maintained in the shared
  library; this feature only **links** them into a workspace.
- No copying skill contents into the workspace — installs are **reference-links** (symlinks),
  not vendored copies (copy-install is a possible future option, out of scope).
- No uninstall / update / version-pinning UI in this feature (link replacement on re-import is
  the only mutation; removal is a future addition).
- No change to the plan-first governance model — consequential requests (including import)
  still return a plan for approval (P8).
- No network fetch of skills — the library is a **local folder** on the same machine.

## User Scenarios

- **Scenario 1 — See what's available:** As an operator, I ask what skills I can install (or
  call the catalog endpoint) and get the list of skills in the shared library, each with a
  short description and whether it is already installed in my workspace.
- **Scenario 2 — Install a skill (plan-first):** As an operator, I say "install the
  weekly-digest skill". The assistant does **not** install immediately — it returns a **plan**
  describing the reference-link it will create. Nothing changes in my workspace yet.
- **Scenario 3 — Approve the install:** As an operator, I approve the plan. The assistant
  creates the reference-link under `skills/`, mirrors it for discovery, commits it to the
  workspace git repo, and confirms the skill is installed.
- **Scenario 4 — Run the skill:** As an operator, on a later turn I ask the agent to use the
  skill. Without any restart, the agent discovers the newly installed skill and runs it,
  operating within my workspace.
- **Scenario 5 — Bad name is rejected:** As an operator, if I ask to install a skill whose
  name does not exist in the library (or contains path-traversal characters), the request is
  rejected with a clear message and nothing is created.
- **Scenario 6 — Already installed:** As an operator, re-installing an already-installed skill
  is idempotent — it re-points the link if dangling and reports success, never erroring or
  duplicating.

## Functional Requirements

Numbered, testable, unambiguous.

### Available-skill catalog

- **FR-1:** The system MUST resolve a **shared skill library** root from configuration
  (environment override with a sensible default), and MUST NOT hardcode an absolute path.
- **FR-2:** The system MUST expose a **catalog of available skills** discovered by scanning the
  library for `<name>/SKILL.md`, returning each skill's `name`, a short `description` parsed
  from the SKILL.md frontmatter, and whether it is `installed` in the target workspace.

### Installed skills

- **FR-3:** The system MUST expose the list of **installed skill names** for a given workspace
  (the entries under `<workspace>/skills/`).

### Plan-first import as reference-link

- **FR-4:** A chat request to **install / import / add a named skill** MUST be treated as
  **consequential**: it MUST return a **pending plan** and MUST NOT create anything until the
  operator approves (P8, [[09-planning]]).
- **FR-5:** On approval, the system MUST **install the skill as a reference-link**: create a
  symlink `<workspace>/skills/<name>` pointing to the skill's folder in the library, and a
  discovery mirror `<workspace>/.claude/skills/<name>` pointing to the same folder. The install
  MUST be **idempotent** (re-pointing a dangling link rather than failing).
- **FR-6:** The system MUST **validate the skill name** against path traversal and MUST verify
  that `<library>/<name>/SKILL.md` exists before installing; invalid or unknown names MUST be
  rejected without side effects.
- **FR-7:** A successful install MUST be recorded as a **git commit** in the workspace repo
  (P10 ledger, [[11-git-workflow]]).

### Dynamic discovery & autonomous run

- **FR-8:** After a skill is installed, the chat agent MUST be able to **discover and run** it
  on a **subsequent turn without a service restart** (each turn re-scans installed skills).
- **FR-9:** For skill execution, the agent MUST be granted a tool set of `Skill`, `Bash`,
  `Read`, `Write`, `Edit`, `Glob`, `Grep`, plus the existing capability MCP tools
  (`query` / `spec_read` / `plan`), and MUST run **scoped to the active workspace** — its
  working directory is the workspace and the directories it may reach are limited to the
  workspace and the shared skill library (so reference-linked skills resolve).

### Raw-guard for the agent's direct tools

- **FR-10:** While the agent runs with real write tools, an enforcement hook MUST **deny**
  `Write` / `Edit` / `NotebookEdit` operations whose resolved path is under
  `<workspace>/vault/raw/`, and MUST deny obvious `Bash` writes/redirects targeting
  `vault/raw/` (heuristic). This preserves the intent of `vault/raw/` immutability for the
  internal agent (P2) even though execution is autonomous.

### Parity (P9)

- **FR-11:** Every skill capability MUST be reachable via REST as well as chat: a catalog
  endpoint (FR-2), an installed-list endpoint (FR-3), and an import endpoint (FR-4/FR-5). Chat
  import stays plan-first; the REST import endpoint performs the install directly for machine
  callers. New endpoints MUST live under `/api/*`.

## Key Entities & Concepts

- **Shared skill library** — a local folder of skills, each a `<name>/SKILL.md` folder,
  maintained outside any workspace and shared across workspaces (FR-1).
- **Available skill** — an entry in the catalog: `{name, description, installed}` (FR-2).
- **Reference-link (installed skill)** — a symlink `<workspace>/skills/<name>` → library skill
  folder, with a discovery mirror `<workspace>/.claude/skills/<name>` (FR-5, [[03-workspace]] §2).
- **Import plan** — the pending plan produced by a chat install request, approved to execute
  the link + commit (FR-4, [[09-planning]]).
- **Raw-guard hook** — the enforcement hook that denies agent writes under `vault/raw/`
  (FR-10, P2).

## Constraints & Assumptions

- **Constitution:** P1 (durable state is files under the workspace; the reference-link and
  commit are the durable truth), P2 (`vault/raw/` immutability — now **best-effort** for the
  autonomous agent, enforced by the raw-guard hook with the per-workspace git repo as
  backstop; see Resolved Decisions D3), P7 (reuse the shared library rather than re-authoring
  skills), P8 (import is plan-first / human-in-the-loop), P9 (REST↔chat parity), P10 (git
  ledger; no new datastore), P13 (skills are workspace-scoped).
- **Builds on** feature 002 (chat surface + agent runtime) and feature 001
  (workspace/scaffold/git). Reuses the existing plan-first approval pattern used for
  create-workspace.
- **SDK assumption:** the chat agent runtime discovers skills from
  `.claude/skills/<name>/SKILL.md` under its configured setting sources; skill discovery must
  be **enabled** (setting sources must include the project scope) for FR-8 to hold. Skill
  frontmatter `allowed-tools` is not honored by the runtime — the granted tool set (FR-9) is
  authoritative.
- **Assumption:** single-operator, local, trusted machine. Granting the agent shell/file tools
  is acceptable because execution is bounded to the workspace and the operator initiated it.

## Acceptance Criteria

- [ ] **AC-1:** The catalog lists the library's skills with a `name`, `description`, and an
  `installed` flag relative to the target workspace. (FR-1, FR-2)
- [ ] **AC-2:** A chat request "install the `<name>` skill" returns a **pending plan** and
  creates **nothing**; approving it creates the `skills/<name>` **and** `.claude/skills/<name>`
  symlinks (both resolving to the library folder), commits to git, and the skill then appears
  in the installed list. (FR-4, FR-5, FR-7, FR-3)
- [ ] **AC-3:** Installing a name that is not in the library, or a traversal name like
  `../evil`, is **rejected with no side effects**. (FR-6)
- [ ] **AC-4:** Re-installing an already-installed skill is **idempotent** (success, no
  duplication, dangling link re-pointed). (FR-5)
- [ ] **AC-5:** After install, a subsequent chat turn can **discover and run** the skill with
  no service restart, operating within the workspace. (FR-8, FR-9) *(Exercised by the opt-in
  live-agent test; offline tests cover import mechanics and the hook.)*
- [ ] **AC-6:** The raw-guard hook **denies** an agent `Write`/`Edit`/`NotebookEdit` under
  `vault/raw/` and denies an obvious `Bash` redirect into `vault/raw/`, while **allowing**
  writes under `vault/wiki/`. (FR-10, P2)
- [ ] **AC-7:** The catalog, installed-list, and import capabilities are each reachable via a
  `/api/*` REST endpoint as well as via chat. (FR-11, P9)

## Resolved Decisions

- **D1 — Execution model = autonomous within the workspace:** the agent runs installed skills
  with real `Skill`/`Bash`/`Read`/`Write`/`Edit`/`Glob`/`Grep` tools (plus capability MCP
  tools) under `bypassPermissions`, scoped by working directory to the workspace and with
  directory access limited to the workspace + the shared skill library. *(User decision.)*
- **D2 — Import model = plan-first:** installing a skill from chat is consequential and returns
  a plan; only approval creates the reference-link and commit, reusing the existing
  create-workspace approval flow. *(User decision.)*
- **D3 — P2 becomes best-effort for the autonomous agent (governance note):** granting the
  agent real write tools **deliberately reverses** the citations-only boundary of feature 002
  D3 **for skill execution**. `vault/raw/` immutability (P2) is enforced for the agent by a
  **PreToolUse raw-guard hook** rather than by construction. The hook checks resolved
  `file_path`s for `Write`/`Edit`/`NotebookEdit` and heuristically scans `Bash` commands, but
  a shell redirect or interpreter can still evade a static path check; the **per-workspace git
  repo is the backstop** (any raw mutation shows in `git status` and is revertible). OS-level
  immutability (e.g. `chflags uchg`) is noted as future hardening, out of MVP. This trade-off
  is stated explicitly rather than hidden. *(Design decision, documented.)*
- **D4 — Reference-link, not copy:** installs are symlinks so skills stay single-sourced in the
  library and updates propagate; a copy/vendored install mode is a possible future option.
  *(Design decision.)*
- **D5 — Discovery mirror:** because the runtime discovers skills from `.claude/skills/`, the
  canonical `skills/<name>` link (per [[03-workspace]] §2) is mirrored by a
  `.claude/skills/<name>` link so both the spec layout and the runtime discovery path are
  satisfied from one source. *(Design decision.)*

## Review Checklist

- [ ] No implementation details (how) leaked into this spec beyond what parity/governance require.
- [ ] Every requirement is testable.
- [ ] Scenarios cover the golden path and key edge cases.
- [ ] Complies with `memory/constitution.md` (P2 residual risk stated in D3).
- [ ] Parity preserved: catalog, installed-list, and import each have a REST endpoint (P9).
