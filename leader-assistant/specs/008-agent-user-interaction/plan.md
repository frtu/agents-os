# Implementation Plan: Agent–User Interaction

**Feature ID:** `008-agent-user-interaction` · **Spec:** [`spec.md`](spec.md)
**Status:** Implemented
**Created:** 2026-08-23 · **Last Updated:** 2026-08-23

> Supplies the **how** the spec deferred (Open Questions): push transport, the on-disk shape of a
> pending interaction, the REST endpoint shapes, and the card presentation. Requirements are
> referenced, not restated.

## Constitution Check

- [x] **P1 durable record is truth** — the pending interaction lives in the conversation's `sessions/`
  file frontmatter, not in memory; recovery reads disk.
- [x] **P6 traceability** — request, options, resolution, timeout, and "chat about it" turns are all
  appended to the session record.
- [x] **P8 human-in-the-loop** — decline / timeout / "chat about it" / new task never authorize; only an
  explicit option selection executes.
- [x] **P9 parity** — the same request/response protocol is reachable over REST and the chat/UI surface;
  the UI is a pure HTTP client of `/api/chat/interaction*`.
- [x] **P13 workspace-scoped** — every call resolves through the active workspace.

## Decided technical choices

- **Delivery model — turn-boundary, not mid-turn push.** A blocking interaction is emitted as the
  final `ChatDelta.interaction` of a turn (over the existing SSE chat stream), and the durable
  `pending-interaction` record is the source of truth. This keeps the exchange deterministic and
  offline-testable while satisfying FR-1 (the frontend renders it before the turn ends) and FR-11
  (durability). No new transport (WebSocket) is introduced.
- **Storage shape.** A single mutable frontmatter field `pending-interaction: {json}` in
  `sessions/<id>.md`, parallel to `pending-plan`. The JSON is a serialized `models.Interaction` plus,
  for a plan-wrapping approval, an embedded `plan` + `request` payload (FR-17). Turn/event blocks stay
  append-only; only the frontmatter field mutates. (`app/conversation.py`)
- **REST endpoints** (`app/api.py`, all under the existing `/api/chat` namespace):
  - `GET  /api/chat/interaction` → the still-pending `Interaction | None` (auto-resolves an elapsed one
    to `status="expired"`), for reload recovery (FR-11).
  - `POST /api/chat/interaction` (`InteractionResponse`) → `ChatAnswer` (FR-12/FR-16).
  - `POST /api/chat/interaction/stream` → SSE of `ChatDelta` for the resumed turn.
- **Response protocol.** `choice` is one of: an **option id** (authorize/select), `"decline"`, or
  `"chat"` ("chat about it"). Idempotency and id-scoping are enforced in
  `capabilities.respond_to_interaction_stream` (FR-16).
- **"Chat about it" (FR-7/D8/D9).** Runs one scoped routine turn (context = the interaction's prompt +
  options) **without resolving**, then re-presents the same decision as a **new id** that supersedes
  the old (fresh `created` ⇒ fresh countdown). The old id becomes non-answerable.
- **Timeout (FR-9/D6).** `LEADER_INTERACTION_TIMEOUT` (default 30s) via `config.interaction_timeout_seconds`,
  with an optional per-request override. Expiry is computed from `created + timeout_seconds`; on expiry the
  interaction aborts with the fixed message **"Something goes wrong, please retry later."** and takes no
  action. The card's countdown is a client-side wheel that clicks a hidden expire trigger at zero.
- **Plan-first as approval (FR-17).** A consequential turn still sets `pending_plan` (backward compat with
  the legacy `approve=true` chat path) **and** emits an approval interaction wrapping the plan. Any
  resolution clears both fields so the plan can never execute twice.
- **UI card (`app/ui.py`, FR-8/FR-10).** A compact **chat bubble** sized to read as an assistant message
  (not a full-width panel), shown just above the chat box: prompt + the proposals as **radio options with
  the constant "chat about it" as the final option** + an animated spinner/countdown. **Selecting a radio
  option auto-submits** the answer (`Radio.input`) — no Submit button. A **top-right ✕** on the bubble
  declines (safe default, FR-14) — no Decline button. The bottom chat box always starts a new task.
  Reload recovery re-renders the card from `GET /api/chat/interaction`.

## Agent-initiated interactions (FR-18)

- **One narrow MCP tool — `request_interaction`.** Registered on the agent's MCP server (spec 006)
  alongside the other capability tools, so the model can raise a card on its own judgment during a
  routine turn (previously only the deterministic plan-first path could). It is **workspace- and
  conversation-bound** like every other tool — the selector and `conversation_id` are injected from the
  run context, never taken from tool args (spec 006 FR-6) — and it is **not** on the default blacklist.
- **Clarification + notification only.** The tool accepts `kind ∈ {clarification, notification}` and
  wraps `capabilities.create_interaction`, which validates the option bounds (clarification 2–4,
  notification 0; FR-6) and one-blocking-at-a-time (FR-15). **`approval` is intentionally not exposed**
  to the agent — authorization of consequential work stays with the deterministic plan-first path
  (FR-14/FR-17), so the model cannot manufacture its own consent gate.
- **Surfacing.** Handlers append each raised `Interaction` to a mutable list threaded through
  `agent.run_stream` (same pattern as `citations`). After the stream the routine turn picks the first
  blocking (clarification) card, else the first notification, and emits it on the final `ChatDelta`
  (replacing the previous hard-coded `interaction=None`). Blocking cards are already persisted by
  `create_interaction` (FR-11) so reload re-renders via `GET /api/chat/interaction`.
- **Parity (P9).** The tool only adds an *initiation path*; delivery/response are still the same
  `ChatDelta` + REST endpoints, so REST == chat is preserved.

## Deliberately not done

- **No agent-initiated approval.** The agent may raise clarification/notification only; approval remains
  produced solely by the plan-first path (FR-14/FR-17).
- **No multi-select / free-form options, no background-job queue** — out of scope per the spec Non-Goals.

## Test mapping

`tests/test_interaction_api.py` covers AC-1…AC-13 (see the per-test spec-id comments), driven over the
REST surface with the capability layer used directly where the backend must *create* a mid-task request.
