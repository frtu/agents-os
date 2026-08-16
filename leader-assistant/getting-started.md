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
# from the app/ directory
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
  API base   : http://localhost:8000
  Swagger UI : http://localhost:8000/docs
  ReDoc      : http://localhost:8000/redoc
  OpenAPI    : http://localhost:8000/openapi.json
  Health     : http://localhost:8000/health
```

Open **http://localhost:8000/docs** — the Swagger UI lets you try every endpoint from
the browser. Visiting `/` redirects there. Press `Ctrl+C` to stop.

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

| Method | Path | What it does |
|--------|------|--------------|
| `GET`  | `/health` | Liveness check. |
| `GET`  | `/api/vaults` | List vaults + the resolved root and default. |
| `POST` | `/api/vaults` | Create/scaffold a vault. |
| `GET`  | `/api/vaults/{selector}` | Inspect a vault (path, page count). |
| `POST` | `/api/ingest` | Add a source; writes a summary, updates the portal, commits. |
| `POST` | `/api/query` | Search the vault; returns an answer with citations. |
| `POST` | `/api/plan` | Get a step-by-step plan; risky work is flagged for approval. |
| `GET`  | `/api/lint` | Report hygiene issues (orphan / thin pages). |
| `GET`  | `/api/spec` | Read a vault page's raw Markdown. |

Full request/response shapes are documented interactively at **/docs**.

## 7. Troubleshooting

- **Port already in use** — start with a different `LEADER_PORT`.
- **Can't find your files** — check which vault root is active via `GET /api/vaults`
  (it echoes the resolved `root` and `default`).
- **Command not found: uv** — install uv: see https://docs.astral.sh/uv/.

## Learn more

- `CLAUDE.md` — developer guide (architecture, conventions, commands).
- `specs/` — the full specification this service is built from (start at
  `specs/README.md`).
