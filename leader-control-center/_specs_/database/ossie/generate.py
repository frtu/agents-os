"""Generate the Apache Ossie semantic model for the LCC canonical storage model.

Usage (from leader-control-center/):
  uv run --no-project --with pyyaml python _specs_/database/ossie/generate.py \
    _specs_/database/ossie/leader-control-center.ossie.yaml
"""
import json
import sys

import yaml

S, I, F, B, T, O = "String", "Integer", "Float", "Boolean", "DateTimeTz", "Opaque"
VENDOR = "LEADER_CONTROL_CENTER"
DM = "_specs_/database/data-model.md"


def ext(d):
    return [{"vendor_name": VENDOR, "data": json.dumps(d, separators=(",", ":"))}]


def col(expr):
    return {"dialects": [{"dialect": "ANSI_SQL", "expression": expr}]}


# field tuple: (name, datatype, description, mvp_note | None, label | None)
def F_(name, dt, desc, mvp=None, label=None, dim=None):
    f = {"name": name, "expression": col(name), "datatype": dt}
    if dim is not None:
        f["dimension"] = {"is_time": dim}
    if label:
        f["label"] = label
    f["description"] = desc
    if mvp:
        f["custom_extensions"] = ext({"mvp": mvp})
    return f


def ID(desc="Primary key (string id, e.g. story_ab12cd34)."):
    return F_("id", S, desc, dim=False)


def FK(name, target, mvp=None):
    return F_(name, S, f"Reference to {target}.id.", mvp, dim=False)


def STATUS(values, mvp=None, name="status"):
    return F_(name, S, "One of: " + " | ".join(values) + ".", mvp, dim=False)


def AUDIT(mvp=None):
    return [
        F_("created_at", T, "Row creation instant (UTC).", mvp),
        F_("updated_at", T, "Last mutation instant (UTC).", mvp),
        F_("version", I, "Optimistic-locking counter; bumped on every write, guarded with WHERE version = ?.", mvp, dim=False),
    ]


def DS(name, context, mutability, domain, desc, fields, mvp, api=(), synonyms=(), pk=("id",), uniq=None, anchor=None):
    d = {"name": name, "source": f"lcc.main.{name}"}
    if pk:
        d["primary_key"] = list(pk)
    if uniq:
        d["unique_keys"] = uniq
    d["description"] = desc
    if synonyms:
        d["ai_context"] = {"synonyms": list(synonyms)}
    d["fields"] = fields
    d["custom_extensions"] = ext({
        "bounded_context": context,
        "mutability": mutability,
        "domain_type": domain,
        "spec": f"{DM}#{anchor or name.replace('_', '-')}",
        "mvp": mvp,
        "api": list(api),
    })
    return d


NO_AUDIT = "missing: not a Resource (no created_at/updated_at/version)"

datasets = [
    # --- Tenancy / catalog ------------------------------------------------
    DS("workspace", "Identity", "mutable", "Workspace", "Top-level tenant boundary.",
       [ID(), F_("name", S, "Display name."), F_("created_at", T, "Creation instant.")],
       {"status": "not-implemented"}, anchor="workspace--portfolio"),
    DS("portfolio", "Planning", "mutable", "Portfolio",
       "Group of initiatives sharing a catalog (capabilities, providers, definitions) and default AI config.",
       [ID(), FK("workspace_id", "workspace"), F_("name", S, "Display name."),
        F_("default_ai_config", O, "jsonb: default model/provider settings.")],
       {"status": "not-implemented", "note": "portfolio_id is the constant 'portfolio_default' on child rows; no portfolio row exists"},
       anchor="workspace--portfolio"),
    DS("capability", "Catalog", "mutable", "Capability",
       "WHAT ability is required (e.g. Code Review). Versioned catalog entry referenced by Structured tasks.",
       [ID(), FK("portfolio_id", "portfolio", "missing"), F_("name", S, "Capability name."),
        F_("description", S, "What the capability does."),
        F_("inputs", O, "jsonb: input contract.", "string (free text), not JSON"),
        F_("outputs", O, "jsonb: output contract.", "string (free text), not JSON"),
        F_("version", I, "Catalog version of the capability contract.", "missing", dim=False),
        STATUS(["Active", "Deprecated"], "missing")],
       {"collection": "capabilities", "path": "$", "extra_fields": ["supported_providers (inverse of provider.supported_capabilities)"], "audit": NO_AUDIT},
       api=["GET /capabilities"], synonyms=["ability", "skill"]),
    DS("provider", "Catalog", "mutable", "Provider",
       "WHO performs a capability: OpenAI, Anthropic, Human, MCP, Temporal activity. Interchangeable.",
       [ID(), FK("portfolio_id", "portfolio", "missing"), F_("name", S, "Provider name."),
        STATUS(["llm", "mcp", "human", "activity"], name="type"),
        F_("supported_capabilities", O, "uuid[] of capability ids.", "inverted: stored as capability.supported_providers"),
        F_("config", O, "jsonb: provider configuration.", "missing"),
        F_("credential_ref", S, "Reference to credential.id; secrets live outside the DB.", "missing", dim=False),
        STATUS(["Active", "Disabled"], "missing")],
       {"collection": "providers", "path": "$", "audit": NO_AUDIT},
       api=["GET /providers"], synonyms=["executor", "model", "agent backend"]),
    DS("provider_capability", "Catalog", "mutable", "ProviderCapability",
       "Junction realizing provider.supported_capabilities (storage.md preferred alternative to the uuid[] column).",
       [FK("provider_id", "provider"), FK("capability_id", "capability")],
       {"status": "proposed", "derivable_from": "capabilities.$.supported_providers[*]"},
       pk=("provider_id", "capability_id"), anchor="provider"),
    DS("workflow_definition", "Catalog", "mutable", "WorkflowDefinition",
       "Reusable authoring-time blueprint (JSON-Schema input + DSL) that seeds initiatives, stories and schedules. Not the workflow engine.",
       [ID(), FK("portfolio_id", "portfolio"), F_("name", S, "Blueprint name."),
        F_("input", O, "jsonb: JSON Schema of instance parameters."),
        F_("definition", S, "DSL body."), STATUS(["Active", "Archived"], "missing (storage D6)")] + AUDIT(),
       {"collection": "workflow_definitions", "path": "$", "delete": "hard delete; referencing story/schedule rows keep a dangling id",
        "target": "archive instead of delete (storage D6)"},
       api=["GET /workflow-definitions", "GET /workflow-definitions/{id}", "POST /workflow-definitions",
            "PATCH /workflow-definitions/{id}", "DELETE /workflow-definitions/{id}"],
       synonyms=["template", "blueprint"]),
    DS("activity_definition", "Catalog", "mutable", "ActivityDefinition",
       "Reusable Bash or Webhook building block executed by the activity provider.",
       [ID(), FK("portfolio_id", "portfolio"), F_("name", S, "Name."), F_("description", S, "Description."),
        STATUS(["Bash", "Webhook"], name="kind"), F_("input", O, "jsonb: JSON Schema of parameters."),
        F_("timeout_seconds", I, "Execution timeout.", dim=False), F_("script", S, "Bash body."),
        STATUS(["GET", "POST", "PUT", "PATCH", "DELETE"], name="method"), F_("url", S, "Webhook URL."),
        F_("headers", O, "jsonb: headers; may hold ${env:NAME} refs."), F_("content_type", S, "Body content type."),
        F_("body_template", S, "Webhook body template."), STATUS(["Active", "Archived"], "missing (storage D6)")] + AUDIT(),
       {"collection": "activity_definitions", "path": "$", "delete": "hard delete", "target": "archive instead of delete (storage D6)"},
       api=["GET /activity-definitions", "GET /activity-definitions/{id}", "POST /activity-definitions",
            "PATCH /activity-definitions/{id}", "DELETE /activity-definitions/{id}",
            "POST /activity-definitions/{id}/render", "POST /activity-definitions/{id}/test"],
       synonyms=["activity", "script", "webhook"]),
    # --- Planning (immutable intent) ---------------------------------------
    DS("initiative", "Planning", "mutable-intent", "Initiative", "Business objective; hosts epics and schedules.",
       [ID(), FK("portfolio_id", "portfolio"), F_("title", S, "Title."), F_("description", S, "Description."),
        STATUS(["Draft", "Ready", "Archived"], "adds Deleted (soft delete; stories reparented to init_misc)"),
        FK("workflow_definition_id", "workflow_definition")] + AUDIT(),
       {"collection": "initiatives", "path": "$", "extra_fields": ["order (board position, POST /initiatives/reorder)"]},
       api=["GET /initiatives", "POST /initiatives", "PATCH /initiatives/{id}", "POST /initiatives/reorder",
            "POST /initiatives/{id}/delete", "GET /initiatives/{id}/board"],
       synonyms=["objective", "program", "board"]),
    DS("epic", "Planning", "mutable-intent", "Epic", "Major deliverable inside an initiative.",
       [ID(), FK("initiative_id", "initiative"), F_("title", S, "Title."),
        F_("description", S, "Description.", "missing"), STATUS(["Draft", "Ready", "Archived"], "missing")] + AUDIT("missing"),
       {"collection": "epics", "path": "$", "note": "thin EpicRow(id, initiative_id, title); exactly one implicit epic per initiative; no API",
        "target": "full canonical columns, still implicit (storage D9)"}),
    DS("story", "Planning", "mutable-intent", "Story",
       "Unit of business value; the thing that is started, executed and supervised.",
       [ID(), FK("epic_id", "epic"), F_("title", S, "Title."), F_("description", S, "Description."),
        F_("priority", I, "Priority (lower = more urgent).", dim=False),
        STATUS(["Draft", "Ready", "Archived"], "adds Deleted (soft delete)"),
        FK("workflow_definition_id", "workflow_definition"),
        F_("template_input", O, "jsonb: instance params, validated against workflow_definition.input."),
        FK("schedule_id", "schedule"), F_("scheduled_for", T, "Occurrence that created this story.")] + AUDIT(),
       {"collection": "stories", "path": "$", "embedded": ["acceptance_criteria[] (canonical: own table)"]},
       api=["POST /stories", "PATCH /stories/{id}", "DELETE /stories/{id}", "POST /stories/draft",
            "GET /stories/{id}/tasks", "GET /stories/{id}/artifacts", "POST /stories/{id}/start"],
       synonyms=["card", "work item", "ticket"]),
    DS("schedule", "Planning", "mutable", "Schedule", "Time trigger that creates Stories from a Workflow Definition.",
       [ID(), FK("initiative_id", "initiative"), F_("name", S, "Name."), FK("workflow_definition_id", "workflow_definition"),
        F_("template_input", O, "jsonb: params for created stories."), F_("story_title_template", S, "Title template."),
        F_("spec", O, "jsonb: {kind: Once|Interval|Cron, ...}."),
        STATUS(["Skip", "BufferOne", "AllowParallel"], name="overlap_policy"),
        F_("catch_up_window_seconds", I, "Missed-occurrence catch-up window.", "stored as ISO-8601 duration string catch_up_window (e.g. PT1H)", dim=False),
        F_("keep_completed", I, "Completed stories retained.", dim=False),
        STATUS(["Active", "Paused", "Completed", "Archived"]),
        STATUS(["Manual", "ConsecutiveFailures", "InvalidTemplate"], name="pause_reason"),
        F_("consecutive_failures", I, "Failure streak driving auto-pause.", dim=False),
        F_("next_occurrence_at", T, "Next fire instant."), F_("created_by", S, "Author.", dim=False)] + AUDIT(),
       {"collection": "schedules", "path": "$"},
       api=["GET /schedules", "POST /schedules/preview", "POST /schedules", "GET /schedules/{id}",
            "PATCH /schedules/{id}", "POST /schedules/{id}/pause", "POST /schedules/{id}/resume",
            "POST /schedules/{id}/trigger", "POST /schedules/{id}/archive"],
       synonyms=["recurrence", "cron", "trigger"], anchor="schedule--schedule_run"),
    DS("schedule_run", "Planning", "append-only", "ScheduleRun", "One occurrence of a schedule and its outcome.",
       [ID(), FK("schedule_id", "schedule"), F_("scheduled_for", T, "Occurrence instant."), F_("fired_at", T, "Actual fire instant."),
        STATUS(["Started", "Buffered", "Skipped", "Missed", "FailedToStart"]),
        F_("reason", S, "Why it was skipped/missed/failed (P9)."), FK("story_id", "story"), F_("error", S, "Failure cause.")],
       {"collection": "schedule_runs", "path": "$", "extra_fields": ["settled_at", "outcome"],
        "constraint_gap": "unique(schedule_id, scheduled_for) enforced in code only"},
       api=["GET /schedules/{id}/runs", "POST /schedules/{id}/trigger"],
       uniq=[["schedule_id", "scheduled_for"]], anchor="schedule--schedule_run"),
    DS("task", "Planning", "mutable-intent", "Task", "Step of a story: Structured (capability) or GoalOriented (goal + success criteria).",
       [ID(), FK("story_id", "story"), F_("name", S, "Name."), STATUS(["Structured", "GoalOriented"], name="planning_mode"),
        FK("capability_id", "capability"), F_("capability_version", I, "Pinned capability version.", "missing", dim=False),
        F_("goal", S, "GoalOriented goal."), F_("success_criteria", O, "jsonb: success criteria list."),
        STATUS(["Draft", "Ready", "Cancelled"]), F_("order", I, "Position within the story.", dim=False)] + AUDIT(),
       {"collection": "tasks", "path": "$", "embedded": ["dependencies[] (canonical: dependency table)"]},
       api=["GET /stories/{id}/tasks", "POST /tasks/{id}/ready", "POST /tasks/{id}/start"], synonyms=["step"]),
    DS("dependency", "Planning", "mutable-intent", "Dependency", "Edge of the per-story task DAG.",
       [FK("task_id", "task"), FK("depends_on_task_id", "task")],
       {"collection": "tasks", "path": "$.dependencies[*]", "note": "embedded list of task ids"},
       pk=("task_id", "depends_on_task_id")),
    DS("acceptance_criteria", "Planning", "mutable-intent", "AcceptanceCriteria", "Done-definition line for a story or a task (exactly one set).",
       [ID(), FK("story_id", "story"), FK("task_id", "task", "missing: task-level criteria unsupported"), F_("description", S, "Criterion text.")],
       {"collection": "stories", "path": "$.acceptance_criteria[*]"}),
    # --- Runtime (disposable execution) ------------------------------------
    DS("story_execution", "Runtime", "mutable-runtime", "StoryExecution", "One run of a story.",
       [ID(), FK("story_id", "story"), F_("attempt", I, "Run number for the story (1-based).", "missing (storage D1)", dim=False),
        STATUS(["Created", "Running", "Waiting", "Completed", "Cancelled", "Failed"]),
        F_("started_at", T, "Start instant."), F_("completed_at", T, "End instant.")],
       {"collection": "story_executions", "path": "$", "extra_fields": ["progress"], "audit": NO_AUDIT,
        "history_gap": "start/retry pop the previous execution; only the latest run per story survives",
        "target": "superseded runs move read-only to collection story_executions_archive (storage D1)"},
       api=["POST /stories/{id}/start", "GET /executions/{id}", "POST /executions/{id}/cancel", "POST /executions/{id}/retry"],
       synonyms=["run", "execution"]),
    DS("task_execution", "Runtime", "mutable-runtime", "TaskExecution", "Run of one task inside a story execution.",
       [ID(), FK("story_execution_id", "story_execution"), FK("task_id", "task"),
        STATUS(["Created", "Running", "WaitingDecision", "Completed", "Failed", "Cancelled"]),
        F_("started_at", T, "Start instant."), F_("completed_at", T, "End instant.")],
       {"collection": "story_executions", "path": "$.task_executions[*]", "extra_fields": ["task_name", "attempt", "waiting_reason"]}),
    DS("capability_execution", "Runtime", "mutable-runtime", "CapabilityExecution", "Capability invocation under an Execution Strategy (HOW).",
       [ID(), FK("task_execution_id", "task_execution"), FK("capability_id", "capability"),
        STATUS(["SingleProvider", "Retry", "Parallel", "Consensus", "HumanReview", "Pipeline", "Loop", "FanOut"], name="strategy"),
        STATUS(["Pending", "Running", "Waiting", "Completed", "Failed"])],
       {"collection": "story_executions", "path": "$.task_executions[*].capability_executions[*]", "extra_fields": ["capability_name"]},
       synonyms=["strategy run"]),
    DS("provider_execution", "Runtime", "mutable-runtime", "ProviderExecution", "One provider attempt for a capability execution.",
       [ID(), FK("capability_execution_id", "capability_execution"), FK("provider_id", "provider"),
        STATUS(["Scheduled", "Running", "Succeeded", "Failed", "Cancelled"]), F_("attempt", I, "Attempt number (1-based).", dim=False),
        F_("started_at", T, "Start instant."), F_("ended_at", T, "End instant."), F_("result", O, "jsonb: provider output.", "missing")],
       {"collection": "story_executions", "path": "$.task_executions[*].capability_executions[*].provider_executions[*]", "extra_fields": ["provider_name"]},
       synonyms=["attempt", "provider call"]),
    # --- Human interaction --------------------------------------------------
    DS("human_request", "HumanInteraction", "mutable-runtime", "HumanRequest",
       "Every pause is a Human Request; open ones form the Attention Queue.",
       [ID(), FK("execution_id", "story_execution"), FK("initiative_id", "initiative"),
        STATUS(["Approval", "Clarification", "Budget", "ToolPermission", "MissingInformation", "ChooseOption", "RiskAcceptance"], name="type"),
        F_("prompt", S, "Question asked of the human."), F_("options", O, "jsonb: [{id,label}] for ChooseOption."),
        STATUS(["low", "medium", "high"], name="priority"),
        STATUS(["Created", "Visible", "Acknowledged", "Resolved", "Closed"]), F_("created_at", T, "Pause instant.")],
       {"collection": "human_requests", "path": "$",
        "extra_fields": ["story_id", "story_title", "initiative_title (denormalized)", "actions (allowed DecisionKinds)"]},
       api=["GET /attention", "GET /executions/{id}/decisions"],
       synonyms=["decision request", "pause", "approval request", "attention item"], anchor="human_request"),
    DS("decision", "HumanInteraction", "immutable", "Decision", "The single answer to a Human Request. Never updated.",
       [ID(), FK("human_request_id", "human_request"),
        STATUS(["Approve", "Reject", "Clarify", "Continue", "Abort", "Retry", "SelectOption", "Custom"], name="decision"),
        F_("selected_option", S, "Chosen option id.", dim=False), F_("comment", S, "Free-text rationale."),
        FK("user_id", "app_user", "stored as free-text 'user' (no FK)"), F_("created_at", T, "Decision instant.")],
       {"collection": "decisions", "path": "$", "extra_fields": ["action_name (Custom)"]},
       api=["GET /executions/{id}/decisions/history", "POST /executions/{id}/decisions/{rid}/{approve|reject|clarify|continue|abort|retry|select|custom}"],
       synonyms=["answer", "verdict", "approval"], uniq=[["human_request_id"]]),
    # --- Artifacts -----------------------------------------------------------
    DS("artifact", "Artifacts", "immutable", "Artifact", "Versioned output of an execution; a new version is a new row.",
       [ID(), FK("execution_id", "story_execution"),
        STATUS(["Markdown", "Document", "Specification", "Presentation", "Spreadsheet", "Diagram", "Image", "PDF", "SourceCode", "TestReport", "Research", "Architecture", "JSON"], name="type"),
        F_("version", I, "Artifact version (1-based).", dim=False), F_("owner", S, "Owning party.", "missing", dim=False),
        F_("created_by", S, "Producer (provider or user).", dim=False),
        F_("location", S, "Blob/object-store URI of the content.", "missing: content stored inline in the JSON document"),
        F_("metadata", O, "jsonb: metadata.", "missing"), FK("parent_artifact_id", "artifact"), F_("created_at", T, "Creation instant.")],
       {"collection": "artifacts", "path": "$", "extra_fields": ["story_id", "name", "content (inline)", "language"],
        "target": "content in data/artifacts/<sha256>; location + metadata on the row (storage D5)"},
       api=["GET /stories/{id}/artifacts", "GET /artifacts/{id}"], synonyms=["output", "deliverable"]),
    # --- Events & projections ----------------------------------------------
    DS("event", "Events", "append-only", "DomainEvent", "Append-only source of truth; projections are rebuilt from it.",
       [ID(), F_("type", S, "Event type, e.g. StoryStarted."), STATUS(["Planning", "Runtime", "Decision", "Artifact", "Notification", "System"], name="category"),
        F_("aggregate_id", S, "Aggregate the event belongs to.", dim=False), FK("initiative_id", "initiative"),
        F_("payload", O, "jsonb: event body."), F_("actor", S, "Who/what caused it.", dim=False),
        F_("occurred_at", T, "Occurrence instant."), F_("sequence", I, "Monotonic per aggregate_id.", dim=False)],
       {"status": "not-persisted", "note": "realtime bus only (WS /stream, global in-memory sequence); snapshot written instead",
        "target": "append-only SQLite event table written with each aggregate upsert (storage D2)"},
       api=["WS /stream"], uniq=[["aggregate_id", "sequence"]], anchor="event-append-only-source-of-truth"),
    DS("timeline_entry", "Projections", "derived", "TimelineEvent", "Per-execution narrative projection.",
       [ID(), FK("execution_id", "story_execution"), F_("type", S, "Entry type."), F_("payload", O, "jsonb: details.", "category + detail columns instead of payload"),
        F_("occurred_at", T, "Occurrence instant.")],
       {"collection": "timeline", "path": "$", "note": "written directly, not derived from events"},
       api=["GET /executions/{id}/timeline"], synonyms=["history", "activity log"], anchor="projections-rebuildable-from-events"),
    DS("attention_item", "Projections", "derived", "AttentionItem", "Open human requests, global queue.",
       [ID(), FK("initiative_id", "initiative"), FK("execution_id", "story_execution"), F_("type", S, "Request type."),
        F_("priority", S, "Priority.", dim=False), F_("waiting_since", T, "Pause instant.")],
       {"status": "derived-on-read", "derivable_from": "human_requests where status not in (Resolved, Closed)"},
       api=["GET /attention"], synonyms=["attention queue", "inbox"], anchor="projections-rebuildable-from-events"),
    DS("notification", "Projections", "mutable", "Notification", "Per-user notification.",
       [ID(), FK("user_id", "app_user", "missing (single global list)"), F_("type", S, "Notification type."),
        F_("payload", O, "jsonb: body.", "message string instead"), F_("read", B, "Read flag.", "status UNREAD|READ|ACKED|CLOSED instead"),
        F_("created_at", T, "Creation instant.")],
       {"collection": "notifications", "path": "$"},
       api=["GET /notifications", "POST /notifications/{id}/open", "POST /notifications/{id}/ack", "POST /notifications/{id}/close"],
       anchor="projections-rebuildable-from-events"),
    # --- Identity -----------------------------------------------------------
    DS("app_user", "Identity", "mutable", "User", "Human supervisor.",
       [ID(), FK("portfolio_id", "portfolio"), F_("name", S, "Name."), F_("email", S, "Email.", dim=False),
        STATUS(["Viewer", "Supervisor", "Admin"], name="role")],
       {"status": "not-implemented"}, synonyms=["user", "leader", "supervisor"], anchor="identity--access"),
    DS("credential", "Identity", "mutable", "Credential", "Named secret reference; secret material is external.",
       [ID(), FK("portfolio_id", "portfolio"), F_("name", S, "Name."), F_("secret_ref", S, "External secret reference.", dim=False)],
       {"status": "not-implemented"}, anchor="identity--access"),
]


def R(frm, to, fcols, tcols=("id",), name=None):
    fcols = [fcols] if isinstance(fcols, str) else list(fcols)
    return {"name": name or f"{frm}_{fcols[0].removesuffix('_id')}_{to}", "from": frm, "to": to,
            "from_columns": fcols, "to_columns": list(tcols)}


relationships = [
    R("portfolio", "workspace", "workspace_id"),
    R("capability", "portfolio", "portfolio_id"), R("provider", "portfolio", "portfolio_id"),
    R("provider_capability", "provider", "provider_id"), R("provider_capability", "capability", "capability_id"),
    R("workflow_definition", "portfolio", "portfolio_id"), R("activity_definition", "portfolio", "portfolio_id"),
    R("initiative", "portfolio", "portfolio_id"), R("initiative", "workflow_definition", "workflow_definition_id"),
    R("epic", "initiative", "initiative_id"), R("story", "epic", "epic_id"),
    R("story", "workflow_definition", "workflow_definition_id"), R("story", "schedule", "schedule_id"),
    R("schedule", "initiative", "initiative_id"), R("schedule", "workflow_definition", "workflow_definition_id"),
    R("schedule_run", "schedule", "schedule_id"), R("schedule_run", "story", "story_id"),
    R("task", "story", "story_id"), R("task", "capability", "capability_id"),
    R("dependency", "task", "task_id", name="dependency_dependent_task"),
    R("dependency", "task", "depends_on_task_id", name="dependency_prerequisite_task"),
    R("acceptance_criteria", "story", "story_id"), R("acceptance_criteria", "task", "task_id"),
    R("story_execution", "story", "story_id"),
    R("task_execution", "story_execution", "story_execution_id"), R("task_execution", "task", "task_id"),
    R("capability_execution", "task_execution", "task_execution_id"), R("capability_execution", "capability", "capability_id"),
    R("provider_execution", "capability_execution", "capability_execution_id"), R("provider_execution", "provider", "provider_id"),
    R("human_request", "story_execution", "execution_id"), R("human_request", "initiative", "initiative_id"),
    R("decision", "human_request", "human_request_id"), R("decision", "app_user", "user_id"),
    R("artifact", "story_execution", "execution_id"), R("artifact", "artifact", "parent_artifact_id", name="artifact_parent_version"),
    R("event", "initiative", "initiative_id"),
    R("timeline_entry", "story_execution", "execution_id"),
    R("attention_item", "initiative", "initiative_id"), R("attention_item", "story_execution", "execution_id"),
    R("notification", "app_user", "user_id"),
    R("app_user", "portfolio", "portfolio_id"), R("credential", "portfolio", "portfolio_id"),
]

OPEN_HR = "human_request.status IN ('Created', 'Visible', 'Acknowledged')"
TERMINAL = "IN ('Completed', 'Failed', 'Cancelled')"


def M(name, expr, dt, desc, synonyms=()):
    m = {"name": name, "expression": col(expr), "datatype": dt, "description": desc}
    if synonyms:
        m["ai_context"] = {"synonyms": list(synonyms)}
    return m


metrics = [
    M("attention_queue_size", f"COUNT(CASE WHEN {OPEN_HR} THEN 1 END)", I,
      "Open Human Requests awaiting a Decision (the Attention Queue).", ["open decisions", "pending approvals", "inbox size"]),
    M("high_priority_attention", f"COUNT(CASE WHEN {OPEN_HR} AND human_request.priority = 'high' THEN 1 END)", I,
      "Open high-priority Human Requests."),
    M("decision_count", "COUNT(decision.id)", I, "Decisions recorded (immutable)."),
    M("decision_latency_avg", "AVG(decision.created_at - human_request.created_at)", O,
      "Mean pause-to-decision interval (INTERVAL; dialect-specific epoch extraction needed for seconds).",
      ["time to decision", "human response time"]),
    M("story_execution_count", "COUNT(story_execution.id)", I, "Story executions (runs)."),
    M("story_executions_waiting", "COUNT(CASE WHEN story_execution.status = 'Waiting' THEN 1 END)", I,
      "Runs blocked on a human."),
    M("story_execution_success_rate",
      f"SUM(CASE WHEN story_execution.status = 'Completed' THEN 1.0 ELSE 0 END) / NULLIF(COUNT(CASE WHEN story_execution.status {TERMINAL} THEN 1 END), 0)",
      F, "Completed / terminal story executions.", ["success rate", "completion rate"]),
    M("task_execution_failure_rate",
      f"SUM(CASE WHEN task_execution.status = 'Failed' THEN 1.0 ELSE 0 END) / NULLIF(COUNT(CASE WHEN task_execution.status {TERMINAL} THEN 1 END), 0)",
      F, "Failed / terminal task executions."),
    M("provider_success_rate",
      "SUM(CASE WHEN provider_execution.status = 'Succeeded' THEN 1.0 ELSE 0 END) / NULLIF(COUNT(CASE WHEN provider_execution.status IN ('Succeeded', 'Failed', 'Cancelled') THEN 1 END), 0)",
      F, "Succeeded / terminal provider attempts; compare providers for the same capability."),
    M("provider_attempts_avg", "AVG(provider_execution.attempt)", F, "Mean attempt number per provider execution (retry pressure)."),
    M("human_requests_per_execution", "COUNT(human_request.id) * 1.0 / NULLIF(COUNT(DISTINCT story_execution.id), 0)", F,
      "Human interventions per run (autonomy indicator)."),
    M("artifacts_produced", "COUNT(artifact.id)", I, "Artifact versions produced."),
    M("schedule_runs_failed_to_start", "COUNT(CASE WHEN schedule_run.status = 'FailedToStart' THEN 1 END)", I,
      "Occurrences that could not create a Story."),
    M("schedule_runs_missed", "COUNT(CASE WHEN schedule_run.status IN ('Missed', 'Skipped') THEN 1 END)", I,
      "Occurrences skipped by overlap policy or missed outside the catch-up window."),
    M("unread_notifications", "COUNT(CASE WHEN notification.read = FALSE THEN 1 END)", I, "Unread notifications."),
]

model = {
    "version": "0.2.0.dev0",
    "name": "leader_control_center",
    "description": ("Semantic/ontology layer for the Leader Control Center canonical storage model "
                    "(_specs_/database/data-model.md): a human-in-the-loop control plane supervising durable AI workflows. "
                    "Sources name the canonical normalized tables; the as-built SQLite realization of each dataset is in its "
                    f"{VENDOR} extension (mvp)."),
    "ai_context": {
        "instructions": ("Planning (initiative > epic > story > task) is immutable intent; Runtime "
                         "(story_execution > task_execution > capability_execution > provider_execution) is disposable; "
                         "history (event, decision, artifact) is permanent. Capability = what, execution strategy = how, "
                         "provider = who. Every pause is a human_request and each yields exactly one decision. "
                         "The Attention Queue is the set of open human_requests. Planning never references Runtime."),
        "synonyms": ["LCC", "supervision console", "control plane"],
        "examples": [
            "How many approvals are waiting, by initiative?",
            "What is the mean time to decision this week?",
            "Which provider has the best success rate for the Code Review capability?",
            "Which schedules failed to start a story in the last 24 hours?",
        ],
    },
    "datasets": datasets,
    "relationships": relationships,
    "metrics": metrics,
    "custom_extensions": ext({
        "spec": DM,
        "storage_overlay": "backend/storage.md",
        "mvp_physical": "SQLite aggregates(collection, id, ord, data JSON) at ../data/leader-control-center.db",
        "local_sources": "canonical-named SQL views over aggregates resolve each dataset source locally (storage D4)",
        "ids": "prefix_ + ULID, opaque strings (storage D7)",
        "invariants": [
            "Planning has no FK to Runtime",
            "event, decision, artifact rows are immutable",
            "dependency is a DAG within a story",
            "one decision per human_request",
            "schedule_run unique (schedule_id, scheduled_for)",
            "optimistic locking via version on mutable aggregates",
        ],
    }),
}

HEADER = """\
# Apache Ossie (incubating) semantic model — Leader Control Center
# Spec: Ossie core-spec 0.2.0.dev0 (https://github.com/apache/ossie/tree/main/core-spec)
# Canonical schema: _specs_/database/data-model.md · mapping: _specs_/database/api-storage-mapping.md
# Vendor extension LEADER_CONTROL_CENTER carries bounded context, mutability, API surface and
# the as-built SQLite realization ("mvp") per dataset/field.
# GENERATED by _specs_/database/ossie/generate.py — edit the generator, not this file.
"""

with open(sys.argv[1], "w") as fh:
    fh.write(HEADER)
    yaml.safe_dump(model, fh, sort_keys=False, allow_unicode=True, width=120)
