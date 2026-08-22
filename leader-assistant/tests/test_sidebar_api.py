"""Tests for the sidebar's backing REST endpoints (feature 004-assistant-sidebar).

Drives the FastAPI app over HTTP (``TestClient``), one test per user story, offline
and deterministic on a throwaway workspace (see ``conftest.py``). Covers the three
new capabilities the sidebar surfaces — browse ``vault/wiki/``, upload into
``vault/raw/`` + ingest, and list/resume conversations — plus the amended P2
invariant that uploads (a *human* action) reach ``vault/raw/`` while the ingestion
pipeline still never mutates it.
"""

from __future__ import annotations


def _make_workspace(client, name="demo"):
    assert client.post("/api/workspaces", json={"name": name}).status_code == 200
    return name


def test_wiki_tree_scoped_to_wiki(client):
    # FR-8/FR-10/FR-15: the browser returns the vault/wiki/ subtree only, never raw/ etc.
    # FR-10a: a fresh workspace's scaffolded dirs are empty, so only files (portal.md,
    # log.md) show — every empty folder is pruned.
    v = _make_workspace(client)
    r = client.get("/api/wiki-tree", params={"workspace": v})
    assert r.status_code == 200
    body = r.json()
    assert body["workspace"] == v and body["root"] == "vault/wiki"
    top = {n["name"] for n in body["nodes"]}
    dirs = {n["name"] for n in body["nodes"] if n["type"] == "dir"}
    assert dirs == set()  # FR-10a: empty scaffolded dirs (sources, concepts, …) are pruned
    assert "portal.md" in top  # files with data still show
    assert "raw" not in top and "sessions" not in top and "output" not in top


def test_wiki_tree_prunes_empty_folders(client):
    # FR-10a: a folder appears only once it (transitively) contains a file; empty ones are hidden.
    v = _make_workspace(client)
    client.post(
        "/api/upload",
        data={"workspace": v, "provenance": "notes"},
        files=[("files", ("note.md", b"# Note\ncontent here", "text/markdown"))],
    )
    body = client.get("/api/wiki-tree", params={"workspace": v}).json()
    dirs = {n["name"] for n in body["nodes"] if n["type"] == "dir"}
    # sources/ now holds the ingested page, so it appears; concepts/ is still empty → pruned.
    assert "sources" in dirs and "concepts" not in dirs


def test_wiki_tree_rejects_symlink_escape(client, isolated_workspace_root, tmp_path):
    # FR-10: a symlink under vault/wiki/ MUST NOT expose paths outside vault/wiki/ (escaping the
    # workspace, or reaching the forbidden vault/raw/, sessions/, vault/output/).
    v = _make_workspace(client)
    wiki = isolated_workspace_root / v / "vault" / "wiki"
    secret = tmp_path / "secret"
    secret.mkdir()
    (secret / "password.txt").write_text("TOPSECRET")
    (wiki / "sneaky").symlink_to(secret)  # escapes the workspace entirely
    (wiki / "raw-link").symlink_to(isolated_workspace_root / v / "vault" / "raw")  # forbidden area

    def flat(nodes):
        for n in nodes:
            yield n["name"]
            yield from flat(n["children"])

    names = set(flat(client.get("/api/wiki-tree", params={"workspace": v}).json()["nodes"]))
    assert "sneaky" not in names and "password.txt" not in names
    assert "raw-link" not in names


def test_upload_deposits_raw_and_ingests(client, tmp_path):
    # FR-12/FR-16 + P2 v1.1.0: a text upload lands in vault/raw/ (human-owned) AND is ingested.
    v = _make_workspace(client)
    r = client.post(
        "/api/upload",
        data={"workspace": v, "provenance": "notes"},
        files=[("files", ("meeting.md", b"# Sync\nWe decided to ship.", "text/markdown"))],
    )
    assert r.status_code == 200
    report = r.json()
    assert report["count"] == 1 and report["files"][0]["ingested"] is True
    assert report["files"][0]["raw_path"] == "vault/raw/notes/meeting.md"
    assert report["files"][0]["source_page"].startswith("vault/wiki/sources/notes/")
    # The ingested content is now queryable, proving the pipeline ran end-to-end.
    q = client.post("/api/query", json={"workspace": v, "question": "ship"})
    assert q.status_code == 200 and q.json()["citations"]
    # And it shows up in the vault/wiki/ browser under sources/.
    tree = client.get("/api/wiki-tree", params={"workspace": v}).json()
    sources = next(n for n in tree["nodes"] if n["name"] == "sources")
    assert any(c["name"] == "notes" for c in sources["children"])


def test_upload_binary_stored_not_ingested(client):
    # FR-14: a non-text file is stored under vault/raw/ but reported as not ingested (no crash).
    v = _make_workspace(client)
    r = client.post(
        "/api/upload",
        data={"workspace": v, "provenance": "assets"},
        files=[("files", ("logo.bin", bytes([0, 1, 2, 255]), "application/octet-stream"))],
    )
    assert r.status_code == 200
    f = r.json()["files"][0]
    assert f["ingested"] is False and f["error"] and f["raw_path"] == "vault/raw/assets/logo.bin"


def test_upload_filename_traversal_is_neutralised(client):
    # Security: a malicious filename cannot escape vault/raw/ (path-traversal guard).
    v = _make_workspace(client)
    r = client.post(
        "/api/upload",
        data={"workspace": v, "provenance": "notes"},
        files=[("files", ("../../evil.md", b"nope", "text/markdown"))],
    )
    assert r.status_code == 200
    assert r.json()["files"][0]["raw_path"] == "vault/raw/notes/evil.md"


def test_sessions_list_and_resume(client, offline_agent):
    # FR-17/FR-19/FR-20: two chat turns create resumable sessions, listed and fetchable.
    # FR-25 contract: the list is newest-first and every summary carries an ISO `created`
    # date — the two inputs the sidebar's date-bucketed Sessions panel groups on.
    from datetime import date

    v = _make_workspace(client)
    first = client.post("/api/chat", json={"workspace": v, "message": "what did we decide?"})
    second = client.post("/api/chat", json={"workspace": v, "message": "and the deadline?"})
    assert first.status_code == 200 and second.status_code == 200
    cid1, cid2 = first.json()["conversation_id"], second.json()["conversation_id"]
    assert cid1 != cid2

    listed = client.get("/api/sessions", params={"workspace": v})
    assert listed.status_code == 200
    convos = listed.json()["conversations"]
    ids = [c["conversation_id"] for c in convos]
    assert set(ids) == {cid1, cid2}
    assert ids[0] == cid2  # newest first (FR-25 reverse-chronological)
    for c in convos:  # every summary is bucketable: an ISO date + a title
        date.fromisoformat(c["created"])
        assert c["title"]

    detail = client.get(f"/api/sessions/{cid1}", params={"workspace": v})
    assert detail.status_code == 200
    roles = [m["role"] for m in detail.json()["messages"]]
    assert "user" in roles and "assistant" in roles


def test_session_date_bucketing(monkeypatch):
    # FR-25: conversations group under relative-date headers in a fixed order, newest
    # first, with empty buckets dropped. Exercises the UI's pure bucketing helpers on a
    # frozen reference date so the mapping is deterministic (no server / clock needed).
    from datetime import date

    from app import ui

    ref = date(2026, 8, 16)
    cases = {
        "2026-08-16": "Today",
        "2026-08-15": "Yesterday",
        "2026-08-12": "This Week",   # 4 days back
        "2026-08-06": "This Month",  # >7 days but same calendar month
        "2026-07-20": "Older",       # previous month
        "not-a-date": "Today",       # malformed dates degrade to Today, never crash
    }
    for created, bucket in cases.items():
        assert ui._bucket_for(created, ref) == bucket

    # _grouped_sessions preserves the canonical header order and drops empty buckets.
    sample = [
        {"conversation_id": "c-old", "created": "2026-07-20", "title": "Retro", "turn_count": 1},
        {"conversation_id": "c-today", "created": "2026-08-16", "title": "Ship it", "turn_count": 2},
    ]
    monkeypatch.setattr(ui, "_get_sessions", lambda _v: {"conversations": sample})
    groups = ui._grouped_sessions("demo", today=ref)
    headers = [h for h, _ in groups]
    assert headers == ["Today", "Older"]  # canonical order, empty buckets omitted
    assert groups[0][1][0][1] == "c-today" and groups[1][1][0][1] == "c-old"


def test_session_detail_missing_is_404(client):
    v = _make_workspace(client)
    assert client.get("/api/sessions/nope", params={"workspace": v}).status_code == 404


def test_wiki_tree_names_are_single_line_with_tooltip():
    # FR-9b: each folder/file renders on one line (CSS ellipsis truncation) and carries the
    # full, untruncated name in a data-tip attribute so hover reveals it (folder/file tooltip).
    from app import ui

    long_dir = "a-really-long-folder-name-that-would-wrap-past-the-panel-border"
    long_file = "an-extremely-long-file-name-that-should-truncate.md"
    nodes = [{
        "name": long_dir, "type": "dir",
        "children": [{"name": long_file, "type": "file"}],
    }]
    out = ui._render_nodes(nodes)

    # Folder tooltip: summary carries the full folder name; the label span truncates while the
    # default <summary> keeps its disclosure triangle.
    assert f'<summary data-tip="{long_dir}"><span class="label">' in out
    # File tooltip: the file div carries the full file name.
    assert f'data-tip="{long_file}"' in out and "class='file'" in out

    # The CSS keeps names on one line and truncates rather than wraps, and a body-level
    # tooltip element (.wiki-tip) escapes the panel's overflow clipping.
    assert "text-overflow: ellipsis" in ui._CSS and "white-space: nowrap" in ui._CSS
    assert ".wiki-tip" in ui._CSS
    # The hover tooltip is wired from data-tip via a load-time script.
    assert "data-tip" in ui._WIKI_TIP_JS
