# Implementation Plan: Import & run shared skills in a workspace (005)

**Feature ID:** `005-skill-import` · **Status:** Draft · **Created:** 2026-08-17

Companion to [`spec.md`](spec.md). Records the **decided** design and the technical facts it
rests on. Cite requirements as `spec 005 FR-N` in code comments.

## Context

The chat agent (`app/agent.py`) reaches the model through `claude-agent-sdk` with **only** the
in-process capability MCP tools (`query`/`spec_read`/`plan`) and `setting_sources=[]` —
deliberately no filesystem/Bash tools and no skill loading (feature 002 D3, FR-2). This
feature lets a user, **from chat**, reference-link any skill from the shared library into
`<workspace>/skills/` and have the agent **dynamically discover and run** those skills on
later turns. It decides the TBD left open by [[03-workspace]] §2.

## Resolved technical facts (validated against SDK v0.2.139 source)

- Skills are discovered by the CLI from `.claude/skills/<name>/SKILL.md` under
  `setting_sources`. `setting_sources=[]` **disables skills entirely** → must become
  `["project"]`. `skills="all"` auto-adds the `Skill` tool.
- SKILL.md `allowed-tools` frontmatter is **ignored** by the SDK; tool access is the SDK
  `allowed_tools` list only.
- A fresh `query()` per turn re-scans skills → dynamic loading works because `ask_stream`
  already opens a new `query()` each turn.
- **`can_use_tool` is NOT invoked under `bypassPermissions`** (SDK emits a warning to use a
  PreToolUse hook). The `vault/raw/` guard for the agent's direct tools must be a **PreToolUse
  hook**.

## Governance note (deliberate, documented — spec 005 D3)

This reverses the citations-only browse boundary (002 D3 / FR-2) *for skill execution*: the
agent gains real Read/Bash/Write scoped to the workspace. Import stays plan-first (P8) and
every capability keeps REST parity (P9). **P2 (`vault/raw/` immutability) becomes best-effort,
not by-construction** — a PreToolUse hook denies writes resolving under `<workspace>/vault/raw/`
and heuristically denies Bash writes there; the per-workspace git repo is the backstop.

## Spec changes (done)

1. New `specs/005-skill-import/{spec,plan,tasks}.md` (this folder).
2. `specs/03-workspace.md` §2 — replace the TBD block with the reference-link definition,
   `.claude/skills/` discovery mirror, and enumeration; add ACs.
3. `specs/13-api.md` — add the three skill endpoints/capability to the parity surface + an AC.

## Code changes

### `app/config.py`
- Add `skills_library_root() -> Path`: env `LEADER_SKILLS_SOURCE`, default =
  `Path(__file__).resolve().parent.parent.parent / "skills"` (the `agents-os-frtu/skills`
  sibling of the repo). No hardcoded absolute path (spec 005 FR-1).

### `app/vault.py`
- `scaffold_workspace`: also `mkdir` `<workspace>/.claude/skills/` (SDK discovery mirror),
  idempotent.
- `install_skill_link(workspace, name, source) -> Path`: create **two** symlinks to `source` —
  canonical `<workspace>/skills/<name>` (spec) and mirror `<workspace>/.claude/skills/<name>`
  (SDK discovery). Idempotent (replace dangling) (spec 005 FR-5).
- `list_installed_skill_names(workspace) -> list[str]` (entries under `skills/`) (FR-3).

### `app/models.py`
- `SkillSummary {name, description, installed}`, `SkillCatalog {source_root, skills[]}`,
  `InstalledSkills {workspace, skills[]}`, `ImportSkillRequest {workspace?, name}`,
  `ImportSkillReport {workspace, name, link_path, committed, message}`.

### `app/capabilities.py`
- `_IMPORT_SKILL` regex near `_CREATE_WORKSPACE`: match `install|import|add … skill <name>`.
- `list_available_skills() -> SkillCatalog`: scan `config.skills_library_root()` for
  `<name>/SKILL.md`, parse `name`/`description` from YAML frontmatter; mark `installed` (FR-2).
- `list_installed_skills(selector) -> InstalledSkills` (FR-3).
- `import_skill(selector, name) -> ImportSkillReport`: validate `name` via `_safe_name`
  (traversal guard) and that `<library>/<name>/SKILL.md` exists; call `vault.install_skill_link`;
  `_git_commit(workspace, f"chore(skills): import {name}")` (FR-5/6/7).
- Wire into `ask_stream`: `_IMPORT_SKILL.search(message)` branch parallel to `_CONSEQUENTIAL`
  that sets a pending plan (plan-first, FR-4).
- `_execute_pending`: add an `_IMPORT_SKILL.search(request)` branch mirroring `_CREATE_WORKSPACE`
  → calls `import_skill`, returns executed.

### `app/agent.py`
- `run_stream(...)` accepts `workspace_path: Path`; update the call site in
  `capabilities.ask_stream` to pass the already-resolved `wpath`.
- `ClaudeAgentOptions`: `setting_sources=["project"]`, `cwd=str(workspace_path)`,
  `add_dirs=[str(workspace_path), str(config.skills_library_root())]`, `skills="all"`,
  `permission_mode="bypassPermissions"`,
  `allowed_tools=["Skill","Bash","Read","Write","Edit","Glob","Grep", *_tool_names()]`,
  `hooks={"PreToolUse":[<raw_guard>]}` (FR-8/9).
- `_raw_guard_hook(workspace_path)`: PreToolUse hook inspecting `tool_input` (`file_path` for
  Write/Edit/NotebookEdit; heuristic scan of `command` for Bash); deny when the path resolves
  under `<workspace>/vault/raw/` (reuse `vault.guard_write_path`). Pure, unit-testable (FR-10).
- Update the module docstring: skill execution is a deliberate, workspace-scoped expansion of
  the tool set (was citations-only in 002 D3).

### `app/api.py` (parity, P9 — spec 005 FR-11)
- `GET  /api/skills` → `capabilities.list_available_skills()`
- `GET  /api/skills/installed?workspace=` → `capabilities.list_installed_skills(...)`
- `POST /api/skills/import` `{workspace?, name}` → `capabilities.import_skill(...)` (direct
  install for REST callers; chat stays plan-first).

## Tests (`tests/`, offline + deterministic)

- **conftest**: set `LEADER_SKILLS_SOURCE` to a tmp library with a couple of fake
  `<name>/SKILL.md` folders so tests never depend on the real library.
- `test_skills_api.py`: available catalog lists fakes with descriptions; `POST
  /api/skills/import` creates both symlinks resolving to source, git-committed, appears in
  installed list; traversal name rejected; chat "install the <x> skill" → `pending_plan` set,
  nothing created, `approve=true` → symlinks created (reuses `offline_agent`); REST parity for
  the three routes.
- `test_agent_raw_guard.py`: unit-test `_raw_guard_hook` — deny Write/Edit under `vault/raw/`,
  allow under `vault/wiki/`, deny obvious Bash `> vault/raw/...`.
- **Opt-in live test** (`LEADER_LIVE_AGENT=1`): import a real skill, then a chat turn asks the
  agent to run it; assert it loaded/executed.

## Key risks (from design review)

1. `setting_sources` must be `["project"]` or **no skills load** — the single most important line.
2. Raw-guard must be a **PreToolUse hook** (not `can_use_tool`, dead under bypassPermissions);
   Bash writes to `vault/raw/` remain a residual risk (git backstop).
3. Granting real Read/Bash/Write reverses the 002 D3 citations-only boundary — spec'd
   deliberately (D3).
4. Symlink targets live outside the workspace → include the library root in `add_dirs`.
