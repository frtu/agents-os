"""Feature 011 layer 2 — workflow reporting: score, accumulate, pause.

Unit-level: layer 2 is exercised directly, with layers 1 and 3 present only as their default stubs
(``Operation`` announcements and ``AskChecker``) — which is the FR-35/AC-1 claim under test. No
``pytest-asyncio`` in this repo, so ``permit`` is driven with ``asyncio.run`` like the other async
tests in the suite.
"""

from __future__ import annotations

import ast
import asyncio
import inspect
import json
from pathlib import Path

import pytest

from app import workflow
from app.execution_gate import Operation
from app.workflow import ScoredOperation, ScoringModifier, Verdict, WorkflowRun, score_operation

WORKFLOW_SOURCE = Path(workflow.__file__)


def op(**kw) -> Operation:
    """An announcement with sane defaults, so each test states only what it is about."""
    base = {
        "kind": "capability",
        "name": "query",
        "target": "vault/wiki/portal.md",
        "tier": "auto",
        "reversibility": "read-only — nothing to undo",
    }
    base.update(kw)
    return Operation(**base)


def weights_file(tmp_path, monkeypatch, payload: dict) -> Path:
    path = tmp_path / ".leader-risk-weights.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("LEADER_RISK_WEIGHTS_PATH", str(path))
    return path


# --- FR-8: score = tier base + data-declared modifiers, clamped 1-5 ---------


def test_score_is_tier_base_when_no_modifier_fires_fr8():
    # FR-8: base comes from the declared tier — auto 1, reversible 2, approval 4.
    assert score_operation(op(tier="auto")).score == 1
    reversible = op(
        name="ingest", tier="reversible", reversibility="`git revert` the ingest commit"
    )
    assert score_operation(reversible).score == 2
    approval = op(
        name="deposit", tier="approval", target="notes/x.md", reversibility="`git revert` it"
    )
    assert score_operation(approval).score == 4


def test_score_adds_fired_modifier_weights_fr8():
    # FR-8: reversible base 2 + EXTERNALLY_VISIBLE 1 = 3.
    external = op(
        name="publish",
        tier="reversible",
        target="vault/output/report.md",
        reversibility="`git revert` the commit",
        external=True,
    )
    scored = score_operation(external)
    assert scored.modifiers == ("EXTERNALLY_VISIBLE",)
    assert scored.score == 3


def test_score_clamps_to_five_fr8():
    # FR-8: approval 4 + irreversible 1 + privilege 1 + sensitive 1 would be 7; the scale stops at 5.
    scored = score_operation(
        op(
            name="import_skill",
            target="skills/weekly-digest",
            tier="approval",
            reversibility="unlink skills/<name> — but any run it enabled is not undone",
        )
    )
    assert {"IRREVERSIBLE_OUTSIDE_GIT", "PRIVILEGE_GRANTING"} <= set(scored.modifiers)
    assert scored.score == 5


def test_score_clamps_to_one_fr8(tmp_path, monkeypatch):
    # FR-8: a hand-edited base below the scale cannot drive a score under 1.
    weights_file(tmp_path, monkeypatch, {"tier_base": {"auto": -4}})
    assert score_operation(op(tier="auto")).score == 1


def test_score_survives_a_typo_in_the_weights_file(tmp_path, monkeypatch):
    # FR-32: a corrupt config falls back to defaults; scoring is never switched off by a typo.
    path = tmp_path / ".leader-risk-weights.json"
    path.write_text("{ not json", encoding="utf-8")
    monkeypatch.setenv("LEADER_RISK_WEIGHTS_PATH", str(path))
    assert score_operation(op(tier="reversible")).score == 2


# --- FR-9 / FR-10: what a modifier may look at, and what it must say --------


def test_modifiers_only_see_an_operation_fr9_ac7():
    # AC-7 / FR-9: every condition takes exactly one argument, an Operation. Trust mode, precedent
    # and the request's wording are not reachable from a modifier because they are not passed in.
    for modifier in workflow.MODIFIERS:
        params = list(inspect.signature(modifier.condition).parameters.values())
        assert len(params) == 1, modifier.name
        assert modifier.condition(op()) in (True, False), modifier.name


def test_no_modifier_mentions_trust_precedent_or_wording_fr9_ac7():
    # AC-7 / FR-9: neither the declared names/descriptions nor the module's imports may reach
    # layer 3's inputs. Enforced structurally on the source so a future modifier cannot smuggle
    # one in.
    forbidden = ("trust", "auto_approve", "precedent", "experience", "operator identity", "message")
    for modifier in workflow.MODIFIERS:
        blob = f"{modifier.name} {modifier.description}".lower()
        assert not any(word in blob for word in forbidden), modifier.name

    tree = ast.parse(WORKFLOW_SOURCE.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").lstrip("."))
            imported.update(a.name for a in node.names)
        elif isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
    # FR-34: layer 2 imports the layer-1 contract and config, nothing else of ours.
    assert not {"judge", "experience", "concierge", "capabilities", "agent"} & imported


def test_justification_states_effect_and_undo_path_fr10():
    # FR-10: one line, the concrete effect plus how it is undone, plus why it scored up.
    scored = score_operation(
        op(
            kind="tool",
            name="Write",
            target="vault/wiki/log.md",
            tier="reversible",
            reversibility="recoverable from the workspace git repo",
        )
    )
    assert "\n" not in scored.justification
    assert "Write on vault/wiki/log.md" in scored.justification
    assert "recoverable from the workspace git repo" in scored.justification
    assert "SENSITIVE_TARGET" in scored.modifiers
    # the human-readable reason travels with it, verbatim
    reason = next(m.description for m in workflow.MODIFIERS if m.name == "SENSITIVE_TARGET")
    assert reason in scored.justification


# --- the individual modifiers ----------------------------------------------


def test_irreversible_modifier_matches_meaning_not_one_string_fr9():
    # FR-9: the effect table owns the wording; both live phrasings must fire, and a read must not.
    fired = lambda o: score_operation(o).modifiers  # noqa: E731
    assert "IRREVERSIBLE_OUTSIDE_GIT" in fired(
        op(
            name="create_workspace",
            target="demo",
            tier="approval",
            reversibility="delete the workspace directory manually; no git revert covers it",
        )
    )
    assert "IRREVERSIBLE_OUTSIDE_GIT" in fired(
        op(
            name="import_skill",
            target="weekly-digest",
            tier="approval",
            reversibility="unlink skills/<name> — but any run it enabled is not undone",
        )
    )
    assert "IRREVERSIBLE_OUTSIDE_GIT" not in fired(op())
    assert "IRREVERSIBLE_OUTSIDE_GIT" not in fired(
        op(tier="reversible", reversibility="`git revert` the ingest commit in the workspace repo")
    )


@pytest.mark.parametrize(
    "command",
    [
        "rm -rf vault/output",
        "mv a.md b.md",
        "git reset --hard HEAD~1",
        "git push --force origin master",
        "sed -i 's/a/b/' notes.md",
        "cat new.md > vault/wiki/portal.md",
        "truncate -s 0 log.txt",
    ],
)
def test_destructive_shell_fires_fr9(command):
    # FR-9: coarse detection of a shell command whose effect is a deletion or overwrite.
    scored = score_operation(op(kind="tool", name="Bash", target=command, tier="reversible"))
    assert "DESTRUCTIVE_SHELL" in scored.modifiers, command


@pytest.mark.parametrize(
    "command",
    [
        "git status",
        "ls -la vault/wiki",
        'grep -rn "rm" vault/wiki',
        "uv run --extra dev pytest -q",
        "echo hello >> vault/wiki/log.md",
        "git log --oneline 2>&1",
    ],
)
def test_destructive_shell_does_not_fire_on_reads_fr9(command):
    scored = score_operation(op(kind="tool", name="Bash", target=command, tier="reversible"))
    assert "DESTRUCTIVE_SHELL" not in scored.modifiers, command


def test_breadth_fires_on_a_glob_or_three_targets_fr9():
    fired = lambda target: score_operation(  # noqa: E731
        op(kind="tool", name="Edit", target=target, tier="reversible")
    ).modifiers
    assert "BREADTH_MANY_TARGETS" in fired("vault/wiki/concepts/*.md")
    assert "BREADTH_MANY_TARGETS" in fired("a/one.md b/two.md c/three.md")
    assert "BREADTH_MANY_TARGETS" not in fired("a/one.md b/two.md")
    assert "BREADTH_MANY_TARGETS" not in fired("vault/wiki/portal.md")


def test_sensitive_targets_fire_fr9():
    for target in (
        "vault/wiki/log.md",
        ".git/config",
        ".leader-settings.json",
        ".leader-experience.jsonl",
        ".leader-risk-weights.json",
        "memory/constitution.md",
    ):
        scored = score_operation(
            op(kind="tool", name="Write", target=target, tier="reversible")
        )
        assert "SENSITIVE_TARGET" in scored.modifiers, target
    # a .gitignore is not the git database
    assert "SENSITIVE_TARGET" not in score_operation(
        op(kind="tool", name="Write", target=".gitignore", tier="reversible")
    ).modifiers


# --- FR-36 / FR-32: separate evolution, fresh weights ----------------------


def test_adding_a_modifier_needs_no_effect_table_change_fr36(tmp_path, monkeypatch):
    # FR-36 / AC-6: a new modifier is declared data plus a weight in the JSON file. `capabilities`
    # (and its EFFECTS table) is untouched — layer 2 cannot even import it (FR-34).
    from app import capabilities

    before = dict(capabilities.EFFECTS)
    weights_file(tmp_path, monkeypatch, {"modifiers": {"TOUCHES_YAML": 2}})
    monkeypatch.setattr(
        workflow,
        "MODIFIERS",
        workflow.MODIFIERS
        + (
            ScoringModifier(
                name="TOUCHES_YAML",
                description="rewrites structured front matter",
                condition=lambda o: o.target.endswith(".yaml"),
            ),
        ),
    )
    scored = score_operation(
        op(kind="tool", name="Write", target="conf.yaml", tier="reversible")
    )
    assert scored.modifiers == ("TOUCHES_YAML",)
    assert scored.score == 4
    assert dict(capabilities.EFFECTS) == before


def test_adding_a_capability_needs_no_modifier_change_fr36():
    # FR-36 / AC-6: a capability layer 2 has never heard of scores from its declared tier alone.
    scored = score_operation(
        op(
            name="brand_new_capability",
            target="vault/wiki/synthesis/idea.md",
            tier="reversible",
            reversibility="`git revert` the commit",
        )
    )
    assert scored.modifiers == ()
    assert scored.score == 2


def test_weights_are_read_fresh_from_the_json_file_fr32_ac18(tmp_path, monkeypatch):
    # AC-18 / FR-32: retune by hand-editing the file; the next operation scores differently, with no
    # restart and no code change.
    external = op(
        name="publish",
        tier="reversible",
        target="vault/output/report.md",
        reversibility="`git revert` the commit",
        external=True,
    )
    assert score_operation(external).score == 3

    path = weights_file(tmp_path, monkeypatch, {"modifiers": {"EXTERNALLY_VISIBLE": 3}})
    assert score_operation(external).score == 5

    path.write_text(json.dumps({"modifiers": {"EXTERNALLY_VISIBLE": 0}}), encoding="utf-8")
    assert score_operation(external).score == 2


def test_gate_threshold_is_read_fresh_by_the_run_fr32(tmp_path, monkeypatch):
    monkeypatch.delenv("LEADER_GATE_THRESHOLD", raising=False)
    weights_file(tmp_path, monkeypatch, {"thresholds": {"gate": 2}})
    run = WorkflowRun(objective="tidy the wiki", workspace="demo")
    assert run.threshold == 2


# --- FR-6/FR-7/FR-11/FR-12/FR-13: the run ---------------------------------


def reversible_write(target: str) -> Operation:
    return op(
        kind="tool",
        name="Write",
        target=target,
        tier="reversible",
        reversibility="recoverable from the workspace git repo",
    )


def gating_delete() -> Operation:
    return op(
        kind="tool",
        name="Bash",
        target="rm vault/wiki/concepts/old.md",
        tier="reversible",
        reversibility="recoverable from the workspace git repo",
    )


def test_run_lets_low_scores_through_and_records_them_fr6_fr7():
    # FR-6/FR-7: one run per request; every announcement is recorded, scored, justified.
    run = WorkflowRun(objective="answer a question", workspace="demo")

    async def drive():
        return [await run.permit(op()) for _ in range(3)]

    assert all(p.allow for p in drive_sync(drive))
    assert [s.status for s in run.operations] == ["executed"] * 3
    assert all(s.score == 1 and s.justification for s in run.operations)
    assert run.state == "running"
    assert run.pending_report is None


def test_report_includes_already_executed_operations_fr11_ac5():
    # AC-5 / FR-11: the operator sees the blast radius — the three rewrites *and* the delete.
    seen: list = []

    class Recorder:
        async def review(self, report):
            seen.append(report)
            return Verdict(decision="ask", reasoning="need a human", source="default")

    run = WorkflowRun(objective="reorganise the wiki", workspace="demo", checker=Recorder())

    async def drive():
        for page in ("one.md", "two.md", "three.md"):
            assert (await run.permit(reversible_write(f"vault/wiki/{page}"))).allow
        return await run.permit(gating_delete())

    denied = drive_sync(drive)
    assert denied.allow is False
    (report,) = seen
    assert len(report.accumulated) == 4
    assert [s.status for s in report.accumulated] == ["executed"] * 3 + ["pending"]
    assert report.accumulated[-1] is report.gating
    assert report.gating.score >= run.threshold
    assert all(s.justification for s in report.accumulated)
    assert report.objective == "reorganise the wiki"
    assert run.pending_report is report


def test_run_pauses_at_the_first_gate_and_nothing_after_it_runs_fr12_ac4():
    # AC-4 / FR-12: pause at the first operation reaching the threshold; everything announced after
    # it is denied and recorded `not-reached`, without consulting the checker again.
    calls: list = []

    class CountingChecker:
        async def review(self, report):
            calls.append(report)
            return Verdict(decision="ask", reasoning="ask the operator", source="default")

    run = WorkflowRun(objective="tidy up", workspace="demo", checker=CountingChecker())

    async def drive():
        first = await run.permit(gating_delete())
        after = [await run.permit(reversible_write("vault/wiki/later.md")) for _ in range(2)]
        return first, after

    first, after = drive_sync(drive)
    assert first.allow is False
    assert all(p.allow is False for p in after)
    assert len(calls) == 1
    assert run.awaiting is True
    assert [s.status for s in run.operations] == ["pending", "not-reached", "not-reached"]


def test_default_ask_checker_pauses_the_run_fr13_fr35_ac1():
    # AC-1 / FR-13/FR-35: layer 2 is correct with layer 3 absent — the default checker asks.
    run = WorkflowRun(objective="install a skill", workspace="demo")
    permit = drive_sync(
        lambda: run.permit(
            op(
                name="import_skill",
                target="weekly-digest",
                tier="approval",
                reversibility="unlink skills/<name> — but any run it enabled is not undone",
            )
        )
    )
    assert permit.allow is False
    assert run.awaiting is True
    assert run.verdict.decision == "ask"
    assert run.verdict.source == "default"
    assert workflow.ASK_DEFAULT_REASON in (run.verdict.reasoning or "")


def test_checker_approval_lets_the_operation_run_fr13():
    class Approver:
        async def review(self, report):
            return Verdict(decision="approve", reasoning="precedent", source="precedent")

    run = WorkflowRun(objective="tidy up", workspace="demo", checker=Approver())
    permit = drive_sync(lambda: run.permit(gating_delete()))
    assert permit.allow is True
    assert [s.status for s in run.operations] == ["executed"]
    assert run.state == "running"
    assert run.verdict.source == "precedent"


def test_approval_resumes_the_same_operation_once_fr26():
    # FR-26 / AC-15: on approval the paused operation completes in the same turn — and is settled in
    # place, so the audit record holds one entry, not two.
    run = WorkflowRun(objective="tidy up", workspace="demo")
    assert drive_sync(lambda: run.permit(gating_delete())).allow is False

    verdict = run.resume(approved=True)
    assert verdict.decision == "approve"
    assert verdict.source == "user"
    assert run.awaiting is False

    assert drive_sync(lambda: run.permit(gating_delete())).allow is True
    assert [s.status for s in run.operations] == ["executed"]
    # the grant was one-shot: the same shape gates again if attempted a second time
    assert drive_sync(lambda: run.permit(gating_delete())).allow is False


def test_declined_operation_is_not_re_asked_in_the_run_fr27_ac14():
    # AC-14 / FR-27: a decline stops the operation, ends the run, and is never re-asked — the
    # checker is consulted exactly once no matter how often layer 1 retries.
    calls: list = []

    class CountingChecker:
        async def review(self, report):
            calls.append(report)
            return Verdict(decision="ask", reasoning="ask", source="default")

    run = WorkflowRun(objective="tidy up", workspace="demo", checker=CountingChecker())
    assert drive_sync(lambda: run.permit(gating_delete())).allow is False
    run.resume(approved=False, reasoning="not that page")

    retry = drive_sync(lambda: run.permit(gating_delete()))
    assert retry.allow is False
    assert "FR-27" in (retry.reason or "")
    assert len(calls) == 1
    assert run.state == "declined"
    assert run.verdict.decision == "decline"
    assert [s.status for s in run.operations] == ["declined", "not-reached"]
    # nothing else runs either
    assert drive_sync(lambda: run.permit(op())).allow is False


def test_checker_decline_is_final_for_the_run_fr27():
    class Decliner:
        async def review(self, report):
            return Verdict(decision="decline", reasoning="operator refused this before")

    run = WorkflowRun(objective="tidy up", workspace="demo", checker=Decliner())
    assert drive_sync(lambda: run.permit(gating_delete())).allow is False
    assert run.state == "declined"
    with pytest.raises(ValueError):
        run.resume(approved=True)


def test_resume_requires_an_outstanding_ask():
    run = WorkflowRun(objective="nothing risky", workspace="demo")
    with pytest.raises(ValueError):
        run.resume(approved=True)


def test_run_implements_the_gate_protocol_and_installs_fr6():
    # FR-6/FR-3: the run *is* the gate layer 1 announces to, so one run spans a whole execution.
    from app import execution_gate

    run = WorkflowRun(objective="tidy up", workspace="demo")
    assert isinstance(run, execution_gate.Gate)

    async def drive():
        with execution_gate.use_gate(run):
            return await execution_gate.announce(reversible_write("vault/wiki/a.md"))

    assert drive_sync(drive).allow is True
    assert run.operations[0].operation.name == "Write"


# --- FR-14: audit ----------------------------------------------------------


def test_as_dict_reconstructs_the_run_for_audit_fr14_ac19():
    # AC-19 / FR-14: each operation, its modifiers, the verdict, its reasoning and who decided —
    # all JSON-serialisable, and produced without layer 2 writing a file.
    class Asker:
        async def review(self, report):
            return Verdict(decision="ask", reasoning="novel shape", confidence=0.4, source="judge")

    run = WorkflowRun(objective="reorganise the wiki", workspace="demo", checker=Asker())

    async def drive():
        await run.permit(reversible_write("vault/wiki/one.md"))
        await run.permit(gating_delete())

    drive_sync(drive)
    run.resume(approved=False, reasoning="leave that page alone")

    record = run.as_dict()
    assert json.loads(json.dumps(record)) == record  # JSON-serialisable
    assert record["run_id"] == run.run_id
    assert record["objective"] == "reorganise the wiki"
    assert record["workspace"] == "demo"
    assert record["state"] == "declined"
    assert [o["status"] for o in record["operations"]] == ["executed", "declined"]
    gating = record["operations"][-1]
    assert gating["name"] == "Bash"
    assert "DESTRUCTIVE_SHELL" in gating["modifiers"]
    assert gating["justification"]
    assert gating["score"] >= record["threshold"]
    assert record["verdict"] == {
        "decision": "decline",
        "reasoning": "leave that page alone",
        "confidence": 1.0,
        "source": "user",
        "matched_precedent": None,
    }
    # the report behind the ask survives on the record too, so the card can be re-rendered
    assert record["report"]["gating"]["op_id"] == gating["op_id"]


def test_scored_operation_rejects_an_unknown_status():
    scored: ScoredOperation = score_operation(op())
    with pytest.raises(ValueError):
        scored.with_status("maybe")


def drive_sync(coro_factory):
    """Run one async call to completion — the suite has no pytest-asyncio plugin."""
    return asyncio.run(coro_factory())
