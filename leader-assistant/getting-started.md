# Getting Started

Leader Assistant is a **local** knowledge & specification service. It stores everything
as Markdown in a git-versioned *vault* (no database) and exposes a REST API with an
interactive **Swagger UI**. This guide gets it running on your machine.

## 1. Prerequisites

- Python **3.13+**
- [uv](https://docs.astral.sh/uv/) for dependency management

No API key is required to run the current version — it is filesystem-only.

## 2. Install

```bash
# from the / directory
uv sync
```

## 3. Run

```bash
uv run app
```

On startup it prints a banner with the URLs, e.g.:

```text
  Leader Assistant — local service
  --------------------------------
  Web UI     : http://localhost:8000/
  Swagger UI : http://localhost:8000/api/
  ReDoc      : http://localhost:8000/redoc
  OpenAPI    : http://localhost:8000/openapi.json
  Health     : http://localhost:8000/health
```

Open **http://localhost:8000/** for the web UI, or **http://localhost:8000/api/** for
the Swagger UI, which lets you try every endpoint from the browser. Press `Ctrl+C` to
stop.

### Change host / port

```bash
LEADER_PORT=8080 uv run app
```

## 4. Where your data lives

Everything is stored under a **vault** directory. By default vaults live in `./Vaults/`
and are git-ignored. Each vault is its own git repository, so every change is committed
to its own history — never to this project's repo.

Override the location with environment variables:

| Variable | Purpose | Default |
|----------|---------|---------|
| `LEADER_VAULT_ROOT` | folder that holds `Vaults/<name>/` | `./Vaults` |
| `LEADER_VAULT_PATH` | point at one specific vault directory | — |
| `LEADER_DEFAULT_VAULT` | which vault is used when you don't name one | `default` |

```bash
LEADER_VAULT_ROOT=~/my-vaults uv run app
```

A vault is scaffolded automatically the first time you use it:

```text
<vault>/
├── raw/        # your original sources (never modified by the app)
├── wiki/       # generated knowledge (source summaries, concepts, portal.md, log.md)
├── sessions/   # short-term conversation logs
└── output/     # generated artifacts
```

## 5. A 60-second tour (curl)

Assuming the server is on port 8000:

```bash
# health
curl -s localhost:8000/health

# create a vault
curl -s -X POST localhost:8000/api/vaults \
  -H 'content-type: application/json' -d '{"name":"demo"}'

# ingest a source (summarised into wiki/sources/, committed to the vault's git)
curl -s -X POST localhost:8000/api/ingest \
  -H 'content-type: application/json' \
  -d '{"vault":"demo","title":"Team sync","provenance":"transcripts",
       "content":"We decided to ship the API on Friday."}'

# ask a question — answers come back with citations to vault pages
curl -s -X POST localhost:8000/api/query \
  -H 'content-type: application/json' \
  -d '{"vault":"demo","question":"What did we decide to ship?"}'
```

## 6. What the API can do

Every endpoint is a thin call over the shared capability layer, so the chat and
REST surfaces stay in parity. Base URL: `http://localhost:8000`.

| Method | Path | What it does |
|--------|------|--------------|
| `GET`  | `/` | The human web UI (Gradio, spec 003). |
| `GET`  | `/api` | The Swagger UI. |
| `GET`  | `/health` | Liveness check → `{"status":"ok"}`. |
| `GET`  | `/api/vaults` | List vaults + the resolved root and default. |
| `POST` | `/api/vaults` | Create/scaffold a vault. Body: `{"name":"demo"}`. |
| `GET`  | `/api/vaults/{selector}` | Inspect a vault (path, page count). |
| `POST` | `/api/ingest` | Add a source; writes a summary, updates the portal, commits. |
| `POST` | `/api/query` | Search the vault; returns an answer with citations. |
| `POST` | `/api/plan` | Get a step-by-step plan; risky work is flagged for approval. |
| `GET`  | `/api/lint?vault=<name>` | Report hygiene issues (orphan / thin pages). |
| `GET`  | `/api/spec?path=<rel>&vault=<name>` | Read a vault page's raw Markdown. |
| `POST` | `/api/chat` | Chat with the Product Owner (full reply). |
| `POST` | `/api/chat/stream` | Chat, streamed as Server-Sent Events. |

Docs endpoints: **Swagger UI** `/api` · **ReDoc** `/redoc` · **OpenAPI JSON**
`/openapi.json`. Full request/response shapes are documented interactively at
`/api`.

## 7. Chat with the assistant (curl)

The chat surface talks to the assistant as the project's **Product Owner**. It
answers from the vault with citations, and for consequential requests it returns
a **plan** for your approval instead of acting immediately.

**Request body** (both `/api/chat` and `/api/chat/stream`):

```json
{
  "message": "your message",
  "vault": "demo",              // optional; omitted = default vault
  "conversation_id": "abc123",  // optional; omitted = start a new conversation
  "approve": false              // set true to approve this conversation's pending plan
}
```

**Full reply** — the response carries a `conversation_id` you resend to continue:

```bash
curl -s -X POST localhost:8000/api/chat \
  -H 'content-type: application/json' \
  -d '{"vault":"demo","message":"What did we decide to ship?"}'
# → {"vault":"demo","conversation_id":"<id>","reply":"...",
#    "citations":[{"page":"wiki/...","excerpt":"..."}],
#    "pending_plan":null,"executed":false}
```

**Continue the thread** — reuse the returned `conversation_id`:

```bash
curl -s -X POST localhost:8000/api/chat \
  -H 'content-type: application/json' \
  -d '{"vault":"demo","conversation_id":"<id>","message":"Why that date?"}'
```

**Consequential request → plan-first** — nothing is mutated this turn; a
`pending_plan` comes back and is stored with the conversation:

```bash
curl -s -X POST localhost:8000/api/chat \
  -H 'content-type: application/json' \
  -d '{"vault":"demo","message":"delete the onboarding notes"}'
# → "pending_plan": { ...steps... }, "executed": false
```

**Approve the pending plan** — execution happens only on this explicit turn:

```bash
curl -s -X POST localhost:8000/api/chat \
  -H 'content-type: application/json' \
  -d '{"vault":"demo","conversation_id":"<id>","message":"approve","approve":true}'
# → "executed": true
```

**Streamed reply (SSE)** — each event is a `data:` line with the accumulated
reply; the final event has `"done": true`:

```bash
curl -s -N -X POST localhost:8000/api/chat/stream \
  -H 'content-type: application/json' \
  -d '{"vault":"demo","message":"Summarise the project in one paragraph."}'
# data: {"vault":"demo","conversation_id":"<id>","reply":"The ...","done":false, ...}
# data: {"vault":"demo","conversation_id":"<id>","reply":"The project ...","done":true, ...}
```

Every conversation is saved as one Markdown file under the vault's `sessions/`
directory, so a thread can be resumed by its `conversation_id` even after the
service restarts.

> The chat answer path uses the `claude-agent-sdk` runtime, which needs the
> `claude` CLI / credentials to be reachable. When it is not, chat falls back to
> a deterministic cited answer via `query`, so the endpoint still works offline.
> All non-chat endpoints run with no credentials.

## 8. Running the tests

The API test suite lives in `tests/` and drives the FastAPI app over HTTP; each
test maps to a user story / acceptance criterion. `pytest` ships in the `dev`
extra:

```bash
uv run --extra dev pytest                 # full suite (offline, deterministic)
uv run --extra dev pytest -v              # verbose, one line per test
LEADER_LIVE_AGENT=1 uv run --extra dev pytest   # also run the opt-in live-agent test
```

Tests run against a throwaway vault under a temp directory, so they never touch
your real vaults or the project repo.

## 9. Troubleshooting

- **Port already in use** — start with a different `LEADER_PORT`.
- **Can't find your files** — check which vault root is active via `GET /api/vaults`
  (it echoes the resolved `root` and `default`).
- **Command not found: uv** — install uv: see https://docs.astral.sh/uv/.

## Learn more

- `CLAUDE.md` — developer guide (architecture, conventions, commands).
- `specs/` — the full specification this service is built from (start at
  `specs/README.md`).
