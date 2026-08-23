"""Tests for feature 007 (knowledge activities) + spec 22 (metadata management).

Offline and deterministic: exercises capture/ingest separation, the activity interface
(pydantic Input/Output), the ingest workflow orchestrator with its in-process fallback,
foundation-doc bootstrap (verbatim core + extension overlay), and the tbd.md backlog.
Each test links the spec id it covers.
"""

from __future__ import annotations

import pytest

from app import activity_ingest, capabilities, config, models, vault


@pytest.fixture
def foundation_source(tmp_path, monkeypatch):
    """A throwaway foundation-doc source with known content (spec 007 D10, spec 22 R1).

    The autouse skills_library fixture points the skill root at a fake library without
    second-brain/references, so we pin LEADER_FOUNDATION_DOCS_SOURCE explicitly here to make
    byte-identity assertions deterministic.
    """
    src = tmp_path / "refs"
    src.mkdir()
    (src / "wiki-schema.md").write_text("# Wiki Schema CORE\n\nraw/ wiki/ layout.\n", encoding="utf-8")
    (src / "wiki-architecture.md").write_text("# Wiki Architecture CORE\n\nsix categories.\n", encoding="utf-8")
    monkeypatch.setenv("LEADER_FOUNDATION_DOCS_SOURCE", str(src))
    return src


def _ws(name="demo"):
    capabilities.create_workspace(name)
    return vault.resolve_workspace(name)


# --- capture (FR-1/FR-2/FR-3) ----------------------------------------------


def test_capture_writes_only_raw_no_processing(foundation_source, isolated_workspace_root):
    # AC-1 / FR-1/FR-3: capture deposits under vault/raw/ and does no processing, no auto-ingest.
    ws = _ws()
    portal_before = (ws / "vault" / "wiki" / "portal.md").read_text()
    log_before = (ws / "vault" / "wiki" / "log.md").read_text()

    dest = capabilities.capture(ws, "notes", "a.txt", b"hello raw")

    assert dest == ws / "vault" / "raw" / "notes" / "a.txt"
    assert dest.read_bytes() == b"hello raw"
    # No knowledge processing happened: no sources page, portal/log untouched.
    assert capabilities._latest_source_page(ws) == ""
    assert (ws / "vault" / "wiki" / "portal.md").read_text() == portal_before
    assert (ws / "vault" / "wiki" / "log.md").read_text() == log_before


# --- activity interface (FR-5) ---------------------------------------------


def test_activity_output_is_progress_and_errors():
    # AC-2 / FR-5: the Output Object is exactly a progress list and an error list.
    out = models.ActivityOutput(progress=["did a thing"], errors=["a failure"])
    assert out.progress == ["did a thing"] and out.errors == ["a failure"]
    assert set(models.ActivityOutput().model_dump().keys()) == {"progress", "errors"}


def test_activity_input_carries_workspace_and_context(foundation_source, isolated_workspace_root):
    # FR-5/FR-11: Input Object carries the workspace path + injected overlay context.
    ws = _ws()
    inp = activity_ingest.build_input("demo", ws)
    assert inp.workspace == "demo" and inp.workspace_path == str(ws)
    assert "Path mapping" in inp.context and "wiki-schema" in inp.context


# --- overlay context (FR-11, spec 22 R5) -----------------------------------


def test_overlay_context_includes_core_and_extension(foundation_source, isolated_workspace_root):
    # FR-11: the injected context carries core + extension for each foundation doc + path map.
    ws = _ws()
    ctx = activity_ingest.build_overlay_context(ws)
    assert "raw/` → `vault/raw/" in ctx
    assert "Wiki Schema CORE" in ctx  # core content present
    assert "extension (authoritative overrides)" in ctx  # extension overlaid, extension-wins


# --- ingest orchestrator + fallback (FR-7/FR-8) ----------------------------


def test_ingest_fallback_returns_output_object(foundation_source, isolated_workspace_root):
    # AC-5 / FR-7: with the activity disabled (default), ingest uses the deterministic
    # in-process fallback and still returns a valid Output Object (progress + errors).
    _ws()
    report = capabilities.ingest(
        models.IngestRequest(workspace="demo", title="Note", content="hello world", provenance="notes")
    )
    assert report.source_page.startswith("vault/wiki/sources/notes/")
    assert report.progress and report.errors == []


def test_ingest_orchestrator_falls_back_when_activity_unavailable(
    foundation_source, isolated_workspace_root, monkeypatch
):
    # AC-5 / FR-7: even with the activity enabled, an unavailable runtime falls back cleanly.
    _ws()
    monkeypatch.setenv("LEADER_INGEST_ACTIVITY", "1")

    def _boom(*_a, **_k):
        raise capabilities.AgentUnavailable("no runtime")

    monkeypatch.setattr(capabilities, "_ingest_via_activity", _boom)
    report = capabilities.ingest(
        models.IngestRequest(workspace="demo", title="Note", content="hi there", provenance="notes")
    )
    assert report.source_page.startswith("vault/wiki/sources/notes/")
    assert report.progress


def test_ingest_produces_wiki_and_never_writes_raw(foundation_source, isolated_workspace_root):
    # AC-6 / FR-8/FR-2: ingest writes sources/portal/log + commits, nothing under vault/raw/.
    ws = _ws()
    report = capabilities.ingest(
        models.IngestRequest(workspace="demo", title="Widgets", content="widgets are blue", provenance="notes")
    )
    assert (ws / report.source_page).is_file()
    assert report.portal_updated is True and report.committed is True
    # No knowledge write leaked under vault/raw/.
    raw_files = list((ws / "vault" / "raw").rglob("*.md")) + list((ws / "vault" / "raw").rglob("*.txt"))
    assert raw_files == []


# --- foundation & extension docs (FR-9/FR-10, spec 22) ---------------------


def test_foundation_docs_bootstrapped_verbatim(foundation_source, isolated_workspace_root):
    # AC-7/AC-12 / FR-9: vault/docs/ holds byte-identical core copies + two extensions.
    ws = _ws()
    docs = ws / "vault" / "docs"
    for name in ("wiki-schema", "wiki-architecture"):
        core = docs / f"{name}.md"
        assert core.read_bytes() == (foundation_source / f"{name}.md").read_bytes()
        assert (docs / f"{name}-extension.md").is_file()


def test_foundation_core_unchanged_after_ingest(foundation_source, isolated_workspace_root):
    # AC-7 / spec 22 R2: an ingest run must not mutate the immutable core.
    ws = _ws()
    core = ws / "vault" / "docs" / "wiki-schema.md"
    before = core.read_bytes()
    capabilities.ingest(
        models.IngestRequest(workspace="demo", title="Note", content="x y z", provenance="notes")
    )
    assert core.read_bytes() == before


def test_extension_encodes_path_overrides_and_provenance(foundation_source, isolated_workspace_root):
    # AC-8 / FR-10, spec 22 R4/R7: extension references the core, records provenance + overrides.
    ws = _ws()
    ext = (ws / "vault" / "docs" / "wiki-schema-extension.md").read_text()
    assert "extends: wiki-schema.md" in ext
    assert "source-hash:" in ext and "copied:" in ext
    assert "`raw/` → `vault/raw/`" in ext
    assert "index file: `wiki/index.md` → `vault/wiki/portal.md`" in ext


# --- tbd.md backlog (FR-14/FR-15) ------------------------------------------


def test_tbd_created_sectioned_by_topic_and_theme(foundation_source, isolated_workspace_root):
    # AC-11 / FR-14/FR-15: tbd.md exists, organized into topic/theme sections.
    ws = _ws()
    tbd = (ws / "vault" / "wiki" / "tbd.md").read_text()
    assert tbd.count("## ") >= 2  # multiple topic/theme sections, not a flat list
    assert "## Sources" in tbd


def test_ingest_updates_tbd_backlog(foundation_source, isolated_workspace_root):
    # AC-11 / FR-14: an ingest run records a checked-off item in tbd.md under Sources.
    ws = _ws()
    capabilities.ingest(
        models.IngestRequest(workspace="demo", title="Meeting", content="notes here", provenance="notes")
    )
    tbd = (ws / "vault" / "wiki" / "tbd.md").read_text()
    assert "[x]" in tbd and "ingested 'Meeting'" in tbd
