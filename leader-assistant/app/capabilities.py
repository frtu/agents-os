"""Surface-agnostic capability layer — the parity boundary (Constitution P9).

Both the REST surface (api.py) and any future chat surface call these
functions; neither talks to the filesystem directly. Requests that are
consequential return a plan for approval rather than executing (spec 13-api AC2).
"""

from __future__ import annotations

import re
import subprocess
from datetime import date
from pathlib import Path
from typing import AsyncIterator

from . import models, vault
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
    return [p for p in wiki.rglob("*.md") if p.name not in ("portal.md", "log.md")]


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


def ingest(req: models.IngestRequest) -> models.IngestReport:
    """Create a vault/wiki/sources summary page, update portal, append log, commit.

    Note: raw content is summarised into vault/wiki/sources/; vault/raw/ itself is never
    written by the assistant (spec 03-workspace AC2).
    """
    name, workspace = _resolve_scaffolded(req.workspace)
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
    committed = _git_commit(workspace, f"ingest: {req.title}")

    return models.IngestReport(
        workspace=name,
        source_page=rel,
        portal_updated=True,
        committed=committed,
        message=f"Ingested '{req.title}' into {rel}",
    )


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

    def build(d: Path) -> list[models.WikiNode]:
        nodes: list[models.WikiNode] = []
        for child in sorted(d.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
            if child.name.startswith("."):
                continue
            rel = child.relative_to(wiki).as_posix()
            if child.is_dir():
                nodes.append(
                    models.WikiNode(name=child.name, path=rel, type="dir", children=build(child))
                )
            else:
                nodes.append(models.WikiNode(name=child.name, path=rel, type="file"))
        return nodes

    return models.WikiTree(workspace=name, root="vault/wiki", nodes=build(wiki) if wiki.is_dir() else [])


def _safe_name(filename: str | None) -> str:
    """Strip any directory components from an uploaded filename (path-traversal guard)."""
    return Path(filename or "upload").name or "upload"


def deposit_raw(workspace: Path, provenance: str, filename: str, data: bytes) -> Path:
    """Write a human-uploaded original into `vault/raw/<provenance>/` (Constitution P2 v1.1.0).

    This is the **sanctioned human channel** into `vault/raw/`: it deliberately does NOT go
    through `guard_write_path` (which forbids the *ingestion pipeline* from touching vault/raw/).
    It still validates that the resolved destination stays inside `vault/raw/`.
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
    """Deposit uploaded originals into `vault/raw/` then ingest text ones (FR-12/FR-16).

    Text-decodable files are ingested via the existing `ingest` pipeline (producing a
    `vault/wiki/sources` summary + portal/log update). Binary files are stored under `vault/raw/`
    only, with a note. Never mutates existing raw content (create/overwrite by name is a
    human action; ingestion still never touches vault/raw/).
    """
    name, workspace = _resolve_scaffolded(selector)
    prov = _slug(provenance)
    results: list[models.UploadedFile] = []
    for filename, data in files:
        safe = _safe_name(filename)
        raw_path = deposit_raw(workspace, prov, safe, data)
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
    """Stream a chat turn (FR-1..FR-6, FR-13). Yields accumulating ChatDelta.

    The final delta carries done=true plus any pending_plan / executed flag.
    """
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
