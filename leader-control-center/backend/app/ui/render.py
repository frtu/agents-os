"""Pure rendering for the backend console (spec 002): API JSON → sidebar HTML
trees and main-area detail views. No Gradio here, so everything is testable
with a plain `ConsoleApi`.

Every sidebar entry carries a *ref* in `data-ref` that `open_ref` resolves:
`initiative:<id>`, `story:<initiativeId>/<storyId>`, `task:<storyId>/<taskId>`,
`workflow:<id>`, `activity:<id>`, `schedule:<id>`, `execution:<id>`,
`notification:<id>`, `attention:<id>`, or a group header `group:<name>`.
"""
from __future__ import annotations

import html
import json
from collections.abc import Callable
from typing import Any

from app.ui.client import ApiError, ConsoleApi

# Board column order, as the API returns it (spec planning board projection).
COLUMNS = ("Todo", "Ready", "Running", "Blocked", "Completed")

ICONS = {
    "initiative": "🎯",
    "story": "📖",
    "task": "☑️",
    "workflow": "🧩",
    "activity": "⚙️",
    "schedule": "⏰",
    "execution": "▶️",
    "notification": "🔔",
    "attention": "✋",
}

# spec 002 FR-4/FR-5/FR-8: group headers, by ref name → (label, icon kind).
GROUPS = {
    "initiatives": ("Initiatives", "initiative"),
    "workflows": ("Workflows", "workflow"),
    "activities": ("Activities", "activity"),
    "schedules": ("Schedules", "schedule"),
    "executions": ("Executions", "execution"),
    "notifications": ("Notifications", "notification"),
    "attention": ("Attention", "attention"),
}

View = tuple[str, str, Any]  # (title markdown, body markdown, raw JSON)


# --- HTML tree primitives (spec 002 FR-6) ---------------------------------


def _esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _label(ref: str, kind: str, text: str, meta: str = "") -> str:
    """A clickable label: icon + truncated text, full text on hover (FR-6)."""
    tip = f"{text} — {meta}" if meta else text
    meta_html = f"<span class='meta'>{_esc(meta)}</span>" if meta else ""
    return (
        f"<span class='entry' data-ref='{_esc(ref)}' data-tip='{_esc(tip)}'>"
        f"<span class='ico'>{ICONS.get(kind, '•')}</span>"
        f"<span class='label'>{_esc(text)}</span>{meta_html}</span>"
    )


def _leaf(ref: str, kind: str, text: str, meta: str = "") -> str:
    return f"<div class='leaf'>{_label(ref, kind, text, meta)}</div>"


def _node(summary: str, children: str, open_: bool = False) -> str:
    return f"<details{' open' if open_ else ''}><summary>{summary}</summary>{children}</details>"


def _group(name: str, count: int | None, children: str) -> str:
    """A collapsible group whose header label opens the group's table (FR-8)."""
    label, kind = GROUPS[name]
    meta = "" if count is None else str(count)
    return _node(_label(f"group:{name}", kind, label, meta), children or _empty(), open_=True)


def _empty(text: str = "None") -> str:
    return f"<div class='leaf none'><em>{_esc(text)}</em></div>"


def error_html(err: Exception) -> str:
    """spec 002 FR-10: a failed read is shown in place, with its cause."""
    return f"<div class='lc-error'>⚠️ {_esc(err)}</div>"


def _tree(body: str) -> str:
    return f"<div class='lc-tree'>{body}</div>"


def _guard(build: Callable[[], str]) -> str:
    try:
        return build()
    except ApiError as e:
        return error_html(e)


# --- data helpers ----------------------------------------------------------


def _cards(board: dict) -> list[dict]:
    """Board cards in column order then API order (stories by priority)."""
    return [card for col in COLUMNS for card in board.get("columns", {}).get(col, [])]


def _boards(api: ConsoleApi) -> list[tuple[dict, dict]]:
    return [(s, api.board(s["initiative"]["id"])) for s in api.initiatives()]


def _executions(api: ConsoleApi) -> list[dict]:
    """spec 002 FR-5: the latest Story Execution of every Story that has one,
    with its Initiative and Story for labelling (derived from the boards — the
    API has no execution list)."""
    rows: list[dict] = []
    for summary, board in _boards(api):
        for card in _cards(board):
            if card.get("execution"):
                rows.append({
                    "execution": card["execution"],
                    "story": card["story"],
                    "initiative": summary["initiative"],
                    "column": card["column"],
                })
    return rows


# --- sidebar trees (spec 002 FR-3..FR-6) ----------------------------------


def board_tree(api: ConsoleApi) -> str:
    """spec 002 FR-3: Initiatives → Stories (with column) → Tasks."""

    def build() -> str:
        nodes: list[str] = []
        summaries = api.initiatives()
        for s in summaries:
            ini = s["initiative"]
            try:
                stories = _story_nodes(api, ini["id"])
            except ApiError as e:
                stories = error_html(e)
            nodes.append(_node(
                _label(f"initiative:{ini['id']}", "initiative", ini["title"], str(s["storyCount"])),
                stories,
            ))
        return _tree(_group("initiatives", len(summaries), "".join(nodes)))

    return _guard(build)


def _story_nodes(api: ConsoleApi, initiative_id: str) -> str:
    parts: list[str] = []
    for card in _cards(api.board(initiative_id)):
        story = card["story"]
        try:
            tasks = sorted(api.story_tasks(story["id"]), key=lambda t: t.get("order", 0))
            leaves = "".join(
                _leaf(f"task:{story['id']}/{t['id']}", "task", t["name"], t["status"]) for t in tasks
            ) or _empty("No tasks")
        except ApiError as e:
            leaves = error_html(e)
        parts.append(_node(
            _label(f"story:{initiative_id}/{story['id']}", "story", story["title"], card["column"]),
            leaves,
        ))
    return "".join(parts) or _empty("No stories")


def definitions_tree(api: ConsoleApi) -> str:
    """spec 002 FR-4: Workflows, Activities, Schedules."""
    groups: list[str] = []
    for name, load, leaf in (
        ("workflows", api.workflow_definitions,
         lambda d: _leaf(f"workflow:{d['id']}", "workflow", d["name"])),
        ("activities", api.activity_definitions,
         lambda d: _leaf(f"activity:{d['id']}", "activity", d["name"], d["kind"])),
        ("schedules", api.schedules,
         lambda v: _leaf(f"schedule:{v['schedule']['id']}", "schedule",
                         v["schedule"]["name"], v["schedule"]["status"])),
    ):
        try:
            items = load()
            groups.append(_group(name, len(items), "".join(leaf(i) for i in items)))
        except ApiError as e:
            groups.append(_group(name, None, error_html(e)))
    return _tree("".join(groups))


def executions_tree(api: ConsoleApi) -> str:
    """spec 002 FR-5: Executions, Notifications, Attention."""
    groups: list[str] = []
    for name, load, leaf in (
        ("executions", lambda: _executions(api),
         lambda r: _leaf(f"execution:{r['execution']['id']}", "execution",
                         r["story"]["title"], r["execution"]["status"])),
        ("notifications", api.notifications,
         lambda n: _leaf(f"notification:{n['id']}", "notification", n["message"], n["status"])),
        ("attention", api.attention,
         lambda h: _leaf(f"attention:{h['id']}", "attention",
                         f"{h['storyTitle']}: {h['prompt']}", h["type"])),
    ):
        try:
            items = load()
            groups.append(_group(name, len(items), "".join(leaf(i) for i in items)))
        except ApiError as e:
            groups.append(_group(name, None, error_html(e)))
    return _tree("".join(groups))


# --- Markdown helpers ------------------------------------------------------


def _cell(value: Any) -> str:
    if value is None or value == "":
        return "—"
    return str(value).replace("|", "\\|").replace("\n", " ")


def _table(headers: list[str], rows: list[list[Any]]) -> str:
    if not rows:
        return "_None._"
    head = "| " + " | ".join(headers) + " |\n|" + "---|" * len(headers)
    body = "\n".join("| " + " | ".join(_cell(c) for c in row) + " |" for row in rows)
    return f"{head}\n{body}"


def _fields(pairs: list[tuple[str, Any]]) -> str:
    return "\n".join(f"- **{k}:** {_cell(v)}" for k, v in pairs)


def _code(value: Any, lang: str = "") -> str:
    text = value if isinstance(value, str) else json.dumps(value, indent=2)
    return f"```{lang}\n{text}\n```" if text else "_Empty._"


def _title(kind: str, text: str) -> str:
    return f"### {ICONS.get(kind, '')} {text}"


# --- detail views (spec 002 FR-7) ------------------------------------------


def _initiative(api: ConsoleApi, ini_id: str) -> View:
    board = api.board(ini_id)
    ini = board["initiative"]
    counts = [[col, len(board["columns"].get(col, []))] for col in COLUMNS]
    stories = [
        [c["story"]["title"], c["column"], c["story"]["priority"],
         (c.get("execution") or {}).get("status"), c["openHumanRequests"]]
        for c in _cards(board)
    ]
    body = "\n\n".join([
        ini["description"] or "_No description._",
        _fields([("Status", ini["status"]), ("Open Human Requests", board["openHumanRequests"]),
                 ("Workflow Definition", ini.get("workflowDefinitionId"))]),
        "#### Stories per column", _table(["Column", "Stories"], counts),
        "#### Stories", _table(["Story", "Column", "Priority", "Execution", "Open requests"], stories),
    ])
    return _title("initiative", ini["title"]), body, board


def _story(api: ConsoleApi, ini_id: str, story_id: str) -> View:
    card = next((c for c in _cards(api.board(ini_id)) if c["story"]["id"] == story_id), None)
    if card is None:
        raise ApiError(f"story {story_id}", 404, f"Story not on the board of initiative {ini_id}")
    story = card["story"]
    tasks = sorted(api.story_tasks(story_id), key=lambda t: t.get("order", 0))
    execution = card.get("execution")
    body = "\n\n".join([
        story["description"] or "_No description._",
        _fields([("Column", card["column"]), ("Priority", story["priority"]),
                 ("Planning status", story["status"]),
                 ("Latest execution", f"{execution['status']} ({execution['id']})" if execution else None),
                 ("Open Human Requests", card["openHumanRequests"]),
                 ("Schedule", story.get("scheduleId"))]),
        "#### Acceptance criteria",
        "\n".join(f"- {a['description']}" for a in story.get("acceptanceCriteria") or []) or "_None._",
        "#### Tasks",
        _table(["#", "Task", "Mode", "Status", "Capability"],
               [[t["order"], t["name"], t["planningMode"], t["status"], t.get("capabilityId")] for t in tasks]),
    ])
    return _title("story", story["title"]), body, {"card": card, "tasks": tasks}


def _task(api: ConsoleApi, story_id: str, task_id: str) -> View:
    task = next((t for t in api.story_tasks(story_id) if t["id"] == task_id), None)
    if task is None:
        raise ApiError(f"task {task_id}", 404, f"Task not found in story {story_id}")
    body = "\n\n".join([
        _fields([("Story", story_id), ("Order", task["order"]), ("Planning mode", task["planningMode"]),
                 ("Status", task["status"]), ("Capability", task.get("capabilityId")),
                 ("Goal", task.get("goal")),
                 ("Dependencies", ", ".join(task.get("dependencies") or []) or None)]),
        "#### Success criteria",
        "\n".join(f"- {c}" for c in task.get("successCriteria") or []) or "_None._",
    ])
    return _title("task", task["name"]), body, task


def _workflow(api: ConsoleApi, wd_id: str) -> View:
    wd = api.workflow_definition(wd_id)
    body = "\n\n".join([
        _fields([("Id", wd["id"]), ("Version", wd["version"]), ("Updated", wd["updatedAt"])]),
        "#### Input", _code(wd.get("input") or {}, "json"),
        "#### Definition", _code(wd.get("definition") or ""),
    ])
    return _title("workflow", wd["name"]), body, wd


def _activity(api: ConsoleApi, ad_id: str) -> View:
    ad = api.activity_definition(ad_id)
    if ad["kind"] == "Bash":
        request = _code(ad.get("script") or "", "bash")
    else:
        request = "\n\n".join([
            _fields([("Request", f"{ad.get('method')} {ad.get('url')}"),
                     ("Content type", ad.get("contentType"))]),
            "Headers", _code(ad.get("headers") or {}, "json"),
            "Body template", _code(ad.get("bodyTemplate") or ""),
        ])
    body = "\n\n".join([
        ad.get("description") or "_No description._",
        _fields([("Kind", ad["kind"]), ("Timeout", f"{ad['timeoutSeconds']}s")]),
        "#### Input", _code(ad.get("input") or {}, "json"),
        "#### " + ("Script" if ad["kind"] == "Bash" else "Webhook"), request,
    ])
    return _title("activity", ad["name"]), body, ad


def _schedule(api: ConsoleApi, schedule_id: str) -> View:
    view = api.schedule(schedule_id)
    runs = api.schedule_runs(schedule_id)
    s = view["schedule"]
    body = "\n\n".join([
        f"**{view['sentence']}**",
        _fields([("Status", s["status"]), ("Pause reason", s.get("pauseReason")),
                 ("Initiative", s["initiativeId"]), ("Workflow Definition", s["workflowDefinitionId"]),
                 ("Overlap policy", s["overlapPolicy"]), ("Catch-up window", s["catchUpWindow"]),
                 ("Consecutive failures", s["consecutiveFailures"])]),
        "#### Next occurrences",
        "\n".join(f"- {o}" for o in view.get("nextOccurrences") or []) or "_None._",
        "#### Recent runs",
        _table(["Scheduled for", "Status", "Outcome", "Story", "Reason"],
               [[r["scheduledFor"], r["status"], r.get("outcome"), r.get("storyId"),
                 r.get("error") or r.get("reason")] for r in runs]),
    ])
    return _title("schedule", s["name"]), body, {"view": view, "runs": runs}


def _execution(api: ConsoleApi, execution_id: str) -> View:
    ex = api.execution(execution_id)
    decisions = api.open_decisions(execution_id)
    timeline = api.timeline(execution_id)
    body = "\n\n".join([
        _fields([("Story", ex["storyId"]), ("Status", ex["status"]),
                 ("Progress", f"{round(ex['progress'] * 100)}%"),
                 ("Started", ex.get("startedAt")), ("Completed", ex.get("completedAt"))]),
        "#### Task executions",
        _table(["Task", "Status", "Attempt", "Waiting reason"],
               [[t["taskName"], t["status"], t["attempt"], t.get("waitingReason")]
                for t in ex.get("taskExecutions") or []]),
        "#### Open decisions",
        _table(["Type", "Priority", "Prompt", "Actions"],
               [[d["type"], d["priority"], d["prompt"], ", ".join(d.get("actions") or [])]
                for d in decisions]),
        "#### Timeline",
        _table(["When", "Event", "Category", "Detail"],
               [[e["occurredAt"], e["type"], e["category"], e.get("detail")] for e in timeline]),
    ])
    return _title("execution", f"Execution {ex['id']}"), body, {
        "execution": ex, "openDecisions": decisions, "timeline": timeline,
    }


def _from_list(items: list[dict], item_id: str, read: str) -> dict:
    item = next((i for i in items if i["id"] == item_id), None)
    if item is None:
        raise ApiError(read, 404, f"{item_id} is no longer open")
    return item


def _notification(api: ConsoleApi, notification_id: str) -> View:
    n = _from_list(api.notifications(), notification_id, f"notification {notification_id}")
    body = "\n\n".join([n["message"], _fields([("Type", n["type"]), ("Status", n["status"]),
                                                ("Created", n["createdAt"])])])
    return _title("notification", n["type"]), body, n


def _attention(api: ConsoleApi, request_id: str) -> View:
    h = _from_list(api.attention(), request_id, f"human request {request_id}")
    options = "\n".join(f"- {o['label']}" for o in h.get("options") or []) or "_None._"
    body = "\n\n".join([
        f"> {h['prompt']}",
        _fields([("Initiative", h["initiativeTitle"]), ("Story", h["storyTitle"]),
                 ("Execution", h["executionId"]), ("Type", h["type"]), ("Priority", h["priority"]),
                 ("Status", h["status"]), ("Created", h["createdAt"]),
                 ("Actions", ", ".join(h.get("actions") or []))]),
        "#### Options", options,
    ])
    return _title("attention", f"{h['type']} — {h['storyTitle']}"), body, h


# --- group tables (spec 002 FR-8) ------------------------------------------


def _group_view(api: ConsoleApi, name: str) -> View:
    label, kind = GROUPS[name]
    if name == "initiatives":
        items = api.initiatives()
        table = _table(["Initiative", "Status", "Stories", "Open requests"],
                       [[s["initiative"]["title"], s["initiative"]["status"], s["storyCount"],
                         s["openHumanRequests"]] for s in items])
    elif name == "workflows":
        items = api.workflow_definitions()
        table = _table(["Workflow", "Id", "Updated"],
                       [[d["name"], d["id"], d["updatedAt"]] for d in items])
    elif name == "activities":
        items = api.activity_definitions()
        table = _table(["Activity", "Kind", "Timeout", "Description"],
                       [[d["name"], d["kind"], f"{d['timeoutSeconds']}s", d.get("description")] for d in items])
    elif name == "schedules":
        items = api.schedules()
        table = _table(["Schedule", "Status", "When", "Next", "Last run"],
                       [[v["schedule"]["name"], v["schedule"]["status"], v["sentence"],
                         v["schedule"].get("nextOccurrenceAt"), (v.get("lastRun") or {}).get("status")]
                        for v in items])
    elif name == "executions":
        items = _executions(api)
        table = _table(["Initiative", "Story", "Status", "Progress", "Started"],
                       [[r["initiative"]["title"], r["story"]["title"], r["execution"]["status"],
                         f"{round(r['execution']['progress'] * 100)}%", r["execution"].get("startedAt")]
                        for r in items])
    elif name == "notifications":
        items = api.notifications()
        table = _table(["Message", "Type", "Status", "Created"],
                       [[n["message"], n["type"], n["status"], n["createdAt"]] for n in items])
    else:  # attention
        items = api.attention()
        table = _table(["Initiative", "Story", "Type", "Priority", "Prompt"],
                       [[h["initiativeTitle"], h["storyTitle"], h["type"], h["priority"], h["prompt"]]
                        for h in items])
    return _title(kind, f"{label} ({len(items)})"), table, items


# --- dispatch ----------------------------------------------------------------

HOME: View = (
    "### Leader Control Center",
    "Pick an entry in the sidebar — **Board** (Initiatives, Stories, Tasks), "
    "**Definitions** (Workflows, Activities, Schedules) or **Executions** "
    "(Executions, Notifications, Attention). Click a group header for a table.\n\n"
    "_Read-only: answer decisions in the main frontend or via the API._",
    None,
)


def open_ref(api: ConsoleApi, ref: str | None) -> View:
    """Resolve a sidebar ref to its detail view (spec 002 FR-7, FR-8, FR-10)."""
    ref = (ref or "").strip()
    if not ref:
        return HOME
    kind, _, rest = ref.partition(":")
    try:
        if kind == "group" and rest in GROUPS:
            return _group_view(api, rest)
        if kind in ("story", "task") and "/" in rest:
            parent, _, child = rest.partition("/")
            return (_story if kind == "story" else _task)(api, parent, child)
        handler = {
            "initiative": _initiative, "workflow": _workflow, "activity": _activity,
            "schedule": _schedule, "execution": _execution,
            "notification": _notification, "attention": _attention,
        }.get(kind)
        if handler and rest:
            return handler(api, rest)
    except ApiError as e:  # spec 002 FR-10: say which read failed and why
        return "### ⚠️ Could not open entry", f"`{ref}` — {e}", None
    return "### ⚠️ Unknown entry", f"`{ref}` is not a console entry.", None
