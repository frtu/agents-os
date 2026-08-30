"""API tests for the REST capability surface (feature 001 user stories).

Covers the getting-started tour: health, workspace lifecycle, ingest → cited
query, plan-first governance, lint, and reading a page. Each hits the FastAPI app
over HTTP via TestClient, exactly as an external caller would.
"""

from __future__ import annotations

from app import capabilities


def test_health_liveness(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_workspace_create_list_inspect(client):
    # Story: a user creates a workspace, lists it, and inspects it.
    # spec 011 AC-9/AC-17: creating a workspace is approval-tier, and at cold start every gated
    # operation asks — so REST answers 409 with the assessment plus the card that answers it.
    created = client.post("/api/workspaces", json={"name": "demo"})
    assert created.status_code == 409
    risk = created.json()
    assert risk["gating"]["name"] == "create_workspace"
    assert risk["gating"]["target"] == "demo"
    assert 1 <= risk["gating"]["score"] <= 5
    assert risk["decision"] == "ask"

    # spec 011 FR-25/AC-15: the ask is the existing 008 card on the existing route, and approving
    # resumes the paused operation to completion.
    answered = client.post(
        "/api/chat/interaction",
        json={
            "conversation_id": risk["conversation_id"],
            "interaction_id": risk["interaction_id"],
            "choice": "approve",
        },
    )
    assert answered.status_code == 200
    assert answered.json()["executed"] is True

    listed = client.get("/api/workspaces")
    assert listed.status_code == 200
    assert "demo" in listed.json()["workspaces"]
    assert listed.json()["default"] == "_default_"

    info = client.get("/api/workspaces/demo")
    assert info.status_code == 200
    assert info.json()["name"] == "demo"


def test_ingest_then_cited_query(client):
    # Story: ingest a source, then ask a question and get citations back.
    capabilities.create_workspace("demo")
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
    capabilities.create_workspace("demo")
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
    # Story: an approval-tier action is flagged risky and needs approval (P8).
    # Spec 009 FR-3: the tier comes from the resolved capability's declared effect,
    # not from risky-sounding words in the request.
    r = client.post("/api/plan", json={"request": "create a workspace named archive"})
    assert r.status_code == 200
    body = r.json()
    assert body["risk"] == "risky"
    assert body["requires_approval"] is True
    assert body["capability"] == "create_workspace"
    assert body["effect_tier"] == "approval"
    assert body["reversibility"]
    assert len(body["steps"]) >= 1


def test_lint_reports_on_a_fresh_workspace(client):
    capabilities.create_workspace("demo")
    r = client.get("/api/lint", params={"workspace": "demo"})
    assert r.status_code == 200
    body = r.json()
    assert body["workspace"] == "demo"
    assert isinstance(body["findings"], list)
    assert isinstance(body["ok"], bool)


def test_spec_read_page_and_missing(client):
    capabilities.create_workspace("demo")
    ok = client.get("/api/spec", params={"workspace": "demo", "path": "vault/wiki/portal.md"})
    assert ok.status_code == 200
    assert "Portal" in ok.json()["content"]

    missing = client.get("/api/spec", params={"workspace": "demo", "path": "vault/wiki/nope.md"})
    assert missing.status_code == 404
