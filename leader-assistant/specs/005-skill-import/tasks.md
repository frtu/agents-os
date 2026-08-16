# Tasks: Import & run shared skills in a workspace (005)

Ordered build for feature `005-skill-import`. Each task cites the spec requirement it
satisfies. See [`spec.md`](spec.md) and [`plan.md`](plan.md).

- [ ] **T001 — Specs (spec-first):** write `spec.md`, `plan.md`, `tasks.md`; update
  [[03-workspace]] §2 (reference-link + `.claude/skills/` mirror + enumeration + ACs) and
  [[13-api]] (skills in the parity surface + AC). *(spec 005 all FR)*
- [ ] **T002 — Config:** add `config.skills_library_root()` (env `LEADER_SKILLS_SOURCE`,
  default = repo-sibling `skills/`). *(FR-1)*
- [ ] **T003 — Vault:** scaffold `.claude/skills/`; add `install_skill_link` (two symlinks,
  idempotent) and `list_installed_skill_names`. *(FR-3, FR-5)*
- [ ] **T004 — Models:** `SkillSummary`, `SkillCatalog`, `InstalledSkills`,
  `ImportSkillRequest`, `ImportSkillReport`. *(FR-2, FR-3, FR-5, FR-11)*
- [ ] **T005 — Capabilities:** `_IMPORT_SKILL` regex; `list_available_skills`,
  `list_installed_skills`, `import_skill` (name validation + git commit); wire plan-first into
  `ask_stream` and execute in `_execute_pending`. *(FR-2, FR-3, FR-4, FR-5, FR-6, FR-7)*
- [ ] **T006 — Agent:** `run_stream(workspace_path=…)`; `setting_sources=["project"]`, `cwd`,
  `add_dirs`, `skills="all"`, `bypassPermissions`, expanded `allowed_tools`, PreToolUse
  `_raw_guard_hook`. *(FR-8, FR-9, FR-10)*
- [ ] **T007 — API (parity):** `GET /api/skills`, `GET /api/skills/installed`,
  `POST /api/skills/import`. *(FR-11)*
- [ ] **T008 — Tests:** conftest tmp library; `test_skills_api.py` (catalog, plan-first import
  + approve, traversal reject, parity); `test_agent_raw_guard.py` (hook logic); opt-in live
  test. Run `uv run --extra dev pytest` green. *(AC-1..AC-7)*
