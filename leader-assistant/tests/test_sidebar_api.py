"""Tests for the sidebar's backing REST endpoints (feature 004-assistant-sidebar).

Drives the FastAPI app over HTTP (``TestClient``), one test per user story, offline
and deterministic on a throwaway workspace (see ``conftest.py``). Covers the three
new capabilities the sidebar surfaces — browse ``vault/wiki/``, upload into
``vault/raw/`` + ingest, and list/resume conversations — plus the amended P2
invariant that uploads (a *human* action) reach ``vault/raw/`` while the ingestion
pipeline still never mutates it.
"""

from __future__ import annotations

import pathlib


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


def test_wiki_tree_excludes_readme_and_prunes_readme_only_folders(client, isolated_workspace_root):
    # FR-10a: README.md is never listed; a folder whose subtree holds only README.md is empty
    # after that exclusion → pruned. A sibling folder with real content is kept, but its own
    # README.md is still not listed.
    v = _make_workspace(client)
    wiki = isolated_workspace_root / v / "vault" / "wiki"
    (wiki / "concepts" / "patterns").mkdir(parents=True, exist_ok=True)
    (wiki / "concepts" / "patterns" / "README.md").write_text("# Patterns\n")  # README-only → prune
    (wiki / "projects").mkdir(parents=True, exist_ok=True)
    (wiki / "projects" / "README.md").write_text("# Projects\n")  # excluded from listing
    (wiki / "projects" / "alpha.md").write_text("# Alpha\nreal content\n")  # real → keep folder

    def flat(nodes):
        for n in nodes:
            yield n["path"]
            yield from flat(n["children"])

    paths = set(flat(client.get("/api/wiki-tree", params={"workspace": v}).json()["nodes"]))
    assert "concepts" not in paths and "concepts/patterns" not in paths  # README-only subtree pruned
    assert "projects" in paths and "projects/alpha.md" in paths  # kept for real content
    assert "projects/README.md" not in paths  # README.md is never listed (FR-10a)


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


def test_session_detail_title_matches_list_fr33(client, offline_agent):
    # spec 004 FR-33: the detail endpoint returns the SAME derived title as the Sessions list, so the
    # chat-panel header and the left menu label come from one backend source (P9 parity).
    v = _make_workspace(client)
    posted = client.post("/api/chat", json={"workspace": v, "message": "what did we decide?"})
    cid = posted.json()["conversation_id"]

    summary = next(
        c for c in client.get("/api/sessions", params={"workspace": v}).json()["conversations"]
        if c["conversation_id"] == cid
    )
    detail = client.get(f"/api/sessions/{cid}", params={"workspace": v}).json()
    assert detail["title"] == summary["title"]
    assert detail["title"]  # non-empty for a real turn


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


def test_workspace_picker_lists_others_and_none(monkeypatch):
    # FR-4: clicking the box reveals a picker of all OTHER workspaces (active excluded);
    # when there are no others it degrades to the non-selectable `<none>` sentinel.
    from app import ui

    monkeypatch.setattr(ui, "_list_workspaces", lambda: {"workspaces": ["alpha", "beta", "gamma"]})
    picker = ui._on_focus("beta")
    assert picker["visible"] is True
    assert picker["choices"] == ["alpha", "gamma"]  # active (beta) excluded

    # A lone workspace has no others → the picker shows `<none>`.
    monkeypatch.setattr(ui, "_list_workspaces", lambda: {"workspaces": ["solo"]})
    only = ui._on_focus("solo")
    assert only["choices"] == ["<none>"] and only["visible"] is True


def test_workspace_typing_narrows_and_toggles_create(monkeypatch):
    # FR-4/FR-5: typing narrows the picker to matching OTHER workspaces, and the Create
    # (+) button is shown ONLY when the text differs from the original (active) name.
    from app import ui

    monkeypatch.setattr(ui, "_list_workspaces", lambda: {"workspaces": ["alpha", "beta", "bravo"]})

    # Typing "br" while active=alpha → narrows to bravo, Create shown (name changed).
    picker, create = ui._suggest("br", "alpha")
    assert picker["choices"] == ["bravo"]
    assert create["visible"] is True

    # Text equal to the active name → Create hidden (unchanged from original).
    _, create_same = ui._suggest("alpha", "alpha")
    assert create_same["visible"] is False

    # Empty text → Create hidden, picker offers all others.
    picker_empty, create_empty = ui._suggest("", "alpha")
    assert create_empty["visible"] is False
    assert picker_empty["choices"] == ["beta", "bravo"]


def test_workspace_pick_switches_active_and_ignores_none(monkeypatch):
    # FR-4/FR-7: choosing a real workspace switches active + updates the `Active` indicator;
    # the `<none>` sentinel is a no-op.
    from app import ui

    monkeypatch.setattr(ui, "_wiki_html", lambda v: f"<em>{v}</em>")
    box2, active2, _p, _w, status2, create2 = ui._pick_workspace("beta", "alpha")
    assert box2 == "beta" and active2 == "beta"
    assert status2 == "**Active:** beta" and create2["visible"] is False

    # The sentinel returns bare no-op updates and never names a new active workspace.
    box, active, _p2, _w2, _s2, _c2 = ui._pick_workspace("<none>", "alpha")
    assert box.get("__type__") == "update" and "value" not in box
    assert active.get("__type__") == "update"


def test_initial_selects_default_and_hides_create(monkeypatch):
    # FR-3/FR-5/FR-7: on load the box is pre-filled with the active workspace, the picker lists
    # the others (hidden until focus), the `Active` indicator names it, and Create starts hidden.
    from app import ui

    monkeypatch.setattr(ui, "_wiki_html", lambda v: f"<em>{v}</em>")
    monkeypatch.setattr(ui, "_list_workspaces", lambda: {"workspaces": ["alpha", "beta"], "default": "beta"})
    box, active, picker, _wiki, status, create, *_ = ui._initial()
    assert box == "beta" and active == "beta" and status == "**Active:** beta"
    assert create["visible"] is False
    assert picker["visible"] is False and picker["choices"] == ["alpha"]  # others, hidden

    # Default not in the list → fall back to the first workspace.
    monkeypatch.setattr(ui, "_list_workspaces", lambda: {"workspaces": ["alpha"], "default": "gone"})
    _b, active2, _p, _w, _s, _c, *_ = ui._initial()
    assert active2 == "alpha"

    # No workspaces at all → no active, empty box, "nothing yet" indicator.
    monkeypatch.setattr(ui, "_list_workspaces", lambda: {"workspaces": [], "default": "x"})
    box3, active3, _p3, _w3, status3, _c3, *_ = ui._initial()
    assert box3 == "" and active3 is None and "No workspaces yet" in status3


def test_initial_surfaces_api_error(monkeypatch):
    # FR-23: if the API is unreachable at load, the sidebar shows the error rather than crashing.
    from app import ui

    def boom():
        raise RuntimeError("connection refused")

    monkeypatch.setattr(ui, "_list_workspaces", boom)
    box, active, _picker, wiki, status, create, *_ = ui._initial()
    assert box == "" and active is None
    assert "API not reachable" in wiki and "API error" in status
    assert create["visible"] is False


def test_refresh_falls_back_when_active_removed_elsewhere(monkeypatch):
    # FR-5: Refresh re-fetches from the backend so changes made ELSEWHERE are reflected. If the
    # active workspace was deleted elsewhere it falls back to the first remaining one.
    from app import ui

    monkeypatch.setattr(ui, "_wiki_html", lambda v: f"<em>{v}</em>")

    # beta was removed elsewhere; the list no longer contains it → fall back to alpha.
    monkeypatch.setattr(ui, "_list_workspaces", lambda: {"workspaces": ["alpha", "gamma"]})
    box, active, picker, _w, status, create = ui._refresh("beta")
    assert active == "alpha" and box == "alpha" and status == "**Active:** alpha"
    assert picker["choices"] == ["gamma"] and picker["visible"] is False
    assert create["visible"] is False

    # Active still present → preserved.
    monkeypatch.setattr(ui, "_list_workspaces", lambda: {"workspaces": ["alpha", "beta"]})
    _b, active2, _p, _w2, _s, _c = ui._refresh("beta")
    assert active2 == "beta"


def test_refresh_surfaces_api_error(monkeypatch):
    # FR-23: a backend failure during Refresh is surfaced, not swallowed.
    from app import ui

    def boom():
        raise RuntimeError("down")

    monkeypatch.setattr(ui, "_list_workspaces", boom)
    _b, active, _p, _w, status, create = ui._refresh("beta")
    assert active == "beta"  # keep the current selection on error
    assert status.startswith("Could not list workspaces")
    assert create["visible"] is False


def test_create_vault_action_validates_and_creates(monkeypatch):
    # FR-6: Create makes the typed name active via POST /api/workspaces; empty/invalid names
    # surface a validation error (not a silent no-op) and keep Create visible to retry.
    from app import ui

    monkeypatch.setattr(ui, "_wiki_html", lambda v: f"<em>{v}</em>")

    # Empty name → validation error, Create stays visible.
    _b, active, _p, _w, status, create = ui._create_vault_action("   ", "alpha")
    assert active == "alpha" and "Enter a workspace name" in status
    assert create["visible"] is True

    # Success → the new name is created, becomes active, Create hidden.
    created = {}
    monkeypatch.setattr(ui, "_create_workspace", lambda n: created.setdefault("name", n))
    box, active2, _p2, _w2, status2, create2 = ui._create_vault_action("newspace", "alpha")
    assert created["name"] == "newspace"
    assert box == "newspace" and active2 == "newspace" and status2 == "**Active:** newspace"
    assert create2["visible"] is False

    # Backend error → surfaced, active unchanged, Create stays visible to retry.
    def boom(_n):
        raise RuntimeError("name collision")

    monkeypatch.setattr(ui, "_create_workspace", boom)
    _b3, active3, _p3, _w3, status3, create3 = ui._create_vault_action("dup", "alpha")
    assert active3 == "alpha" and "Could not create workspace" in status3
    assert create3["visible"] is True


def test_render_nodes_escapes_untrusted_names():
    # Security: a wiki folder/file name is HTML-escaped in BOTH the visible label and the
    # data-tip tooltip attribute, so a crafted name cannot inject markup into the panel.
    from app import ui

    evil = '<img src=x onerror=alert(1)>"'
    out = ui._render_nodes([{"name": evil, "type": "dir", "children": [
        {"name": evil, "type": "file"}]}])
    assert "<img src=x" not in out  # raw markup never emitted
    assert "&lt;img src=x onerror=alert(1)&gt;" in out  # escaped label
    assert "&quot;" in out  # the quote is escaped inside data-tip


def test_wiki_html_empty_and_error_states(monkeypatch):
    # FR-23: the wiki browser degrades gracefully — no selection, load failure, and an empty
    # tree each show a message instead of failing silently.
    from app import ui

    assert "No workspace selected." in ui._wiki_html(None)

    def boom(_w):
        raise RuntimeError("nope")

    monkeypatch.setattr(ui, "_get_wiki_tree", boom)
    assert "Could not load wiki tree" in ui._wiki_html("demo")

    monkeypatch.setattr(ui, "_get_wiki_tree", lambda _w: {"nodes": []})
    assert "wiki/ is empty." in ui._wiki_html("demo")


def test_workspace_status_renamed_to_active():
    # FR-7: the indicator is labeled `Active` (not `Active vault`).
    from app import ui

    assert ui._status("demo") == "**Active:** demo"
    assert "Active vault" not in ui._status("demo")


def test_workspace_panel_layout_labels():
    # FR-2/FR-2a/FR-3/FR-5: panel titled "Area (Workspaces)", the box placeholder is
    # "workspace name", and the Create (+) button starts hidden (name unchanged).
    from app import ui

    demo = ui.build_demo()
    labels = [getattr(c, "label", None) for c in demo.blocks.values()]
    assert "Area (Workspaces)" in labels  # renamed from "Vault"/"Workspaces" (FR-2)
    placeholders = [getattr(c, "placeholder", None) for c in demo.blocks.values()]
    assert "workspace name" in placeholders
    create = next(c for c in demo.blocks.values() if getattr(c, "elem_id", None) == "create-vault")
    assert create.visible is False


def test_sidebar_panels_default_expansion_and_titles():
    # FR-2/FR-2a: three panels titled Area (Workspaces) / Knowledge / Sessions; the two
    # advanced panels start collapsed, Sessions starts expanded.
    from app import ui

    demo = ui.build_demo()
    by_id = {getattr(c, "elem_id", None): c for c in demo.blocks.values()}
    area, knowledge, sessions = by_id["area-panel"], by_id["knowledge-panel"], by_id["sessions-panel"]
    assert (area.label, knowledge.label, sessions.label) == (
        "Area (Workspaces)", "Knowledge", "Sessions",
    )
    assert area.open is False  # advanced surface, collapsed by default
    assert knowledge.open is False
    assert sessions.open is True  # primary surface, expanded


def test_panel_tooltips_wired_with_bold_markdown():
    # FR-2b: each panel header carries its purpose tooltip; the Area tooltip keeps `**bold**`
    # markdown and the bridge converts it to <b> at render time.
    from app import ui

    js = ui._PANEL_TIP_JS
    assert "'area-panel': 'Manage multiple **separated** and **isolated** area and interests'" in js
    assert "'knowledge-panel': 'Accumulated knowledge in this area'" in js
    assert "'sessions-panel': 'All previous cases (conversations)'" in js
    # `**x**` -> <b>x</b> conversion (escaped backslashes in the Python source string).
    assert "\\*\\*(.+?)\\*\\*" in js and "<b>$1</b>" in js
    assert ".panel-tip {" in ui._CSS


def test_session_detail_missing_is_404(client):
    v = _make_workspace(client)
    assert client.get("/api/sessions/nope", params={"workspace": v}).status_code == 404


def test_sessions_render_as_clickable_text_not_buttons(monkeypatch):
    # FR-19/FR-25: each conversation renders as clickable text (a .session div with data-cid),
    # prefixed with a 💬 discussion icon — NOT a per-conversation <button> — grouped under
    # collapsible <details open> relative-date sections. Exercises the pure UI renderer on a
    # frozen "today" so the Today/Older headers are deterministic (no server / clock needed).
    from datetime import date

    from app import ui

    sample = [
        {"conversation_id": "c-today", "created": date.today().isoformat(),
         "title": "Ship it", "turn_count": 2},
        {"conversation_id": "c-old", "created": "2020-01-01",
         "title": "Retro", "turn_count": 1},
    ]
    monkeypatch.setattr(ui, "_get_sessions", lambda _v: {"conversations": sample})
    out = ui._sessions_html("demo")

    # Collapsible date sections, expanded by default, in canonical order (Today before Older).
    assert "<details open><summary>Today</summary>" in out
    assert "<details open><summary>Older</summary>" in out
    assert out.index("Today") < out.index("Older")

    # Each conversation is a clickable-text row carrying its id, with a 💬 icon and label — and
    # the whole rendered block contains NO <button> (selection, not an action; the New-conversation
    # button and hidden trigger are separate Gradio components, not part of this HTML).
    assert '<div class=\'session\' data-cid="c-today"' in out
    assert '<div class=\'session\' data-cid="c-old"' in out
    assert "<span class='ico'>💬</span>" in out
    assert "<span class='label'>Ship it · 2 turn(s)</span>" in out
    assert "<button" not in out and "</button>" not in out

    # The full label is exposed as a native title tooltip on the row.
    assert 'title="Ship it · 2 turn(s)"' in out


def test_sessions_render_escapes_untrusted_text(monkeypatch):
    # Security: a conversation title is HTML-escaped so it cannot inject markup into the panel.
    from datetime import date

    from app import ui

    sample = [{"conversation_id": "c1", "created": date.today().isoformat(),
               "title": "<img src=x onerror=alert(1)>", "turn_count": 1}]
    monkeypatch.setattr(ui, "_get_sessions", lambda _v: {"conversations": sample})
    out = ui._sessions_html("demo")
    assert "<img src=x" not in out
    assert "&lt;img src=x onerror=alert(1)&gt;" in out


def test_sessions_empty_state(monkeypatch):
    # FR-23: an empty Sessions list shows a "nothing yet" message rather than failing.
    from app import ui

    monkeypatch.setattr(ui, "_get_sessions", lambda _v: {"conversations": []})
    assert "No conversations yet." in ui._sessions_html("demo")
    # No active workspace short-circuits to the same empty state.
    assert "No conversations yet." in ui._sessions_html(None)


def test_session_click_bridge_is_wired():
    # FR-19/FR-20: clicking session text (not a button) resumes the conversation. A delegated
    # listener stashes the clicked id in window.__lastCid and clicks the hidden #session-go
    # trigger, whose js shim injects that id as _open_session's argument. Assert the bridge parts.
    from app import ui

    # Delegated listener targets the rendered rows, records the id, and fires the hidden trigger.
    assert ".session-tree [data-cid]" in ui._SESSION_JS
    assert "t.getAttribute('data-cid')" in ui._SESSION_JS
    assert "window.__lastCid = cid" in ui._SESSION_JS
    assert "document.getElementById('session-go')" in ui._SESSION_JS
    # spec 004 FR-32: selecting a session also updates ?conversation in place (silent, no reload).
    assert "searchParams.set('conversation'" in ui._SESSION_JS
    assert "history.replaceState" in ui._SESSION_JS
    # The js shim replaces the placeholder arg with the clicked id, passing the vault through.
    assert ui._SESSION_PICK_JS == "(pick, vault) => [window.__lastCid || '', vault]"
    # The bridge components stay in the DOM (CSS-hidden), because Gradio drops visible=False ones.
    assert ".session-bridge { display: none !important; }" in ui._CSS
    # And the sessions panel is styled as a text tree with a 💬-icon column.
    assert ".session-tree" in ui._CSS and ".session-tree .session .ico" in ui._CSS


def test_open_session_resumes_and_strips_nonce(monkeypatch):
    # FR-20: _open_session loads a thread's messages and returns the conversation id to continue
    # it. The bridge may append a `|<nonce>` suffix (repeat-click de-duplication); it is stripped.
    from app import ui

    monkeypatch.setattr(
        ui, "_get_session_detail",
        lambda _v, _c: {"messages": [{"role": "user", "text": "hi"},
                                     {"role": "assistant", "text": "yo"}]},
    )
    msgs, cid = ui._open_session("abc123", "demo")
    assert cid == "abc123"
    assert [m["role"] for m in msgs] == ["user", "assistant"]
    assert [m["content"] for m in msgs] == ["hi", "yo"]

    # A `<cid>|<nonce>` value is normalised back to the bare id.
    _, cid2 = ui._open_session("abc123|1700000000000", "demo")
    assert cid2 == "abc123"

    # An empty selection is a no-op (no conversation resumed).
    _, cid3 = ui._open_session("", "demo")
    assert cid3 is None


def test_conv_title_md_uses_backend_title_fr33(monkeypatch):
    # spec 004 FR-33: the chat-panel header label is the detail endpoint's derived title.
    from app import ui

    monkeypatch.setattr(ui, "_get_session_detail", lambda v, c: {"title": "Ship the release"})
    assert ui._conv_title_md("abc123", "demo") == "### Ship the release"


def test_conv_title_md_degrades_to_new_conversation_fr33(monkeypatch):
    # spec 004 FR-33: no id, a titleless thread, or a load error all fall back to "New conversation".
    from app import ui

    assert ui._conv_title_md(None, "demo") == "### New conversation"
    monkeypatch.setattr(ui, "_get_session_detail", lambda v, c: {"title": ""})
    assert ui._conv_title_md("abc123", "demo") == "### New conversation"

    def boom(v, c):
        raise RuntimeError("no such session")

    monkeypatch.setattr(ui, "_get_session_detail", boom)
    assert ui._conv_title_md("ghost", "demo") == "### New conversation"


def test_ui_wires_conversation_header_and_copy_fr33_fr34():
    # spec 004 FR-33/FR-34: a titled header row sits atop the chat panel with a copy-id control;
    # copy reads the id from the #conv-url mirror (DOM source of truth) and no-ops when empty.
    from app import ui

    src = pathlib.Path(ui.__file__).read_text()
    assert 'elem_id="conv-header"' in src
    assert 'elem_id="conv-title"' in src
    assert 'elem_id="copy-conv-id"' in src        # copy button the JS labels "Copied ✓"
    assert "_COPY_CONV_JS" in src
    assert "navigator.clipboard.writeText(cid)" in ui._COPY_CONV_JS
    assert "#conv-url textarea" in ui._COPY_CONV_JS  # reads the same mirror as the sync JS
    assert "if (!cid) return" in ui._COPY_CONV_JS    # graceful no-op with no active id


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
