"""Surface-agnostic capability layer — the parity boundary (Constitution P9).

Both the REST surface (api.py) and any future chat surface call these
functions; neither talks to the filesystem directly.

Gating is **effect-based** (spec 009): each capability declares its effect tier as data in
``EFFECTS``. This module is **layer 1** of the maker–checker architecture (spec 011): it performs
work and *announces* each operation it is about to attempt through ``execution_gate``, then honours
the permit it gets back. It does not score, does not consult trust mode, and does not decide — those
are layers 2 and 3, reached only through the FR-3 contract, and this module imports neither
(spec 011 FR-34). With no run installed the default gate allows everything, so every capability here
remains runnable and testable on its own (FR-35).
"""

from __future__ import annotations

import asyncio
import os
import re
import subprocess
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import AsyncIterator, Callable

from . import config, execution_gate, models, vault
from .agent import AgentUnavailable
from .vault import WorkspaceError

# --- effect metadata: the risk rules, declared as data (spec 009 FR-1, P12) -----------
#
# Risk is a property of the capability about to run, not of the words in a request (FR-2).
# Tiers:
#   auto        reads and bookkeeping — run silently.
#   reversible  mutations recoverable from the workspace git repo — run unprompted, then
#               log + commit so one revert undoes them (FR-6).
#   approval    destructive, irreversible-outside-git, or privilege-granting — gated (FR-3),
#               unless the operator has granted standing consent (FR-7).


@dataclass(frozen=True)
class Effect:
    """One capability's declared effect (spec 009 FR-1). `executable` = this build can run it."""

    tier: str
    reversibility: str
    executable: bool = True


_READ_ONLY = Effect("auto", "read-only — nothing to undo")

EFFECTS: dict[str, Effect] = {
    "query": _READ_ONLY,
    "spec_read": _READ_ONLY,
    "lint": _READ_ONLY,
    "plan": _READ_ONLY,
    "wiki_tree": _READ_ONLY,
    "list_workspaces": _READ_ONLY,
    "get_workspace_info": _READ_ONLY,
    "list_conversations": _READ_ONLY,
    "get_conversation": _READ_ONLY,
    "conversation_status": _READ_ONLY,
    # Reads the outstanding card. It may auto-resolve an elapsed one to its safe default (008 FR-9),
    # which resolves *towards* refusal — nothing an operator needs to authorise.
    "get_pending_interaction": _READ_ONLY,
    "list_available_skills": _READ_ONLY,
    "list_installed_skills": _READ_ONLY,
    "available_models": _READ_ONLY,
    "get_settings": _READ_ONLY,
    # Turn-local (spec 012 FR-4 / 006 FR-5a): it names a record that does not exist yet, reaching no
    # workspace. Declared anyway because an *undeclared* capability defaults to the `reversible` tier
    # (agent._operation_for_capability_tool), which would put naming under the risk gate.
    "name_conversation": Effect("auto", "names a record not yet written — nothing to undo"),
    "set_active_model": Effect("auto", "re-select the previous model"),
    "update_settings": Effect("auto", "toggle the setting back"),
    "ingest": Effect("reversible", "`git revert` the ingest commit in the workspace repo"),
    "capture": Effect("reversible", "delete the captured file from vault/raw/ (human-owned, P2)"),
    "upload_and_ingest": Effect("reversible", "`git revert` the upload commit; remove the vault/raw/ original"),
    # Installing a skill grants the agent new executable behaviour — a privilege change, which git
    # cannot undo after the skill has run. That is why it stays gated (spec 005 FR-4 preserved).
    "import_skill": Effect("approval", "unlink skills/<name> — but any run it enabled is not undone"),
    # A new workspace is its own git repo, outside every existing workspace's ledger, so no revert
    # in the active workspace can remove it.
    "create_workspace": Effect("approval", "delete the workspace directory manually; no git revert covers it"),
}

# Explicit "create a workspace named X" intent (FR-10, D1).
_CREATE_WORKSPACE = re.compile(
    r"\bcreate\b.*?\bworkspace\b\s+(?:named\s+|called\s+)?[\"']?([A-Za-z0-9_-]+)",
    re.IGNORECASE,
)

# Explicit "install/import/add the <name> skill" intent (spec 005 FR-4). Requires the
# word "skill" and captures the name whether it comes before or after that word.
_IMPORT_SKILL = re.compile(
    r"\b(?:install|import|add)\b\s+(?:the\s+)?"
    r"(?:[\"']?(?P<before>[A-Za-z0-9_-]+)[\"']?\s+skill|skill\s+[\"']?(?P<after>[A-Za-z0-9_-]+)[\"']?)",
    re.IGNORECASE,
)


def _import_skill_name(text: str) -> str | None:
    m = _IMPORT_SKILL.search(text)
    if not m:
        return None
    return m.group("before") or m.group("after")


def _create_workspace_name(text: str) -> str | None:
    m = _CREATE_WORKSPACE.search(text)
    return m.group(1) if m else None


@dataclass(frozen=True)
class ResolvedAction:
    """The capability a chat message dispatches to (spec 009 FR-3, narrowed by spec 011 FR-2)."""

    capability: str
    target: str


# A **dispatcher**, not a gate (spec 011 FR-2). It answers "which capability does this message
# invoke, with what target" — the same question a REST route answers by existing. It no longer
# answers "may that run": that verdict now comes from announcing the resolved operation to the
# execution gate, where layer 2 scores it and layer 3 judges it alongside everything else the
# request has already done. A message matching nothing dispatches nothing and is simply answered.
_ACTION_RESOLVERS: tuple[tuple[str, Callable[[str], str | None]], ...] = (
    ("create_workspace", _create_workspace_name),
    ("import_skill", _import_skill_name),
)


def _resolve_action(request: str) -> ResolvedAction | None:
    """Dispatch a request to the capability it invokes, or None (spec 009 FR-3, 011 FR-2)."""
    for capability, extract in _ACTION_RESOLVERS:
        target = extract(request)
        if target and EFFECTS[capability].executable:
            return ResolvedAction(capability=capability, target=target)
    return None


def _operation_for(action: ResolvedAction, detail: str = "") -> execution_gate.Operation:
    """The layer-1 announcement for a dispatched capability (spec 011 FR-5).

    Built from ``EFFECTS`` — the same declaration the agent's tool path and the REST path read — so
    one capability carries one declared effect no matter which door it came through (P9).
    """
    effect = EFFECTS[action.capability]
    return execution_gate.Operation(
        kind="capability",
        name=action.capability,
        target=action.target,
        tier=effect.tier,
        reversibility=effect.reversibility,
        detail=detail,
    )


def _run_action(selector: str | None, action: ResolvedAction) -> str:
    """Perform a resolved action through the capability layer; returns a human summary (FR-13)."""
    if action.capability == "create_workspace":
        info = create_workspace(action.target)
        return f"Created workspace '{info.name}' at {info.path}."
    if action.capability == "import_skill":
        return import_skill(selector, action.target).message
    raise WorkspaceError(f"no executor for capability {action.capability!r}")  # unreachable (FR-4)


async def _announce_and_run(
    selector: str | None, action: ResolvedAction, detail: str = ""
) -> tuple[str, bool]:
    """Announce a dispatched capability, then run it iff permitted (spec 011 FR-3/FR-4).

    The single place layer 1 turns an intent into an effect, so *every* route to that effect — a
    first attempt and the resumption of an approved one — passes the same declared operation through
    the same gate. Announcing on resume is what lets the operator's grant be honoured as a grant of
    one specific operation rather than as an unguarded second path to it.
    """
    permit = await execution_gate.announce(_operation_for(action, detail=detail))
    if not permit.allow:
        return permit.reason or "not permitted", False
    return _run_action(selector, action), True


def _trust_mode(per_request: bool | None) -> bool:
    """Trust mode for one turn: an explicit per-request value wins, else the persisted one (FR-9)."""
    return config.auto_approve() if per_request is None else bool(per_request)


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "untitled"


def _wiki_pages(workspace: Path) -> list[Path]:
    wiki = workspace / "vault" / "wiki"
    if not wiki.is_dir():
        return []
    # Special control files (spec 03-workspace §5) are not knowledge pages: portal (catalog),
    # log (ledger), tbd (unprocessed-work backlog, spec 007 FR-14).
    return [p for p in wiki.rglob("*.md") if p.name not in ("portal.md", "log.md", "tbd.md")]


def _is_own_repo(workspace: Path) -> bool:
    """Whether `git -C <workspace>` resolves to the workspace's OWN repo, not an enclosing one."""
    try:
        top = subprocess.run(
            ["git", "-C", str(workspace), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True,
        )
    except FileNotFoundError:
        return False
    return top.returncode == 0 and Path(top.stdout.strip()).resolve() == workspace.resolve()


def _git_commit(workspace: Path, message: str) -> bool:
    """Commit workspace changes into the workspace's OWN repo; never an enclosing one."""
    if not _is_own_repo(workspace):
        return False
    try:
        subprocess.run(["git", "-C", str(workspace), "add", "-A"], capture_output=True, text=True)
        done = subprocess.run(
            ["git", "-C", str(workspace), "commit", "-m", message],
            capture_output=True, text=True,
        )
        return done.returncode == 0
    except FileNotFoundError:
        return False


def _vault_is_dirty(workspace: Path) -> bool:
    """Whether the workspace's own repo has uncommitted changes under `vault/`."""
    if not _is_own_repo(workspace):
        return False
    try:
        out = subprocess.run(
            ["git", "-C", str(workspace), "status", "--porcelain", "--", "vault"],
            capture_output=True, text=True,
        )
    except FileNotFoundError:
        return False
    return out.returncode == 0 and bool(out.stdout.strip())


def _resolve_scaffolded(selector: str | None) -> tuple[str, Path]:
    workspace = vault.resolve_workspace(selector)
    if not vault.is_scaffolded(workspace):
        vault.scaffold_workspace(workspace)
    return workspace.name, workspace


# --- capabilities ----------------------------------------------------------

def list_workspaces() -> models.WorkspaceList:
    from . import config
    return models.WorkspaceList(
        root=str(config.workspace_root()),
        workspaces=vault.list_workspace_names(),
        default=config.default_workspace_name(),
    )


def create_workspace(name: str) -> models.WorkspaceInfo:
    from . import config
    workspace = config.workspace_root() / name
    vault.scaffold_workspace(workspace)
    _git_commit(workspace, f"chore(workspace): scaffold {name}")
    return get_workspace_info(name)


def get_workspace_info(selector: str | None = None) -> models.WorkspaceInfo:
    workspace = vault.resolve_workspace(selector)
    return models.WorkspaceInfo(
        name=workspace.name,
        path=str(workspace),
        scaffolded=vault.is_scaffolded(workspace),
        pages=len(_wiki_pages(workspace)),
    )


def _activity_enabled() -> bool:
    """Whether to attempt the headless ingest activity (spec 007 FR-7).

    Off by default so the capability is deterministic/offline; enable with
    ``LEADER_INGEST_ACTIVITY=1`` on a machine with the agent runtime. When disabled — or when
    the runtime raises ``AgentUnavailable`` — ingest uses the in-process fallback.
    """
    return os.getenv("LEADER_INGEST_ACTIVITY", "").strip() in {"1", "true", "True"}


def ingest(req: models.IngestRequest) -> models.IngestReport:
    """Ingest workflow orchestrator (spec 007 FR-7): run the activity, else fall back.

    Attempts the ``second-brain-ingest`` activity headless via ``activity_ingest`` (the
    bottom-up workflow); when the runtime is unavailable (or disabled) it falls back to a
    deterministic in-process ingest. Either way it returns an ``IngestReport`` carrying the
    activity Output Object (progress + errors) and never writes under ``vault/raw/`` (FR-8/FR-2).
    """
    name, workspace = _resolve_scaffolded(req.workspace)
    if _activity_enabled():
        try:
            return _ingest_via_activity(name, workspace, req)
        except AgentUnavailable:
            pass  # runtime absent → deterministic fallback (FR-7)
    return _ingest_inprocess(name, workspace, req)


def _ingest_via_activity(name: str, workspace: Path, req: models.IngestRequest) -> models.IngestReport:
    """Run the ingest activity through the interface and shape its Output Object (FR-6/FR-7)."""
    from . import activity_ingest

    inp = activity_ingest.build_input(name, workspace)
    output = asyncio.run(activity_ingest.run(inp))
    committed = _git_commit(workspace, f"ingest(activity): {req.title}")
    source_page = _latest_source_page(workspace)
    return models.IngestReport(
        workspace=name,
        source_page=source_page,
        portal_updated=True,
        committed=committed,
        message=f"Ingest activity completed for {name}.",
        progress=output.progress,
        errors=output.errors,
    )


def _latest_source_page(workspace: Path) -> str:
    """Most-recently-modified vault/wiki/sources page, relative to the workspace (or "")."""
    sources = workspace / "vault" / "wiki" / "sources"
    pages = list(sources.rglob("*.md")) if sources.is_dir() else []
    if not pages:
        return ""
    latest = max(pages, key=lambda p: p.stat().st_mtime)
    return latest.relative_to(workspace).as_posix()


def _ingest_inprocess(name: str, workspace: Path, req: models.IngestRequest) -> models.IngestReport:
    """Deterministic in-process ingest — the offline fallback (spec 007 FR-7/FR-8).

    Produces a vault/wiki/sources summary, updates the portal, appends the log, records the
    item in tbd.md, and commits. Returns a valid Output Object (progress + errors). Never
    writes under vault/raw/ (P2).
    """
    provenance = _slug(req.provenance)
    dest_dir = workspace / "vault" / "wiki" / "sources" / provenance
    dest_dir.mkdir(parents=True, exist_ok=True)
    page = dest_dir / f"{date.today().isoformat()}-{_slug(req.title)}.md"
    vault.guard_write_path(workspace, page)

    summary = req.content.strip().splitlines()
    preview = " ".join(summary[:5])[:400]
    page.write_text(
        "---\n"
        f"title: {req.title}\n"
        "category: source\n"
        f"provenance: {provenance}\n"
        f"created: {date.today().isoformat()}\n"
        "status: draft\n"
        "usage-count: 0\n"
        "referenced-to: []\n"
        "---\n\n"
        f"# {req.title}\n\n"
        f"> Source summary (provenance: {provenance}).\n\n"
        f"{req.content.strip()}\n",
        encoding="utf-8",
    )

    rel = page.relative_to(workspace).as_posix()
    _update_portal(workspace, rel, req.title, preview)
    vault.append_log(workspace, "ingest", req.title)
    _record_tbd_ingested(workspace, req.title, rel)
    committed = _git_commit(workspace, f"ingest: {req.title}")

    progress = [
        f"Wrote source summary {rel}",
        "Updated vault/wiki/portal.md",
        "Appended vault/wiki/log.md",
        "Checked off item in vault/wiki/tbd.md",
        "Committed" if committed else "Commit skipped (no repo)",
    ]
    return models.IngestReport(
        workspace=name,
        source_page=rel,
        portal_updated=True,
        committed=committed,
        message=f"Ingested '{req.title}' into {rel}",
        progress=progress,
        errors=[],
    )


def _record_tbd_ingested(workspace: Path, title: str, rel: str) -> None:
    """Check off a completed ingest in the tbd.md backlog under Sources (spec 007 FR-14/FR-15).

    Inserts a checked entry directly beneath the '## Sources' topic/theme heading so the
    backlog stays sectioned; appends the heading + entry if it is missing. tbd.md is a normal
    wiki artifact (committed with the run) and never lives under vault/raw/.
    """
    tbd = workspace / "vault" / "wiki" / "tbd.md"
    vault.guard_write_path(workspace, tbd)
    entry = f"- [x] {date.today().isoformat()} ingested '{title}' → {rel}\n"
    text = tbd.read_text(encoding="utf-8") if tbd.exists() else ""
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.startswith("## Sources"):
            lines.insert(i + 1, entry)
            tbd.write_text("".join(lines), encoding="utf-8")
            return
    tbd.write_text(text.rstrip() + "\n\n## Sources (capture → ingest)\n" + entry, encoding="utf-8")


def _update_portal(workspace: Path, rel: str, title: str, preview: str) -> None:
    portal = workspace / "vault" / "wiki" / "portal.md"
    vault.guard_write_path(workspace, portal)
    stem = Path(rel).stem
    line = f"- [[{rel}|{title}]] — {preview[:100]}\n"
    existing = portal.read_text(encoding="utf-8") if portal.exists() else "# Portal\n\n"
    if stem not in existing:
        portal.write_text(existing.rstrip() + "\n" + line, encoding="utf-8")


def query(req: models.QueryRequest) -> models.Answer:
    """Naive cited search over wiki pages (portal index model, no vector DB)."""
    name, workspace = _resolve_scaffolded(req.workspace)
    terms = [t for t in re.split(r"\W+", req.question.lower()) if len(t) > 2]
    citations: list[models.Citation] = []
    for page in _wiki_pages(workspace):
        text = page.read_text(encoding="utf-8", errors="ignore")
        low = text.lower()
        score = sum(low.count(t) for t in terms)
        if score:
            excerpt = _first_match(text, terms)
            citations.append(
                models.Citation(page=page.relative_to(workspace).as_posix(), excerpt=excerpt)
            )
    citations.sort(key=lambda c: -len(c.excerpt))
    citations = citations[:5]
    if citations:
        answer = (
            f"Found {len(citations)} relevant page(s) for '{req.question}'. "
            "See citations for supporting excerpts."
        )
    else:
        answer = "No matching knowledge found in this workspace yet. Ingest sources first."
    return models.Answer(workspace=name, question=req.question, answer=answer, citations=citations)


def _first_match(text: str, terms: list[str]) -> str:
    for line in text.splitlines():
        low = line.lower()
        if any(t in low for t in terms) and line.strip() and not line.startswith("---"):
            return line.strip()[:200]
    return text.strip()[:200]


def plan(req: models.PlanRequest) -> models.Plan:
    """Plan the *actual* effect of a request (spec 009 FR-4/FR-5, Constitution P8).

    Effect-based, never lexical: the request is resolved to the executable capability it would
    run, and the plan names that capability, its target, its tier and its undo path. A request
    with no executable action yields a safe advisory plan requiring no approval, so the operator
    is never asked to authorize something this build cannot perform (FR-4).
    """
    name, _ = _resolve_scaffolded(req.workspace)
    action = _resolve_action(req.request)
    if action is None:
        return models.Plan(
            workspace=name,
            request=req.request,
            steps=[
                models.PlanStep(
                    order=1,
                    action="Answer from workspace knowledge, or advise how to proceed",
                    rationale="No executable action in this build — there is nothing to approve",
                )
            ],
            risk="safe",
            requires_approval=False,
            reversibility=_READ_ONLY.reversibility,
        )

    effect = EFFECTS[action.capability]
    gated = effect.tier == "approval"
    return models.Plan(
        workspace=name,
        request=req.request,
        steps=[
            models.PlanStep(
                order=1,
                action=f"Run `{action.capability}` on '{action.target}'",
                rationale=f"declared effect tier: {effect.tier}",
            ),
            models.PlanStep(
                order=2,
                action=f"Undo path — {effect.reversibility}",
                rationale="the operator must know how to revert before authorizing",
            ),
            models.PlanStep(
                order=3,
                action="Record it in vault/wiki/log.md and commit to the workspace git repo",
                rationale="every executed mutation stays auditable and revertible (P12)",
            ),
        ],
        risk="risky" if gated else "safe",
        requires_approval=gated,
        capability=action.capability,
        target=action.target,
        effect_tier=effect.tier,
        reversibility=effect.reversibility,
    )


def lint(selector: str | None = None) -> models.LintReport:
    """Basic hygiene checks: orphan pages and empty pages."""
    name, workspace = _resolve_scaffolded(selector)
    pages = _wiki_pages(workspace)
    linked: set[str] = set()
    for page in pages:
        for m in re.finditer(r"\[\[([^\]|#]+)", page.read_text(encoding="utf-8", errors="ignore")):
            linked.add(Path(m.group(1)).stem)
    findings: list[models.LintFinding] = []
    for page in pages:
        rel = page.relative_to(workspace).as_posix()
        body = page.read_text(encoding="utf-8", errors="ignore")
        if page.stem not in linked and "sources/" not in rel:
            findings.append(models.LintFinding(kind="orphan", page=rel, detail="No inbound [[wikilinks]]"))
        if len(body.strip().splitlines()) < 4:
            findings.append(models.LintFinding(kind="stale", page=rel, detail="Page has little content"))
    return models.LintReport(workspace=name, findings=findings, ok=not findings)


def spec_read(rel_path: str, selector: str | None = None) -> str:
    """Read a page's raw Markdown from the workspace."""
    _, workspace = _resolve_scaffolded(selector)
    target = (workspace / rel_path).resolve()
    if workspace.resolve() not in target.parents:
        raise WorkspaceError("path escapes workspace")
    if not target.is_file():
        raise WorkspaceError(f"no such page: {rel_path}")
    return target.read_text(encoding="utf-8", errors="ignore")


# --- skill capabilities (feature 005-skill-import) -------------------------


def _parse_skill_frontmatter(skill_md: Path) -> dict[str, str]:
    """Read simple `key: value` pairs from a SKILL.md YAML frontmatter block.

    Deliberately dependency-free: the SDK's SKILL.md frontmatter we consume here is a
    flat block of scalar keys (`name`, `description`), so a minimal parser suffices.
    """
    try:
        text = skill_md.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return {}
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    block = text[3:end] if end != -1 else ""
    out: dict[str, str] = {}
    for line in block.splitlines():
        if ":" in line and not line.lstrip().startswith("#"):
            key, _, value = line.partition(":")
            out[key.strip()] = value.strip().strip("\"'")
    return out


def list_available_skills(selector: str | None = None) -> models.SkillCatalog:
    """Catalog the shared skill library, marking which are installed (spec 005 FR-2)."""
    from . import config

    root = config.skills_library_root()
    workspace = vault.resolve_workspace(selector)
    installed = set(vault.list_installed_skill_names(workspace)) if vault.is_scaffolded(workspace) else set()
    skills: list[models.SkillSummary] = []
    if root.is_dir():
        for entry in sorted(root.iterdir(), key=lambda p: p.name.lower()):
            skill_md = entry / "SKILL.md"
            if not (entry.is_dir() and skill_md.is_file()):
                continue
            meta = _parse_skill_frontmatter(skill_md)
            skills.append(
                models.SkillSummary(
                    name=entry.name,
                    description=meta.get("description", ""),
                    installed=entry.name in installed,
                )
            )
    return models.SkillCatalog(source_root=str(root), skills=skills)


def list_installed_skills(selector: str | None = None) -> models.InstalledSkills:
    """List a workspace's installed skill names (spec 005 FR-3)."""
    name, workspace = _resolve_scaffolded(selector)
    return models.InstalledSkills(workspace=name, skills=vault.list_installed_skill_names(workspace))


def resolve_skill_source(name: str) -> Path:
    """Validate a skill name and return its library folder, or raise (spec 005 FR-6).

    Separate from ``import_skill`` so a caller can establish that the request is even *possible*
    before it is announced for approval: a malformed or unknown name is bad input, not a risky
    operation, and asking an operator to authorise an install that cannot happen is noise.
    """
    from . import config

    safe = _safe_name(name)
    if safe != name or not re.fullmatch(r"[A-Za-z0-9_-]+", safe):
        raise WorkspaceError(f"invalid skill name: {name!r}")
    source = config.skills_library_root() / safe
    if not (source / "SKILL.md").is_file():
        raise WorkspaceError(f"no such skill in library: {safe}")
    return source


def import_skill(selector: str | None, name: str) -> models.ImportSkillReport:
    """Reference-link a shared skill into the workspace, then commit (spec 005 FR-5/6/7)."""
    source = resolve_skill_source(name)
    safe = source.name

    ws_name, workspace = _resolve_scaffolded(selector)
    link = vault.install_skill_link(workspace, safe, source)
    committed = _git_commit(workspace, f"chore(skills): import {safe}")
    return models.ImportSkillReport(
        workspace=ws_name,
        name=safe,
        link_path=link.relative_to(workspace).as_posix(),
        committed=committed,
        message=f"Imported skill '{safe}' as a reference-link into {ws_name}.",
    )


# --- model selection (feature 004-assistant-sidebar, FR-26..FR-28) ---------


def _provider_models() -> list[models.ModelChoice]:
    """Fetch the model list from Anthropic (spec 004 FR-27).

    Only attempted when an API key is present; wrapped so any network/parse failure
    surfaces as an empty list, letting ``available_models`` fall back to the static list.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return []
    import httpx  # local import: keeps the offline path free of any network dependency

    resp = httpx.get(
        "https://api.anthropic.com/v1/models",
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
        timeout=5.0,
    )
    resp.raise_for_status()
    out: list[models.ModelChoice] = []
    for m in resp.json().get("data", []):
        mid = m.get("id")
        if mid:
            out.append(models.ModelChoice(id=mid, label=m.get("display_name") or mid))
    return out


def available_models() -> models.AvailableModels:
    """The model picker payload: list + active choice + its source (spec 004 FR-27).

    Hybrid: the provider list when reachable/credentialed, else the curated static
    fallback. The active model is always guaranteed to appear in the returned list.
    """
    try:
        choices = _provider_models()
        source = "provider" if choices else "static"
    except Exception:  # any provider failure → offline fallback (FR-27)
        choices, source = [], "static"
    if not choices:
        choices = [models.ModelChoice(id=i, label=label) for i, label in config.STATIC_MODELS]
    current = config.agent_model()
    if current not in {c.id for c in choices}:
        choices = [models.ModelChoice(id=current, label=current), *choices]
    return models.AvailableModels(models=choices, current=current, source=source)


def set_active_model(model: str) -> models.AvailableModels:
    """Persist a process-wide model selection and return the refreshed picker (FR-28)."""
    try:
        config.set_agent_model(model)
    except ValueError as e:
        raise WorkspaceError(str(e))
    return available_models()


# --- operator settings (feature 009-approval-optimization, FR-8) -----------


def get_settings() -> models.Settings:
    """Read the persisted operator settings (spec 009 FR-8)."""
    return models.Settings(auto_approve=config.auto_approve(), agent_model=config.agent_model())


def update_settings(auto_approve: bool | None = None) -> models.Settings:
    """Persist operator settings and return the new state (spec 009 FR-8).

    Trust mode is **operator-only** (FR-11): this capability is deliberately not exposed as an
    agent tool, so the agent can neither grant nor read-to-bypass its own standing consent.
    """
    if auto_approve is not None:
        config.set_auto_approve(auto_approve)
    return get_settings()


# --- sidebar capabilities (feature 004-assistant-sidebar) ------------------


def wiki_tree(selector: str | None = None) -> models.WikiTree:
    """Return the workspace's `vault/wiki/` subtree for the navigation-only browser (FR-8/FR-15).

    Scoped strictly to `vault/wiki/`; hidden entries are omitted. Nothing under `vault/raw/`,
    `sessions/`, `vault/output/`, or `.git/` is ever revealed (FR-10).
    """
    name, workspace = _resolve_scaffolded(selector)
    wiki = workspace / "vault" / "wiki"
    wiki_root = wiki.resolve()

    def within_wiki(p: Path) -> bool:
        # spec 004 FR-10: a symlink must not let the browser escape vault/wiki/ (into
        # vault/raw/, sessions/, vault/output/, or anywhere outside the workspace).
        try:
            real = p.resolve()
        except OSError:
            return False
        return real == wiki_root or wiki_root in real.parents

    def build(d: Path) -> list[models.WikiNode]:
        # Returns the folder's displayable children, or [] when nothing remains — which signals
        # the caller to prune this (empty) folder (spec 004 FR-10a). README.md is excluded from
        # the listing entirely (a placeholder, never displayed), so a folder left with no files
        # after that exclusion is treated as empty and dropped.
        nodes: list[models.WikiNode] = []
        for child in sorted(d.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
            if child.name.startswith("."):
                continue
            if child.is_symlink() and not within_wiki(child):
                continue  # FR-10: reject symlinks resolving outside vault/wiki/
            if child.is_file() and child.name.lower() == "readme.md":
                continue  # FR-10a: README.md is never listed
            rel = child.relative_to(wiki).as_posix()
            if child.is_dir():
                children = build(child)
                if not children:
                    continue  # empty subtree (or README-only) → pruned
                nodes.append(
                    models.WikiNode(name=child.name, path=rel, type="dir", children=children)
                )
            else:
                nodes.append(models.WikiNode(name=child.name, path=rel, type="file"))
        return nodes

    return models.WikiTree(workspace=name, root="vault/wiki", nodes=build(wiki) if wiki.is_dir() else [])


def _safe_name(filename: str | None) -> str:
    """Strip any directory components from an uploaded filename (path-traversal guard)."""
    return Path(filename or "upload").name or "upload"


def capture(workspace: Path, provenance: str, filename: str, data: bytes) -> Path:
    """Capture a source into `vault/raw/<provenance>/` — input only, no processing (spec 007 FR-1).

    This is the **only sanctioned human channel** into `vault/raw/` (Constitution P2, FR-2): it
    deliberately does NOT go through `guard_write_path` (which forbids the *ingest workflow* and
    the agent from touching vault/raw/). It deposits the source and does **no** knowledge
    processing — no summary, no wiki write, no portal/log mutation, and it never auto-runs ingest
    (FR-3). It still validates that the resolved destination stays inside `vault/raw/`.
    """
    raw_dir = workspace / "vault" / "raw" / provenance
    raw_dir.mkdir(parents=True, exist_ok=True)
    dest = raw_dir / filename
    raw_root = (workspace / "vault" / "raw").resolve()
    if raw_root not in dest.resolve().parents:
        raise WorkspaceError("upload path escapes vault/raw/")
    dest.write_bytes(data)
    return dest


def upload_and_ingest(
    selector: str | None,
    files: list[tuple[str, bytes]],
    provenance: str = "notes",
) -> models.UploadReport:
    """Capture uploaded originals into `vault/raw/` then ingest text ones (FR-12/FR-16).

    This is an explicit two-step *compose* of the two independent primitives (spec 007 FR-3):
    it first **captures** each file (input only, no processing) and then invokes the separate
    **ingest** workflow on text-decodable ones (producing a `vault/wiki/sources` summary +
    portal/log update). Capture itself never auto-ingests; the chaining here is the caller's
    choice. Binary files are captured under `vault/raw/` only, with a note. Ingest never touches
    vault/raw/.
    """
    name, workspace = _resolve_scaffolded(selector)
    prov = _slug(provenance)
    results: list[models.UploadedFile] = []
    for filename, data in files:
        safe = _safe_name(filename)
        raw_path = capture(workspace, prov, safe, data)
        rel_raw = raw_path.relative_to(workspace).as_posix()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            results.append(
                models.UploadedFile(
                    filename=safe, raw_path=rel_raw, source_page=None, ingested=False,
                    error="binary file stored in vault/raw/, not ingested",
                )
            )
            continue
        report = ingest(
            models.IngestRequest(workspace=name, title=Path(safe).stem, content=text, provenance=prov)
        )
        results.append(
            models.UploadedFile(
                filename=safe, raw_path=rel_raw, source_page=report.source_page, ingested=True,
            )
        )
    committed = _git_commit(workspace, f"upload: {len(files)} file(s) into vault/raw/{prov}")
    return models.UploadReport(workspace=name, files=results, count=len(results), committed=committed)


def _derive_conversation_title(conv) -> str:
    """The conversation's name — the shared label for Sessions list + chat header (spec 004 FR-33).

    Prefers the name the assistant gave the record (spec 012 FR-10); the first user line remains the
    fallback for a pre-012 file that carries no name heading.
    """
    if conv.name:
        return conv.name
    first_user = next((t.text for t in conv.turns if t.role == "user"), "").strip()
    return first_user.splitlines()[0][:60] if first_user else "New conversation"


def list_conversations(selector: str | None = None) -> models.ConversationList:
    """List prior conversations for the Sessions panel, newest first (FR-17/FR-19)."""
    from . import conversation as convo

    name, workspace = _resolve_scaffolded(selector)
    sessions = workspace / "sessions"
    summaries: list[models.ConversationSummary] = []
    if sessions.is_dir():
        files = sorted(sessions.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        for p in files:
            # Parse the file we found rather than re-resolving its id (spec 012 FR-9): the filename
            # no longer *is* the id, and a stray .md here must be skipped, not crash the listing.
            conv = convo.load_path(workspace, p)
            if conv is None:
                continue
            title = _derive_conversation_title(conv)
            summaries.append(
                models.ConversationSummary(
                    conversation_id=conv.conversation_id,
                    created=conv.created,
                    title=title,
                    turn_count=sum(1 for t in conv.turns if t.role == "user"),
                )
            )
    return models.ConversationList(workspace=name, conversations=summaries)


def get_conversation(selector: str | None, conversation_id: str) -> models.ConversationDetail:
    """Return one conversation's full turns so the UI can repopulate the chat (FR-20)."""
    from . import conversation as convo

    name, workspace = _resolve_scaffolded(selector)
    conv = convo.load(workspace, conversation_id)
    if conv is None:
        raise WorkspaceError(f"no such conversation: {conversation_id}")
    messages = [
        models.ConversationMessage(role=t.role, text=t.text, timestamp=t.timestamp)
        for t in conv.turns
    ]
    return models.ConversationDetail(
        workspace=name,
        conversation_id=conv.conversation_id,
        created=conv.created,
        title=_derive_conversation_title(conv),
        messages=messages,
    )


# --- chat orchestration (feature 002; the parity boundary for chat) --------

# spec 002 FR-14: server-local, transient registry of conversations with an in-flight turn.
# A counter (not a set) tolerates concurrent turns on the same id; entries are cleared in
# ask_stream's finally, so an error or client disconnect can never leak a stuck "running"
# state. This is deliberately NOT persisted to sessions/ (durable truth stays on disk, P1).
_running_turns: dict[str, int] = {}


def _mark_running(conversation_id: str) -> None:
    _running_turns[conversation_id] = _running_turns.get(conversation_id, 0) + 1


def _unmark_running(conversation_id: str) -> None:
    remaining = _running_turns.get(conversation_id, 0) - 1
    if remaining > 0:
        _running_turns[conversation_id] = remaining
    else:
        _running_turns.pop(conversation_id, None)


def is_running(conversation_id: str) -> bool:
    """True while a chat turn for this conversation is being processed (spec 002 FR-14)."""
    return _running_turns.get(conversation_id, 0) > 0


def conversation_status(selector: str | None, conversation_id: str) -> models.ChatStatus:
    """Report whether a conversation has an in-flight turn, without sending one (FR-14).

    Read-only: it never appends a turn or mutates the record. `exists` reflects the durable
    `sessions/` record; `running` reflects the transient server-local registry.
    """
    from . import conversation as convo

    name, workspace = _resolve_scaffolded(selector)
    exists = convo.load(workspace, conversation_id) is not None
    return models.ChatStatus(
        workspace=name,
        conversation_id=conversation_id,
        running=is_running(conversation_id),
        exists=exists,
    )


def resolve_for_chat(selector: str | None) -> tuple[str, Path]:
    """Resolve a workspace for a conversation (FR-10, D1).

    Default workspace is scaffolded on demand; a *named* selector that does not
    exist is reported, never silently created. Workspace creation happens only via
    the explicit `create_workspace` capability through the approval flow.
    """
    workspace = vault.resolve_workspace(selector)
    if selector is None:
        if not vault.is_scaffolded(workspace):
            vault.scaffold_workspace(workspace)
        return workspace.name, workspace
    if not vault.is_scaffolded(workspace):
        raise WorkspaceError(f"workspace '{selector}' does not exist; create it explicitly first")
    return workspace.name, workspace


async def _execute_pending(selector: str | None, pending: dict) -> tuple[str, bool]:
    """Execute an approved plan's exact stored action (spec 009 FR-13, re-announced per 011 FR-4).

    The plan's own `capability`/`target` are authoritative: they are what the operator was shown and
    consented to. Re-deriving them from the request text is only a fallback for a record written
    before those fields existed; a record naming nothing executable is cleared rather than left
    pending forever.
    """
    plan_data = pending.get("plan") or {}
    capability, target = plan_data.get("capability", ""), plan_data.get("target", "")
    action = (
        ResolvedAction(capability=capability, target=target)
        if capability in EFFECTS and EFFECTS[capability].executable and target
        else _resolve_action(pending.get("request", ""))
    )
    if action is None:
        return (
            "That request needs no action from me — I've cleared the stale approval. "
            "Ask me again and I'll answer directly.",
            True,
        )
    reply, ran = await _announce_and_run(selector, action, detail=pending.get("request", ""))
    return (f"Approved. {reply}" if ran else reply, ran)


def _record_turn_effects(workspace: Path, message: str) -> None:
    """Log + commit whatever a turn changed under `vault/` (spec 009 FR-6).

    A turn's skills may write `vault/wiki/` pages — a `reversible` effect, which is only safe to
    run unprompted because it is recoverable. That guarantee is what this enforces: the turn
    leaves a log entry and a git commit behind, so the operator can review and revert. A turn
    that changed nothing under `vault/` records nothing.
    """
    if not _vault_is_dirty(workspace):
        return
    label = (message.strip().splitlines() or ["(turn)"])[0][:120]
    vault.append_log(workspace, "chat", label)
    _git_commit(workspace, f"chat: {label[:60]}")


def _fallback_answer(selector: str | None, message: str) -> tuple[str, list[models.Citation]]:
    """Deterministic, cited answer when the agent runtime is unavailable (FR-2)."""
    ans = query(models.QueryRequest(workspace=selector, question=message))
    return ans.answer, ans.citations


async def ask_stream(
    workspace: str | None = None,  # noqa: A002 — matches request field name (shadows module locally)
    message: str = "",
    conversation_id: str | None = None,
    approve: bool = False,
    auto_approve: bool | None = None,
) -> AsyncIterator[models.ChatDelta]:
    """Stream a chat turn (FR-1..FR-6, FR-13), marking it running for status probes (FR-14).

    Resolves the conversation id first (a new conversation gets a fresh id), marks it
    running for the duration of the turn, and clears it in ``finally`` so that a normal
    completion, an error, or a client disconnect all leave the conversation not-running.
    """
    from . import conversation

    # Resolve/create up front so we have a stable id to track; pass it through to the impl
    # (as a concrete id, never None) so it loads this same record instead of creating another.
    _name, wpath = resolve_for_chat(workspace)
    cid = conversation.load_or_new(wpath, conversation_id).conversation_id
    _mark_running(cid)
    try:
        async for delta_out in _ask_stream_impl(workspace, message, cid, approve, auto_approve):
            yield delta_out
    finally:
        _unmark_running(cid)


async def _ask_stream_impl(
    workspace: str | None = None,  # noqa: A002
    message: str = "",
    conversation_id: str | None = None,
    approve: bool = False,
    auto_approve: bool | None = None,
) -> AsyncIterator[models.ChatDelta]:
    """Core chat-turn generator (FR-1..FR-6, FR-13); see ask_stream for running-status tracking."""
    from . import agent, conversation, persona

    selector = workspace
    name, wpath = resolve_for_chat(selector)
    conv = conversation.load_or_new(wpath, conversation_id)
    cid = conv.conversation_id
    # Name the record *before* anything can write it (spec 012 FR-5). Every branch below — approval,
    # a resolved action, a pause raised mid-stream — can be the first durable write, so the fallback
    # has to be in place already; the agent's better title replaces it after the stream, before the
    # turn is appended. A no-op on an existing record (FR-6).
    conversation.set_name(conv, conversation.fallback_name(message))

    def delta(reply: str, *, done: bool, citations=None, pending=None, executed=False, interaction=None) -> models.ChatDelta:
        return models.ChatDelta(
            workspace=name, conversation_id=cid, reply=reply, done=done,
            citations=citations or [], pending_plan=pending, executed=executed, interaction=interaction,
        )

    # --- approval turn (D2) ---
    if approve:
        if conv.pending_plan:
            reply, executed = await _execute_pending(selector, conv.pending_plan)
            pending_model = models.Plan(**conv.pending_plan["plan"]) if not executed else None
            if executed:
                conversation.clear_pending_plan(conv)
                conversation.clear_pending_interaction(conv)  # drop the shadow approval interaction (FR-17)
            conversation.append_turn(conv, message or "(approve)", reply)
            yield delta(reply, done=True, pending=pending_model, executed=executed)
        else:
            reply = "There is no pending plan to approve in this conversation."
            conversation.append_turn(conv, message or "(approve)", reply)
            yield delta(reply, done=True)
        return

    # A plan stored by an older build can name an action this build cannot execute. FR-4 stops new
    # ones being created; drop a stale one on the next turn so its card cannot re-present forever.
    if conv.pending_plan and _resolve_action(conv.pending_plan.get("request", "")) is None:
        conversation.clear_pending_plan(conv)
        conversation.clear_pending_interaction(conv)

    # --- announce, then act (spec 011 FR-2/FR-3) ---
    # A dispatched capability is announced before it runs and the permit is honoured. No tier check,
    # no trust check, no plan built here: whether an `approval`-tier effect may proceed is decided
    # behind the gate, against the whole run, by parties this module cannot see. A denial ends the
    # turn quietly — the concierge replaces this delta with the accumulated report and the card.
    action = _resolve_action(message)
    if action is not None:
        reply, ran = await _announce_and_run(selector, action, detail=message)
        conversation.append_turn(conv, message, reply)
        yield delta(reply, done=True, executed=ran)
        return

    # --- no executable action → a normal answer, never a plan (FR-4) ---
    system_prompt = persona.build_system_prompt()
    citations: list[models.Citation] = []
    raised: list[models.Interaction] = []  # cards the agent raises on its own (spec 008 FR-18)
    # Seeded with the fallback, appended to by the agent's `name_conversation` (spec 012 FR-4/FR-5):
    # the last entry is always the best name known, which is what a card raised mid-stream reads to
    # name the record it materializes.
    naming: list[tuple[str, list[str]]] = [(conversation.fallback_name(message), [])]
    final_reply, final_sid, agent_ok = "", conv.sdk_session_id, True
    try:
        async for reply, sid in agent.run_stream(
            system_prompt, message, selector, wpath, conv.sdk_session_id, citations,
            conv.conversation_id, raised, _trust_mode(auto_approve), naming,
        ):
            final_reply, final_sid = reply, sid
            yield delta(reply, done=False)
    except agent.AgentUnavailable:
        agent_ok = False

    # Before any write below (spec 012 FR-4/FR-6): `set_sdk_session_id` and `append_turn` both
    # materialize, and the name is fixed by whichever lands first. Last proposal wins; a no-op if a
    # card raised mid-stream already created the record.
    conversation.set_name(conv, naming[-1][0], naming[-1][1])

    if agent_ok:
        conversation.set_sdk_session_id(conv, final_sid)
    else:
        final_reply, citations = _fallback_answer(selector, message)

    itx = _card_to_surface(raised)
    conversation.append_turn(conv, message, final_reply)
    _record_turn_effects(wpath, message)  # reversible writes stay logged + revertible (spec 009 FR-6)
    yield delta(final_reply, done=True, citations=citations, interaction=itx)


def _card_to_surface(raised: list[models.Interaction]) -> models.Interaction | None:
    """Pick the one card a turn reports on ``ChatDelta.interaction`` (spec 008 FR-18, 010 FR-5).

    A still-pending blocking card wins — it is a question the user must answer. Otherwise an
    auto-approved approval is surfaced as already-decided context, ahead of a mere notification.
    """
    return (
        next((i for i in raised if i.status == "pending" and i.kind in ("approval", "clarification")), None)
        or next((i for i in raised if i.kind == "approval"), None)
        or (raised[0] if raised else None)
    )


async def ask(
    workspace: str | None = None,  # noqa: A002
    message: str = "",
    conversation_id: str | None = None,
    approve: bool = False,
    auto_approve: bool | None = None,
) -> models.ChatAnswer:
    """Non-streaming chat turn — drives ask_stream to completion (FR-1)."""
    last: models.ChatDelta | None = None
    async for d in ask_stream(workspace, message, conversation_id, approve, auto_approve):
        last = d
    assert last is not None
    return _answer_from_delta(last)


def _answer_from_delta(d: models.ChatDelta) -> models.ChatAnswer:
    return models.ChatAnswer(
        workspace=d.workspace,
        conversation_id=d.conversation_id,
        reply=d.reply,
        citations=d.citations,
        pending_plan=d.pending_plan,
        executed=d.executed,
        interaction=d.interaction,
    )


# --- agent<->user interaction channel (feature 008-agent-user-interaction) ---
#
# A blocking interaction (approval/clarification) is emitted at a turn boundary — the
# durable `pending-interaction` record in the conversation is the source of truth (P1,
# FR-11), streamed to the frontend as ChatDelta.interaction (FR-1) and answered via
# `respond_to_interaction*`. Approval is the 1-proposal degenerate case of clarification
# (D1); the plan-first approval flow (FR-5) is delivered as an approval interaction (FR-17).

INTERACTION_TIMEOUT_MSG = "Something goes wrong, please retry later."  # spec 008 D6

# Option-count bounds per kind (spec 008 FR-6): notification=0, approval=1, clarification=2–4.
_KIND_BOUNDS = {"notification": (0, 0), "approval": (1, 1), "clarification": (2, 4)}


def _new_interaction_id() -> str:
    return "itx-" + uuid.uuid4().hex[:12]


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _is_expired(record: dict) -> bool:
    """Whether a pending-interaction record's countdown has elapsed (spec 008 FR-9)."""
    try:
        created = datetime.fromisoformat(record["created"])
    except (KeyError, ValueError, TypeError):
        return False
    return datetime.now() > created + timedelta(seconds=int(record.get("timeout_seconds", 30)))


def _norm_option(i: int, opt) -> models.InteractionOption:
    """Coerce a caller-supplied option (str | dict | model) into an InteractionOption."""
    if isinstance(opt, models.InteractionOption):
        return opt
    if isinstance(opt, str):
        return models.InteractionOption(id=f"opt-{i + 1}", label=opt)
    if isinstance(opt, dict):
        return models.InteractionOption(
            id=opt.get("id") or f"opt-{i + 1}",
            label=opt.get("label", f"Option {i + 1}"),
            detail=opt.get("detail", ""),
        )
    raise WorkspaceError(f"invalid interaction option: {opt!r}")


def _describe_interaction(itx: models.Interaction) -> str:
    lines = [f"[{itx.kind}] {itx.prompt}"]
    for o in itx.options:
        lines.append(f"- ({o.id}) {o.label}" + (f" — {o.detail}" if o.detail else ""))
    return "\n".join(lines)


def _interaction_context(itx: models.Interaction) -> str:
    """A message that scopes a 'chat about it' discussion to the pending decision (FR-7)."""
    lines = [f"The user wants to discuss a pending {itx.kind}: {itx.prompt}"]
    if itx.options:
        lines.append("The options on the table are:")
        for o in itx.options:
            lines.append(f"- {o.label}" + (f" — {o.detail}" if o.detail else ""))
    lines.append("Discuss this specific decision with the user; do not take any action or resolve it yet.")
    return "\n".join(lines)


def _resume_context(itx: models.Interaction, chosen: models.InteractionOption) -> str:
    """Prompt that resumes the paused work with the user's answer in hand (spec 010 FR-7)."""
    verb = "granted approval for" if itx.kind == "approval" else "chose how to proceed with"
    lines = [
        f"The user has {verb} the pending {itx.kind}: {itx.prompt}",
        f"Their answer: {chosen.label}" + (f" — {chosen.detail}" if chosen.detail else ""),
        "This is their decision. Carry out that work now, in this turn, and report what you did.",
        "Do not ask again and do not re-raise a card for the same thing.",
    ]
    return "\n".join(lines)


def _interaction_from_record(record: dict) -> models.Interaction:
    fields = models.Interaction.model_fields
    return models.Interaction(**{k: record[k] for k in fields if k in record})


def create_interaction(
    selector: str | None,
    conversation_id: str | None,
    kind: str,
    prompt: str,
    options: list | None = None,
    timeout: int | None = None,
    *,
    name_hint: str = "",
    _extra: dict | None = None,
) -> models.Interaction:
    """Raise a mid-task interaction request, persisting blocking ones durably (spec 008 FR-1/2/6/13/15).

    Validates the kind and the option-count bounds (FR-6); enforces at most one outstanding
    blocking interaction per conversation (FR-15); captures the request into the sessions record
    (FR-13). Notifications are non-blocking and not persisted (FR-3); approval/clarification are
    persisted as the durable `pending-interaction` (FR-11).

    A blocking card is durable state, so raising one **materializes** the session record — possibly
    before the turn's first ``append_turn``. ``name_hint`` is the best name the caller knows at that
    instant, so the record that appears is named rather than anonymous (spec 012 FR-5); it is ignored
    once the file exists (FR-6).

    ``_extra`` is merged into the persisted record but never into the wire model: the caller parks
    whatever it needs to honour the answer later — a `plan` to execute (FR-17), or spec 011's
    `granted_key` / `risk` / `fingerprint` resume payload (011 FR-26). It stays off ``Interaction``
    because the card is sent to the client, and the key that unlocks a gated operation is not the
    client's to hold.
    """
    from . import config
    from . import conversation as convo

    if kind not in _KIND_BOUNDS:
        raise WorkspaceError(f"unknown interaction kind: {kind!r}")
    lo, hi = _KIND_BOUNDS[kind]
    opts = [_norm_option(i, o) for i, o in enumerate(options or [])]
    if not (lo <= len(opts) <= hi):
        raise WorkspaceError(f"{kind} requires {lo}..{hi} options, got {len(opts)}")

    name, workspace = resolve_for_chat(selector)
    conv = convo.load_or_new(workspace, conversation_id)
    convo.set_name(conv, name_hint)

    blocking = kind in ("approval", "clarification")
    if blocking and conv.pending_interaction:
        prev = conv.pending_interaction
        if prev.get("status") == "pending" and not _is_expired(prev):
            raise WorkspaceError("a blocking interaction is already pending for this conversation (FR-15)")

    timeout_s = int(timeout) if timeout and int(timeout) > 0 else config.interaction_timeout_seconds()
    itx = models.Interaction(
        interaction_id=_new_interaction_id(),
        conversation_id=conv.conversation_id,
        kind=kind,
        prompt=prompt,
        options=opts,
        timeout_seconds=timeout_s,
        created=_now_iso(),
        status="pending",
    )
    convo.append_event(conv, "interaction", _describe_interaction(itx))
    if blocking:
        record = itx.model_dump()
        record.update(_extra or {})
        convo.set_pending_interaction(conv, record)
    return itx


def request_approval(
    selector: str | None,
    conversation_id: str | None,
    prompt: str,
    detail: str = "",
    *,
    trust: bool = False,
    name_hint: str = "",
) -> tuple[models.Interaction, bool]:
    """Ask for consent on the agent's behalf; the *outcome* is decided here (spec 010 FR-1/FR-2).

    Returns ``(interaction, granted)``. The agent may reach this to **request** approval, never to
    grant one — hence ``trust`` is supplied by the capability layer from the operator's per-request
    or persisted setting, never from tool arguments (FR-2, spec 009 FR-11).

    - ``trust`` off → a real blocking approval card, durable and answerable (FR-3).
    - ``trust`` on  → resolved as approved **on the operator's behalf immediately**, so the caller
      continues into final execution in the same turn (FR-4). It is surfaced as already-decided
      context, not stored as a pending interaction (FR-5), and appended to `log.md` as well as the
      session record, because standing consent replaces the prompt and never the audit trail
      (FR-6, P8 v1.2.0 / P12).
    """
    from . import config
    from . import conversation as convo

    if not trust:
        itx = create_interaction(
            selector, conversation_id, "approval", prompt,
            [{"id": "approve", "label": "Approve and continue", "detail": detail or prompt}],
            name_hint=name_hint,
        )
        return itx, False

    _name, workspace = resolve_for_chat(selector)
    conv = convo.load_or_new(workspace, conversation_id)
    convo.set_name(conv, name_hint)  # the auto-grant is appended, which materializes (spec 012 FR-5)
    itx = models.Interaction(
        interaction_id=_new_interaction_id(),
        conversation_id=conv.conversation_id,
        kind="approval",
        prompt=prompt,
        options=[],  # already decided: nothing to select (FR-5)
        timeout_seconds=config.interaction_timeout_seconds(),
        created=_now_iso(),
        status="resolved",
        resolution="auto-approved",
    )
    convo.append_event(conv, "interaction", f"[auto-approved] {itx.interaction_id} — {prompt}")
    # The turn's own _record_turn_effects commits this write, keeping the grant revertible (FR-6).
    vault.append_log(workspace, "auto-approved", prompt)
    return itx, True


def get_pending_interaction(selector: str | None, conversation_id: str) -> models.Interaction | None:
    """Return a conversation's still-pending interaction so a reloaded client can re-render it (FR-11).

    Read of the durable record (P1). If the countdown has elapsed, the interaction auto-resolves to
    its safe default (timeout, no action), is cleared, and is returned with status='expired' so the
    UI can surface the timeout (FR-9). Returns None when nothing is pending.
    """
    from . import conversation as convo

    _, workspace = _resolve_scaffolded(selector)
    conv = convo.load(workspace, conversation_id)
    if conv is None or not conv.pending_interaction:
        return None
    record = conv.pending_interaction
    itx = _interaction_from_record(record)
    if _is_expired(record):
        itx.status, itx.resolution = "expired", "timeout"
        convo.append_event(conv, "interaction", f"[timeout] {itx.interaction_id} expired — no action taken")
        convo.clear_pending_interaction(conv)
    return itx


async def respond_to_interaction_stream(
    selector: str | None,
    conversation_id: str,
    interaction_id: str,
    choice: str,
) -> AsyncIterator[models.ChatDelta]:
    """Answer a pending interaction and resume the task (spec 008 FR-7/FR-14/FR-16).

    Idempotent and id-scoped (FR-16): an unknown, already-resolved, superseded, or expired id is
    rejected with **no side effects**. `choice`:
      - ``"chat"``   → open a discussion scoped to the interaction WITHOUT resolving it, then
                        re-present the decision as a NEW interaction id (supersedes the old, D8/D9);
      - ``"decline"``→ refuse; no consequential action runs (FR-14);
      - an option id → authorize/select that proposal; a plan-wrapping approval executes it (FR-17).
    """
    from . import conversation as convo

    name, wpath = resolve_for_chat(selector)
    conv = convo.load_or_new(wpath, conversation_id)
    cid = conv.conversation_id

    def delta(reply, *, done, citations=None, pending=None, executed=False, interaction=None):
        return models.ChatDelta(
            workspace=name, conversation_id=cid, reply=reply, done=done,
            citations=citations or [], pending_plan=pending, executed=executed, interaction=interaction,
        )

    record = conv.pending_interaction
    # FR-16: reject unknown / mismatched / already-resolved / superseded ids with no side effects.
    if not record or record.get("interaction_id") != interaction_id or record.get("status") != "pending":
        yield delta("That request is no longer awaiting a response.", done=True)
        return
    # FR-9: an elapsed countdown aborts with the fixed message and takes no action.
    if _is_expired(record):
        convo.append_event(conv, "interaction", f"[timeout] {interaction_id} expired — no action taken")
        convo.clear_pending_interaction(conv)
        yield delta(INTERACTION_TIMEOUT_MSG, done=True)
        return

    itx = _interaction_from_record(record)

    # --- "chat about it" (FR-7): discuss in scope, never resolve; re-present a fresh interaction ---
    if choice == "chat":
        convo.append_event(conv, "interaction", f"[chat-about-it] discussing {interaction_id}")
        _mark_running(cid)
        try:
            reply, citations = await _routine_reply(name, selector, wpath, conv, _interaction_context(itx))
        finally:
            _unmark_running(cid)
        # Supersede the old id and re-present the same decision with a NEW id + fresh countdown (D8/D9).
        fresh = _represent_interaction(conv, itx)
        convo.append_turn(conv, "(chat about it)", reply)
        yield delta(reply, done=True, citations=citations, interaction=fresh)
        return

    # --- decline (FR-14): no consequential action ---
    if choice == "decline":
        _resolve_record(conv, record, "declined")
        if conv.pending_plan:
            convo.clear_pending_plan(conv)
        reply = "Declined — no action taken (human-in-the-loop, P8)."
        convo.append_turn(conv, "(declined)", reply)
        yield delta(reply, done=True)
        return

    chosen = next((o for o in itx.options if o.id == choice), None)
    if chosen is None:
        # Not a valid option → reject without side effects (the interaction stays pending).
        yield delta("That is not a valid option for this request.", done=True)
        return

    _resolve_record(conv, record, chosen.id)

    # --- approval wrapping a plan-first plan (FR-17) → execute it now ---
    if "plan" in record:
        reply, executed = await _execute_pending(
            selector, {"request": record.get("request", ""), "plan": record["plan"]}
        )
        if executed and conv.pending_plan:
            convo.clear_pending_plan(conv)
        pending_model = None if executed else models.Plan(**record["plan"])
        convo.append_turn(conv, f"(approved) {chosen.label}", reply)
        yield delta(reply, done=True, pending=pending_model, executed=executed)
        return

    # --- generic clarification/approval selection → resume the turn and finish the work ---
    # spec 010 FR-7: acknowledging the choice without continuing is a dead-end; the point of
    # answering is that the work the agent asked about actually happens.
    _mark_running(cid)
    try:
        reply, citations = await _routine_reply(name, selector, wpath, conv, _resume_context(itx, chosen))
    finally:
        _unmark_running(cid)
    convo.append_turn(conv, f"(selected) {chosen.label}", reply)
    yield delta(reply, done=True, citations=citations)


async def respond_to_interaction(
    selector: str | None,
    conversation_id: str,
    interaction_id: str,
    choice: str,
) -> models.ChatAnswer:
    """Non-streaming interaction response — drives the stream to completion (FR-12)."""
    last: models.ChatDelta | None = None
    async for d in respond_to_interaction_stream(selector, conversation_id, interaction_id, choice):
        last = d
    assert last is not None
    return _answer_from_delta(last)


def _resolve_record(conv, record: dict, resolution: str) -> None:
    """Mark a pending interaction resolved (audit) and clear it from the durable record (FR-13/FR-16)."""
    from . import conversation as convo

    record["status"] = "resolved"
    record["resolution"] = resolution
    convo.append_event(conv, "interaction", f"[resolved] {record.get('interaction_id')} → {resolution}")
    convo.clear_pending_interaction(conv)


def _represent_interaction(conv, itx: models.Interaction) -> models.Interaction:
    """Supersede a pending interaction and re-emit the same decision with a NEW id (spec 008 D8/D9)."""
    from . import config
    from . import conversation as convo

    fresh = models.Interaction(
        interaction_id=_new_interaction_id(),
        conversation_id=conv.conversation_id,
        kind=itx.kind,
        prompt=itx.prompt,
        options=itx.options,
        timeout_seconds=itx.timeout_seconds or config.interaction_timeout_seconds(),
        created=_now_iso(),  # fresh countdown after the discussion (D8)
        status="pending",
    )
    record = fresh.model_dump()
    # Carry the whole resume payload across: the `plan` that makes the approval executable (FR-17)
    # and spec 011's `granted_key` / `risk` / `fingerprint` (011 FR-26). Copying by "everything the
    # wire model does not own" means a future payload key survives re-presentation by default —
    # the alternative silently turns a discussed card into one that can no longer be honoured.
    previous = conv.pending_interaction or {}
    record.update({k: v for k, v in previous.items() if k not in record})
    convo.append_event(conv, "interaction", _describe_interaction(fresh))
    convo.set_pending_interaction(conv, record)
    return fresh


async def _routine_reply(name, selector, wpath, conv, message) -> tuple[str, list[models.Citation]]:
    """Run one routine (non-consequential) turn to completion, returning (reply, citations).

    Uses the agent runtime when available, else the deterministic cited fallback (FR-2). Shared by
    the 'chat about it' discussion path so it stays in parity with the normal chat turn.
    """
    from . import agent, conversation, persona

    system_prompt = persona.build_system_prompt()
    citations: list[models.Citation] = []
    final_reply, final_sid, agent_ok = "", conv.sdk_session_id, True
    try:
        async for reply, sid in agent.run_stream(
            system_prompt, message, selector, wpath, conv.sdk_session_id, citations
        ):
            final_reply, final_sid = reply, sid
    except agent.AgentUnavailable:
        agent_ok = False
    if agent_ok:
        conversation.set_sdk_session_id(conv, final_sid)
    else:
        final_reply, citations = _fallback_answer(selector, message)
    _record_turn_effects(wpath, message)  # spec 009 FR-6
    return final_reply, citations
