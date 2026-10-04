# Activity Definitions (UI menu: "Tasks")

An **Activity Definition** is a reusable, parameterized building block that a
Temporal workflow runs as an Activity. It is Portfolio-level Catalog data, like
Capability and Workflow Definition. Two kinds exist:

| Kind | What it does when executed |
| ---- | -------------------------- |
| `Bash` | Runs a bash script on a Temporal worker host. |
| `Webhook` | Sends an HTTP request (POST/PUT/PATCH) with a templated payload to a configured URL. |

The sidebar menu is labelled **Tasks** because leaders think of these as "tasks
a workflow can run". In the domain, API and code the term is **Activity
Definition**, because *Task* already means a unit of planned work
(Story → Task, see [../overview/glossary.md](../overview/glossary.md)).

---

## Decisions

| # | Decision | Rationale |
| - | -------- | --------- |
| A1 | Domain term **Activity Definition**; menu label "Tasks". | No clash with planning Tasks; fits the existing Provider type `activity` ([providers.md](./providers.md)). |
| A2 | **v1 = CRUD + preview + webhook test.** Bash scripts are stored and syntax-checked (`bash -n`, parse only), never executed from the UI. | Running pasted scripts from the browser would be remote code execution on the backend host. Bash runs only on a Temporal worker (future). |
| A3 | **Parameters are a JSON Schema** (`input`), edited with the same visual builder as Workflow Definitions. | One parameter format across the product; react-jsonschema-form renders it for testing. |
| A4 | **Secrets are environment references** (`${env:NAME}`) in headers, resolved at send time. | Only the reference is stored; matches "reference credentials, never inline secrets" ([providers.md](./providers.md#credentials--security)). |

---

## Model

```
ActivityDefinition {
  id, portfolioId, name, description
  kind: Bash | Webhook
  input: JSON Schema                  # parameters (A3)
  timeoutSeconds: int                 # default 300 (Bash) / 30 (Webhook)
  # Bash
  script: string
  # Webhook
  method: POST | PUT | PATCH          # default POST
  url: string                         # http(s); may contain {{param}}
  headers: { name: value }            # values may contain {{param}} and ${env:NAME}
  contentType: string                 # default application/json
  bodyTemplate: string
}
```

---

## Templates

Placeholders are `{{name}}`, where `name` is a property of `input`. A
placeholder that is not declared in `input.properties` is rejected on save
(`422`). Values are encoded for the place they are inserted into, so a value can
never break out of its slot:

| Where | `{{name}}` becomes | Example |
| ----- | ------------------ | ------- |
| Bash script | shell-quoted value | `echo {{topic}}` → `echo 'Q3 risk'` |
| Webhook URL | URL-encoded value | `/search?q={{topic}}` → `?q=Q3%20risk` |
| Webhook JSON body | JSON-encoded value (strings keep quotes) | `{"topic": {{topic}}}` → `{"topic": "Q3 risk"}` |
| Webhook other body / headers | value as text | `Bearer ${env:HOOK_TOKEN}` |

- With `contentType: application/json`, the rendered body must parse as JSON.
- `${env:NAME}` is only allowed in header values. It is resolved from the backend
  process environment at send time; a missing variable fails the send (`422`).
  Previews show it masked (`${env:NAME}`), never the secret.
- Missing values: a required parameter missing from the input fails with `422`;
  an optional one renders from the schema `default`, else as empty/`null`.

---

## Commands & API (`/api/v1`)

```
GET    /activity-definitions               list (id, name, kind, updatedAt)
GET    /activity-definitions/{id}          full definition
POST   /activity-definitions               create
PATCH  /activity-definitions/{id}          update (partial)
DELETE /activity-definitions/{id}          delete
POST   /activity-definitions/{id}/render   { input } → rendered script or request (no side effects)
POST   /activity-definitions/{id}/test     { input } → send the webhook once, return the response
```

- Like Workflow Definitions, these are edited directly (catalog data), not
  through planning commands.
- `/render` works for both kinds. `/test` is Webhook-only (`422` for Bash, per A2).
- `/test` response: `{ request: {method, url, headers(masked), body}, status,
  durationMs, responseHeaders, responseBody (truncated to 4 KB) }`. A network
  error or timeout returns `200` with `error` set, because the test itself ran.
- Realtime: `ActivityDefinitionUpdated` on create/update/delete.
- Validation (`422`): empty name; Bash without script or failing `bash -n`;
  Webhook URL not `http(s)`; unknown placeholder; JSON body template that cannot
  render to JSON; `input` that is not a JSON Schema object.

---

## Relationship to Temporal (future)

```
Capability (what)  ──fulfilled by──▶  Provider type `activity`
                                         └─ ActivityDefinition (how, concretely)
Temporal worker:  run_activity_definition(definitionId, version, input)
                    Bash    → subprocess with timeoutSeconds, stdout/stderr → Artifact
                    Webhook → same render + send as /test, response → Artifact
```

- A Workflow Definition step (e.g. `notify(channel)`) will reference an Activity
  Definition by name, so workflows are composed from these blocks.
- Executions record the definition `version` they ran, so later edits never
  change history.
- Bash runs only on worker hosts, never in the API process (A2).

---

## Data

```
activity_definition(id, portfolio_id, name, description, kind,
                    input jsonb, timeout_seconds,
                    script,                                   -- Bash
                    method, url, headers jsonb, content_type, body_template,  -- Webhook
                    created_at, updated_at, version)
```

SQLite MVP: one JSON document per definition, like the other aggregates.

---

## Frontend

Sidebar item **Tasks** (between Workflow and Schedules). Same layout as the
Workflow page: list on the left (name + kind badge), editor on the right:

- Name, description, kind (Bash / Webhook).
- **Parameters**: the JSON Schema visual builder.
- **Bash**: script editor (monospace) and timeout.
- **Webhook**: method, URL, header rows (name/value), content type, body template.
- **Try it**: a parameter form (react-jsonschema-form from `input`) with
  **Preview** (render, no side effects) and, for webhooks, **Send test**, which
  shows status, duration and the response body.
- Delete asks for confirmation.
