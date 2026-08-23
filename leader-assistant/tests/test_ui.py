"""Tests for the web UI surface (feature 003-assistant-ui).

Covers the route wiring the spec fixes — UI at `/`, Swagger at `/api/`, REST
endpoints still under `/api/<resource>` — and the parity invariant that the UI is
a pure presentation layer: `app/ui.py` reaches the backend only over HTTP and
never imports the capability/vault layer (spec 003 FR-3/FR-10/AC-8, P9).
"""

from __future__ import annotations

import ast
import pathlib
import types

from app import ui

UI_PATH = pathlib.Path(__file__).resolve().parent.parent / "app" / "ui.py"


def _req(**params):
    """A minimal stand-in for gr.Request exposing dict-able query_params."""
    return types.SimpleNamespace(query_params=params)


def test_root_serves_web_ui(client):
    # AC-1: the root path is the startup surface (Gradio UI), not an API redirect.
    r = client.get("/")
    assert r.status_code == 200
    assert "gradio" in r.text.lower()


def test_swagger_relocated_to_api(client):
    # AC-2: Swagger UI is served at /api/ ...
    docs = client.get("/api")
    assert docs.status_code == 200
    assert "swagger" in docs.text.lower() or "openapi" in docs.text.lower()
    assert client.get("/openapi.json").status_code == 200


def test_api_endpoints_still_resolve(client):
    # AC-2: ... and the /api/<resource> endpoints are not shadowed by the docs route.
    assert client.get("/api/workspaces").status_code == 200
    created = client.post("/api/workspaces", json={"name": "demo"})
    assert created.status_code == 200
    # chat endpoint exists (unprocessable without a body proves it is routed, not 404)
    assert client.post("/api/chat", json={}).status_code == 422


def test_ui_module_imports_no_backend_layer():
    # AC-8: the UI must not import app.capabilities / app.vault (it calls /api/* only).
    tree = ast.parse(UI_PATH.read_text())
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
    forbidden = {"app.capabilities", "capabilities", "app.vault", "vault", ".capabilities", ".vault"}
    assert not (imported & forbidden), f"UI must not import backend layer: {imported & forbidden}"


def test_ui_client_targets_api_paths():
    # FR-3/FR-4/FR-6: the UI's HTTP calls go to /api/* paths.
    src = UI_PATH.read_text()
    assert "/api/workspaces" in src
    assert "/api/chat/stream" in src


# --- spec 004 deep-linkable URL state (FR-29/FR-30/FR-31, AC-14) --------------


def test_initial_restores_workspace_and_open_sidebar_from_url(monkeypatch):
    # FR-29: ?workspace=beta&sidebar=open restores that workspace active and opens the sidebar.
    monkeypatch.setattr(ui, "_list_workspaces",
                        lambda: {"workspaces": ["alpha", "beta"], "default": "alpha"})
    monkeypatch.setattr(ui, "_wiki_html", lambda ws: "")
    out = ui._initial(_req(workspace="beta", sidebar="open"))
    assert out[1] == "beta"           # active workspace state
    assert out[6]["open"] is True     # sidebar update opens


def test_initial_defaults_and_hides_sidebar_without_params(monkeypatch):
    # FR-29: absent params ⇒ default workspace, sidebar closed (FR-1 default).
    monkeypatch.setattr(ui, "_list_workspaces",
                        lambda: {"workspaces": ["alpha", "beta"], "default": "alpha"})
    monkeypatch.setattr(ui, "_wiki_html", lambda ws: "")
    out = ui._initial(_req())
    assert out[1] == "alpha"
    assert out[6]["open"] is False


def test_initial_unknown_workspace_falls_back_to_default(monkeypatch):
    # FR-29: an unknown ?workspace falls back to the default workspace.
    monkeypatch.setattr(ui, "_list_workspaces",
                        lambda: {"workspaces": ["alpha", "beta"], "default": "alpha"})
    monkeypatch.setattr(ui, "_wiki_html", lambda ws: "")
    out = ui._initial(_req(workspace="ghost", sidebar="closed"))
    assert out[1] == "alpha"
    assert out[6]["open"] is False


def test_ui_wires_deep_link_navigation_and_silent_toggle():
    # FR-30: workspace select/create navigates to the deep-linked URL (full reload).
    # FR-31: sidebar toggle updates the URL silently via history.replaceState (no reload).
    src = UI_PATH.read_text()
    assert "window.location.href" in src          # FR-30 full reload
    assert "_NAV_WORKSPACE_JS" in src
    assert "history.replaceState" in src          # FR-31 silent update
    assert "sidebar.expand(" in src and "sidebar.collapse(" in src
    assert "searchParams.set('workspace'" in src
    assert "searchParams.set('sidebar'" in src


# --- spec 004 conversation deep-link (FR-32, AC-15) ---------------------------


def test_initial_restores_conversation_from_url(monkeypatch):
    # FR-32: ?conversation=<id> restores that thread into the chat, scoped to the active workspace.
    monkeypatch.setattr(ui, "_list_workspaces",
                        lambda: {"workspaces": ["alpha"], "default": "alpha"})
    monkeypatch.setattr(ui, "_wiki_html", lambda ws: "")
    captured = {}

    def fake_detail(ws, cid):
        captured["args"] = (ws, cid)
        return {"messages": [{"role": "user", "text": "hi"},
                             {"role": "assistant", "text": "hello there"}]}

    monkeypatch.setattr(ui, "_get_session_detail", fake_detail)
    out = ui._initial(_req(workspace="alpha", conversation="conv-123"))
    assert captured["args"] == ("alpha", "conv-123")   # detail fetched, workspace-scoped
    chat_msgs, conv = out[7], out[8]
    assert conv == "conv-123"
    assert [m["content"] for m in chat_msgs] == ["hi", "hello there"]


def test_initial_unknown_conversation_starts_fresh(monkeypatch):
    # FR-32: an unknown/erroring ?conversation degrades to a fresh thread (greeting), not an error.
    monkeypatch.setattr(ui, "_list_workspaces",
                        lambda: {"workspaces": ["alpha"], "default": "alpha"})
    monkeypatch.setattr(ui, "_wiki_html", lambda ws: "")

    def boom(ws, cid):
        raise RuntimeError("no such session")

    monkeypatch.setattr(ui, "_get_session_detail", boom)
    out = ui._initial(_req(workspace="alpha", conversation="ghost"))
    chat_msgs, conv = out[7], out[8]
    assert conv is None
    assert chat_msgs == [{"role": "assistant", "content": ui.GREETING}]


def test_initial_no_conversation_param_starts_fresh(monkeypatch):
    # FR-32: absent ?conversation ⇒ fresh thread, no session lookup.
    monkeypatch.setattr(ui, "_list_workspaces",
                        lambda: {"workspaces": ["alpha"], "default": "alpha"})
    monkeypatch.setattr(ui, "_wiki_html", lambda ws: "")
    monkeypatch.setattr(ui, "_get_session_detail",
                        lambda *a: (_ for _ in ()).throw(AssertionError("should not fetch")))
    out = ui._initial(_req(workspace="alpha"))
    assert out[8] is None
    assert out[7] == [{"role": "assistant", "content": ui.GREETING}]


def test_ui_wires_conversation_deep_link():
    # FR-32: selecting a session updates ?conversation at click time (_SESSION_JS); new chat / turn
    # completion sync it via the hidden #conv-url mirror + _CONV_SYNC_JS. All silent (replaceState).
    src = UI_PATH.read_text()
    assert "_CONV_SYNC_JS" in src
    assert 'elem_id="conv-url"' in src                    # hidden mirror the sync JS reads
    assert "searchParams.set('conversation'" in src       # set on select / active thread
    assert "searchParams.delete('conversation'" in src    # cleared for New conversation / no thread
    # select-time update lives in the session click listener, not a State-input .then
    assert "history.replaceState" in src


# --- spec 004 settings quick menu (FR-26/FR-35, AC-12/AC-18) ------------------


def test_toggle_settings_flips_state_and_visibility():
    # FR-35: the ⚙ button toggles the quick menu; re-toggling dismisses it.
    open_state, upd = ui._toggle_settings(False)
    assert open_state is True and upd.get("visible") is True
    open_state, upd = ui._toggle_settings(True)
    assert open_state is False and upd.get("visible") is False


def test_model_picker_lives_in_quick_menu_not_sidebar():
    # FR-26/FR-35: the Model selector is inside the settings quick menu (a popover beside the chat
    # Submit), not in the left sidebar. Verify by structure: the picker is declared after the
    # settings-menu group and after the main-area chat box (i.e. outside gr.Sidebar).
    src = UI_PATH.read_text()
    assert 'elem_id="settings-menu"' in src               # the quick-menu popover exists
    assert 'elem_id="settings-btn"' in src                # the button beside Submit exists
    assert 'elem_id="model-picker"' in src                # the Model selector still exists
    # It moved out of the sidebar: it is declared after both the settings-menu group and the
    # chat box, which are in the main area below the sidebar block.
    assert src.index('elem_id="settings-menu"') < src.index('elem_id="model-picker"')
    assert src.index("box = gr.Textbox") < src.index('elem_id="model-picker"')
    # The old top-of-sidebar placement comment is gone.
    assert "top of the sidebar" not in src.lower() and "top-of-sidebar" not in src.lower()


def test_ui_wires_settings_toggle_and_dismiss():
    # FR-35: the button click runs _toggle_settings; click-away dismissal JS is loaded.
    src = UI_PATH.read_text()
    assert "settings_btn.click(_toggle_settings" in src
    assert "_SETTINGS_DISMISS_JS" in src


def test_settings_menu_css_unclips_inner_group():
    # FR-35 regression: Gradio renders the menu's inner group `position:absolute`, which collapsed
    # #settings-menu to a ~26px pill and clipped the popover (Model selector) so it looked empty.
    # The CSS must pull the inner group back into flow and let the popover size to its content.
    css = ui._CSS
    assert "#settings-menu > * { position: static !important; }" in css
    assert "overflow: visible;" in css  # #settings-menu must not clip the (previously) overflowing group


# --- spec 004 full-height, bottom-anchored conversation (FR-36, AC-19) --------


def test_chatbot_has_no_fixed_height_and_input_grows_fr36():
    # FR-36: the transcript is not a fixed-height box (it flexes to fill), and the input can grow
    # past one line (lines=1, max_lines>1) so it expands upward instead of a single fixed row.
    src = UI_PATH.read_text()
    chat_decl = src[src.index("chat = gr.Chatbot"):src.index("chat = gr.Chatbot") + 200]
    assert "height=" not in chat_decl                       # no fixed height on the chatbot
    box_start = src.index('placeholder="Ask about the project')
    box_decl = src[box_start:box_start + 160]
    assert "max_lines=" in box_decl and "lines=1" in box_decl


def test_full_height_bottom_anchored_css_fr36():
    # FR-36: the layout chain is capped to the viewport (100vh) as a flex column, the chatbot flexes
    # to fill (min-height:0 so it shrinks as the input grows), and messages anchor to the bottom via
    # an auto top-margin on the message list (collapses to 0 on overflow so scrolling still works).
    css = ui._CSS
    assert "height: 100vh !important;" in css
    assert "main.contain > .column { display: flex; flex-direction: column; }" in css
    assert "#chatbot { flex: 1 1 auto; min-height: 0; }" in css
    assert "#chat-input-wrap { flex: 0 0 auto; }" in css
    assert "#chatbot .message-wrap { margin-top: auto; }" in css


# --- spec 008 interaction card as an in-chat message bubble (FR-10, AC-7) -----


def test_interaction_card_renders_as_in_chat_message():
    # spec 008 FR-8/FR-10/AC-7: the card is an assistant message inside the chat scroll (built by
    # _card_html), NOT a separate surface. There is no #interaction-card group and no #conversation-panel
    # wrapper; the card is emitted as `.itx-card` HTML with a data-itx-id, and only a hidden bridge
    # (#itx-go / #itx-choice / #itx-expire) backs it.
    src = UI_PATH.read_text()
    assert 'elem_id="interaction-card"' not in src         # no separate card surface
    assert 'elem_id="conversation-panel"' not in src       # no external panel wrapper
    assert "def _card_html" in src                         # card is built as message HTML
    assert "class='itx-card'" in src and "data-itx-id=" in src
    # the hidden bridge components exist (the card's clicks route through them)
    assert 'elem_id="itx-go"' in src
    assert 'elem_id="itx-choice"' in src
    assert 'elem_id="itx-expire"' in src


def test_ui_wires_in_chat_card_bridge():
    # spec 008 FR-7/FR-12/FR-16: the in-chat card answers via a JS click-bridge — a delegated listener
    # (_ITX_JS) stashes the choice and clicks #itx-go, whose handler runs _submit_interaction.
    src = UI_PATH.read_text()
    assert "_ITX_JS" in src and "js=_ITX_JS" in src        # bridge listener defined + loaded
    # DOMPurify in gr.Chatbot strips data-* attrs, so the choice is encoded in the button id
    # (id="itx-opt-<choice>") — the bridge reads that, not a data-* attribute.
    assert 'id^="itx-opt-"' in src                         # the selector the bridge reads
    assert "getElementById('itx-go')" in src               # JS clicks the hidden trigger
    assert "itx_go.click(" in src                           # the trigger runs the answer handler
    assert "_submit_interaction" in src
