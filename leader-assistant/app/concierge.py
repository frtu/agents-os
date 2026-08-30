"""The single entry point every surface uses (spec 011 FR-23/FR-24).

Every user→backend call — REST or chat — enters here. The concierge owns the **sequence** and
nothing else (FR-24):

    open run → invoke execution → on pause consult the judge → surface an ask
             → resume on the answer → record experience asynchronously

It is the one module allowed to know all three layers, which is precisely why the layers need not
know each other (FR-34). It holds no policy: scoring belongs to ``workflow``, deciding to ``judge``,
acting to ``capabilities`` and the agent. What lives here is glue with a shape:

* **Adapters.** ``experience.PrecedentSummary`` → ``judge.Precedent``; ``workflow.RiskReport`` →
  ``models.RiskAssessment``/``models.Plan``. Each layer names its own data; nobody imports anyone's.
* **Cross-request resume.** A run object dies with the request that opened it, but an ask outlives
  it. The gating operation's ``awaiting_key`` is persisted on the durable 008 interaction record and
  fed back through ``WorkflowRun.pre_grant`` on the answering call, so a fresh run honours a decision
  made against its predecessor (FR-26) and a restart does not orphan the card (P1).
* **Experience capture.** Judge verdicts are recorded by wrapping the checker; operator answers are
  recorded here. Both are fire-and-forget (FR-30).
"""

from __future__ import annotations

from typing import AsyncIterator, Callable, TypeVar

from . import config, execution_gate, experience, judge, models, workflow
from .execution_gate import Operation
from .workflow import RiskReport, WorkflowRun

T = TypeVar("T")


class ApprovalRequired(Exception):
    """A run paused for an operator decision (spec 011 FR-12/FR-25).

    Raised on the REST path, where there is no conversation to hang a card on. Carries the whole
    accumulated assessment so the caller can show the blast radius, not just the refusal.
    """

    def __init__(self, assessment: models.RiskAssessment) -> None:
        super().__init__(assessment.reasoning or "operator approval is required before this can run")
        self.assessment = assessment


class Declined(Exception):
    """The checker refused. Decline is decline (spec 011 FR-27, D8)."""

    def __init__(self, assessment: models.RiskAssessment) -> None:
        super().__init__(assessment.reasoning or "the operation was declined")
        self.assessment = assessment


# --- layer adapters ---------------------------------------------------------------------


def _precedent_for(report: RiskReport) -> judge.Precedent | None:
    """Look up operator precedent for the gating operation and hand it to layer 3 as plain data.

    The two dataclasses are deliberately separate declarations with matching field names: layer 3
    must be usable with no experience store at all (FR-34/FR-35), so the mapping lives here rather
    than either side importing the other.
    """
    summary = experience.lookup(experience.operation_fingerprint(report.gating.operation))
    if summary is None:
        return None
    return judge.Precedent(
        precedent_id=summary.precedent_id,
        fingerprint=summary.fingerprint,
        approvals=summary.approvals,
        declines=summary.declines,
        last_decision=summary.last_decision,
    )


def _operation_model(scored: workflow.ScoredOperation) -> models.RiskOperation:
    op = scored.operation
    return models.RiskOperation(
        op_id=op.op_id,
        kind=op.kind,
        name=op.name,
        target=op.target,
        tier=op.tier,
        reversibility=op.reversibility,
        external=op.external,
        score=scored.score,
        modifiers=list(scored.modifiers),
        justification=scored.justification,
        status=scored.status,
    )


def assessment_for(run: WorkflowRun) -> models.RiskAssessment:
    """The wire form of why a run stopped (spec 011 FR-11/FR-14).

    ``accumulated`` is the report's list when one was built (the gating operation plus everything
    already executed), falling back to the run's own operations so a caller always sees the blast
    radius rather than a bare refusal.
    """
    report = run.pending_report
    verdict = run.verdict
    scored = report.accumulated if report else run.operations
    return models.RiskAssessment(
        run_id=run.run_id,
        objective=run.objective,
        gating=_operation_model(report.gating) if report else None,
        accumulated=[_operation_model(s) for s in scored],
        decision=verdict.decision if verdict else "ask",
        reasoning=verdict.reasoning if verdict else workflow.ASK_DEFAULT_REASON,
        source=verdict.source if verdict else "default",
        matched_precedent=verdict.matched_precedent if verdict else None,
    )


def plan_for(run: WorkflowRun) -> models.Plan | None:
    """Render the pause as the existing ``Plan`` contract (spec 011 FR-25, 13-api AC2).

    Spec 011 adds no new asking surface: an ask reaches the operator as the 008 approval card and
    the plan shape both surfaces already render. The steps are the accumulated operations, so the
    plan shows what has *already* run alongside what is now being attempted.
    """
    report = run.pending_report
    if report is None:
        return None
    gating = report.gating
    return models.Plan(
        workspace=run.workspace,
        request=run.objective,
        steps=[
            models.PlanStep(
                order=i + 1,
                action=f"{s.operation.name} on {s.operation.target or '(no target)'} — risk {s.score}/5",
                rationale=s.justification,
            )
            for i, s in enumerate(report.accumulated)
        ],
        risk="risky",
        requires_approval=True,
        capability=gating.operation.name,
        target=gating.operation.target,
        effect_tier=gating.operation.tier,
        reversibility=gating.operation.reversibility,
    )


# --- experience capture -----------------------------------------------------------------


class _RecordingChecker:
    """The checker, with every *decisive* verdict captured as experience (spec 011 FR-30).

    Wrapping rather than editing either layer: ``workflow`` must not know the store exists (FR-34)
    and ``judge`` must not write anything (FR-22). An ``ask`` records nothing — it is a deferral,
    not a decision; the operator's answer is recorded by ``_record_operator_decision``.
    """

    def __init__(self, inner: workflow.Checker) -> None:
        self._inner = inner

    async def review(self, report: RiskReport) -> workflow.Verdict:
        verdict = await self._inner.review(report)
        if verdict.decision in ("approve", "decline"):
            experience.record_async(
                run_id=report.run_id,
                operation=report.gating.operation,
                decision=verdict.decision,
                source=verdict.source,
                score=report.gating.score,
                objective=report.objective,
                workspace=report.workspace,
                outcome="executed" if verdict.decision == "approve" else "blocked",
                matched_precedent=verdict.matched_precedent,
                reasoning=verdict.reasoning,
            )
        return verdict


def _record_operator_decision(record: dict, approved: bool, workspace: str) -> None:
    """Capture the operator's own answer (spec 011 FR-29/FR-30, source ``user``).

    Only these records establish precedent (``experience.lookup`` counts ``source == "user"``
    alone), which is what stops a grant from bootstrapping its own authority.
    """
    fingerprint = record.get("fingerprint")
    if not fingerprint:
        return
    experience.record_async(
        run_id=record.get("run_id", ""),
        operation=fingerprint,
        decision="approve" if approved else "decline",
        source=experience.OPERATOR_SOURCE,
        score=int(record.get("score") or 1),
        objective=record.get("objective", ""),
        workspace=workspace,
        outcome="executed" if approved else "blocked",
        reasoning=record.get("prompt", ""),
    )


# --- runs -------------------------------------------------------------------------------


def trust_mode(per_request: bool | None) -> bool:
    """Trust for one call: an explicit per-request value wins, else the persisted one (009 FR-9)."""
    return config.auto_approve() if per_request is None else bool(per_request)


def build_run(
    objective: str,
    workspace: str,
    *,
    trust: bool | None = None,
    granted_key: str = "",
    checker: workflow.Checker | None = None,
) -> WorkflowRun:
    """Open a run wired to the real judge (spec 011 FR-6/FR-13/FR-24).

    ``checker`` is injectable so a test — or a build with layer 3 removed — can substitute the
    default ask-checker and still exercise everything else (FR-35).
    """
    resolved = trust_mode(trust)
    inner = checker or judge.Judge(
        trust=resolved,
        precedent_lookup=_precedent_for,
        experience_empty=experience.is_empty,
    )
    run = WorkflowRun(objective=objective, workspace=workspace, checker=_RecordingChecker(inner))
    if granted_key:
        run.pre_grant(granted_key)
    return run


async def invoke(
    capability: str,
    target: str,
    run_fn: Callable[[], T],
    *,
    workspace: str = "",
    objective: str = "",
    trust: bool | None = None,
    detail: str = "",
) -> T:
    """Run one capability through a gated run — the REST entry point (spec 011 FR-23).

    The same capability, announced with the same declared effect, is scored by the same layer 2 and
    judged by the same layer 3 as it would be when the agent calls it as a tool: that identity is
    what makes REST and chat reach the same verdict for the same request (P9, AC-15).
    """
    from . import capabilities

    effect = capabilities.EFFECTS.get(capability)
    operation = Operation(
        kind="capability",
        name=capability,
        target=target,
        # An unregistered capability is treated as the worst case rather than waved through: the
        # effect table is the declaration, and an absent declaration is not a claim of safety.
        tier=effect.tier if effect else "approval",
        reversibility=effect.reversibility if effect else "no declared undo path",
        detail=detail,
    )
    run = build_run(objective or f"{capability} {target}".strip(), workspace, trust=trust)
    with execution_gate.use_gate(run):
        permit = await execution_gate.announce(operation)
        if not permit.allow:
            raise _stopped(run, workspace)
        return run_fn()


def _card_selector(workspace: str) -> str | None:
    """Where a REST-originated card can live.

    Conversations live inside a workspace, but the operation being asked about may be *creating*
    one — so a card about a workspace that does not exist yet is hung on the default workspace
    rather than not raised at all.
    """
    from . import capabilities

    if not workspace:
        return None
    try:
        capabilities.resolve_for_chat(workspace)
    except Exception:  # noqa: BLE001 — an unresolvable workspace just means "use the default"
        return None
    return workspace


def _stopped(run: WorkflowRun, workspace: str) -> Exception:
    """The exception a paused or declined REST call raises (spec 011 FR-25/FR-27).

    A pause also raises the real 008 card and reports its ids on the assessment, so the machine
    caller answers on the route the UI already uses (`POST /api/chat/interaction`) instead of
    receiving a refusal it has no way to act on.
    """
    assessment = assessment_for(run)
    if assessment.decision == "decline":
        return Declined(assessment)
    selector = _card_selector(workspace)
    card = _ask_card(selector, None, run, assessment, plan_for(run))
    if card is not None:
        assessment.interaction_id = card.interaction_id
        assessment.conversation_id = card.conversation_id
        # The card lives in a *specific* workspace's sessions, which is not always the workspace the
        # operation targets (a card about creating one is hung on the default). Reporting where it
        # actually lives is what makes the ids above resolvable — the pair alone is not an address.
        assessment.workspace = selector or ""
    return ApprovalRequired(assessment)


# --- chat -------------------------------------------------------------------------------


def _pause_reply(run: WorkflowRun, assessment: models.RiskAssessment) -> str:
    """What the operator reads when a run pauses (spec 011 FR-10/FR-11, AC-5).

    The whole accumulated list, each line carrying its score and its one-line justification —
    approving is a judgment about a set of effects, not about one opaque action.
    """
    lines = []
    gating = assessment.gating
    if gating is not None:
        lines.append(
            f"I stopped before running `{gating.name}` on "
            f"`{gating.target or '(no target)'}` — risk {gating.score}/5, "
            f"at or above the review threshold of {run.threshold}."
        )
    lines.append("\nEverything this request would do:")
    for op in assessment.accumulated:
        mark = {"executed": "done", "pending": "waiting", "declined": "refused"}.get(op.status, op.status)
        lines.append(f"- [{mark}] {op.name} on {op.target or '(no target)'} — {op.score}/5 — {op.justification}")
    if assessment.reasoning:
        lines.append(f"\nWhy I am asking: {assessment.reasoning}")
    lines.append("\nApprove to continue from where I stopped, or decline and I will go no further.")
    return "\n".join(lines)


def _decline_reply(assessment: models.RiskAssessment) -> str:
    lines = ["I did not run this — it was declined."]
    if assessment.reasoning:
        lines.append(f"\nReason: {assessment.reasoning}")
    if assessment.accumulated:
        lines.append("\nWhat was assessed:")
        for op in assessment.accumulated:
            lines.append(f"- [{op.status}] {op.name} on {op.target or '(no target)'} — {op.score}/5 — {op.justification}")
    return "\n".join(lines)


def _card_extra(run: WorkflowRun, assessment: models.RiskAssessment, plan: models.Plan | None) -> dict:
    """The resume payload persisted alongside the 008 card (spec 011 FR-26).

    ``granted_key`` and ``fingerprint`` are the whole point: the first lets a later run complete the
    paused operation, the second lets the operator's answer become precedent. ``plan`` is stored
    only for a **capability** pause, where the exact action can be re-executed directly; a **tool**
    pause is completed by resuming execution instead, so storing a plan there would send the answer
    down a path that cannot honour it.
    """
    gating = assessment.gating
    extra: dict = {
        "risk": assessment.model_dump(),
        "granted_key": run.awaiting_key or "",
        "run_id": run.run_id,
        "objective": run.objective,
        "score": gating.score if gating else 1,
    }
    report = run.pending_report
    if report is not None:
        extra["fingerprint"] = experience.operation_fingerprint(report.gating.operation)
    if plan is not None and gating is not None and gating.kind == "capability":
        extra["plan"] = plan.model_dump()
        extra["request"] = run.objective
    return extra


def _ask_card(
    selector: str | None,
    conversation_id: str,
    run: WorkflowRun,
    assessment: models.RiskAssessment,
    plan: models.Plan | None,
) -> models.Interaction | None:
    """Surface the ask as the existing 008 approval card (spec 011 FR-25).

    FR-15 allows only one outstanding blocking card per conversation. If the turn already raised
    one, that question is already in front of the operator; re-raising would replace a live
    decision with a different one, so the pause is reported in prose and the existing card stands.
    """
    from . import capabilities
    from . import conversation as convo

    gating = assessment.gating
    prompt = (
        f"Approve `{gating.name}` on `{gating.target or '(no target)'}` (risk {gating.score}/5)?"
        if gating
        else f"Approve this work? {run.objective}"
    )
    try:
        return capabilities.create_interaction(
            selector,
            conversation_id,
            "approval",
            prompt,
            [{"id": "approve", "label": "Approve and continue", "detail": assessment.reasoning or prompt}],
            name_hint=convo.fallback_name(run.objective),
            _extra=_card_extra(run, assessment, plan),
        )
    except Exception:  # noqa: BLE001 — a card we cannot raise must not lose the operator's turn
        return None


def _persist_pending_plan(
    selector: str | None, conversation_id: str, run: WorkflowRun, plan: models.Plan | None
) -> None:
    """Record a capability pause as a durable pending plan (spec 002 FR-5, spec 011 FR-26).

    The 008 card is the question; this is the answerable work behind it. Persisting both is what
    lets a pause be answered either way — by clicking the card or by resending the turn with
    ``approve=true`` — and lets either survive a restart (spec 002 AC-10).
    """
    from . import conversation as convo

    gating = run.pending_report.gating.operation if run.pending_report else None
    if plan is None or gating is None or gating.kind != "capability":
        return
    try:
        from . import capabilities

        _name, wpath = capabilities.resolve_for_chat(selector)
        conv = convo.load_or_new(wpath, conversation_id)
        # A REST pause has no chat turn to name the record, so the objective is the best name
        # available (spec 012 FR-5). A no-op if the chat turn already named it.
        convo.set_name(conv, convo.fallback_name(run.objective))
        convo.set_pending_plan(conv, run.objective, plan.model_dump())
    except Exception:  # noqa: BLE001 — a record we cannot persist must not lose the operator's turn
        return


def _settle(
    run: WorkflowRun,
    final: models.ChatDelta,
    selector: str | None,
) -> models.ChatDelta:
    """Turn a finished run's state into the final delta (spec 011 FR-24).

    Three outcomes. Ran clean: the delta passes through untouched. Paused: an approval card and the
    accumulated report replace the reply. Declined: the refusal is reported and nothing is offered
    to approve, because a decline is not a question.
    """
    if run.state == "running":
        return final

    assessment = assessment_for(run)
    plan = plan_for(run)

    if run.state == "declined":
        return final.model_copy(
            update={"reply": _decline_reply(assessment), "pending_plan": None, "executed": False}
        )

    _persist_pending_plan(selector, final.conversation_id, run, plan)
    card = _ask_card(selector, final.conversation_id, run, assessment, plan)
    return final.model_copy(
        update={
            "reply": _pause_reply(run, assessment),
            "pending_plan": plan,
            "executed": False,
            "interaction": card or final.interaction,
        }
    )


async def _gated(
    stream: AsyncIterator[models.ChatDelta],
    run: WorkflowRun,
    selector: str | None,
) -> AsyncIterator[models.ChatDelta]:
    """Drive an execution stream under ``run``, then settle its final delta.

    Intermediate deltas pass straight through so streaming stays live; only the ``done`` delta is
    held back, because until execution finishes we do not know whether the run paused.
    """
    final: models.ChatDelta | None = None
    with execution_gate.use_gate(run):
        async for delta in stream:
            if delta.done:
                final = delta
                break
            yield delta
    if final is not None:
        yield _settle(run, final, selector)


async def chat_stream(
    workspace: str | None = None,  # noqa: A002 — matches the request field name
    message: str = "",
    conversation_id: str | None = None,
    approve: bool = False,
    auto_approve: bool | None = None,
) -> AsyncIterator[models.ChatDelta]:
    """A chat turn, gated end to end (spec 011 FR-23/FR-24)."""
    from . import capabilities

    if approve:
        async for delta in _approve_pending(workspace, conversation_id, auto_approve):
            yield delta
        return

    name, _wpath = capabilities.resolve_for_chat(workspace)
    run = build_run(message, name, trust=auto_approve)
    stream = capabilities.ask_stream(
        workspace=workspace,
        message=message,
        conversation_id=conversation_id,
        auto_approve=auto_approve,
    )
    async for delta in _gated(stream, run, workspace):
        yield delta


async def chat(
    workspace: str | None = None,  # noqa: A002
    message: str = "",
    conversation_id: str | None = None,
    approve: bool = False,
    auto_approve: bool | None = None,
) -> models.ChatAnswer:
    """Non-streaming chat turn — drives ``chat_stream`` to completion."""
    last: models.ChatDelta | None = None
    async for delta in chat_stream(workspace, message, conversation_id, approve, auto_approve):
        last = delta
    assert last is not None
    return _answer(last)


def _answer(delta: models.ChatDelta) -> models.ChatAnswer:
    return models.ChatAnswer(
        workspace=delta.workspace,
        conversation_id=delta.conversation_id,
        reply=delta.reply,
        citations=delta.citations,
        pending_plan=delta.pending_plan,
        executed=delta.executed,
        interaction=delta.interaction,
    )


def _pending_record(workspace: str | None, conversation_id: str | None) -> tuple[str, dict]:
    """The conversation's durable pending-interaction record, or ``("", {})``.

    A pure read (spec 012 FR-2): asking "is anything pending?" about an id that never had a message
    must not leave an empty record behind for the Sessions panel to list.
    """
    from . import capabilities
    from . import conversation as convo

    if not conversation_id:
        return "", {}
    _name, wpath = capabilities.resolve_for_chat(workspace)
    conv = convo.load(wpath, conversation_id)
    return (conv.conversation_id, conv.pending_interaction or {}) if conv else ("", {})


def _pending_plan_record(workspace: str | None, conversation_id: str | None) -> dict:
    """The conversation's durable pending-plan record, or ``{}`` — a pure read (spec 012 FR-2)."""
    from . import capabilities
    from . import conversation as convo

    if not conversation_id:
        return {}
    _name, wpath = capabilities.resolve_for_chat(workspace)
    conv = convo.load(wpath, conversation_id)
    return (conv.pending_plan or {}) if conv else {}


async def _approve_plan(
    workspace: str | None,
    conversation_id: str,
    pending: dict,
    auto_approve: bool | None,
) -> AsyncIterator[models.ChatDelta]:
    """Execute a durable pending plan under a run pre-granted for that exact operation (FR-26).

    The plan the operator was shown *is* the grant: it names one capability and one target, so the
    resumed run is seeded with that operation's key and nothing else. Any other operation the
    resumption tries still faces the gate, which is why re-announcing on execute (FR-4) costs
    nothing here and buys the guarantee that consent is not a blanket unlock.
    """
    from . import capabilities

    name, _wpath = capabilities.resolve_for_chat(workspace)
    plan = pending.get("plan") or {}
    capability, target = str(plan.get("capability") or ""), str(plan.get("target") or "")
    key = ""
    if capability:
        # The effect comes from EFFECTS, not from the stored plan: a persisted plan can outlive the
        # declaration it was built from, and the gate must key on what this build would really do.
        effect = capabilities.EFFECTS.get(capability)
        key = workflow.operation_key(
            Operation(
                kind="capability",
                name=capability,
                target=target,
                tier=effect.tier if effect else str(plan.get("effect_tier") or "approval"),
                reversibility=(
                    effect.reversibility if effect else str(plan.get("reversibility") or "")
                ),
            )
        )
    run = build_run(
        str(pending.get("request") or "(resumed)"), name, trust=auto_approve, granted_key=key
    )
    stream = capabilities.ask_stream(
        workspace=workspace,
        message="approve",
        conversation_id=conversation_id,
        approve=True,
        auto_approve=auto_approve,
    )
    async for delta in _gated(stream, run, workspace):
        yield delta


async def _approve_pending(
    workspace: str | None,
    conversation_id: str | None,
    auto_approve: bool | None,
) -> AsyncIterator[models.ChatDelta]:
    """``approve=true`` is sugar for answering the outstanding approval card (spec 011 FR-25).

    One resume path, reached two ways. Feature 002's approve-to-execute turn and feature 008's card
    click must not be able to diverge: whichever the operator uses, the same stored decision is
    applied to the same paused operation.
    """
    from . import capabilities

    cid, record = _pending_record(workspace, conversation_id)
    option = next(
        (o.get("id") for o in record.get("options", []) if isinstance(o, dict) and o.get("id")),
        "approve",
    )
    if not record or record.get("status") != "pending" or record.get("kind") != "approval":
        # No live card, but the pause may still be on record as a plan — a card can be expired,
        # superseded, or never raisable, and none of those should strand approvable work.
        pending_plan = _pending_plan_record(workspace, cid)
        if pending_plan:
            async for delta in _approve_plan(workspace, cid, pending_plan, auto_approve):
                yield delta
            return
        name, _ = capabilities.resolve_for_chat(workspace)
        yield models.ChatDelta(
            workspace=name,
            conversation_id=cid,
            reply="There is nothing awaiting your approval in this conversation.",
            done=True,
        )
        return
    async for delta in respond_stream(
        workspace, cid, record["interaction_id"], option, auto_approve=auto_approve
    ):
        yield delta


async def respond_stream(
    workspace: str | None,
    conversation_id: str,
    interaction_id: str,
    choice: str,
    auto_approve: bool | None = None,
) -> AsyncIterator[models.ChatDelta]:
    """Answer a pending interaction, resuming the paused work under a fresh run (FR-26/FR-27).

    An approval seeds the new run with the stored ``granted_key``, so the operation that paused the
    previous run is let through exactly once and execution completes in this turn. A decline seeds
    nothing: the work does not run, and the same operation is not re-asked.
    """
    from . import capabilities

    name, _wpath = capabilities.resolve_for_chat(workspace)
    cid, record = _pending_record(workspace, conversation_id)
    matched = record.get("interaction_id") == interaction_id and record.get("status") == "pending"
    risk = record.get("risk") if matched else None

    declined = choice == "decline"
    if risk is not None and choice != "chat":
        _record_operator_decision(record, approved=not declined, workspace=name)

    run = build_run(
        (record.get("objective") if matched else "") or "(resumed)",
        name,
        trust=auto_approve,
        granted_key="" if declined or risk is None else str(record.get("granted_key") or ""),
    )
    stream = capabilities.respond_to_interaction_stream(workspace, cid, interaction_id, choice)
    async for delta in _gated(stream, run, workspace):
        yield delta


async def respond(
    workspace: str | None,
    conversation_id: str,
    interaction_id: str,
    choice: str,
    auto_approve: bool | None = None,
) -> models.ChatAnswer:
    """Non-streaming interaction response — drives ``respond_stream`` to completion."""
    last: models.ChatDelta | None = None
    async for delta in respond_stream(workspace, conversation_id, interaction_id, choice, auto_approve):
        last = delta
    assert last is not None
    return _answer(last)
