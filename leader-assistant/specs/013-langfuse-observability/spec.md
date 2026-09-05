# Feature Specification: Langfuse Observability

**Feature ID:** `013-langfuse-observability`
**Status:** Implemented
**Created:** 2026-09-05 · **Last Updated:** 2026-09-05

> Amends [[17-observability]] §5/§6. Primary spec references: [[15-integrations]] (an external
> service boundary), [[001-leader-assistant]] plan (environment table).
> Amends no constitutional principle. Exercises **P1/P10** (tracing is process telemetry, never
> written into the vault as knowledge) and **P9** (the same three call sites are traced whichever
> surface — REST or chat — reached them, since REST and chat both drive the same capability layer
> down to the same `agent`/`activity_ingest`/`judge` functions).

## Summary

The app makes exactly three kinds of real model call — an interactive chat turn, an ingest
activity (two phases), and the risk judge's single-turn review — all through
`claude_agent_sdk.query()`. This feature traces every one of them to a local Langfuse instance, so
a developer can see what a turn actually did (prompt, reply, tool activity via the SDK's own
event stream, token usage, cost) without reading logs.

## Goals

- Every `query()` call site emits a Langfuse generation with input, output, token usage and cost.
- Zero behavioural change, zero network call, and zero new failure mode when Langfuse is not
  configured (no `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY`) — this must hold for the whole
  automated test suite without any test-only stubbing.
- One conversation's turns group into one Langfuse session; one ingest's two phases group into one
  Langfuse trace.

## Non-Goals

- Enriching the judge's trace with the triggering operation/run id (would require changing the
  `_ask_model` callable's signature threaded through `Judge._recommend`; deferred).
- A first-party UI for viewing traces — the operator uses Langfuse's own local UI directly.
- A durability guarantee that a hard kill (`SIGKILL`) flushes buffered spans; only a graceful
  shutdown does.
- Any traced data being treated as vault knowledge — it never reaches `wiki/` or `log.md`.

## User Scenarios

- **Scenario 1 — chat turn:** As a developer running the app locally with Langfuse configured,
  when I send a chat message, the assistant answers as normal and a `chat-turn` generation appears
  in Langfuse tagged with the conversation id as its session, so I can see every turn of that
  conversation grouped together with the prompt/reply/cost.
- **Scenario 2 — ingest:** As a developer, when I ingest a source, the assistant ingests as normal
  and one `ingest` trace appears in Langfuse containing two nested generations, `ingest-phase1` and
  `ingest-phase2`, so I can see both halves of the bridge without hunting through two unrelated
  traces.
- **Scenario 3 — no credentials:** As a developer with no Langfuse instance running (or the keys
  unset), the assistant behaves identically to before this feature — no error, no delay, no
  degraded response — because tracing is inert without configuration.
- **Scenario 4 — judge review:** As a developer investigating why a request paused for approval,
  when I open Langfuse, I see the `judge-review` generation with the prompt the checker was given
  and the raw model text it returned, alongside the reasoning already visible in the interaction
  card.

## Functional Requirements

- **FR-1:** The system MUST wrap `app/agent.py::run_stream`'s `query()` loop in a Langfuse
  generation named `chat-turn`, with `model` set to the active agent model, `input` the user
  message, and `session_id` the conversation id.
- **FR-2:** The system MUST wrap each of `app/activity_ingest.py::_headless`'s two calls in a
  Langfuse generation named `ingest-phase1`/`ingest-phase2`, both nested under one `ingest` span
  created by `run()`.
- **FR-3:** The system MUST wrap `app/judge.py::sdk_ask_model`'s `query()` loop in a Langfuse
  generation named `judge-review`.
- **FR-4:** Every generation MUST, on receiving the SDK's `ResultMessage`, update its `output` and
  populate `usage_details`/`cost_details` from that message's `usage`/`total_cost_usd` fields.
- **FR-5:** Tracing MUST introduce no new required environment variable — the Langfuse client
  reads `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY`/`LANGFUSE_BASE_URL` natively, already present
  in this repo's `.env` convention (spec 03-workspace §0).
- **FR-6:** Absent `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY`, every tracing call MUST be a no-op
  (no network call, no raised exception) — verified by unit test, not merely asserted.
- **FR-7:** On a graceful app shutdown, the system MUST attempt (best-effort) to flush any
  buffered spans.

## Key Entities & Concepts

- **Generation** — one traced model call (Langfuse term): input, output, model, token usage, cost.
- **Span** — a parent observation grouping child generations into one trace (used for ingest's
  two phases).
- **Session** — a Langfuse grouping of traces sharing a `session_id`; used here to group one
  conversation's chat-turn generations.

## Constraints & Assumptions

- Constraint (P1/P10, `memory/constitution.md`): no external system becomes canonical storage;
  Langfuse is observability-only, never read back by the app.
- Constraint (P9): tracing lives inside the functions the REST and chat surfaces both already
  funnel through (`agent.run_stream`, `activity_ingest`, `judge`), so it applies identically
  regardless of which surface triggered the call — no surface-specific tracing code.
- Assumption: the Langfuse Python SDK's documented fail-open behavior (a disabled no-op client
  when keys are absent) is stable across the pinned version range — verified directly against the
  installed 4.15.1 before relying on it.
- Assumption: OpenTelemetry's context propagation across `await` within one asyncio task correctly
  nests a child observation under a still-open parent without passing span objects around —
  verified directly (a sync and an async nesting probe) before designing `ingest`'s span/generation
  split on it.

## Acceptance Criteria

- [x] AC-1: With `LANGFUSE_PUBLIC_KEY`/`SECRET_KEY` unset, `uv run --extra dev pytest` passes with
  no test needing to stub or disable tracing.
- [x] AC-2: A chat turn produces one `chat-turn` generation carrying the conversation id as its
  Langfuse session id.
- [x] AC-3: One ingest produces one `ingest` trace with two nested phase generations, not two
  independent traces.
- [x] AC-4: A `ResultMessage`'s `usage`/`total_cost_usd` land on the generation's
  `usage_details`/`cost_details` whenever the SDK provides them.
- [x] AC-5: No vault/wiki file or `log.md` entry is written by tracing itself.

## Review Checklist

- [x] No implementation details beyond what's needed to make FRs testable.
- [x] Every requirement is testable (FR-6 has a dedicated unit test; the rest are exercised by the
  existing offline test suite continuing to pass unmodified, which is the regression proof).
- [x] Scenarios cover the golden path (configured) and the key edge case (unconfigured).
- [x] Complies with `memory/constitution.md` (P1/P9/P10).
- [x] No local↔remote conflict — this is a purely additive, optional integration.
