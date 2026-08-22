"""Gradio web UI — the human startup surface (features 003 + 004).

The UI is a *pure presentation layer*: it reaches the workspace only by calling the
backend REST API over HTTP (same origin), never `app.capabilities` / `app.vault`
directly (spec 003 FR-3/AC-8, spec 004 FR-18, Constitution P9). It is mounted on
the FastAPI app at `/` (see `app/api.py`); Swagger lives at `/api/`.

Feature 004 adds a **collapsible left sidebar** (`gr.Sidebar`) of three **independently
collapsible** panels (`gr.Accordion`), top-to-bottom (spec 004 FR-2):

- **Workspace** — a **typeahead** (placeholder `workspace name`, live suggestions, icon-only
  refresh/create buttons with hover labels).
- **Wiki** — a navigation-only **`vault/wiki/` browser** and, below it, an **upload** section
  (files / drag-and-drop) whose progress bar replaces it while files are deposited into
  `vault/raw/` and ingested.
- **Sessions** — a **New conversation** button at the top, then all prior conversations
  listed reverse-chronologically and grouped under relative-date headers (Today, Yesterday,
  This Week, This Month, Older), each rendered as **clickable text** (selection, not an action)
  and resumable by id (FR-19/FR-24/FR-25).

Every panel is backed by a REST endpoint (`/api/workspaces`, `/api/wiki-tree`, `/api/upload`,
`/api/sessions[/{id}]`) — no capability the API lacks.

Chat streams from `POST /api/chat/stream` (SSE) with a full-reply fallback to
`POST /api/chat`. Consequential replies carry a `pending_plan` which the UI shows with
an explicit **Approve plan** control (spec 003 FR-8, P8) — no auto-approval.
"""

from __future__ import annotations

import html
import json
import os
from datetime import date

import gradio as gr
import httpx

THINKING = '<span class="thinking">…thinking…</span>'
GREETING = (
    "Hi — I'm your project's Product Owner assistant. Pick a workspace, then ask me "
    "anything about the project. I answer from the workspace with citations."
)
APPROVE_MSG = "Approve the pending plan and execute it."
RAW_SUBDIRS = ["notes", "clippings", "docs", "transcripts", "assets"]

# Tooltip labels for the icon-only vault buttons, applied on load (spec 004 FR-5).
_TOOLTIP_JS = """
() => {
  const set = (id, t) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.title = t;
    el.querySelectorAll('button').forEach(b => b.title = t);
  };
  set('refresh-vault', 'Refresh workspace list');
  set('create-vault', 'Create new workspace');
}
"""

# spec 004 FR-9b: a custom hover tooltip for the wiki tree. Native `title` tooltips render
# unreliably inside the Gradio HTML panel, so we drive one from the `data-tip` attribute and
# append it to <body> (position:fixed) so it escapes the panel's overflow clipping. Delegated
# listeners on document survive Gradio re-rendering the tree on workspace switch/refresh.
_WIKI_TIP_JS = """
() => {
  if (window.__wikiTipInit) return;
  window.__wikiTipInit = true;
  const tip = document.createElement('div');
  tip.className = 'wiki-tip';
  document.body.appendChild(tip);
  const target = (e) => e.target && e.target.closest
    ? e.target.closest('.wiki-tree [data-tip]') : null;
  document.addEventListener('mouseover', (e) => {
    const t = target(e);
    if (!t) return;
    tip.textContent = t.getAttribute('data-tip');
    const r = t.getBoundingClientRect();
    tip.style.left = Math.round(r.left) + 'px';
    tip.style.top = Math.round(r.bottom + 4) + 'px';
    tip.style.display = 'block';
  });
  document.addEventListener('mouseout', (e) => {
    if (target(e)) tip.style.display = 'none';
  });
}
"""

# spec 004 FR-19: sessions render as clickable text (not Gradio buttons), so a delegated click
# listener bridges a click on a `.session [data-cid]` entry to the resume handler. It stashes the
# clicked id in `window.__lastCid` and clicks a hidden trigger button (#session-go); that button's
# `.click` uses a `js` shim (_SESSION_PICK_JS) to inject `__lastCid` as the handler's argument.
# (Mutating a hidden Textbox's value from JS does not update Gradio's Svelte store, so the value
# never reaches the backend — a hidden button + js-injected arg is the reliable bridge.)
_SESSION_JS = """
() => {
  if (window.__sessInit) return;
  window.__sessInit = true;
  document.addEventListener('click', (e) => {
    const t = e.target && e.target.closest ? e.target.closest('.session-tree [data-cid]') : null;
    if (!t) return;
    window.__lastCid = t.getAttribute('data-cid');
    const go = document.getElementById('session-go');
    if (go) go.click();
  });
}
"""

# js shim for the hidden trigger: replace the (ignored) placeholder arg with the last-clicked id,
# passing the active workspace through unchanged, so _open_session(conversation_id, vault) runs.
_SESSION_PICK_JS = "(pick, vault) => [window.__lastCid || '', vault]"

_CSS = """
#refresh-vault button, #create-vault button { font-size: 1.1rem; padding: 0 6px; }
.wiki-tree { font-size: 0.9rem; line-height: 1.5; max-height: 240px;
             overflow-y:auto; overflow-x:hidden;
             border:1px solid var(--border-color-primary); border-radius:6px; padding:6px 8px; }
.wiki-tree details { margin-left: 0.4em; }
/* spec 004 FR-9b: names stay on one line and truncate with an ellipsis instead of wrapping.
   Keep the summary as the default list-item so the folder disclosure triangle survives;
   truncate an inner .label span rather than the summary itself. */
.wiki-tree summary { cursor: pointer; white-space: nowrap; overflow: hidden; }
.wiki-tree summary .label {
  display: inline-block; max-width: calc(100% - 1.4em); vertical-align: bottom;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.wiki-tree .file {
  margin-left: 1.2em; opacity: 0.85;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
/* spec 004 FR-9b: full-name hover tooltip, appended to <body> so it is never clipped. */
.wiki-tip {
  position: fixed; z-index: 10000; display: none; pointer-events: none;
  max-width: 60vw; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  background: var(--background-fill-primary, #1f2937);
  color: var(--body-text-color, #f3f4f6);
  border: 1px solid var(--border-color-primary, #4b5563); border-radius: 4px;
  padding: 2px 8px; font-size: 0.8rem; box-shadow: 0 2px 6px rgba(0,0,0,0.35);
}
/* spec 004 FR-19/FR-25: a prior conversation is a selection, not an action — render each entry
   as clickable text (with a 💬 icon), grouped under collapsible relative-date sections. */
.session-tree { font-size: 0.9rem; line-height: 1.55; }
.session-tree details { margin: 0 0 2px 0; }
.session-tree summary {
  cursor: pointer; font-weight: 600; padding: 2px 0;
  color: var(--body-text-color-subdued); white-space: nowrap;
}
.session-tree .session {
  cursor: pointer; display: flex; align-items: center; gap: 6px;
  padding: 2px 4px 2px 1.1em; border-radius: 4px;
  white-space: nowrap; overflow: hidden;
}
.session-tree .session .ico { flex: none; opacity: 0.7; }
.session-tree .session .label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.session-tree .session:hover { background: var(--background-fill-secondary); }
/* The JS click bridge needs its target textbox in the DOM, so hide it with CSS rather than
   `visible=False` (Gradio removes invisible components from the DOM entirely). */
.session-bridge { display: none !important; }
"""


def _api_base() -> str:
    """Base URL of our own REST API (same process/port as this UI)."""
    override = os.getenv("LEADER_API_BASE")
    if override:
        return override.rstrip("/")
    host = os.getenv("LEADER_HOST", "127.0.0.1")
    if host == "0.0.0.0":
        host = "127.0.0.1"
    port = os.getenv("LEADER_PORT", "8000")
    return f"http://{host}:{port}"


# --- REST API client helpers (UI -> /api/* over HTTP only) -----------------


def _list_workspaces() -> dict:
    r = httpx.get(f"{_api_base()}/api/workspaces", timeout=10.0)
    r.raise_for_status()
    return r.json()


def _create_workspace(name: str) -> dict:
    r = httpx.post(f"{_api_base()}/api/workspaces", json={"name": name}, timeout=30.0)
    r.raise_for_status()
    return r.json()


def _get_wiki_tree(workspace: str) -> dict:
    r = httpx.get(f"{_api_base()}/api/wiki-tree", params={"workspace": workspace}, timeout=15.0)
    r.raise_for_status()
    return r.json()


def _get_sessions(workspace: str) -> dict:
    r = httpx.get(f"{_api_base()}/api/sessions", params={"workspace": workspace}, timeout=15.0)
    r.raise_for_status()
    return r.json()


def _get_session_detail(workspace: str, conversation_id: str) -> dict:
    r = httpx.get(
        f"{_api_base()}/api/sessions/{conversation_id}", params={"workspace": workspace}, timeout=15.0
    )
    r.raise_for_status()
    return r.json()


def _post_upload(workspace: str, provenance: str, filename: str, data: bytes) -> dict:
    r = httpx.post(
        f"{_api_base()}/api/upload",
        data={"workspace": workspace, "provenance": provenance},
        files={"files": (filename, data)},
        timeout=120.0,
    )
    r.raise_for_status()
    return r.json()


async def _stream_chat(workspace, message, conversation_id, approve):
    """Yield decoded ChatDelta dicts from the SSE chat stream.

    Emits a single ``{"error": ...}`` dict on a non-2xx response so callers can
    surface it to the user (FR-11) instead of failing silently.
    """
    payload = {
        "message": message,
        "workspace": workspace or None,
        "conversation_id": conversation_id,
        "approve": approve,
    }
    async with httpx.AsyncClient(base_url=_api_base(), timeout=httpx.Timeout(None)) as c:
        async with c.stream("POST", "/api/chat/stream", json=payload) as r:
            if r.status_code != 200:
                body = (await r.aread()).decode(errors="replace")[:300]
                yield {"error": f"API {r.status_code}: {body}"}
                return
            async for line in r.aiter_lines():
                line = line.strip()
                if line.startswith("data:"):
                    try:
                        yield json.loads(line[len("data:"):].strip())
                    except json.JSONDecodeError:
                        continue


# --- rendering helpers ------------------------------------------------------


def _format_extras(citations, pending_plan) -> str:
    parts: list[str] = []
    if citations:
        parts.append("\n\n**Sources**")
        for c in citations:
            parts.append(f"- `{c.get('page','?')}` — {c.get('excerpt','')}")
    if pending_plan:
        parts.append(f"\n\n**Plan awaiting approval** (risk: {pending_plan.get('risk','?')})")
        for s in pending_plan.get("steps", []):
            parts.append(f"{s.get('order','?')}. {s.get('action','')} — {s.get('rationale','')}")
        parts.append("\n_Click **Approve plan** below to execute — nothing changes until you do._")
    return "\n".join(parts)


def _render_nodes(nodes: list[dict]) -> str:
    """Render wiki-tree nodes as collapsible HTML (navigation only, spec 004 FR-9)."""
    parts: list[str] = []
    for n in nodes:
        raw_name = n.get("name", "?")
        name = html.escape(raw_name)
        # spec 004 FR-9b: data-tip carries the full name so the truncated label still
        # reveals the whole folder/file name on hover (folder tooltip / file tooltip).
        # A custom hover tooltip (_WIKI_TIP_JS) reads it — native title tooltips render
        # unreliably inside the Gradio HTML panel.
        tip = html.escape(raw_name, quote=True)
        if n.get("type") == "dir":
            parts.append(
                f"<details><summary data-tip=\"{tip}\"><span class=\"label\">📁 {name}</span></summary>"
                f"{_render_nodes(n.get('children', []))}</details>"
            )
        else:
            parts.append(f"<div class='file' data-tip=\"{tip}\">📄 {name}</div>")
    return "".join(parts)


def _wiki_html(workspace: str | None) -> str:
    if not workspace:
        return "<em>No workspace selected.</em>"
    try:
        tree = _get_wiki_tree(workspace)
    except Exception as e:  # surface, never fail silently (FR-23)
        return f"<em>Could not load wiki tree: {html.escape(str(e))}</em>"
    body = _render_nodes(tree.get("nodes", [])) or "<em>wiki/ is empty.</em>"
    return f"<div class='wiki-tree'>{body}</div>"


_SESSION_BUCKETS = ("Today", "Yesterday", "This Week", "This Month", "Older")


def _bucket_for(created: str, today: date) -> str:
    """Map a conversation's ``created`` date to a relative time bucket (spec 004 FR-25)."""
    try:
        d = date.fromisoformat(created)
    except (ValueError, TypeError):
        return "Today"
    delta = (today - d).days
    if delta <= 0:
        return "Today"
    if delta == 1:
        return "Yesterday"
    if delta <= 7:
        return "This Week"
    if d.year == today.year and d.month == today.month:
        return "This Month"
    return "Older"


def _grouped_sessions(
    workspace: str | None, today: date | None = None
) -> list[tuple[str, list[tuple[str, str]]]]:
    """Conversations bucketed newest-first by relative date, empty buckets dropped.

    Returns ``[(bucket_header, [(label, conversation_id), ...]), ...]`` in
    ``_SESSION_BUCKETS`` order; the API already returns conversations newest-first.
    """
    if not workspace:
        return []
    try:
        convos = _get_sessions(workspace).get("conversations", [])
    except Exception:
        return []
    today = today or date.today()
    grouped: dict[str, list[tuple[str, str]]] = {b: [] for b in _SESSION_BUCKETS}
    for c in convos:
        label = f"{c.get('title', '(untitled)')} · {c.get('turn_count', 0)} turn(s)"
        grouped[_bucket_for(c.get("created", ""), today)].append((label, c["conversation_id"]))
    return [(b, items) for b in _SESSION_BUCKETS if (items := grouped[b])]


def _sessions_html(workspace: str | None) -> str:
    """Render prior conversations as collapsible date sections of clickable text (FR-19/FR-25).

    Each conversation is a `.session` row (💬 icon + label) carrying its id in `data-cid`; a
    delegated JS listener (_SESSION_JS) turns a click into the resume handler. Date groups are
    native `<details open>` so each is independently collapsible (expanded by default).
    """
    groups = _grouped_sessions(workspace)
    if not groups:
        return "<div class='session-tree'><em>No conversations yet.</em></div>"
    parts: list[str] = []
    for header, items in groups:
        rows = "".join(
            f"<div class='session' data-cid=\"{html.escape(cid, quote=True)}\" "
            f"title=\"{html.escape(label, quote=True)}\">"
            f"<span class='ico'>💬</span><span class='label'>{html.escape(label)}</span></div>"
            for label, cid in items
        )
        parts.append(f"<details open><summary>{html.escape(header)}</summary>{rows}</details>")
    return f"<div class='session-tree'>{''.join(parts)}</div>"


# --- Gradio event handlers --------------------------------------------------


def _text(content) -> str:
    """Flatten Gradio chat content (str or list of {text,type} parts) to a string."""
    if isinstance(content, list):
        return " ".join(p.get("text", "") for p in content if isinstance(p, dict)).strip()
    return content or ""


def _user_submit(msg, history):
    msg = (msg or "").strip()
    if not msg:
        return "", history or []
    return "", (history or []) + [{"role": "user", "content": msg}]


def _add_approve_msg(history):
    return (history or []) + [{"role": "user", "content": APPROVE_MSG}]


async def _run_turn(history, conversation_id, workspace, approve):
    """Stream one assistant turn, updating the last message as text arrives."""
    user_msg = _text(history[-1]["content"]) if history else ""
    history = history + [{"role": "assistant", "content": THINKING}]
    yield history, conversation_id, gr.update(visible=False)

    reply, cid = "", conversation_id
    citations, pending = [], None
    try:
        async for data in _stream_chat(workspace, user_msg, conversation_id, approve):
            if "error" in data:
                history[-1]["content"] = f"⚠️ {data['error']}"
                yield history, cid, gr.update(visible=False)
                return
            reply = data.get("reply", reply)
            cid = data.get("conversation_id", cid)
            citations = data.get("citations") or citations
            pending = data.get("pending_plan") or pending
            history[-1]["content"] = reply or THINKING
            yield history, cid, gr.update(visible=False)
    except Exception as e:  # network/transport failure -> surface it (FR-11)
        history[-1]["content"] = f"⚠️ Could not reach the API: {e}"
        yield history, cid, gr.update(visible=False)
        return

    history[-1]["content"] = (reply or "…") + _format_extras(citations, pending)
    yield history, cid, gr.update(visible=bool(pending))


async def _respond(history, conversation_id, workspace):
    async for out in _run_turn(history, conversation_id, workspace, approve=False):
        yield out


async def _approve(history, conversation_id, workspace):
    async for out in _run_turn(history, conversation_id, workspace, approve=True):
        yield out


# --- sidebar handlers (feature 004) ----------------------------------------


# The picker (FR-4) lists the *other* workspaces; when there are none it shows a single
# non-selectable sentinel so the empty state is visible rather than a blank box.
_NONE_SENTINEL = "<none>"


def _others(vaults, active):
    """The workspaces other than the active one — the pool the picker offers (FR-4)."""
    return [v for v in vaults if v != active]


def _picker_update(choices, *, visible):
    """A dropdown update that degrades an empty ``choices`` to the ``<none>`` sentinel (FR-4)."""
    shown = choices if choices else [_NONE_SENTINEL]
    return gr.update(choices=shown, value=None, visible=visible)


def _status(active):
    """The `Active` indicator text at the top of the Workspaces panel (FR-7)."""
    if active:
        return f"**Active:** {active}"
    return "No workspaces yet — type a name and click ＋."


def _initial():
    """Populate the sidebar on page load (server is up by then)."""
    try:
        info = _list_workspaces()
    except Exception as e:
        return (
            "", None, gr.update(choices=[], visible=False),
            f"<em>API not reachable: {html.escape(str(e))}</em>",
            f"API error: {e}", gr.update(visible=False),
        )
    vaults = info.get("workspaces", [])
    default = info.get("default", "default")
    active = default if default in vaults else (vaults[0] if vaults else None)
    wiki = _wiki_html(active) if active else "<em>No workspaces yet.</em>"
    # FR-3: box pre-filled with the active name (the "original"); FR-5: Create hidden until changed.
    return (
        active or "", active,
        _picker_update(_others(vaults, active), visible=False),
        wiki, _status(active), gr.update(visible=False),
    )


def _on_focus(active):
    """Clicking/focusing the box reveals the picker of the *other* workspaces (FR-4)."""
    try:
        vaults = _list_workspaces().get("workspaces", [])
    except Exception:
        vaults = []
    return _picker_update(_others(vaults, active), visible=True)


def _suggest(typed, active):
    """Typing narrows the picker (FR-4) and toggles the Create button (FR-5).

    Create is shown only when the box value differs from the original (active) name.
    """
    typed_s = (typed or "").strip()
    try:
        vaults = _list_workspaces().get("workspaces", [])
    except Exception:
        vaults = []
    others = _others(vaults, active)
    matches = [v for v in others if typed_s.lower() in v.lower()] if typed_s else others
    # Keep the picker visible while there is anything to show — real matches, or the
    # <none> sentinel when no other workspace exists at all.
    has_none = not others
    picker = _picker_update(matches, visible=bool(matches) or has_none)
    show_create = bool(typed_s) and typed_s != (active or "")
    return picker, gr.update(visible=show_create)


def _pick_workspace(selected, active):
    """Selecting a workspace switches the active one and re-scopes panels (FR-4/FR-21)."""
    if not selected or selected == _NONE_SENTINEL:
        return (gr.update(), gr.update(), gr.update(visible=False),
                gr.update(), gr.update(), gr.update(visible=False))
    # Box now equals the active name again → Create hidden (FR-5).
    return (
        selected, selected, gr.update(visible=False),
        _wiki_html(selected), _status(selected), gr.update(visible=False),
    )


def _refresh(active):
    """Refresh icon button: re-fetch state and re-render the panel + wiki browser (FR-5)."""
    try:
        vaults = _list_workspaces().get("workspaces", [])
    except Exception as e:
        return (gr.update(), active, gr.update(visible=False), gr.update(),
                f"Could not list workspaces: {e}", gr.update(visible=False))
    active = active if active in vaults else (vaults[0] if vaults else None)
    wiki = _wiki_html(active) if active else "<em>No workspaces yet.</em>"
    return (
        active or "", active,
        _picker_update(_others(vaults, active), visible=False),
        wiki, _status(active), gr.update(visible=False),
    )


def _create_vault_action(name, active):
    """Create-new-workspace icon button: create the typed name, make it active (FR-6)."""
    name = (name or "").strip()
    if not name:
        return (gr.update(), active, gr.update(visible=False), gr.update(),
                "Enter a workspace name to create.", gr.update(visible=True))
    try:
        _create_workspace(name)
    except Exception as e:
        return (name, active, gr.update(visible=False), gr.update(),
                f"Could not create workspace: {e}", gr.update(visible=True))
    return (name, name, gr.update(visible=False), _wiki_html(name),
            _status(name), gr.update(visible=False))


def _do_upload(files, provenance, vault, progress=gr.Progress()):
    """Upload files into raw/ + ingest; the progress bar replaces the section (FR-11/13)."""
    if not vault:
        yield (gr.update(), gr.update(visible=False), "Select or create a vault first.",
               gr.update(), gr.update())
        return
    if not files:
        yield (gr.update(), gr.update(visible=False), "Add at least one file to upload.",
               gr.update(), gr.update())
        return

    # Replace the upload section with the progress area (FR-13).
    yield (gr.update(visible=False), gr.update(visible=True, value="**Uploading…**"), "",
           gr.update(), gr.update())

    ok, errors = 0, []
    for fp in progress.tqdm(files, desc="Uploading & ingesting"):
        fname = os.path.basename(fp)
        try:
            with open(fp, "rb") as fh:
                data = fh.read()
            report = _post_upload(vault, provenance, fname, data)
            note = report.get("files", [{}])[0].get("error")
            if note:
                errors.append(f"{fname}: {note}")
            else:
                ok += 1
        except Exception as e:
            errors.append(f"{fname}: {e}")

    msg = f"Uploaded {ok} file(s) into raw/{provenance} and ingested."
    if errors:
        msg += "  \n_Notes:_ " + "; ".join(errors)
    # Restore the upload section, hide progress, refresh the wiki tree, clear the picker.
    yield (gr.update(visible=True), gr.update(visible=False), msg, gr.update(value=None),
           _wiki_html(vault))


def _open_session(conversation_id, vault):
    """Resume a prior conversation in the chat (FR-20).

    The value arrives from the JS bridge as ``<cid>|<nonce>`` (the nonce guarantees `.change`
    fires on repeat clicks); strip it back to the bare conversation id.
    """
    if conversation_id and "|" in conversation_id:
        conversation_id = conversation_id.rsplit("|", 1)[0]
    if not conversation_id:
        return gr.update(), None
    try:
        detail = _get_session_detail(vault, conversation_id)
    except Exception as e:
        return [{"role": "assistant", "content": f"⚠️ Could not load session: {e}"}], None
    msgs = [
        {"role": ("user" if m.get("role") == "user" else "assistant"), "content": m.get("text", "")}
        for m in detail.get("messages", [])
    ]
    if not msgs:
        msgs = [{"role": "assistant", "content": GREETING}]
    return msgs, conversation_id


def _new_chat():
    return [{"role": "assistant", "content": GREETING}], None


# --- UI assembly ------------------------------------------------------------


def build_demo() -> gr.Blocks:
    with gr.Blocks(title="Leader Assistant") as demo:
        gr.HTML(f"<style>{_CSS}</style>")
        conversation = gr.State(None)
        active_vault = gr.State(None)

        with gr.Sidebar(open=True, width=340):
            with gr.Accordion("Workspaces", open=True):
                # FR-7: `Active` indicator at the top, above the name box.
                vault_status = gr.Markdown("")
                with gr.Row():
                    vault_box = gr.Textbox(
                        show_label=False, placeholder="workspace name", scale=8, container=False,
                    )
                    # FR-5: left→right after the box: Create (shown only when name changed),
                    # then Refresh at the rightmost (always visible).
                    create_btn = gr.Button(
                        "＋", elem_id="create-vault", scale=1, min_width=40, visible=False,
                    )
                    refresh_btn = gr.Button("↻", elem_id="refresh-vault", scale=1, min_width=40)
                vault_suggest = gr.Dropdown(
                    choices=[], show_label=False, container=False, visible=False,
                    interactive=True, filterable=True,
                )

            with gr.Accordion("Wiki", open=True):
                wiki_view = gr.HTML("<em>Loading…</em>")
                gr.Markdown("**Add files → raw/ + ingest**")
                with gr.Group() as upload_group:
                    uploader = gr.File(
                        file_count="multiple", label="Drag & drop or browse", height=130,
                    )
                    provenance = gr.Dropdown(
                        choices=RAW_SUBDIRS, value="notes", show_label=False, container=False,
                    )
                    upload_btn = gr.Button("Upload & ingest", variant="primary")
                upload_progress = gr.Markdown("", visible=False)
                upload_status = gr.Markdown("")

            with gr.Accordion("Sessions", open=True):
                new_chat_btn = gr.Button("＋ New conversation", size="sm")
                # spec 004 FR-19/FR-25: conversations render as clickable text (💬 + label) in
                # collapsible date sections. Clicks are bridged (JS) into session_pick, whose
                # change fires _open_session — no per-conversation Gradio button.
                sessions_view = gr.HTML("<em>Loading…</em>")
                # Hidden bridge: JS clicks session_go, whose js shim injects the clicked id.
                session_pick = gr.Textbox(
                    elem_classes=["session-bridge"], show_label=False, container=False,
                )
                session_go = gr.Button(elem_id="session-go", elem_classes=["session-bridge"])

        # Main area: chat.
        gr.HTML('<h2 style="margin:8px 2px">Leader <b>Assistant</b></h2>')
        chat = gr.Chatbot(
            height=560, show_label=False,
            value=[{"role": "assistant", "content": GREETING}],
        )
        box = gr.Textbox(show_label=False, submit_btn=True, placeholder="Ask about the project…")
        approve_btn = gr.Button("✅ Approve plan", variant="primary", visible=False)

        # --- wiring ---
        sidebar_out = [vault_box, active_vault, vault_suggest, wiki_view, vault_status, create_btn]
        demo.load(_initial, None, sidebar_out)
        demo.load(_sessions_html, [active_vault], [sessions_view])
        demo.load(None, None, None, js=_TOOLTIP_JS)
        demo.load(None, None, None, js=_WIKI_TIP_JS)
        demo.load(None, None, None, js=_SESSION_JS)

        # FR-4: clicking the box reveals the picker of the other workspaces; typing narrows it
        # and toggles the Create button (FR-5).
        vault_box.focus(_on_focus, [active_vault], [vault_suggest])
        vault_box.input(_suggest, [vault_box, active_vault], [vault_suggest, create_btn])
        vault_suggest.select(_pick_workspace, [vault_suggest, active_vault], sidebar_out)
        refresh_btn.click(_refresh, [active_vault], sidebar_out)
        create_btn.click(_create_vault_action, [vault_box, active_vault], sidebar_out)

        # Re-scope Sessions when the active workspace changes (FR-21) and on explicit refresh.
        active_vault.change(_sessions_html, [active_vault], [sessions_view])
        refresh_btn.click(_sessions_html, [active_vault], [sessions_view])
        # Clicking a session row (JS) clicks session_go; the js shim injects the clicked id so
        # _open_session resumes that conversation in the chat (FR-19/FR-20).
        session_go.click(
            _open_session, [session_pick, active_vault], [chat, conversation],
            js=_SESSION_PICK_JS,
        )

        upload_btn.click(
            _do_upload,
            [uploader, provenance, active_vault],
            [upload_group, upload_progress, upload_status, uploader, wiki_view],
        )

        new_chat_btn.click(_new_chat, None, [chat, conversation])

        box.submit(_user_submit, [box, chat], [box, chat]).then(
            _respond, [chat, conversation, active_vault], [chat, conversation, approve_btn]
        )
        approve_btn.click(_add_approve_msg, [chat], [chat]).then(
            _approve, [chat, conversation, active_vault], [chat, conversation, approve_btn]
        )

    return demo
