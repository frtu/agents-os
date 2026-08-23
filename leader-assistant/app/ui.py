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
# spec 008 D6: on timeout the card is dismissed and the user is told exactly this.
INTERACTION_TIMEOUT_MSG = "Something goes wrong, please retry later."

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

# spec 008 FR-9/D8: the interaction card's countdown. A single global interval drives the
# visible remaining-seconds and, at zero, clicks the hidden #itx-expire trigger so the card is
# dismissed with the timeout message. Called whenever the card is (re)rendered — it re-reads the
# fresh data-seconds from #itx-timer, giving each re-presented interaction a fresh countdown
# (D8: pause during "chat about it", reset after). If the card is hidden, #itx-timer is absent
# and the timer simply stops.
_COUNTDOWN_JS = """
() => {
  if (!window.__itx) window.__itx = {};
  const s = window.__itx;
  if (s.iv) { clearInterval(s.iv); s.iv = null; }
  const timer = document.getElementById('itx-timer');
  if (!timer) return;
  let remaining = parseInt(timer.getAttribute('data-seconds') || '30', 10);
  const out = document.getElementById('itx-remaining');
  const tick = () => {
    if (out) out.textContent = remaining;
    if (remaining <= 0) {
      clearInterval(s.iv); s.iv = null;
      const btn = document.getElementById('itx-expire');
      if (btn) btn.click();
      return;
    }
    remaining -= 1;
  };
  tick();
  s.iv = setInterval(tick, 1000);
}
"""

# spec 004 FR-2b: per-panel header tooltips describing each panel's purpose. Native `title` renders
# unreliably on the accordion header (as with the wiki tree), and the Area tooltip contains `**bold**`
# markdown, so we drive a custom body-level tooltip that converts `**x**`→<b>x</b>. data-panel-tip is
# stamped onto each accordion's header (.label-wrap) by elem_id; a delegated mouseover shows it.
_PANEL_TIP_JS = """
() => {
  if (window.__panelTipInit) return;
  window.__panelTipInit = true;
  const tips = {
    'area-panel': 'Manage multiple **separated** and **isolated** area and interests',
    'knowledge-panel': 'Accumulated knowledge in this area',
    'sessions-panel': 'All previous cases (conversations)',
  };
  for (const [id, t] of Object.entries(tips)) {
    const p = document.getElementById(id);
    if (!p) continue;
    const h = p.querySelector('.label-wrap') || p.querySelector('button') || p;
    if (h) h.setAttribute('data-panel-tip', t);
  }
  const tip = document.createElement('div');
  tip.className = 'panel-tip';
  document.body.appendChild(tip);
  const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const fmt = (s) => esc(s).replace(/\\*\\*(.+?)\\*\\*/g, '<b>$1</b>');
  const target = (e) => e.target && e.target.closest
    ? e.target.closest('[data-panel-tip]') : null;
  document.addEventListener('mouseover', (e) => {
    const t = target(e);
    if (!t) return;
    tip.innerHTML = fmt(t.getAttribute('data-panel-tip'));
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

# spec 004 FR-30: switching/creating a workspace navigates to the deep-linked URL (full reload),
# preserving the current ?sidebar state. Takes the (updated) workspace-name box value.
_NAV_WORKSPACE_JS = """
(ws) => {
  if (!ws) return;
  const u = new URL(window.location);
  u.searchParams.set('workspace', ws);
  if (!u.searchParams.get('sidebar')) u.searchParams.set('sidebar', 'closed');
  window.location.href = u.toString();
}
"""

# spec 004 FR-31: toggling the whole sidebar updates ?sidebar in place (no reload) so the chat and
# transient state survive; the URL stays bookmarkable.
_SIDEBAR_OPEN_JS = """
() => {
  const u = new URL(window.location);
  u.searchParams.set('sidebar', 'open');
  history.replaceState(null, '', u.toString());
}
"""
_SIDEBAR_CLOSED_JS = """
() => {
  const u = new URL(window.location);
  u.searchParams.set('sidebar', 'closed');
  history.replaceState(null, '', u.toString());
}
"""

# spec 004 FR-32: selecting/starting a conversation updates ?conversation in place (no reload) so the
# thread is bookmarkable; an empty id (New conversation) clears the param. Takes the conversation id.
_CONV_URL_JS = """
(cid) => {
  const u = new URL(window.location);
  if (cid) u.searchParams.set('conversation', cid);
  else u.searchParams.delete('conversation');
  history.replaceState(null, '', u.toString());
}
"""

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
/* spec 004 FR-2b: body-level panel tooltip; wraps (unlike .wiki-tip) since the text is a sentence. */
.panel-tip {
  position: fixed; z-index: 10000; display: none; pointer-events: none;
  max-width: 260px; white-space: normal; line-height: 1.4;
  background: var(--background-fill-primary, #1f2937);
  color: var(--body-text-color, #f3f4f6);
  border: 1px solid var(--border-color-primary, #4b5563); border-radius: 4px;
  padding: 4px 8px; font-size: 0.8rem; box-shadow: 0 2px 6px rgba(0,0,0,0.35);
}
/* spec 008 FR-8: the interaction card is visually distinct from the chat box below it — a
   bordered, tinted panel with its own controls and an animated countdown wheel. */
#interaction-card {
  border: 1px solid var(--color-accent, #f59e0b); border-radius: 8px; padding: 12px 14px;
  margin: 6px 2px; background: var(--background-fill-secondary);
  box-shadow: 0 1px 4px rgba(0,0,0,0.15);
}
.itx-timer {
  display: flex; align-items: center; gap: 8px; margin-top: 6px;
  font-size: 0.82rem; color: var(--body-text-color-subdued);
}
.itx-spinner {
  width: 15px; height: 15px; border: 2px solid var(--border-color-primary, #4b5563);
  border-top-color: var(--color-accent, #f59e0b); border-radius: 50%;
  display: inline-block; animation: itx-spin 0.8s linear infinite;
}
@keyframes itx-spin { to { transform: rotate(360deg); } }
/* Hidden expire trigger clicked by the countdown JS at zero. */
.itx-hidden { display: none !important; }
/* spec 004 FR-27: the model-source hint under the top-of-sidebar Model picker. */
.model-src { font-size: 0.75rem; color: var(--body-text-color-subdued); }
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


def _list_models() -> dict:
    r = httpx.get(f"{_api_base()}/api/models", timeout=10.0)
    r.raise_for_status()
    return r.json()


def _set_model(model: str) -> dict:
    r = httpx.post(f"{_api_base()}/api/models", json={"model": model}, timeout=10.0)
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


def _get_pending_interaction(workspace, conversation_id) -> dict | None:
    """Fetch a conversation's still-pending interaction (spec 008 FR-11), for reload recovery."""
    r = httpx.get(
        f"{_api_base()}/api/chat/interaction",
        params={"workspace": workspace, "conversation_id": conversation_id},
        timeout=10.0,
    )
    r.raise_for_status()
    return r.json()


async def _stream_interaction(workspace, conversation_id, interaction_id, choice):
    """Yield decoded ChatDelta dicts from the interaction-response SSE stream (spec 008 FR-12/FR-16)."""
    payload = {
        "workspace": workspace or None,
        "conversation_id": conversation_id,
        "interaction_id": interaction_id,
        "choice": choice,
    }
    async with httpx.AsyncClient(base_url=_api_base(), timeout=httpx.Timeout(None)) as c:
        async with c.stream("POST", "/api/chat/interaction/stream", json=payload) as r:
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
    """Stream one assistant turn, updating the last message as text arrives.

    A consequential turn ends with an approval interaction (spec 008 FR-17); the card owns
    approval, so the legacy Approve button only shows for the rare plan without an interaction.
    """
    user_msg = _text(history[-1]["content"]) if history else ""
    history = history + [{"role": "assistant", "content": THINKING}]
    yield (history, conversation_id, gr.update(visible=False), *_card_updates(None))

    reply, cid = "", conversation_id
    citations, pending, interaction = [], None, None
    try:
        async for data in _stream_chat(workspace, user_msg, conversation_id, approve):
            if "error" in data:
                history[-1]["content"] = f"⚠️ {data['error']}"
                yield (history, cid, gr.update(visible=False), *_card_updates(None))
                return
            reply = data.get("reply", reply)
            cid = data.get("conversation_id", cid)
            citations = data.get("citations") or citations
            pending = data.get("pending_plan") or pending
            interaction = data.get("interaction") or interaction
            history[-1]["content"] = reply or THINKING
            yield (history, cid, gr.update(visible=False), *_card_updates(None))
    except Exception as e:  # network/transport failure -> surface it (FR-11)
        history[-1]["content"] = f"⚠️ Could not reach the API: {e}"
        yield (history, cid, gr.update(visible=False), *_card_updates(None))
        return

    history[-1]["content"] = (reply or "…") + _format_extras(citations, pending)
    show_approve = bool(pending) and not interaction
    yield (history, cid, gr.update(visible=show_approve), *_card_updates(interaction))


async def _respond(history, conversation_id, workspace):
    async for out in _run_turn(history, conversation_id, workspace, approve=False):
        yield out


async def _approve(history, conversation_id, workspace):
    async for out in _run_turn(history, conversation_id, workspace, approve=True):
        yield out


# --- agent<->user interaction card (feature 008) ---------------------------


def _timer_html(seconds: int) -> str:
    """Countdown wheel + remaining-seconds; `data-seconds` seeds the JS timer (spec 008 FR-9)."""
    seconds = int(seconds or 0)
    return (
        f"<div class='itx-timer' id='itx-timer' data-seconds='{seconds}'>"
        f"<span class='itx-spinner'></span>"
        f"<span>Auto-cancels in <b id='itx-remaining'>{seconds}</b>s — nothing changes until you choose.</span>"
        f"</div>"
    )


def _card_updates(interaction: dict | None):
    """Updates for [card, prompt, radio, timer, interaction-state] from a ChatDelta interaction.

    A blocking interaction (approval/clarification) shows the card with its options as radios and
    a fresh countdown (spec 008 FR-6/FR-8). Anything else — no interaction or a non-blocking
    notification — hides the card and clears the state.
    """
    if not interaction or interaction.get("kind") == "notification":
        return (
            gr.update(visible=False),
            gr.update(),
            gr.update(choices=[], value=None, visible=False),
            gr.update(value=""),
            None,
        )
    prompt = interaction.get("prompt", "")
    opts = interaction.get("options", [])
    seconds = int(interaction.get("timeout_seconds", 30) or 30)
    choices = [(o.get("label") or o.get("id"), o.get("id")) for o in opts]
    value = choices[0][1] if len(choices) == 1 else None  # approval pre-selects its lone option
    return (
        gr.update(visible=True),
        gr.update(value=f"**Decision needed** — {prompt}"),
        gr.update(choices=choices, value=value, visible=bool(choices)),
        gr.update(value=_timer_html(seconds)),
        interaction,
    )


async def _run_interaction(history, conversation_id, workspace, interaction, choice):
    """Answer a pending interaction and stream the resumed turn (spec 008 FR-12/FR-16).

    Reflects the human's decision in the transcript, hides the card while the turn runs
    (pausing the countdown, D8), then re-shows the card only if a fresh interaction is
    re-presented ("chat about it", FR-7); otherwise the card stays dismissed.
    """
    if not interaction:
        yield (history, conversation_id, gr.update(visible=False), *_card_updates(None))
        return
    interaction_id = interaction.get("interaction_id")
    label = {"chat": "💬 Let's discuss this first", "decline": "Decline — take no action"}.get(choice)
    if label is None:
        label = next(
            (o.get("label") or o.get("id") for o in interaction.get("options", []) if o.get("id") == choice),
            choice,
        )
    history = history + [
        {"role": "user", "content": label},
        {"role": "assistant", "content": THINKING},
    ]
    yield (history, conversation_id, gr.update(visible=False), *_card_updates(None))

    reply, cid = "", conversation_id
    citations, fresh = [], None
    try:
        async for data in _stream_interaction(workspace, conversation_id, interaction_id, choice):
            if "error" in data:
                history[-1]["content"] = f"⚠️ {data['error']}"
                yield (history, cid, gr.update(visible=False), *_card_updates(None))
                return
            reply = data.get("reply", reply)
            cid = data.get("conversation_id", cid)
            citations = data.get("citations") or citations
            fresh = data.get("interaction") or fresh
            history[-1]["content"] = reply or THINKING
            yield (history, cid, gr.update(visible=False), *_card_updates(None))
    except Exception as e:  # network/transport failure -> surface it (FR-11)
        history[-1]["content"] = f"⚠️ Could not reach the API: {e}"
        yield (history, cid, gr.update(visible=False), *_card_updates(None))
        return

    history[-1]["content"] = (reply or "…") + _format_extras(citations, None)
    yield (history, cid, gr.update(visible=False), *_card_updates(fresh))


async def _submit_interaction(history, conversation_id, workspace, interaction, radio_value):
    if not radio_value:  # nothing selected — keep the card up (countdown restarts on .then)
        yield (history, conversation_id, gr.update(visible=False), *_card_updates(interaction))
        return
    async for out in _run_interaction(history, conversation_id, workspace, interaction, radio_value):
        yield out


async def _decline_interaction(history, conversation_id, workspace, interaction):
    async for out in _run_interaction(history, conversation_id, workspace, interaction, "decline"):
        yield out


async def _chat_interaction(history, conversation_id, workspace, interaction):
    async for out in _run_interaction(history, conversation_id, workspace, interaction, "chat"):
        yield out


def _expire_interaction(history, interaction):
    """Countdown reached zero: dismiss the card and report the fixed timeout message (spec 008 D6)."""
    if not interaction:
        return (history, *_card_updates(None))
    history = (history or []) + [{"role": "assistant", "content": INTERACTION_TIMEOUT_MSG}]
    return (history, *_card_updates(None))


def _recover_card(conversation_id, workspace):
    """Re-render an unanswered card after a reload/session-resume (spec 008 FR-11)."""
    if not conversation_id:
        return _card_updates(None)
    try:
        itx = _get_pending_interaction(workspace, conversation_id)
    except Exception:
        itx = None
    return _card_updates(itx)


# --- model selector (feature 004 FR-26..FR-28) -----------------------------


def _model_choices(data: dict) -> list[tuple[str, str]]:
    """Map an AvailableModels payload to Gradio (label, value) choices."""
    return [(m.get("label") or m["id"], m["id"]) for m in data.get("models", [])]


def _model_initial():
    """Populate the Model dropdown on load: choices, active value, and source hint (FR-26/FR-27)."""
    try:
        data = _list_models()
    except Exception as e:
        return gr.update(choices=[], value=None), f"<em>Models unavailable: {html.escape(str(e))}</em>"
    choices = _model_choices(data)
    return gr.update(choices=choices, value=data.get("current")), _model_hint(data.get("source", ""))


def _model_hint(source: str) -> str:
    where = "from provider" if source == "provider" else "offline list"
    return f"<span class='model-src'>Agent model · {html.escape(where)}</span>"


def _pick_model(model, current):
    """Selecting a model persists it process-wide (FR-28); on failure, revert to the prior value."""
    if not model or model == current:
        return gr.update(), current, gr.update()
    try:
        data = _set_model(model)
    except Exception as e:
        return gr.update(value=current), current, f"<em>Could not set model: {html.escape(str(e))}</em>"
    return gr.update(value=data.get("current")), data.get("current"), _model_hint(data.get("source", ""))


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


def _restore_chat(workspace, conversation_id):
    """Chat + conversation-state to restore a deep-linked thread (spec 004 FR-32).

    An unknown/absent id (or a load error) falls back to a fresh thread with the greeting rather
    than surfacing an error, so a stale bookmark degrades gracefully.
    """
    greeting = [{"role": "assistant", "content": GREETING}]
    if not (workspace and conversation_id):
        return greeting, None
    try:
        detail = _get_session_detail(workspace, conversation_id)
    except Exception:
        return greeting, None
    msgs = [
        {"role": ("user" if m.get("role") == "user" else "assistant"), "content": m.get("text", "")}
        for m in detail.get("messages", [])
    ]
    return (msgs or greeting), (conversation_id if msgs else None)


def _initial(request: gr.Request = None):
    """Populate the sidebar on page load, restoring deep-linked state (spec 004 FR-29/FR-32).

    Reads ``?workspace=``, ``?sidebar=open|closed`` and ``?conversation=`` from the URL: the named
    workspace becomes active when known (else the default), the sidebar opens only when
    ``sidebar=open`` (absent ⇒ the FR-1 default of closed/hidden), and the named conversation is
    restored into the chat scoped to that workspace (unknown/absent ⇒ a fresh thread).
    """
    params = dict(request.query_params) if request is not None else {}
    want_ws = params.get("workspace") or None
    want_conv = params.get("conversation") or None
    sidebar_open = gr.update(open=params.get("sidebar") == "open")
    greeting = [{"role": "assistant", "content": GREETING}]
    try:
        info = _list_workspaces()
    except Exception as e:
        return (
            "", None, gr.update(choices=[], visible=False),
            f"<em>API not reachable: {html.escape(str(e))}</em>",
            f"API error: {e}", gr.update(visible=False), sidebar_open, greeting, None,
        )
    vaults = info.get("workspaces", [])
    default = info.get("default", "default")
    if want_ws and want_ws in vaults:
        active = want_ws  # FR-29: restore the bookmarked workspace.
    else:
        active = default if default in vaults else (vaults[0] if vaults else None)
    wiki = _wiki_html(active) if active else "<em>No workspaces yet.</em>"
    chat_msgs, conv = _restore_chat(active, want_conv)  # FR-32
    # FR-3: box pre-filled with the active name (the "original"); FR-5: Create hidden until changed.
    return (
        active or "", active,
        _picker_update(_others(vaults, active), visible=False),
        wiki, _status(active), gr.update(visible=False), sidebar_open, chat_msgs, conv,
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
        interaction = gr.State(None)  # spec 008: the pending interaction dict, or None
        active_model = gr.State(None)  # spec 004 FR-28: the active agent model selector

        with gr.Sidebar(open=False, width=340) as sidebar:
            # spec 004 FR-26: the Model selector sits at the TOP of the sidebar (above all panels).
            model_picker = gr.Dropdown(
                choices=[], label="Model", show_label=True, container=True,
                interactive=True, filterable=True, elem_id="model-picker",
            )
            model_source = gr.HTML("")

            # spec 004 FR-2a: advanced surface — collapsed by default; FR-2b tooltip via _PANEL_TIP_JS.
            with gr.Accordion("Area (Workspaces)", open=False, elem_id="area-panel"):
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

            # spec 004 FR-2a: advanced surface — collapsed by default; FR-2b tooltip via _PANEL_TIP_JS.
            with gr.Accordion("Knowledge", open=False, elem_id="knowledge-panel"):
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

            # spec 004 FR-2a: primary surface — expanded by default; FR-2b tooltip via _PANEL_TIP_JS.
            with gr.Accordion("Sessions", open=True, elem_id="sessions-panel"):
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
        # spec 008 FR-8: a distinct decision card, above the (always new-task) chat box. It carries
        # its own radio options, a constant "chat about it" affordance, and an animated countdown.
        with gr.Group(visible=False, elem_id="interaction-card") as interaction_card:
            interaction_prompt = gr.Markdown("")
            interaction_radio = gr.Radio(choices=[], show_label=False, container=False, visible=False)
            interaction_timer = gr.HTML("")
            with gr.Row():
                interaction_submit = gr.Button("Submit", variant="primary", scale=2)
                interaction_chat = gr.Button("💬 Chat about it", scale=2)
                interaction_decline = gr.Button("Decline", variant="stop", scale=1)
            # Hidden trigger the countdown JS clicks at zero (spec 008 D6).
            interaction_expire = gr.Button(elem_id="itx-expire", elem_classes=["itx-hidden"])

        box = gr.Textbox(show_label=False, submit_btn=True, placeholder="Ask about the project…")
        approve_btn = gr.Button("✅ Approve plan", variant="primary", visible=False)

        # --- wiring ---
        sidebar_out = [vault_box, active_vault, vault_suggest, wiki_view, vault_status, create_btn]
        card_out = [interaction_card, interaction_prompt, interaction_radio, interaction_timer, interaction]
        # spec 004 FR-29/FR-32: _initial also restores the sidebar open/closed state from ?sidebar and
        # the deep-linked conversation from ?conversation (into chat + conversation state).
        demo.load(_initial, None, sidebar_out + [sidebar, chat, conversation]).then(
            _recover_card, [conversation, active_vault], card_out
        ).then(None, None, None, js=_COUNTDOWN_JS)
        demo.load(_sessions_html, [active_vault], [sessions_view])
        # spec 004 FR-26/FR-27: populate the top-of-sidebar Model picker; FR-28: selecting persists.
        demo.load(_model_initial, None, [model_picker, model_source]).then(
            lambda d=None: d, [model_picker], [active_model]
        )
        demo.load(None, None, None, js=_TOOLTIP_JS)
        demo.load(None, None, None, js=_WIKI_TIP_JS)
        demo.load(None, None, None, js=_SESSION_JS)
        demo.load(None, None, None, js=_PANEL_TIP_JS)

        # FR-4: clicking the box reveals the picker of the other workspaces; typing narrows it
        # and toggles the Create button (FR-5).
        vault_box.focus(_on_focus, [active_vault], [vault_suggest])
        vault_box.input(_suggest, [vault_box, active_vault], [vault_suggest, create_btn])
        # spec 004 FR-30: selecting or creating a workspace navigates to the deep-linked URL
        # (full reload) so the bookmarkable URL always reflects the active workspace.
        vault_suggest.select(_pick_workspace, [vault_suggest, active_vault], sidebar_out).then(
            None, [vault_box], None, js=_NAV_WORKSPACE_JS
        )
        refresh_btn.click(_refresh, [active_vault], sidebar_out)
        create_btn.click(_create_vault_action, [vault_box, active_vault], sidebar_out).then(
            None, [vault_box], None, js=_NAV_WORKSPACE_JS
        )

        # spec 004 FR-31: toggling the whole sidebar updates ?sidebar silently (no reload).
        sidebar.expand(None, None, None, js=_SIDEBAR_OPEN_JS)
        sidebar.collapse(None, None, None, js=_SIDEBAR_CLOSED_JS)

        # spec 004 FR-28: choosing a model persists it process-wide; revert on failure.
        model_picker.change(
            _pick_model, [model_picker, active_model], [model_picker, active_model, model_source]
        )

        # Re-scope Sessions when the active workspace changes (FR-21) and on explicit refresh.
        active_vault.change(_sessions_html, [active_vault], [sessions_view])
        refresh_btn.click(_sessions_html, [active_vault], [sessions_view])
        # Clicking a session row (JS) clicks session_go; the js shim injects the clicked id so
        # _open_session resumes that conversation in the chat (FR-19/FR-20). On resume, recover any
        # still-pending interaction card (spec 008 FR-11) and (re)start its countdown, then reflect
        # the resumed thread in the URL silently (spec 004 FR-32).
        session_go.click(
            _open_session, [session_pick, active_vault], [chat, conversation],
            js=_SESSION_PICK_JS,
        ).then(_recover_card, [conversation, active_vault], card_out).then(
            None, None, None, js=_COUNTDOWN_JS
        ).then(None, [conversation], None, js=_CONV_URL_JS)

        upload_btn.click(
            _do_upload,
            [uploader, provenance, active_vault],
            [upload_group, upload_progress, upload_status, uploader, wiki_view],
        )

        # New conversation clears the chat, dismisses any open interaction card (FR-8), and clears
        # the ?conversation param (spec 004 FR-32).
        new_chat_btn.click(_new_chat, None, [chat, conversation]).then(
            lambda: _card_updates(None), None, card_out
        ).then(None, [conversation], None, js=_CONV_URL_JS)

        # spec 008 FR-8: the bottom chat box always starts a NEW task; it never answers the card.
        # spec 004 FR-32: after a turn, sync ?conversation so a freshly-started thread is bookmarkable.
        turn_out = [chat, conversation, approve_btn, *card_out]
        box.submit(_user_submit, [box, chat], [box, chat]).then(
            _respond, [chat, conversation, active_vault], turn_out
        ).then(None, None, None, js=_COUNTDOWN_JS).then(None, [conversation], None, js=_CONV_URL_JS)
        approve_btn.click(_add_approve_msg, [chat], [chat]).then(
            _approve, [chat, conversation, active_vault], turn_out
        ).then(None, None, None, js=_COUNTDOWN_JS).then(None, [conversation], None, js=_CONV_URL_JS)

        # spec 008 FR-7/FR-12/FR-16: the card's own controls answer the pending interaction.
        interaction_submit.click(
            _submit_interaction,
            [chat, conversation, active_vault, interaction, interaction_radio],
            turn_out,
        ).then(None, None, None, js=_COUNTDOWN_JS)
        interaction_chat.click(
            _chat_interaction, [chat, conversation, active_vault, interaction], turn_out,
        ).then(None, None, None, js=_COUNTDOWN_JS)
        interaction_decline.click(
            _decline_interaction, [chat, conversation, active_vault, interaction], turn_out,
        ).then(None, None, None, js=_COUNTDOWN_JS)
        interaction_expire.click(_expire_interaction, [chat, interaction], [chat, *card_out])

    return demo
