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

A **settings ⚙ button next to the chat Submit** opens a **quick menu** (popover) hosting the
**Model** selector (spec 004 FR-26/FR-35), backed only by `GET`/`POST /api/models`, and the
**Auto-approve (trust mode)** toggle (spec 009 FR-10), backed only by `GET`/`POST /api/settings`.
The menu is built to grow more settings sub-panels; the model control no longer lives in the
sidebar.
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
    const cid = t.getAttribute('data-cid');
    window.__lastCid = cid;
    // spec 004 FR-32: reflect the selected conversation in the URL silently (no reload) so the
    // thread is bookmarkable. Done here (not via a State-input .then) because the clicked id is
    // available directly and gr.State does not reliably reach a js-only listener.
    if (cid) {
      const u = new URL(window.location);
      u.searchParams.set('conversation', cid);
      history.replaceState(null, '', u.toString());
    }
    const go = document.getElementById('session-go');
    if (go) go.click();
  });
}
"""

# js shim for the hidden trigger: replace the (ignored) placeholder arg with the last-clicked id,
# passing the active workspace through unchanged, so _open_session(conversation_id, vault) runs.
_SESSION_PICK_JS = "(pick, vault) => [window.__lastCid || '', vault]"

# spec 008 FR-8/FR-10: the interaction card is an assistant chat message (HTML), so native gr.Radio
# can't live inside it. A delegated click listener bridges a click on any `.itx-card [id^=itx-opt-]`
# control (an option, the "chat about it" affordance, or the ✕ decline) to the answer handler: it stashes
# the choice in `window.__itxChoice` and clicks the hidden #itx-go trigger (same pattern as sessions).
# The choice is carried in the element `id` (id="itx-opt-<choice>"), not a data-* attribute, because
# `gr.Chatbot`'s DOMPurify strips data-* but keeps id. Already-answered cards (`.itx-resolved`) are inert.
_ITX_JS = """
() => {
  if (window.__itxInit) return;
  window.__itxInit = true;
  document.addEventListener('click', (e) => {
    const t = e.target && e.target.closest ? e.target.closest('.itx-card [id^="itx-opt-"]') : null;
    if (!t) return;
    if (t.closest('.itx-resolved')) return;   // an answered/expired card no longer answers
    window.__itxChoice = t.id.slice('itx-opt-'.length);
    const go = document.getElementById('itx-go');
    if (go) go.click();
  });
}
"""

# spec 008 FR-9/D8/D11: the interaction card's countdown. A single global interval drives the
# visible remaining-seconds and, at zero, clicks the hidden #itx-expire trigger so the card is
# dismissed with the timeout message. Called whenever the card is (re)rendered — it re-reads the
# fresh seed from the live card's `.itx-remaining` text, giving each re-presented interaction a fresh
# countdown (D8: pause during "chat about it", reset after). D11 (loop fix): it seeds only from the
# last non-resolved `.itx-card` timer, never arms off a stale/zero seed, and fires #itx-expire at most
# once per timer id — so a resolved/duplicate timer can't drive an expire→re-render→expire join loop.
# Seeding from text (not data-*) survives gr.Chatbot's DOMPurify. No live timer → the timer stops.
_COUNTDOWN_JS = """
() => {
  if (!window.__itx) window.__itx = {};
  const s = window.__itx;
  if (s.iv) { clearInterval(s.iv); s.iv = null; }
  // D11: seed only from the LAST LIVE card's timer (a resolved card has no `.itx-timer`), never a
  // stale/duplicate node — the fix for the expire->re-render->expire join/data loop.
  const timers = document.querySelectorAll('.itx-card:not(.itx-resolved) .itx-timer');
  const timer = timers.length ? timers[timers.length - 1] : null;
  if (!timer) return;
  const tid = timer.id || '';
  const out = timer.querySelector('.itx-remaining');
  let remaining = parseInt((out && out.textContent) || '0', 10);
  // A: never arm off a stale/zero/NaN seed, so we can't synchronously fire a spurious #itx-expire.
  if (!(remaining > 0)) return;
  const tick = () => {
    if (out) out.textContent = remaining;
    if (remaining <= 0) {
      clearInterval(s.iv); s.iv = null;
      // D11: expire this interaction at most once, even if the timer is re-seeded after the click.
      if (s.expired === tid) return;
      s.expired = tid;
      const btn = document.getElementById('itx-expire');
      if (btn) btn.click();
      return;
    }
    remaining -= 1;
  };
  // A: no synchronous first tick — start after the fresh card has painted so the first evaluation
  // reads the live seed, not a mid-render stale one.
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

# spec 004 FR-35: dismiss the settings quick menu on click-away. Clicking outside the menu and
# its ⚙ button (while the menu is open) clicks the button so the Python toggle keeps state in sync.
_SETTINGS_DISMISS_JS = """
() => {
  if (window.__settingsDismissInit) return;
  window.__settingsDismissInit = true;
  document.addEventListener('click', (e) => {
    const menu = document.getElementById('settings-menu');
    const btn = document.getElementById('settings-btn');
    if (!menu || !btn) return;
    if (menu.offsetParent === null) return;  // menu hidden → nothing to dismiss
    if (menu.contains(e.target) || btn.contains(e.target)) return;  // click inside → keep open
    const b = btn.querySelector('button') || btn;
    b.click();  // outside click → re-toggle closed (keeps gr.State in sync)
  }, true);
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

# spec 004 FR-32: sync ?conversation in place (no reload) so the active thread is bookmarkable. A
# js-only listener reads the current id from the hidden #conv-url mirror in the DOM rather than a
# Gradio input, because gr.State/component values do not reach a js-only ("fn=None") listener; a
# non-empty value sets the param, an empty one (New conversation) clears it.
_CONV_SYNC_JS = """
() => {
  const el = document.querySelector('#conv-url textarea, #conv-url input');
  const cid = el ? (el.value || '').trim() : '';
  const u = new URL(window.location);
  if (cid) u.searchParams.set('conversation', cid);
  else u.searchParams.delete('conversation');
  history.replaceState(null, '', u.toString());
}
"""

# spec 004 FR-34: copy the active conversation id to the clipboard. Reads the id from the same
# hidden #conv-url mirror the sync JS uses (the DOM source of truth), no-ops when empty, and gives
# brief "Copied" feedback by swapping the button label.
_COPY_CONV_JS = """
() => {
  const el = document.querySelector('#conv-url textarea, #conv-url input');
  const cid = el ? (el.value || '').trim() : '';
  if (!cid) return;
  navigator.clipboard.writeText(cid);
  const btn = document.querySelector('#copy-conv-id button') || document.querySelector('#copy-conv-id');
  if (btn) { const o = btn.textContent; btn.textContent = '✓'; setTimeout(() => { btn.textContent = o; }, 1200); }
}
"""

_CSS = """
/* spec 004 FR-36: the conversation fills the leftover vertical space, anchors messages to the
   bottom, and lets the input grow upward. Cap the Gradio layout chain to the viewport height and
   make the block column a flex column; then the chatbot flexes to fill and shrinks (min-height:0)
   as the input grows, so the input's top edge rises instead of the page overflowing. */
.gradio-container { height: 100vh !important; }
.main.fillable, .wrap.sidebar-parent, main.contain, main.contain > .column { height: 100%; min-height: 0; }
main.contain > .column { display: flex; flex-direction: column; }
#chatbot { flex: 1 1 auto; min-height: 0; }
#chat-input-wrap { flex: 0 0 auto; }
/* Anchor messages to the bottom of the scroll area: the auto top-margin pushes a short transcript
   flush to the bottom, yet collapses to 0 when the transcript overflows so normal scrolling works. */
#chatbot .bubble-wrap { display: flex; flex-direction: column; }
#chatbot .message-wrap { margin-top: auto; }
#refresh-vault button, #create-vault button { font-size: 1.1rem; padding: 0 6px; }
/* spec 004 FR-33/FR-34: conversation header row — title then an icon-only copy button beside it.
   The title's Gradio block is full-width by default, so constrain it to its content (fit-content)
   so the copy button hugs the title on the left instead of being pushed to the far edge. */
#conv-header { align-items: center; gap: 6px; flex-wrap: nowrap; justify-content: flex-start; }
#conv-title { flex: 0 1 auto; min-width: 0; width: fit-content; max-width: 100%; margin: 0; }
#conv-title h3 { margin: 8px 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
#copy-conv-id { flex: 0 0 auto; min-width: 36px; padding: 0 8px; }
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
/* spec 008 FR-8/FR-10 (plan.md): the interaction card is an assistant chat message (HTML) rendered
   inside the conversation scroll. `.itx-card` is the accent-bordered bubble; its options are inline
   clickable controls (native gr.Radio can't live in a chat message), with an animated countdown.
   A top-right ✕ declines; selecting an option auto-submits (via the JS click-bridge). */
.itx-card {
  position: relative;
  border: 1px solid var(--color-accent, #f59e0b); border-radius: 14px;
  padding: 10px 30px 8px 12px; max-width: min(90%, 520px);
  background: var(--background-fill-secondary); box-shadow: 0 1px 3px rgba(0,0,0,0.12);
}
.itx-prompt { font-size: 0.92rem; margin-bottom: 8px; }
/* The options as a vertical list of clickable "radio-style" buttons. */
.itx-opts { display: flex; flex-direction: column; gap: 6px; }
.itx-opt {
  display: block; width: 100%; text-align: left; cursor: pointer;
  padding: 6px 10px; font-size: 0.88rem; line-height: 1.3;
  border: 1px solid var(--border-color-primary, #4b5563); border-radius: 8px;
  background: var(--background-fill-primary); color: var(--body-text-color);
}
.itx-opt:hover { border-color: var(--color-accent, #f59e0b); background: var(--background-fill-secondary); }
.itx-chat { color: var(--body-text-color-subdued); }
/* An answered/expired card is inert and dimmed; its options/timer are gone. */
.itx-resolved { opacity: 0.7; }
.itx-resolved .itx-choice { font-size: 0.85rem; color: var(--body-text-color-subdued); margin-top: 6px; }
/* Top-right ✕ decline affordance (spec 008 FR-14). */
.itx-close {
  position: absolute; top: 6px; right: 8px; cursor: pointer;
  width: 20px; height: 20px; line-height: 18px; text-align: center;
  padding: 0; border-radius: 50%; font-size: 0.85rem;
  border: 1px solid var(--border-color-primary, #4b5563);
  background: var(--background-fill-primary); color: var(--body-text-color);
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
/* spec 004 FR-27: the model-source hint under the Model picker (now in the settings quick menu). */
.model-src { font-size: 0.75rem; color: var(--body-text-color-subdued); }
/* spec 004 FR-35: the settings quick menu is a popover anchored above the chat input row.
   #chat-input-wrap is the positioned ancestor; the ⚙ button sits beside Submit. */
#chat-input-wrap { position: relative; }
#chat-input-row { align-items: flex-end; gap: 6px; }
#settings-btn { min-width: 44px !important; }
#settings-menu {
  position: absolute; bottom: 100%; right: 0; z-index: 60;
  width: 320px; max-width: 90vw; margin-bottom: 8px; padding: 12px;
  border-radius: 12px; border: 1px solid var(--border-color-primary);
  background: var(--background-fill-primary);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.18);
  overflow: visible;  /* see below: don't clip the inner group Gradio renders position:absolute */
}
/* spec 004 FR-35 fix: Gradio renders the menu's inner group `position:absolute`, which collapses
   #settings-menu to ~26px and (with the group's default overflow:hidden) clips the whole popover,
   so it appeared as an empty pill. Pull the inner group back into flow so the popover sizes to its
   content, and drop its duplicate group chrome so #settings-menu is the single visible box. */
#settings-menu > * { position: static !important; }
#settings-menu > .gr-group {
  border: none !important; background: transparent !important; box-shadow: none !important;
}
#settings-menu-title { margin: 0 0 6px; font-size: 0.85rem; }
/* spec 010 FR-9: the trust-mode state line sits under the input row, always in view. */
#trust-line { margin-top: 4px; padding: 0 4px; min-height: 1rem; }
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


def _get_settings() -> dict:
    r = httpx.get(f"{_api_base()}/api/settings", timeout=10.0)
    r.raise_for_status()
    return r.json()


def _set_auto_approve(enabled: bool) -> dict:
    r = httpx.post(
        f"{_api_base()}/api/settings", json={"auto_approve": bool(enabled)}, timeout=10.0
    )
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


async def _stream_chat(workspace, message, conversation_id, approve, auto_approve=None):
    """Yield decoded ChatDelta dicts from the SSE chat stream.

    Emits a single ``{"error": ...}`` dict on a non-2xx response so callers can
    surface it to the user (FR-11) instead of failing silently. ``auto_approve`` carries the
    quick-menu trust setting on every request (spec 009 FR-10).
    """
    payload = {
        "message": message,
        "workspace": workspace or None,
        "conversation_id": conversation_id,
        "approve": approve,
        "auto_approve": None if auto_approve is None else bool(auto_approve),
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


async def _run_turn(history, conversation_id, workspace, approve, auto_approve=None):
    """Stream one assistant turn, updating the last message as text arrives.

    A consequential turn ends with an approval interaction (spec 008 FR-17); the card owns
    approval, so the legacy Approve button only shows for the rare plan without an interaction.
    """
    user_msg = _text(history[-1]["content"]) if history else ""
    history = history + [{"role": "assistant", "content": THINKING}]
    yield (history, conversation_id, gr.update(visible=False), None)

    reply, cid = "", conversation_id
    citations, pending, interaction = [], None, None
    try:
        async for data in _stream_chat(workspace, user_msg, conversation_id, approve, auto_approve):
            if "error" in data:
                history[-1]["content"] = f"⚠️ {data['error']}"
                yield (history, cid, gr.update(visible=False), None)
                return
            reply = data.get("reply", reply)
            cid = data.get("conversation_id", cid)
            citations = data.get("citations") or citations
            pending = data.get("pending_plan") or pending
            interaction = data.get("interaction") or interaction
            history[-1]["content"] = reply or THINKING
            yield (history, cid, gr.update(visible=False), None)
    except Exception as e:  # network/transport failure -> surface it (FR-11)
        history[-1]["content"] = f"⚠️ Could not reach the API: {e}"
        yield (history, cid, gr.update(visible=False), None)
        return

    history[-1]["content"] = (reply or "…") + _format_extras(citations, pending)
    # spec 008 FR-8/FR-10: a blocking interaction is appended as its own assistant message (the card
    # bubble) inside the chat scroll; the card owns approval, so the legacy Approve button only shows
    # for the rare plan without an interaction.
    card = _card_html(interaction)
    if card:
        history = history + [{"role": "assistant", "content": card}]
    show_approve = bool(pending) and not interaction
    # An auto-approved interaction is context, not a question: render it, but never make it the
    # awaiting-answer state — there is nothing to click and nothing to expire (spec 010 FR-5).
    awaiting = interaction if (interaction or {}).get("status") == "pending" else None
    yield (history, cid, gr.update(visible=show_approve), awaiting)


async def _respond(history, conversation_id, workspace, auto_approve=None):
    async for out in _run_turn(history, conversation_id, workspace, False, auto_approve):
        yield out


async def _approve(history, conversation_id, workspace, auto_approve=None):
    async for out in _run_turn(history, conversation_id, workspace, True, auto_approve):
        yield out


# --- agent<->user interaction card (feature 008) ---------------------------


def _timer_html(seconds: int, iid: str = "") -> str:
    """Countdown wheel + remaining-seconds (spec 008 FR-9/D11). The timer id is scoped per interaction
    (`itx-timer-<iid>`) and the remaining value is a `.itx-remaining` *class* — `gr.Chatbot`'s DOMPurify
    strips data-* but preserves id/class + text. Per-card scoping lets the JS target only the live card
    and fire the expire once (D11), so a stale/resolved timer can never re-arm an expire loop."""
    seconds = int(seconds or 0)
    tid = f"itx-timer-{iid}" if iid else "itx-timer"
    return (
        f"<div class='itx-timer' id='{tid}'>"
        f"<span class='itx-spinner'></span>"
        f"<span>Auto-cancels in <b class='itx-remaining'>{seconds}</b>s — nothing changes until you choose.</span>"
        f"</div>"
    )


CHAT_ABOUT_IT = ("💬 Chat about it", "chat")  # constant final option (spec 008 FR-7)


def _card_html(interaction: dict | None) -> str | None:
    """Build the interaction card as an assistant chat-message HTML string (spec 008 FR-8/FR-10).

    A blocking interaction (approval/clarification) renders as an accent-bordered `.itx-card` bubble
    inside the chat scroll: the prompt, its proposals + the constant "chat about it" as inline
    clickable options (data-itx-choice), a top-right ✕ decline, and an animated countdown. The clicks
    reach the backend via the JS bridge (_ITX_JS → #itx-go). Returns None for no interaction or a
    non-blocking notification. No option is pre-selected — clicking is what submits (P8).

    An already-resolved interaction (trust mode auto-approved it on the operator's behalf) renders
    as an inert `.itx-resolved` bubble with no options and no countdown: it records what was
    authorised, it is not a question (spec 010 FR-5).
    """
    if not interaction or interaction.get("kind") == "notification":
        return None
    iid = html.escape(str(interaction.get("interaction_id", "")))
    if interaction.get("status", "pending") != "pending":
        return _resolved_card_html(iid, interaction)
    prompt = html.escape(interaction.get("prompt", ""))
    seconds = int(interaction.get("timeout_seconds", 30) or 30)
    opts = list(interaction.get("options", [])) + [{"id": CHAT_ABOUT_IT[1], "label": CHAT_ABOUT_IT[0]}]
    # The choice is encoded in the element `id` (id="itx-opt-<choice>") — NOT a data-* attribute —
    # because `gr.Chatbot`'s DOMPurify strips data-* but preserves id/class; the JS bridge reads the id.
    buttons = "".join(
        f"<button class='itx-opt{' itx-chat' if o.get('id') == CHAT_ABOUT_IT[1] else ''}' "
        f"id='itx-opt-{html.escape(str(o.get('id')))}'>"
        f"{html.escape(str(o.get('label') or o.get('id')))}</button>"
        for o in opts
    )
    # data-itx-id is for server-side _neutralize_card matching on the history string (that runs on the
    # Python value, not the rendered DOM, so the stripped attribute in the browser is irrelevant here).
    return (
        f"<div class='itx-card' data-itx-id='{iid}'>"
        f"<button class='itx-close' id='itx-opt-decline' title='Decline — take no action'>✕</button>"
        f"<div class='itx-prompt'>{prompt}</div>"
        f"<div class='itx-opts'>{buttons}</div>"
        f"{_timer_html(seconds, iid)}"
        f"</div>"
    )


_RESOLUTION_LABELS = {
    "auto-approved": "⚡ Approved on your behalf — trust mode is on",
    "declined": "Declined — no action taken",
    "timeout": "⏱ Timed out — no action taken",
}


def _resolved_card_html(iid: str, interaction: dict) -> str:
    """An inert record of an already-decided interaction — context, never answerable (spec 010 FR-5)."""
    resolution = str(interaction.get("resolution") or "resolved")
    label = _RESOLUTION_LABELS.get(resolution, resolution)
    return (
        f"<div class='itx-card itx-resolved' data-itx-id='{iid}'>"
        f"<div class='itx-prompt'>{html.escape(interaction.get('prompt', ''))}</div>"
        f"<div class='itx-choice'>→ {html.escape(label)}</div>"
        f"</div>"
    )


def _choice_label(interaction: dict, choice: str) -> str:
    """The transcript label for a chosen option / decline / chat (spec 008 P6 traceability)."""
    label = {"chat": "💬 Let's discuss this first", "decline": "Decline — take no action"}.get(choice)
    if label is None:
        label = next(
            (o.get("label") or o.get("id") for o in interaction.get("options", []) if o.get("id") == choice),
            choice,
        )
    return label


def _neutralize_card(history, interaction_id: str, label: str):
    """Rewrite the answered/expired card message in place so it can no longer be answered.

    Finds the message carrying `data-itx-id="{interaction_id}"` and replaces it with a static,
    dimmed `.itx-resolved` bubble (prompt + the resolution, no options, no #itx-timer) — so only the
    active card ever carries the countdown ids and a stale card cannot be re-clicked (spec 008 FR-15).
    """
    marker = f"data-itx-id='{html.escape(str(interaction_id))}'"
    out = list(history or [])
    for i in range(len(out) - 1, -1, -1):
        content = out[i].get("content") if isinstance(out[i], dict) else None
        if isinstance(content, str) and marker in content:
            # Recover the prompt text from the card's own markup (kept escaped).
            prompt = ""
            start = content.find("<div class='itx-prompt'>")
            if start != -1:
                start += len("<div class='itx-prompt'>")
                end = content.find("</div>", start)
                if end != -1:
                    prompt = content[start:end]
            out[i] = {"role": "assistant", "content": (
                f"<div class='itx-card itx-resolved' data-itx-id='{html.escape(str(interaction_id))}'>"
                f"<div class='itx-prompt'>{prompt}</div>"
                f"<div class='itx-choice'>→ {html.escape(str(label))}</div>"
                f"</div>"
            )}
            break
    return out


async def _run_interaction(history, conversation_id, workspace, interaction, choice):
    """Answer a pending interaction and stream the resumed turn (spec 008 FR-12/FR-16).

    Neutralizes the active card message in place, reflects the human's decision as a user message,
    then appends a fresh card message only if a new interaction is re-presented ("chat about it",
    FR-7); otherwise the card stays resolved.
    """
    if not interaction:
        yield (history, conversation_id, gr.update(visible=False), None)
        return
    interaction_id = interaction.get("interaction_id")
    label = _choice_label(interaction, choice)
    history = _neutralize_card(history, interaction_id, label) + [
        {"role": "user", "content": label},
        {"role": "assistant", "content": THINKING},
    ]
    yield (history, conversation_id, gr.update(visible=False), None)

    reply, cid = "", conversation_id
    citations, fresh = [], None
    try:
        async for data in _stream_interaction(workspace, conversation_id, interaction_id, choice):
            if "error" in data:
                history[-1]["content"] = f"⚠️ {data['error']}"
                yield (history, cid, gr.update(visible=False), None)
                return
            reply = data.get("reply", reply)
            cid = data.get("conversation_id", cid)
            citations = data.get("citations") or citations
            fresh = data.get("interaction") or fresh
            history[-1]["content"] = reply or THINKING
            yield (history, cid, gr.update(visible=False), None)
    except Exception as e:  # network/transport failure -> surface it (FR-11)
        history[-1]["content"] = f"⚠️ Could not reach the API: {e}"
        yield (history, cid, gr.update(visible=False), None)
        return

    history[-1]["content"] = (reply or "…") + _format_extras(citations, None)
    card = _card_html(fresh)
    if card:
        history = history + [{"role": "assistant", "content": card}]
    yield (history, cid, gr.update(visible=False), fresh)


async def _submit_interaction(history, conversation_id, workspace, interaction, choice):
    """Answer the pending card from the JS bridge (spec 008 FR-7/FR-12/FR-16). `choice` is the
    clicked option id, "chat", or "decline"; empty means no click reached us — keep the card up."""
    choice = (choice or "").strip()
    if not choice:
        yield (history, conversation_id, gr.update(visible=False), interaction)
        return
    async for out in _run_interaction(history, conversation_id, workspace, interaction, choice):
        yield out


def _expire_interaction(history, interaction):
    """Countdown reached zero: neutralize the card and report the fixed timeout message (spec 008 D6)."""
    if not interaction:
        return (history, None)
    history = _neutralize_card(history, interaction.get("interaction_id"), "⏱ Timed out")
    history = history + [{"role": "assistant", "content": INTERACTION_TIMEOUT_MSG}]
    return (history, None)


def _recover_card(history, conversation_id, workspace):
    """Re-append an unanswered card message after a reload/session-resume (spec 008 FR-11)."""
    if not conversation_id:
        return (history, None)
    try:
        itx = _get_pending_interaction(workspace, conversation_id)
    except Exception:
        itx = None
    card = _card_html(itx)
    if card:
        history = (history or []) + [{"role": "assistant", "content": card}]
    return (history, itx)


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


# --- auto-approve / trust mode (feature 009 FR-10) -------------------------


def _trust_hint(enabled: bool) -> str:
    """The always-visible state line under the input row (spec 009 FR-10, spec 010 FR-9)."""
    if enabled:
        return (
            "<span class='model-src'>⚡ Auto-approve ON — I approve consequential actions on your "
            "behalf and continue (still logged &amp; git-committed)</span>"
        )
    return "<span class='model-src'>Auto-approve off — you make the final decision</span>"


def _trust_initial():
    """Load the persisted trust setting into the quick-menu toggle (spec 009 FR-8/FR-10)."""
    try:
        enabled = bool(_get_settings().get("auto_approve"))
    except Exception as e:
        return gr.update(value=False), f"<em>Settings unavailable: {html.escape(str(e))}</em>", False
    return gr.update(value=enabled), _trust_hint(enabled), enabled


def _pick_trust(enabled):
    """Toggling Auto-approve persists it over /api/settings; on failure, revert the checkbox."""
    try:
        data = _set_auto_approve(bool(enabled))
    except Exception as e:
        return gr.update(value=not bool(enabled)), f"<em>Could not save: {html.escape(str(e))}</em>", not bool(enabled)
    now = bool(data.get("auto_approve"))
    return gr.update(value=now), _trust_hint(now), now


def _toggle_settings(is_open: bool):
    """Toggle the settings quick menu open/closed (spec 004 FR-35; re-toggle dismisses)."""
    now = not is_open
    return now, gr.update(visible=now)


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


def _conv_title_md(conversation_id, workspace):
    """Chat-panel header label = the same backend-derived title as the Sessions list (spec 004 FR-33).

    Fetches the conversation-detail title (FR-20 parity) for a live thread; an absent id or a load
    error degrades to the neutral "New conversation" label rather than surfacing an error.
    """
    if not (workspace and conversation_id):
        return "### New conversation"
    try:
        title = (_get_session_detail(workspace, conversation_id).get("title") or "").strip()
    except Exception:
        title = ""
    return f"### {title}" if title else "### New conversation"


# --- UI assembly ------------------------------------------------------------


def build_demo() -> gr.Blocks:
    with gr.Blocks(title="Leader Assistant") as demo:
        gr.HTML(f"<style>{_CSS}</style>")
        conversation = gr.State(None)
        active_vault = gr.State(None)
        interaction = gr.State(None)  # spec 008: the pending interaction dict, or None
        active_model = gr.State(None)  # spec 004 FR-28: the active agent model selector
        trust_state = gr.State(False)  # spec 009 FR-10: persisted auto-approve (trust mode)
        settings_open = gr.State(False)  # spec 004 FR-35: settings quick-menu open/closed

        with gr.Sidebar(open=False, width=340) as sidebar:
            # spec 004 FR-2a: advanced surface — collapsed by default; FR-2b tooltip via _PANEL_TIP_JS.
            with gr.Accordion("Workspaces (Areas)", open=False, elem_id="area-panel"):
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
            with gr.Accordion("Knowledge (Resources)", open=False, elem_id="knowledge-panel"):
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
            with gr.Accordion("Sessions (Projects/Archives)", open=True, elem_id="sessions-panel"):
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

        # Main area: chat. spec 004 FR-33/FR-34: the chat panel's top shows the active conversation's
        # title (same backend-derived label as the Sessions list) with a copy-id control beside it.
        with gr.Row(elem_id="conv-header"):
            conv_title = gr.Markdown("### New conversation", elem_id="conv-title")
            # spec 004 FR-34: icon-only copy control, sitting next to the title on the left.
            copy_conv_btn = gr.Button("⧉", size="sm", scale=0, min_width=36, elem_id="copy-conv-id")
        # spec 008 FR-8/FR-10: the interaction card is an assistant message inside the chat scroll
        # (see _card_html), so it needs no separate surface — just a hidden bridge. A JS listener
        # (_ITX_JS) stashes the clicked option in window.__itxChoice and clicks #itx-go; its js-only
        # click mirrors that global into itx_choice (updating the store), then _submit_interaction
        # answers it. #itx-expire is the hidden trigger the countdown JS clicks at zero (D6).
        # spec 004 FR-36: no fixed height — CSS flexes the panel to fill the vertical space between
        # the header and the input, and anchors messages to the bottom (short threads sit flush low).
        chat = gr.Chatbot(
            show_label=False, elem_id="chatbot",
            value=[{"role": "assistant", "content": GREETING}],
        )
        itx_choice = gr.Textbox(visible=False, elem_id="itx-choice")
        itx_go = gr.Button(elem_id="itx-go", elem_classes=["itx-hidden"])
        itx_expire = gr.Button(elem_id="itx-expire", elem_classes=["itx-hidden"])

        # spec 004 FR-35: the chat input row carries a settings button next to Submit that opens a
        # quick menu (popover) hosting the Model selector (FR-26) — structured to grow more sub-panels.
        with gr.Column(elem_id="chat-input-wrap"):
            with gr.Group(visible=False, elem_id="settings-menu") as settings_menu:
                gr.Markdown("**Settings**", elem_id="settings-menu-title")
                # spec 004 FR-26: the Model selector — first (and, for now, only) sub-panel.
                model_picker = gr.Dropdown(
                    choices=[], label="Model", show_label=True, container=True,
                    interactive=True, filterable=True, elem_id="model-picker",
                )
                model_source = gr.HTML("")
                # spec 009 FR-10 / spec 010 FR-10: the Auto-approve (trust mode) sub-panel — the
                # control stays here, reading/writing the persisted setting over /api/settings only
                # (P9) and riding every request. Its *state line* lives below the input row (010 FR-9).
                auto_approve_box = gr.Checkbox(
                    label="Auto-approve (trust mode)", value=False,
                    interactive=True, elem_id="auto-approve",
                )
            with gr.Row(elem_id="chat-input-row"):
                # spec 004 FR-36: grow upward past one line (bottom edge fixed) up to max_lines,
                # then scroll internally, so the chat area above shrinks instead of the input drifting.
                box = gr.Textbox(
                    show_label=False, submit_btn=True, placeholder="Ask about the project…",
                    scale=8, container=False, lines=1, max_lines=8,
                )
                settings_btn = gr.Button("⚙", elem_id="settings-btn", scale=0, min_width=44)
            # spec 010 FR-9: the trust-mode state line is always in view, beneath the input row, so
            # the operator is never surprised that a consequential action ran without asking.
            auto_approve_hint = gr.HTML("", elem_id="trust-line")
        approve_btn = gr.Button("✅ Approve plan", variant="primary", visible=False)
        # spec 004 FR-32: a hidden mirror of the active conversation id that _CONV_SYNC_JS reads from
        # the DOM to keep ?conversation in sync (js-only listeners can't read gr.State inputs).
        conv_url = gr.Textbox(visible=False, elem_id="conv-url")

        # --- wiring ---
        sidebar_out = [vault_box, active_vault, vault_suggest, wiki_view, vault_status, create_btn]
        # spec 004 FR-29/FR-32: _initial also restores the sidebar open/closed state from ?sidebar and
        # the deep-linked conversation from ?conversation (into chat + conversation state).
        demo.load(_initial, None, sidebar_out + [sidebar, chat, conversation]).then(
            _recover_card, [chat, conversation, active_vault], [chat, interaction]
        ).then(_conv_title_md, [conversation, active_vault], [conv_title]).then(
            None, None, None, js=_COUNTDOWN_JS
        )
        demo.load(_sessions_html, [active_vault], [sessions_view])
        # spec 004 FR-26/FR-27: populate the quick-menu Model picker; FR-28: selecting persists.
        demo.load(_model_initial, None, [model_picker, model_source]).then(
            lambda d=None: d, [model_picker], [active_model]
        )
        # spec 009 FR-10: reflect the persisted trust setting in the quick menu on load.
        demo.load(_trust_initial, None, [auto_approve_box, auto_approve_hint, trust_state])
        demo.load(None, None, None, js=_TOOLTIP_JS)
        demo.load(None, None, None, js=_WIKI_TIP_JS)
        demo.load(None, None, None, js=_SESSION_JS)
        demo.load(None, None, None, js=_ITX_JS)  # spec 008: in-chat card click-bridge
        demo.load(None, None, None, js=_PANEL_TIP_JS)
        demo.load(None, None, None, js=_SETTINGS_DISMISS_JS)

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

        # spec 004 FR-34: copy the active conversation id (read from the #conv-url mirror) to clipboard.
        copy_conv_btn.click(None, None, None, js=_COPY_CONV_JS)

        # spec 004 FR-35: the settings button beside Submit toggles the quick menu (re-toggle
        # dismisses; _SETTINGS_DISMISS_JS also closes on click-away).
        settings_btn.click(_toggle_settings, [settings_open], [settings_open, settings_menu])
        # spec 004 FR-28: choosing a model persists it process-wide; revert on failure.
        # spec 009 FR-8/FR-10: toggling Auto-approve persists it; the hint keeps the state visible.
        auto_approve_box.change(
            _pick_trust, [auto_approve_box], [auto_approve_box, auto_approve_hint, trust_state]
        )
        model_picker.change(
            _pick_model, [model_picker, active_model], [model_picker, active_model, model_source]
        )

        # Re-scope Sessions when the active workspace changes (FR-21) and on explicit refresh.
        active_vault.change(_sessions_html, [active_vault], [sessions_view])
        refresh_btn.click(_sessions_html, [active_vault], [sessions_view])
        # Clicking a session row (JS) clicks session_go; the js shim injects the clicked id so
        # _open_session resumes that conversation in the chat (FR-19/FR-20). On resume, recover any
        # still-pending interaction card (spec 008 FR-11) and (re)start its countdown. The URL's
        # ?conversation is updated by _SESSION_JS at click time (spec 004 FR-32).
        session_go.click(
            _open_session, [session_pick, active_vault], [chat, conversation],
            js=_SESSION_PICK_JS,
        ).then(_recover_card, [chat, conversation, active_vault], [chat, interaction]).then(
            _conv_title_md, [conversation, active_vault], [conv_title]
        ).then(None, None, None, js=_COUNTDOWN_JS)

        upload_btn.click(
            _do_upload,
            [uploader, provenance, active_vault],
            [upload_group, upload_progress, upload_status, uploader, wiki_view],
        )

        # New conversation clears the chat (dropping any open card message, FR-8), clears the pending
        # interaction state, and clears the ?conversation param (spec 004 FR-32) via the hidden mirror.
        new_chat_btn.click(_new_chat, None, [chat, conversation]).then(
            lambda: None, None, [interaction]
        ).then(lambda: "### New conversation", None, [conv_title]).then(
            lambda: "", None, [conv_url]
        ).then(None, None, None, js=_CONV_SYNC_JS)

        # spec 008 FR-8: the bottom chat box always starts a NEW task; it never answers the card.
        # spec 004 FR-32: after a turn, mirror the (possibly newly created) conversation id into the
        # hidden #conv-url box, then _CONV_SYNC_JS syncs ?conversation so the thread is bookmarkable.
        turn_out = [chat, conversation, approve_btn, interaction]
        box.submit(_user_submit, [box, chat], [box, chat]).then(
            _respond, [chat, conversation, active_vault, auto_approve_box], turn_out
        ).then(None, None, None, js=_COUNTDOWN_JS).then(
            lambda cid: cid or "", [conversation], [conv_url]
        ).then(_conv_title_md, [conversation, active_vault], [conv_title]).then(
            None, None, None, js=_CONV_SYNC_JS
        )
        approve_btn.click(_add_approve_msg, [chat], [chat]).then(
            _approve, [chat, conversation, active_vault, auto_approve_box], turn_out
        ).then(None, None, None, js=_COUNTDOWN_JS).then(
            lambda cid: cid or "", [conversation], [conv_url]
        ).then(_conv_title_md, [conversation, active_vault], [conv_title]).then(
            None, None, None, js=_CONV_SYNC_JS
        )

        # spec 008 FR-7/FR-12/FR-16: the in-chat card answers via the JS bridge. Clicking an option
        # (proposal, "chat about it", or the ✕ decline) sets window.__itxChoice and clicks #itx-go;
        # its js-only click mirrors the choice into itx_choice (updating the store), then
        # _submit_interaction answers the pending interaction and streams the resumed turn.
        itx_go.click(None, None, [itx_choice], js="() => window.__itxChoice || ''").then(
            _submit_interaction,
            [chat, conversation, active_vault, interaction, itx_choice],
            turn_out,
        ).then(None, None, None, js=_COUNTDOWN_JS).then(
            lambda cid: cid or "", [conversation], [conv_url]
        ).then(_conv_title_md, [conversation, active_vault], [conv_title]).then(
            None, None, None, js=_CONV_SYNC_JS
        )
        # spec 008 D6: the countdown JS clicks #itx-expire at zero → neutralize the card + timeout msg.
        itx_expire.click(_expire_interaction, [chat, interaction], [chat, interaction]).then(
            None, None, None, js=_COUNTDOWN_JS
        )

    return demo
