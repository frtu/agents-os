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
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import AsyncIterator

from . import config, models, vault
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

    def delta(reply: str, *, done: bool, citations=None, pending=None, executed=False, interaction=None) -> models.ChatDelta:
        return models.ChatDelta(
            workspace=name, conversation_id=cid, reply=reply, done=done,
            citations=citations or [], pending_plan=pending, executed=executed, interaction=interaction,
        )

    # --- approval turn (D2) ---
    if approve:
        if conv.pending_plan:
            reply, executed = _execute_pending(name, selector, conv.pending_plan)
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

    # --- import-skill request → plan-first, no install this turn (spec 005 FR-4) ---
    if _import_skill_name(message):
        p = _plan_for(message, selector)
        p.requires_approval = True  # importing a skill is always consequential
        conversation.set_pending_plan(conv, message, p.model_dump())
        reply = _consequential_reply(p)
        itx = _approval_interaction_for_plan(conv, message, p)  # deliver approval as an interaction (FR-17)
        conversation.append_turn(conv, message, reply)
        yield delta(reply, done=True, pending=p, interaction=itx)
        return

    # --- consequential request → plan-first, no mutation this turn (FR-5) ---
    if _CONSEQUENTIAL.search(message):
        p = _plan_for(message, selector)
        conversation.set_pending_plan(conv, message, p.model_dump())
        reply = _consequential_reply(p)
        itx = _approval_interaction_for_plan(conv, message, p)  # deliver approval as an interaction (FR-17)
        conversation.append_turn(conv, message, reply)
        yield delta(reply, done=True, pending=p, interaction=itx)
        return

    # --- routine request → agent answer via capabilities-as-tools (FR-2/6) ---
    system_prompt = persona.build_system_prompt()
    citations: list[models.Citation] = []
    raised: list[models.Interaction] = []  # cards the agent raises on its own (spec 008 FR-18)
    final_reply, final_sid, agent_ok = "", conv.sdk_session_id, True
    try:
        async for reply, sid in agent.run_stream(
            system_prompt, message, selector, wpath, conv.sdk_session_id, citations,
            conv.conversation_id, raised,
        ):
            final_reply, final_sid = reply, sid
            yield delta(reply, done=False)
    except agent.AgentUnavailable:
        agent_ok = False

    if agent_ok:
        conversation.set_sdk_session_id(conv, final_sid)
    else:
        final_reply, citations = _fallback_answer(selector, message)

    # Surface an agent-raised card: prefer a blocking clarification, else a notification (FR-18).
    itx = next((i for i in raised if i.kind == "clarification"), None) or (raised[0] if raised else None)
    conversation.append_turn(conv, message, final_reply)
    yield delta(final_reply, done=True, citations=citations, interaction=itx)


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
    _plan: dict | None = None,
    _request: str | None = None,
) -> models.Interaction:
    """Raise a mid-task interaction request, persisting blocking ones durably (spec 008 FR-1/2/6/13/15).

    Validates the kind and the option-count bounds (FR-6); enforces at most one outstanding
    blocking interaction per conversation (FR-15); captures the request into the sessions record
    (FR-13). Notifications are non-blocking and not persisted (FR-3); approval/clarification are
    persisted as the durable `pending-interaction` (FR-11). The `_plan`/`_request` payload lets an
    approval wrap a plan-first plan (FR-17).
    """
    from . import config
    from . import conversation as convo

    if kind not in _KIND_BOUNDS:
        raise WorkspaceError(f"unknown interaction kind: {kind!r}")
    lo, hi = _KIND_BOUNDS[kind]
    opts = [_norm_option(i, o) for i, o in enumerate(options or [])]
    if not (lo <= len(opts) <= hi):
        raise WorkspaceError(f"{kind} requires {lo}..{hi} options, got {len(opts)}")

    name, workspace = _resolve_for_chat(selector)
    conv = convo.load_or_create(workspace, conversation_id)

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
        if _plan is not None:
            record["plan"] = _plan
            record["request"] = _request or ""
        convo.set_pending_interaction(conv, record)
    return itx


def _approval_interaction_for_plan(conv, request: str, p: models.Plan) -> models.Interaction:
    """Deliver a plan-first plan as an approval interaction wrapping the plan (spec 008 FR-17).

    The single proposal is "Proceed with this plan"; accepting it executes the stored plan via
    the same path as the legacy approve-to-execute turn. Persisted as the durable pending
    interaction so a reloaded UI can re-render the approval card (FR-11).
    """
    from . import config
    from . import conversation as convo

    itx = models.Interaction(
        interaction_id=_new_interaction_id(),
        conversation_id=conv.conversation_id,
        kind="approval",
        prompt=f"Approve this plan (risk={p.risk})? {request}",
        options=[models.InteractionOption(id="approve", label="Proceed with this plan", detail=p.request)],
        timeout_seconds=config.interaction_timeout_seconds(),
        created=_now_iso(),
        status="pending",
    )
    record = itx.model_dump()
    record["plan"] = p.model_dump()
    record["request"] = request
    convo.append_event(conv, "interaction", _describe_interaction(itx))
    convo.set_pending_interaction(conv, record)
    return itx


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

    name, wpath = _resolve_for_chat(selector)
    conv = convo.load_or_create(wpath, conversation_id)
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
        reply, executed = _execute_pending(name, selector, {"request": record.get("request", ""), "plan": record["plan"]})
        if executed and conv.pending_plan:
            convo.clear_pending_plan(conv)
        pending_model = None if executed else models.Plan(**record["plan"])
        convo.append_turn(conv, f"(approved) {chosen.label}", reply)
        yield delta(reply, done=True, pending=pending_model, executed=executed)
        return

    # --- generic clarification/approval selection → continue with that choice ---
    reply = f"Proceeding with your choice: {chosen.label}."
    convo.append_turn(conv, f"(selected) {chosen.label}", reply)
    yield delta(reply, done=True)


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
    # Preserve any plan payload so the re-presented approval still executes on accept (FR-17).
    if conv.pending_interaction and "plan" in conv.pending_interaction:
        record["plan"] = conv.pending_interaction["plan"]
        record["request"] = conv.pending_interaction.get("request", "")
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
    return final_reply, citations
