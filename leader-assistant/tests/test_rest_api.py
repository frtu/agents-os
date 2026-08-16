"""API tests for the REST capability surface (feature 001 user stories).

Covers the getting-started tour: health, workspace lifecycle, ingest → cited
query, plan-first governance, lint, and reading a page. Each hits the FastAPI app
over HTTP via TestClient, exactly as an external caller would.
"""

from __future__ import annotations


def test_health_liveness(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_workspace_create_list_inspect(client):
    # Story: a user creates a workspace, lists it, and inspects it.
    created = client.post("/api/workspaces", json={"name": "demo"})
    assert created.status_code == 200
    assert created.json()["name"] == "demo"
    assert created.json()["scaffolded"] is True

    listed = client.get("/api/workspaces")
    assert listed.status_code == 200
    assert "demo" in listed.json()["workspaces"]
    assert listed.json()["default"] == "_default_"

    info = client.get("/api/workspaces/demo")
    assert info.status_code == 200
    assert info.json()["name"] == "demo"


def test_ingest_then_cited_query(client):
    # Story: ingest a source, then ask a question and get citations back.
    client.post("/api/workspaces", json={"name": "demo"})
    ingest = client.post(
        "/api/ingest",
        json={
            "workspace": "demo",
            "title": "Team sync",
            "provenance": "transcripts",
            "content": "We decided to ship the API on Friday.",
        },
    )
    assert ingest.status_code == 200
    body = ingest.json()
    assert body["portal_updated"] is True
    assert body["source_page"].startswith("vault/wiki/sources/transcripts/")

    query = client.post(
        "/api/query", json={"workspace": "demo", "question": "What did we decide to ship?"}
    )
    assert query.status_code == 200
    citations = query.json()["citations"]
    assert len(citations) >= 1
    assert any("transcripts" in c["page"] for c in citations)


def test_query_without_matches_has_no_citations(client):
    client.post("/api/workspaces", json={"name": "demo"})
    r = client.post("/api/query", json={"workspace": "demo", "question": "nonexistent topic xyzzy"})
    assert r.status_code == 200
    assert r.json()["citations"] == []


def test_plan_routine_is_safe(client):
    # Story: a routine request is planned as safe, no approval required.
    r = client.post("/api/plan", json={"request": "summarise the onboarding docs"})
    assert r.status_code == 200
    assert r.json()["risk"] == "safe"
    assert r.json()["requires_approval"] is False


def test_plan_consequential_requires_approval(client):
    # Story: a destructive request is flagged risky and needs approval (P8).
    r = client.post("/api/plan", json={"request": "delete the onboarding spec"})
    assert r.status_code == 200
    assert r.json()["risk"] == "risky"
    assert r.json()["requires_approval"] is True
    assert len(r.json()["steps"]) >= 1


def test_lint_reports_on_a_fresh_workspace(client):
    client.post("/api/workspaces", json={"name": "demo"})
    r = client.get("/api/lint", params={"workspace": "demo"})
    assert r.status_code == 200
    body = r.json()
    assert body["workspace"] == "demo"
    assert isinstance(body["findings"], list)
    assert isinstance(body["ok"], bool)


def test_spec_read_page_and_missing(client):
    client.post("/api/workspaces", json={"name": "demo"})
    ok = client.get("/api/spec", params={"workspace": "demo", "path": "vault/wiki/portal.md"})
    assert ok.status_code == 200
    assert "Portal" in ok.json()["content"]

    missing = client.get("/api/spec", params={"workspace": "demo", "path": "vault/wiki/nope.md"})
    assert missing.status_code == 404
