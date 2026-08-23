"""API tests for the Product Owner Chat surface (feature 002 user stories).

Each test maps to an acceptance criterion in
``specs/002-assistant-chat/spec.md``. Routine-answer tests use the
``offline_agent`` fixture to force the deterministic (no-LLM) path so the suite
is reproducible in CI; the live agent runtime is covered by a separate,
opt-in test at the bottom.
"""

from __future__ import annotations

import json
import os

import pytest


def sse_events(text: str) -> list[dict]:
    """Parse an SSE body into the list of JSON payloads it carried."""
    return [json.loads(line[6:]) for line in text.splitlines() if line.startswith("data: ")]


def _ingest(client, workspace, title, content, provenance="notes"):
    client.post("/api/workspaces", json={"name": workspace})
    return client.post(
        "/api/ingest",
        json={"workspace": workspace, "title": title, "provenance": provenance, "content": content},
    )


def test_ac1_chat_reply_with_citation(client, offline_agent):
    # AC-1: a knowledge question yields a coherent reply with >=1 citation.
    _ingest(client, "demo", "Risk engine", "The risk engine decides if work is safe, risky, or rejected.")
    r = client.post("/api/chat", json={"workspace": "demo", "message": "what does the risk engine decide?"})
    assert r.status_code == 200
    body = r.json()
    assert body["reply"]
    assert body["conversation_id"]
    assert len(body["citations"]) >= 1


def test_ac2_followup_resumes_conversation(client, offline_agent, isolated_workspace_root):
    # AC-2 / FR-3: resending the returned conversation_id continues one thread.
    first = client.post("/api/chat", json={"message": "first question"}).json()
    cid = first["conversation_id"]
    second = client.post("/api/chat", json={"message": "second question", "conversation_id": cid})
    assert second.status_code == 200
    assert second.json()["conversation_id"] == cid

    # The single session file accumulated both turns (durable, append-only).
    from app import conversation, vault

    conv = conversation.load(vault.resolve_workspace(None), cid)
    assert conv is not None
    roles = [t.role for t in conv.turns]
    assert roles.count("user") == 2
    assert roles.count("assistant") == 2


def test_ac3_consequential_returns_pending_plan_no_mutation(client, offline_agent, isolated_workspace_root):
    # AC-3 / FR-5: consequential request returns a plan and mutates nothing.
    r = client.post("/api/chat", json={"message": "delete the onboarding spec"})
    assert r.status_code == 200
    body = r.json()
    assert body["pending_plan"] is not None
    assert body["pending_plan"]["requires_approval"] is True
    assert body["executed"] is False

    # No wiki page was created by this turn. (portal/log/tbd are scaffold control files,
    # spec 03-workspace §5 / spec 007 FR-14 — not created by this turn.)
    wiki = isolated_workspace_root / "_default_" / "vault" / "wiki"
    pages = [p for p in wiki.rglob("*.md") if p.name not in ("portal.md", "log.md", "tbd.md")]
    assert pages == []


def test_ac4_routine_answers_without_plan(client, offline_agent):
    # AC-4 / FR-6: a routine question is answered directly, no forced plan.
    r = client.post("/api/chat", json={"message": "what is this project about?"})
    assert r.status_code == 200
    assert r.json()["pending_plan"] is None


def test_ac5_session_record_exists(client, offline_agent, isolated_workspace_root):
    # AC-5 / FR-7: a sessions/ record exists after any turn.
    cid = client.post("/api/chat", json={"message": "hello"}).json()["conversation_id"]
    session_file = isolated_workspace_root / "_default_" / "sessions" / f"{cid}.md"
    assert session_file.is_file()
    assert "## [" in session_file.read_text(encoding="utf-8")


def test_ac6_stream_and_full_converge(client, offline_agent):
    # AC-6 / FR-4: streamed and full-reply modes converge to identical content.
    # A consequential turn is fully deterministic (no LLM), so both surfaces match.
    payload = {"message": "delete the temporary notes"}
    full = client.post("/api/chat", json=payload).json()

    streamed = client.post("/api/chat/stream", json=payload)
    assert streamed.status_code == 200
    events = sse_events(streamed.text)
    assert len(events) >= 1
    assert events[-1]["done"] is True
    assert events[-1]["reply"] == full["reply"]
    assert events[-1]["pending_plan"] is not None


def test_ac8_no_raw_writes_or_log_edits(client, offline_agent, isolated_workspace_root):
    # AC-8 / FR-11: a chat turn never writes raw/ nor edits log.md.
    client.post("/api/workspaces", json={"name": "demo"})
    log_path = isolated_workspace_root / "demo" / "vault" / "wiki" / "log.md"
    log_before = log_path.read_text(encoding="utf-8")

    client.post("/api/chat", json={"workspace": "demo", "message": "tell me about the project"})

    raw_files = [p for p in (isolated_workspace_root / "demo" / "vault" / "raw").rglob("*") if p.is_file()]
    assert raw_files == []
    assert log_path.read_text(encoding="utf-8") == log_before


def test_ac9_default_workspace_used_when_omitted(client, offline_agent, isolated_workspace_root):
    # AC-9 / FR-10: no selector -> the default workspace is used and scaffolded.
    r = client.post("/api/chat", json={"message": "hi"})
    assert r.status_code == 200
    assert r.json()["workspace"] == "_default_"
    assert (isolated_workspace_root / "_default_" / "vault" / "wiki").is_dir()


def test_ac9_missing_named_workspace_is_reported_not_created(client, offline_agent, isolated_workspace_root):
    # AC-9 / FR-10: a named workspace that does not exist is reported, never created.
    r = client.post("/api/chat", json={"workspace": "ghost", "message": "hi"})
    assert r.status_code == 400
    assert not (isolated_workspace_root / "ghost").exists()


def test_ac9_explicit_create_workspace_via_approval(client, offline_agent, isolated_workspace_root):
    # AC-9 / D1: "create workspace X" is consequential; approval creates it.
    first = client.post("/api/chat", json={"message": "create a workspace named proj1"}).json()
    assert first["pending_plan"] is not None
    assert first["executed"] is False
    assert not (isolated_workspace_root / "proj1").exists()

    cid = first["conversation_id"]
    approved = client.post(
        "/api/chat", json={"message": "approve", "conversation_id": cid, "approve": True}
    ).json()
    assert approved["executed"] is True
    assert (isolated_workspace_root / "proj1" / "vault" / "wiki").is_dir()


def test_ac10_resume_after_restart_then_approve(client, offline_agent, isolated_workspace_root):
    # AC-10 / FR-13: a pending plan survives a restart and is still approvable.
    from fastapi.testclient import TestClient

    from app import conversation, vault
    from app.api import app

    first = client.post("/api/chat", json={"message": "create a workspace named survivor"}).json()
    cid = first["conversation_id"]

    # The pending plan is durable on disk, independent of any in-memory state.
    conv = conversation.load(vault.resolve_workspace(None), cid)
    assert conv is not None and conv.pending_plan is not None

    # Simulate a service restart with a brand-new client over the same disk.
    fresh = TestClient(app)
    approved = fresh.post(
        "/api/chat", json={"message": "approve", "conversation_id": cid, "approve": True}
    ).json()
    assert approved["executed"] is True
    assert (isolated_workspace_root / "survivor" / "vault" / "wiki").is_dir()


def test_ac11_status_unknown_conversation_absent_and_not_running(client, isolated_workspace_root):
    # AC-11 / FR-14: an unknown id is neither running nor existing, and probing creates nothing.
    r = client.get("/api/chat/status", params={"conversation_id": "does-not-exist", "workspace": "demo"})
    assert r.status_code == 200
    body = r.json()
    assert body["conversation_id"] == "does-not-exist"
    assert body["running"] is False and body["exists"] is False
    # The probe is read-only: it must not have written a session file for that id.
    assert not (isolated_workspace_root / "demo" / "sessions" / "does-not-exist.md").exists()


def test_ac11_status_after_completed_turn_not_running_but_exists(client, offline_agent, isolated_workspace_root):
    # AC-11 / FR-14: once a turn finishes, the same conversation exists but is not running,
    # and the status probe neither adds a turn nor mutates the record.
    cid = client.post("/api/chat", json={"message": "hello there"}).json()["conversation_id"]
    session_file = isolated_workspace_root / "_default_" / "sessions" / f"{cid}.md"
    before = session_file.read_text(encoding="utf-8")

    r = client.get("/api/chat/status", params={"conversation_id": cid})
    assert r.status_code == 200
    body = r.json()
    assert body["exists"] is True and body["running"] is False
    # Read-only: the probe did not append a turn.
    assert session_file.read_text(encoding="utf-8") == before


def test_fr14_running_registry_counts_and_clears():
    # FR-14: the in-flight registry is a counter (tolerates concurrent turns) that clears fully.
    from app import capabilities as caps

    cid = "reg-count-1"
    assert caps.is_running(cid) is False
    caps._mark_running(cid)
    caps._mark_running(cid)  # a second concurrent turn on the same conversation
    assert caps.is_running(cid) is True
    caps._unmark_running(cid)
    assert caps.is_running(cid) is True  # one turn still in flight
    caps._unmark_running(cid)
    assert caps.is_running(cid) is False
    # Over-unmarking never drives the counter negative or leaves a stale entry.
    caps._unmark_running(cid)
    assert caps.is_running(cid) is False


def test_fr14_ask_stream_marks_running_during_turn_and_clears(monkeypatch, isolated_workspace_root):
    # AC-11 / FR-14: a conversation reads as running *while* its turn streams, then not-running
    # once the generator is exhausted. Driving ask_stream directly keeps this deterministic.
    import asyncio

    from app import agent, capabilities as caps

    cid = "inflight-123456"
    observed: dict[str, bool] = {}

    async def _run_stream(system_prompt, message, selector, wpath, sid, citations, *_a, **_k):
        observed["mid"] = caps.is_running(cid)  # sampled while the turn is being processed
        yield ("partial…", sid)
        yield ("final reply", sid)

    monkeypatch.setattr(agent, "run_stream", _run_stream)

    async def _drive():
        out = []
        async for d in caps.ask_stream(None, "a routine question", cid, False):
            out.append(d)
        return out

    deltas = asyncio.run(_drive())
    assert observed["mid"] is True          # running during the turn (FR-14)
    assert caps.is_running(cid) is False     # cleared once the turn ends
    assert deltas[-1].done is True and deltas[-1].conversation_id == cid


def test_fr14_running_cleared_even_when_turn_errors(monkeypatch, isolated_workspace_root):
    # FR-14: an unexpected error mid-turn must still clear the running flag (finally), so a
    # conversation can never be stuck "running" after a failure.
    import asyncio

    import pytest as _pytest

    from app import agent, capabilities as caps

    cid = "boom-654321"

    async def _boom(system_prompt, message, selector, wpath, sid, citations, *_a, **_k):
        raise RuntimeError("kaboom")
        yield  # pragma: no cover — marks this an async generator

    monkeypatch.setattr(agent, "run_stream", _boom)

    async def _drive():
        async for _ in caps.ask_stream(None, "trigger an error", cid, False):
            pass

    with _pytest.raises(RuntimeError):
        asyncio.run(_drive())
    assert caps.is_running(cid) is False


def test_ac7_capability_parity_between_rest_and_chat(client):
    # AC-7 / P9: every capability the agent can invoke is also a REST route.
    from app.api import app

    paths = {getattr(r, "path", None) for r in app.routes}
    # Agent tools (query, spec_read, plan) + chat-driven create_workspace.
    assert "/api/query" in paths  # query tool
    assert "/api/spec" in paths  # spec_read tool
    assert "/api/plan" in paths  # plan tool
    assert "/api/workspaces" in paths  # create_workspace (approval flow)
    # And the chat surface itself is present in both modes.
    assert "/api/chat" in paths
    assert "/api/chat/stream" in paths
    assert "/api/chat/status" in paths  # FR-14 running-status probe


@pytest.mark.skipif(
    not os.getenv("LEADER_LIVE_AGENT"),
    reason="requires the claude CLI / credentials; set LEADER_LIVE_AGENT=1 to run",
)
def test_live_agent_cited_answer(client):
    # Exercises the real agent tool adapter end-to-end (opt-in).
    _ingest(client, "demo", "Risk engine", "The risk engine decides if work is safe, risky, or rejected.")
    r = client.post(
        "/api/chat",
        json={"workspace": "demo", "message": "According to the workspace, what does the risk engine decide? Cite the page."},
    )
    assert r.status_code == 200
    assert r.json()["citations"]
