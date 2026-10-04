"""Gradio backend console (spec 002), mounted at `/ui` by `app/main.py`.

Same look and interaction model as the `leader-assistant` console: a collapsible
left `gr.Sidebar` of independently collapsible `gr.Accordion` menus — **Board**,
**Definitions**, **Executions** (FR-2) — each holding an HTML tree of clickable
text entries (FR-6). The main area shows the selected entry (FR-7/FR-8).

It is a pure presentation layer: all data comes from `ConsoleApi`, i.e. the
public REST API over HTTP (FR-9). It is read-only — no business command is
reachable from here (spec Non-Goals, P1/P3).
"""
from __future__ import annotations

import gradio as gr

from app.ui.client import ConsoleApi
from app.ui.render import HOME, board_tree, definitions_tree, executions_tree, open_ref

# Sidebar menus, top to bottom (spec 002 FR-2): (label, elem_id, open by default).
MENUS = (
    ("Board", "board-panel", True),
    ("Definitions", "definitions-panel", False),
    ("Executions", "executions-panel", False),
)

# spec 002 FR-6/FR-11/FR-12: entries are clickable text, not Gradio buttons, so a delegated
# click listener bridges a click on `.lc-tree [data-ref]` to the Python handler — the same bridge
# as the leader-assistant sessions list. It stashes the ref in `window.__lcRef`, marks the entry
# active, reflects it in `?item=` (no reload), and clicks the hidden #nav-go trigger whose `js`
# shim (_NAV_PICK_JS) injects the ref as the handler's argument. (A JS-mutated Textbox value never
# reaches Gradio's store, so a hidden button + js-injected arg is the reliable bridge.)
# A click on a group/node label opens it and expands its <details> (never collapses it); the
# disclosure marker still toggles.
_NAV_JS = """
() => {
  if (window.__lcNavInit) return;
  window.__lcNavInit = true;
  document.addEventListener('click', (e) => {
    const t = e.target && e.target.closest ? e.target.closest('.lc-tree [data-ref]') : null;
    if (!t) return;
    const summary = t.closest('summary');
    if (summary) { e.preventDefault(); summary.parentElement.open = true; }
    const ref = t.getAttribute('data-ref');
    window.__lcRef = ref;
    document.querySelectorAll('.lc-tree .entry.active').forEach(el => el.classList.remove('active'));
    t.classList.add('active');
    const u = new URL(window.location);
    u.searchParams.set('item', ref);
    history.replaceState(null, '', u.toString());
    const go = document.getElementById('nav-go');
    if (go) (go.querySelector('button') || go).click();
  });
}
"""

# js shim for the hidden trigger: replace the placeholder arg with the last-clicked ref.
_NAV_PICK_JS = "(pick, current) => [window.__lcRef || '', current]"

# spec 002 FR-12: after the trees re-render (load/refresh), re-mark the selected entry.
_MARK_ACTIVE_JS = """
() => {
  const ref = window.__lcRef || new URL(window.location).searchParams.get('item');
  if (!ref) return;
  window.__lcRef = ref;
  document.querySelectorAll('.lc-tree [data-ref]').forEach(el => {
    el.classList.toggle('active', el.getAttribute('data-ref') === ref);
  });
}
"""

# spec 002 FR-6: full-name hover tooltip from `data-tip`, appended to <body> so the sidebar's
# overflow never clips it (native `title` renders unreliably inside Gradio HTML panels).
_TIP_JS = """
() => {
  if (window.__lcTipInit) return;
  window.__lcTipInit = true;
  const tip = document.createElement('div');
  tip.className = 'lc-tip';
  document.body.appendChild(tip);
  const target = (e) => e.target && e.target.closest ? e.target.closest('.lc-tree [data-tip]') : null;
  document.addEventListener('mouseover', (e) => {
    const t = target(e);
    if (!t) return;
    tip.textContent = t.getAttribute('data-tip');
    const r = t.getBoundingClientRect();
    tip.style.left = Math.round(r.left) + 'px';
    tip.style.top = Math.round(r.bottom + 4) + 'px';
    tip.style.display = 'block';
  });
  document.addEventListener('mouseout', (e) => { if (target(e)) tip.style.display = 'none'; });
}
"""

_CSS = """
#lc-brand { margin: 0; }
#lc-brand h3 { margin: 4px 2px; }
#lc-refresh { min-width: 40px; font-size: 1.1rem; padding: 0 6px; }
.lc-tree { font-size: 0.9rem; line-height: 1.55; }
.lc-tree details { margin: 0 0 2px 0; }
.lc-tree details details { margin-left: 0.9em; }
.lc-tree summary { cursor: pointer; white-space: nowrap; overflow: hidden; }
.lc-tree .leaf { margin-left: 1.4em; }
.lc-tree .entry {
  cursor: pointer; display: inline-flex; align-items: center; gap: 6px;
  max-width: calc(100% - 1.4em); vertical-align: bottom;
  padding: 1px 4px; border-radius: 4px; white-space: nowrap; overflow: hidden;
}
.lc-tree .leaf .entry { max-width: 100%; }
.lc-tree .entry .ico { flex: none; opacity: 0.8; }
.lc-tree .entry .label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.lc-tree .entry .meta {
  flex: none; font-size: 0.72rem; color: var(--body-text-color-subdued);
  border: 1px solid var(--border-color-primary); border-radius: 8px; padding: 0 6px;
}
.lc-tree .entry:hover { background: var(--background-fill-secondary); }
/* spec 002 FR-12: the entry being read is marked. */
.lc-tree .entry.active {
  background: var(--background-fill-secondary); font-weight: 600;
  box-shadow: inset 2px 0 0 var(--color-accent, #f97316);
}
.lc-tree .none { opacity: 0.7; }
/* spec 002 FR-10: a failed read is shown in place. */
.lc-error {
  font-size: 0.85rem; padding: 4px 8px; margin: 2px 0; border-radius: 6px;
  border: 1px solid var(--error-border-color, #ef4444); color: var(--error-text-color, #ef4444);
}
.lc-tip {
  position: fixed; z-index: 10000; display: none; pointer-events: none;
  max-width: 60vw; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  background: var(--background-fill-primary, #1f2937); color: var(--body-text-color, #f3f4f6);
  border: 1px solid var(--border-color-primary, #4b5563); border-radius: 4px;
  padding: 2px 8px; font-size: 0.8rem; box-shadow: 0 2px 6px rgba(0,0,0,0.35);
}
/* The JS bridge needs its targets in the DOM: hide with CSS, not visible=False. */
.lc-bridge { display: none !important; }
"""


def initial_item(request: gr.Request | None) -> str:
    """spec 002 FR-11: the deep-linked entry from `?item=`, or "" for the home view."""
    if request is None:
        return ""
    return (request.query_params.get("item") or "").strip()


def build_console(api: ConsoleApi) -> gr.Blocks:
    """The console Blocks, reading everything through `api` (spec 002 FR-9)."""

    def trees() -> tuple[str, str, str]:
        return board_tree(api), definitions_tree(api), executions_tree(api)

    def show(ref: str, _current: str | None = None):
        title, body, raw = open_ref(api, ref)
        return title, body, raw, ref

    def load(request: gr.Request):
        return (*trees(), *show(initial_item(request)))

    with gr.Blocks(title="Leader Control Center") as demo:
        gr.HTML(f"<style>{_CSS}</style>")
        current = gr.State("")  # the selected ref

        with gr.Sidebar(open=True, width=340):
            with gr.Row(equal_height=True):
                gr.Markdown("### Control Center", elem_id="lc-brand")
                refresh_btn = gr.Button("↻", elem_id="lc-refresh", scale=0, min_width=40)
            views: list[gr.HTML] = []
            for label, elem_id, open_ in MENUS:  # spec 002 FR-2
                with gr.Accordion(label, open=open_, elem_id=elem_id):
                    views.append(gr.HTML("<em>Loading…</em>"))
            # Hidden bridge: JS clicks #nav-go, whose js shim injects the clicked ref.
            nav_pick = gr.Textbox(elem_classes=["lc-bridge"], show_label=False, container=False)
            nav_go = gr.Button(elem_id="nav-go", elem_classes=["lc-bridge"])

        title = gr.Markdown(HOME[0], elem_id="lc-title")
        body = gr.Markdown(HOME[1], elem_id="lc-body")
        with gr.Accordion("Raw JSON", open=False, elem_id="lc-raw-panel"):
            raw = gr.JSON(value=None, show_label=False)

        board_view, definitions_view, executions_view = views
        tree_out = [board_view, definitions_view, executions_view]
        detail_out = [title, body, raw, current]

        demo.load(load, None, tree_out + detail_out).then(None, None, None, js=_MARK_ACTIVE_JS)
        demo.load(None, None, None, js=_NAV_JS)
        demo.load(None, None, None, js=_TIP_JS)
        refresh_btn.click(trees, None, tree_out).then(
            show, [current], detail_out
        ).then(None, None, None, js=_MARK_ACTIVE_JS)
        nav_go.click(show, [nav_pick, current], detail_out, js=_NAV_PICK_JS)

    return demo
