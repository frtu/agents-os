"""Tests for the sidebar's backing REST endpoints (feature 004-assistant-sidebar).

Drives the FastAPI app over HTTP (``TestClient``), one test per user story, offline
and deterministic on a throwaway vault (see ``conftest.py``). Covers the three new
capabilities the sidebar surfaces — browse ``wiki/``, upload into ``raw/`` + ingest,
and list/resume conversations — plus the amended P2 invariant that uploads (a *human*
action) reach ``raw/`` while the ingestion pipeline still never mutates it.
"""

from __future__ import annotations


def _make_vault(client, name="demo"):
    assert client.post("/api/vaults", json={"name": name}).status_code == 200
    return name


def test_wiki_tree_scoped_to_wiki(client):
    # FR-8/FR-10/FR-15: the browser returns the wiki/ subtree only, never raw/ etc.
    v = _make_vault(client)
    r = client.get("/api/wiki-tree", params={"vault": v})
    assert r.status_code == 200
    body = r.json()
    assert body["vault"] == v and body["root"] == "wiki"
    top = {n["name"] for n in body["nodes"]}
    assert "sources" in top and "concepts" in top  # scaffolded wiki dirs
    assert "raw" not in top and "sessions" not in top and "output" not in top


def test_upload_deposits_raw_and_ingests(client, tmp_path):
    # FR-12/FR-16 + P2 v1.1.0: a text upload lands in raw/ (human-owned) AND is ingested.
    v = _make_vault(client)
    r = client.post(
        "/api/upload",
        data={"vault": v, "provenance": "notes"},
        files=[("files", ("meeting.md", b"# Sync\nWe decided to ship.", "text/markdown"))],
    )
    assert r.status_code == 200
    report = r.json()
    assert report["count"] == 1 and report["files"][0]["ingested"] is True
    assert report["files"][0]["raw_path"] == "raw/notes/meeting.md"
    assert report["files"][0]["source_page"].startswith("wiki/sources/notes/")
    # The ingested content is now queryable, proving the pipeline ran end-to-end.
    q = client.post("/api/query", json={"vault": v, "question": "ship"})
    assert q.status_code == 200 and q.json()["citations"]
    # And it shows up in the wiki/ browser under sources/.
    tree = client.get("/api/wiki-tree", params={"vault": v}).json()
    sources = next(n for n in tree["nodes"] if n["name"] == "sources")
    assert any(c["name"] == "notes" for c in sources["children"])


def test_upload_binary_stored_not_ingested(client):
    # FR-14: a non-text file is stored under raw/ but reported as not ingested (no crash).
    v = _make_vault(client)
    r = client.post(
        "/api/upload",
        data={"vault": v, "provenance": "assets"},
        files=[("files", ("logo.bin", bytes([0, 1, 2, 255]), "application/octet-stream"))],
    )
    assert r.status_code == 200
    f = r.json()["files"][0]
    assert f["ingested"] is False and f["error"] and f["raw_path"] == "raw/assets/logo.bin"


def test_upload_filename_traversal_is_neutralised(client):
    # Security: a malicious filename cannot escape raw/ (path-traversal guard).
    v = _make_vault(client)
    r = client.post(
        "/api/upload",
        data={"vault": v, "provenance": "notes"},
        files=[("files", ("../../evil.md", b"nope", "text/markdown"))],
    )
    assert r.status_code == 200
    assert r.json()["files"][0]["raw_path"] == "raw/notes/evil.md"


def test_sessions_list_and_resume(client, offline_agent):
    # FR-17/FR-19/FR-20: two chat turns create resumable sessions, listed and fetchable.
    # FR-25 contract: the list is newest-first and every summary carries an ISO `created`
    # date — the two inputs the sidebar's date-bucketed Sessions panel groups on.
    from datetime import date

    v = _make_vault(client)
    first = client.post("/api/chat", json={"vault": v, "message": "what did we decide?"})
    second = client.post("/api/chat", json={"vault": v, "message": "and the deadline?"})
    assert first.status_code == 200 and second.status_code == 200
    cid1, cid2 = first.json()["conversation_id"], second.json()["conversation_id"]
    assert cid1 != cid2

    listed = client.get("/api/sessions", params={"vault": v})
    assert listed.status_code == 200
    convos = listed.json()["conversations"]
    ids = [c["conversation_id"] for c in convos]
    assert set(ids) == {cid1, cid2}
    assert ids[0] == cid2  # newest first (FR-25 reverse-chronological)
    for c in convos:  # every summary is bucketable: an ISO date + a title
        date.fromisoformat(c["created"])
        assert c["title"]

    detail = client.get(f"/api/sessions/{cid1}", params={"vault": v})
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
    v = _make_vault(client)
    assert client.get("/api/sessions/nope", params={"vault": v}).status_code == 404
