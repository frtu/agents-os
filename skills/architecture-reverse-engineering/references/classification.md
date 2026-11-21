# Classification — from scan hits to components

**Load at step 3** of `SKILL.md`, after the scan. The scan (`scripts/scan_repo.py`) gives **evidence**: hits by bucket, tier and file. This file is the **judgement**: how to turn hits into components, directions, auth and confidence. The patterns themselves live in `config/signals.json`; never restate them here.

## Reading the report

| Field | Meaning | What to do |
| --- | --- | --- |
| `tier: confident` | A distinctive pattern matched | Evidence for the category. Still confirm the **component** by reading the file at the cited line |
| `tier: flag` | A generic word matched (`token`, `topic:`, `fetch(`, `consumed by`) | A lead, not evidence. Open the line; keep it only if it names or configures a real external system |
| `lines` with many entries | The token is used throughout the file | Usually the core client or config block: read it first |
| `summary.truncated` | Hits were capped per category | Re-run with `--bucket` / `--max-hits 0` on the buckets that matter |
| `inventory` | High-signal files that exist | Read the manifests, the main config file, the Dockerfile and the README before the hits |

**Silence caveat:** the scan only knows the patterns in its signals file. An empty bucket is not proof of absence. Always sweep the package tree (`client/`, `connector/`, `adapter/`, `gateway/`, `integration/`, `controller/`, `listener/`, `job/`) and the main config file by hand for systems the patterns missed. Each one you find is a write-back (see `SKILL.md` step 6).

## One component, many hits

Merge hits into components by **what system they point at**, not by file:

- A manifest dependency (`spring-kafka`) + a config block (`kafka.bootstrap-servers`) + a listener (`@KafkaListener`) = **one** component: the Kafka cluster, consumed by this service.
- An SDK + a config block with credentials = one cloud service, with its auth mechanism.
- A database driver + migrations + an ORM = one database, **owned** by this service (migrations live here).
- Test-only hits (`src/test*/`, testcontainers, `TestRestTemplate`) prove nothing about production. Use them only to confirm a production hit, or to spot a peer the tests stub.

## Buckets → diagram layers

| Bucket | Component it suggests | Layer | Notes |
| --- | --- | --- | --- |
| `upstream` (endpoint) | The API surface: one node per controller/router group, not per route | Service (API layer) | The callers come from caller hints, auth and docs, not from the endpoint itself |
| `upstream` (caller-hint) | A caller, when a comment, doc or path names one | Upstream | `/internal/*` paths and webhooks imply a known internal caller: find who |
| `downstream-peer` | Another service this one calls | Downstream | Strongest when a base URL **and** auth wiring (token header, OAuth client, mTLS) exist: that is a real peer, not a util |
| `downstream-cloud` | A managed or third-party service (SDK) | Downstream | Name the product category if the vendor isn't obvious from the code |
| `middleware` | Database, cache, queue, object storage, search | Downstream (stores, queues) | Split **producer vs consumer** and list topics/queues/buckets. Owned (migrations, schema, bucket created here) vs shared (only read) |
| `auth` | The mechanism on an edge, or an issuer | Cross-cutting (issuer) + edge label | Never a component on its own unless it is an identity provider |
| `cross-cutting` | Observability, deploy, secrets infrastructure | Cross-cutting | One node per system, dashed edges |
| `inferred-clue` | Something built, deployed or toggled elsewhere | Inferred (⚠) | See below |

### Upstream — who calls this service

- Endpoints give the surface; callers come from: comments and docs naming a consumer, the auth mechanism (an OIDC/JWT issuer means user-facing or service callers of that issuer; an API-key registry means external clients; mTLS means internal services), and data written by others (tables or streams this service only reads).
- Message consumers (`@KafkaListener`, SQS listeners) make the **producer** of that topic an upstream.
- Schedulers (`@Scheduled`, cron) are an upstream trigger: draw them as an entry point inside the service.

### Inferred components (no code here)

Keep them, marked ⚠, with the clue:

- CI config that pulls or triggers another repo, or a `COPY --from=` an image built elsewhere.
- CRDs or kinds consumed but not defined here (GitOps controllers, secret operators).
- Bot or agent actors in commit messages, dashboard names, alert routes.
- Feature flags (or `enabled: false` blocks) toggling an integration that has no code yet.
- A client or config block for a system that only appears in comments or templates.

## Confidence

| Level | Use when |
| --- | --- |
| **high** | Code or config names the system **and** shows how it is reached (URL, SDK call, topic name) |
| **medium** | The system is named, but how it is reached or what flows is unclear (a dependency with no visible usage, a config block with no client) |
| **low** | Only a clue: a comment, a CI reference, a flag, a template — "something exists here" |

Components in *Components and evidence* are implicitly high or medium. Anything low goes in *Components not defined in this repo*.

## Honesty rules

- **No component without evidence**: every node cites at least one file path.
- **Unknown is a valid answer**: "unknown queue consumer (clue: topic `x` produced, no consumer here)" beats a guessed name.
- **Never copy a secret value** into the doc. Name the key and the mechanism (`client-secret` via env var), never the value. The scan already redacts snippets; keep it that way when you read files.
