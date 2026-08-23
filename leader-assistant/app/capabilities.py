"""Surface-agnostic capability layer — the parity boundary (Constitution P9).

Both the REST surface (api.py) and any future chat surface call these
functions; neither talks to the filesystem directly. Requests that are
consequential return a plan for approval rather than executing (spec 13-api AC2).
"""

from __future__ import annotations

import asyncio
import os
import re
import subprocess
from datetime import date
from pathlib import Path
from typing import AsyncIterator

from . import models, vault
from .agent import AgentUnavailable
from .vault import WorkspaceError

# --- helpers ---------------------------------------------------------------

_CONSEQUENTIAL = re.compile(
    r"\b(delete|remove|drop|overwrite|rewrite|merge|deploy|push|migrate|rename|create)\b",
    re.IGNORECASE,
)

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


def _git_commit(workspace: Path, message: str) -> bool:
    """Commit workspace changes into the workspace's OWN repo; never an enclosing one.

    Refuses to run if `git -C <workspace>` resolves to a repo whose top-level is
    not the workspace itself (e.g. a parent project checkout).
    """
    try:
        top = subprocess.run(
            ["git", "-C", str(workspace), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True,
        )
        if top.returncode != 0:
            return False
        if Path(top.stdout.strip()).resolve() != workspace.resolve():
            return False  # would commit into an enclosing repo — refuse
        subprocess.run(["git", "-C", str(workspace), "add", "-A"], capture_output=True, text=True)
        done = subprocess.run(
            ["git", "-C", str(workspace), "commit", "-m", message],
            capture_output=True, text=True,
        )
        return done.returncode == 0
    except FileNotFoundError:
        return False


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
    """Plan-first for consequential work (Constitution P8, spec 13-api AC2)."""
    name, _ = _resolve_scaffolded(req.workspace)
    consequential = bool(_CONSEQUENTIAL.search(req.request))
    risk = "risky" if consequential else "safe"
    steps = [
        models.PlanStep(order=1, action="Clarify scope and affected pages", rationale="Avoid ambiguity before mutation"),
        models.PlanStep(order=2, action="Draft changes in the workspace's vault", rationale="Keep vault/raw/ immutable"),
        models.PlanStep(order=3, action="Evaluate risk and choose branch policy", rationale="Risky work → feature branch"),
        models.PlanStep(order=4, action="Commit with a typed message", rationale="Every mutation is a git commit"),
    ]
    return models.Plan(
        workspace=name,
        request=req.request,
        steps=steps,
        risk=risk,
        requires_approval=consequential,
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


def import_skill(selector: str | None, name: str) -> models.ImportSkillReport:
    """Reference-link a shared skill into the workspace, then commit (spec 005 FR-5/6/7)."""
    from . import config

    safe = _safe_name(name)
    if safe != name or not re.fullmatch(r"[A-Za-z0-9_-]+", safe):
        raise WorkspaceError(f"invalid skill name: {name!r}")
    source = config.skills_library_root() / safe
    if not (source / "SKILL.md").is_file():
        raise WorkspaceError(f"no such skill in library: {safe}")

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
        nodes: list[models.WikiNode] = []
        for child in sorted(d.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
            if child.name.startswith("."):
                continue
            if child.is_symlink() and not within_wiki(child):
                continue  # FR-10: reject symlinks resolving outside vault/wiki/
            rel = child.relative_to(wiki).as_posix()
            if child.is_dir():
                children = build(child)
                # spec 004 FR-10a: list only folders that contain data; a subtree with no
                # files is pruned so empty folders never appear in the browser.
                if not children:
                    continue
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


def list_conversations(selector: str | None = None) -> models.ConversationList:
    """List prior conversations for the Sessions panel, newest first (FR-17/FR-19)."""
    from . import conversation as convo

    name, workspace = _resolve_scaffolded(selector)
    sessions = workspace / "sessions"
    summaries: list[models.ConversationSummary] = []
    if sessions.is_dir():
        files = sorted(sessions.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        for p in files:
            conv = convo.load(workspace, p.stem)
            if conv is None:
                continue
            first_user = next((t.text for t in conv.turns if t.role == "user"), "").strip()
            title = first_user.splitlines()[0][:60] if first_user else "New conversation"
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
        workspace=name, conversation_id=conv.conversation_id, created=conv.created, messages=messages
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


def _resolve_for_chat(selector: str | None) -> tuple[str, Path]:
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


def _plan_for(request: str, selector: str | None) -> models.Plan:
    return plan(models.PlanRequest(workspace=selector, request=request))


def _consequential_reply(p: models.Plan) -> str:
    steps = "\n".join(f"{s.order}. {s.action} — {s.rationale}" for s in p.steps)
    return (
        f"This request is consequential (risk={p.risk}), so I won't act on it yet. "
        "Here is the plan I propose — reply approving it to proceed:\n\n"
        f"{steps}\n\n"
        "No changes have been made this turn (human-in-the-loop, P8)."
    )


def _execute_pending(name: str, selector: str | None, pending: dict) -> tuple[str, bool]:
    """Execute an approved pending plan via the capability layer (FR-5, D2).

    MVP supports explicit workspace creation deterministically; other action types
    are reported as not-yet-automatable and the plan is kept pending.
    """
    request = pending.get("request", "")
    m = _CREATE_WORKSPACE.search(request)
    if m:
        workspace_name = m.group(1)
        info = create_workspace(workspace_name)
        return (f"Approved. Created workspace '{info.name}' at {info.path}.", True)
    skill = _import_skill_name(request)
    if skill:
        report = import_skill(selector, skill)
        return (f"Approved. {report.message}", True)
    return (
        "Approved, but this action type isn't automatable yet in this build; "
        "the plan remains pending for a future capability.",
        False,
    )


def _fallback_answer(selector: str | None, message: str) -> tuple[str, list[models.Citation]]:
    """Deterministic, cited answer when the agent runtime is unavailable (FR-2)."""
    ans = query(models.QueryRequest(workspace=selector, question=message))
    return ans.answer, ans.citations


async def ask_stream(
    workspace: str | None = None,  # noqa: A002 — matches request field name (shadows module locally)
    message: str = "",
    conversation_id: str | None = None,
    approve: bool = False,
) -> AsyncIterator[models.ChatDelta]:
    """Stream a chat turn (FR-1..FR-6, FR-13), marking it running for status probes (FR-14).

    Resolves the conversation id first (a new conversation gets a fresh id), marks it
    running for the duration of the turn, and clears it in ``finally`` so that a normal
    completion, an error, or a client disconnect all leave the conversation not-running.
    """
    from . import conversation

    # Resolve/create up front so we have a stable id to track; pass it through to the impl
    # (as a concrete id, never None) so it loads this same record instead of creating another.
    _name, wpath = _resolve_for_chat(workspace)
    cid = conversation.load_or_create(wpath, conversation_id).conversation_id
    _mark_running(cid)
    try:
        async for delta_out in _ask_stream_impl(workspace, message, cid, approve):
            yield delta_out
    finally:
        _unmark_running(cid)


async def _ask_stream_impl(
    workspace: str | None = None,  # noqa: A002
    message: str = "",
    conversation_id: str | None = None,
    approve: bool = False,
) -> AsyncIterator[models.ChatDelta]:
    """Core chat-turn generator (FR-1..FR-6, FR-13); see ask_stream for running-status tracking."""
    from . import agent, conversation, persona

    selector = workspace
    name, wpath = _resolve_for_chat(selector)
    conv = conversation.load_or_create(wpath, conversation_id)
    cid = conv.conversation_id

    def delta(reply: str, *, done: bool, citations=None, pending=None, executed=False) -> models.ChatDelta:
        return models.ChatDelta(
            workspace=name, conversation_id=cid, reply=reply, done=done,
            citations=citations or [], pending_plan=pending, executed=executed,
        )

    # --- approval turn (D2) ---
    if approve:
        if conv.pending_plan:
            reply, executed = _execute_pending(name, selector, conv.pending_plan)
            pending_model = models.Plan(**conv.pending_plan["plan"]) if not executed else None
            if executed:
                conversation.clear_pending_plan(conv)
            conversation.append_turn(conv, message or "(approve)", reply)
            yield delta(reply, done=True, pending=pending_model, executed=executed)
        else:
            reply = "There is no pending plan to approve in this conversation."
            conversation.append_turn(conv, message or "(approve)", reply)
            yield delta(reply, done=True)
        return

    # --- import-skill request → plan-first, no install this turn (spec 005 FR-4) ---
    if _import_skill_name(message):
        p = _plan_for(message, selector)
        p.requires_approval = True  # importing a skill is always consequential
        conversation.set_pending_plan(conv, message, p.model_dump())
        reply = _consequential_reply(p)
        conversation.append_turn(conv, message, reply)
        yield delta(reply, done=True, pending=p)
        return

    # --- consequential request → plan-first, no mutation this turn (FR-5) ---
    if _CONSEQUENTIAL.search(message):
        p = _plan_for(message, selector)
        conversation.set_pending_plan(conv, message, p.model_dump())
        reply = _consequential_reply(p)
        conversation.append_turn(conv, message, reply)
        yield delta(reply, done=True, pending=p)
        return

    # --- routine request → agent answer via capabilities-as-tools (FR-2/6) ---
    system_prompt = persona.build_system_prompt()
    citations: list[models.Citation] = []
    final_reply, final_sid, agent_ok = "", conv.sdk_session_id, True
    try:
        async for reply, sid in agent.run_stream(
            system_prompt, message, selector, wpath, conv.sdk_session_id, citations
        ):
            final_reply, final_sid = reply, sid
            yield delta(reply, done=False)
    except agent.AgentUnavailable:
        agent_ok = False

    if agent_ok:
        conversation.set_sdk_session_id(conv, final_sid)
    else:
        final_reply, citations = _fallback_answer(selector, message)

    conversation.append_turn(conv, message, final_reply)
    yield delta(final_reply, done=True, citations=citations)


async def ask(
    workspace: str | None = None,  # noqa: A002
    message: str = "",
    conversation_id: str | None = None,
    approve: bool = False,
) -> models.ChatAnswer:
    """Non-streaming chat turn — drives ask_stream to completion (FR-1)."""
    last: models.ChatDelta | None = None
    async for d in ask_stream(workspace, message, conversation_id, approve):
        last = d
    assert last is not None
    return models.ChatAnswer(
        workspace=last.workspace,
        conversation_id=last.conversation_id,
        reply=last.reply,
        citations=last.citations,
        pending_plan=last.pending_plan,
        executed=last.executed,
    )
