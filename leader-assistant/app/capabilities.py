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

from . import models, vault
from .vault import VaultError

# --- helpers ---------------------------------------------------------------

_CONSEQUENTIAL = re.compile(
    r"\b(delete|remove|drop|overwrite|rewrite|merge|deploy|push|migrate|rename)\b",
    re.IGNORECASE,
)


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "untitled"


def _wiki_pages(v: Path) -> list[Path]:
    wiki = v / "wiki"
    if not wiki.is_dir():
        return []
    return [p for p in wiki.rglob("*.md") if p.name not in ("portal.md", "log.md")]


def _git_commit(v: Path, message: str) -> bool:
    """Commit vault changes into the vault's OWN repo; never an enclosing one.

    Refuses to run if `git -C <vault>` resolves to a repo whose top-level is
    not the vault itself (e.g. a parent project checkout).
    """
    try:
        top = subprocess.run(
            ["git", "-C", str(v), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True,
        )
        if top.returncode != 0:
            return False
        if Path(top.stdout.strip()).resolve() != v.resolve():
            return False  # would commit into an enclosing repo — refuse
        subprocess.run(["git", "-C", str(v), "add", "-A"], capture_output=True, text=True)
        done = subprocess.run(
            ["git", "-C", str(v), "commit", "-m", message],
            capture_output=True, text=True,
        )
        return done.returncode == 0
    except FileNotFoundError:
        return False


def _resolve_scaffolded(selector: str | None) -> tuple[str, Path]:
    v = vault.resolve_vault(selector)
    if not vault.is_scaffolded(v):
        vault.scaffold_vault(v)
    return v.name, v


# --- capabilities ----------------------------------------------------------

def list_vaults() -> models.VaultList:
    from . import config
    return models.VaultList(
        root=str(config.vault_root()),
        vaults=vault.list_vault_names(),
        default=config.default_vault_name(),
    )


def create_vault(name: str) -> models.VaultInfo:
    from . import config
    v = config.vault_root() / name
    vault.scaffold_vault(v)
    _git_commit(v, f"chore(vault): scaffold {name}")
    return get_vault_info(name)


def get_vault_info(selector: str | None = None) -> models.VaultInfo:
    v = vault.resolve_vault(selector)
    return models.VaultInfo(
        name=v.name,
        path=str(v),
        scaffolded=vault.is_scaffolded(v),
        pages=len(_wiki_pages(v)),
    )


def ingest(req: models.IngestRequest) -> models.IngestReport:
    """Create a wiki/sources summary page, update portal, append log, commit.

    Note: raw content is summarised into wiki/sources/; raw/ itself is never
    written by the assistant (spec 03-vault AC2).
    """
    name, v = _resolve_scaffolded(req.vault)
    provenance = _slug(req.provenance)
    dest_dir = v / "wiki" / "sources" / provenance
    dest_dir.mkdir(parents=True, exist_ok=True)
    page = dest_dir / f"{date.today().isoformat()}-{_slug(req.title)}.md"
    vault.guard_write_path(v, page)

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

    rel = page.relative_to(v).as_posix()
    _update_portal(v, rel, req.title, preview)
    vault.append_log(v, "ingest", req.title)
    committed = _git_commit(v, f"ingest: {req.title}")

    return models.IngestReport(
        vault=name,
        source_page=rel,
        portal_updated=True,
        committed=committed,
        message=f"Ingested '{req.title}' into {rel}",
    )


def _update_portal(v: Path, rel: str, title: str, preview: str) -> None:
    portal = v / "wiki" / "portal.md"
    vault.guard_write_path(v, portal)
    stem = Path(rel).stem
    line = f"- [[{rel}|{title}]] — {preview[:100]}\n"
    existing = portal.read_text(encoding="utf-8") if portal.exists() else "# Portal\n\n"
    if stem not in existing:
        portal.write_text(existing.rstrip() + "\n" + line, encoding="utf-8")


def query(req: models.QueryRequest) -> models.Answer:
    """Naive cited search over wiki pages (portal index model, no vector DB)."""
    name, v = _resolve_scaffolded(req.vault)
    terms = [t for t in re.split(r"\W+", req.question.lower()) if len(t) > 2]
    citations: list[models.Citation] = []
    for page in _wiki_pages(v):
        text = page.read_text(encoding="utf-8", errors="ignore")
        low = text.lower()
        score = sum(low.count(t) for t in terms)
        if score:
            excerpt = _first_match(text, terms)
            citations.append(
                models.Citation(page=page.relative_to(v).as_posix(), excerpt=excerpt)
            )
    citations.sort(key=lambda c: -len(c.excerpt))
    citations = citations[:5]
    if citations:
        answer = (
            f"Found {len(citations)} relevant page(s) for '{req.question}'. "
            "See citations for supporting excerpts."
        )
    else:
        answer = "No matching knowledge found in this vault yet. Ingest sources first."
    return models.Answer(vault=name, question=req.question, answer=answer, citations=citations)


def _first_match(text: str, terms: list[str]) -> str:
    for line in text.splitlines():
        low = line.lower()
        if any(t in low for t in terms) and line.strip() and not line.startswith("---"):
            return line.strip()[:200]
    return text.strip()[:200]


def plan(req: models.PlanRequest) -> models.Plan:
    """Plan-first for consequential work (Constitution P8, spec 13-api AC2)."""
    name, _ = _resolve_scaffolded(req.vault)
    consequential = bool(_CONSEQUENTIAL.search(req.request))
    risk = "risky" if consequential else "safe"
    steps = [
        models.PlanStep(order=1, action="Clarify scope and affected pages", rationale="Avoid ambiguity before mutation"),
        models.PlanStep(order=2, action="Draft changes in the vault workspace", rationale="Keep raw/ immutable"),
        models.PlanStep(order=3, action="Evaluate risk and choose branch policy", rationale="Risky work → feature branch"),
        models.PlanStep(order=4, action="Commit with a typed message", rationale="Every mutation is a git commit"),
    ]
    return models.Plan(
        vault=name,
        request=req.request,
        steps=steps,
        risk=risk,
        requires_approval=consequential,
    )


def lint(selector: str | None = None) -> models.LintReport:
    """Basic hygiene checks: orphan pages and empty pages."""
    name, v = _resolve_scaffolded(selector)
    pages = _wiki_pages(v)
    linked: set[str] = set()
    for page in pages:
        for m in re.finditer(r"\[\[([^\]|#]+)", page.read_text(encoding="utf-8", errors="ignore")):
            linked.add(Path(m.group(1)).stem)
    findings: list[models.LintFinding] = []
    for page in pages:
        rel = page.relative_to(v).as_posix()
        body = page.read_text(encoding="utf-8", errors="ignore")
        if page.stem not in linked and "sources/" not in rel:
            findings.append(models.LintFinding(kind="orphan", page=rel, detail="No inbound [[wikilinks]]"))
        if len(body.strip().splitlines()) < 4:
            findings.append(models.LintFinding(kind="stale", page=rel, detail="Page has little content"))
    return models.LintReport(vault=name, findings=findings, ok=not findings)


def spec_read(rel_path: str, selector: str | None = None) -> str:
    """Read a page's raw Markdown from the vault."""
    _, v = _resolve_scaffolded(selector)
    target = (v / rel_path).resolve()
    if v.resolve() not in target.parents:
        raise VaultError("path escapes vault")
    if not target.is_file():
        raise VaultError(f"no such page: {rel_path}")
    return target.read_text(encoding="utf-8", errors="ignore")
