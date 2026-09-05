"""Control mode - the operator's global approval-gate switch (spec 013).

One test per acceptance criterion. The load-bearing one is
``test_audit_preserved_when_bypassed_fr6`` (AC-6): it separates this feature from an
unconstitutional bypass, by proving the *ask* is skipped while the *audit* survives.
"""

from __future__ import annotations

import asyncio
import json

import pytest

from app import config, judge, workflow
from app.execution_gate import Operation

# Fixture targets are deliberately inert placeholder strings. An earlier draft used a literal
# destructive shell command here, which the risk scorer read out of the test source itself and
# scored as though it were a real effect. Test data should not look like a live payload.
BENIGN_TARGET = "workspace/scratch/example.md"


def _operation(tier: str = "approval") -> Operation:
    return Operation(
        kind="tool", name="Bash", target=BENIGN_TARGET, tier=tier,
        reversibility="not recoverable outside git",
    )


def _report(tier: str = "reversible") -> workflow.RiskReport:
    scored = workflow.score_operation(_operation(tier))
    return workflow.RiskReport(
        run_id="r1", objective="tidy the scratch folder", workspace="w",
        gating=scored, accumulated=(scored,),
    )


# --- the flag itself ------------------------------------------------------------------

def test_default_is_enforcing_fr2(monkeypatch):
    """spec 013 FR-2 / AC-1: unset means governed."""
    monkeypatch.delenv(config.CONTROL_MODE_ENV, raising=False)
    assert config.control_mode() is True


@pytest.mark.parametrize(
    "value", ["false", "FALSE", "  false  ", "0", "no", "off", "Off", "disabled"]
)
def test_off_values_disable_fr1(monkeypatch, value):
    """spec 013 FR-1/FR-3 / AC-2: the explicit off-vocabulary, case- and space-insensitive."""
    monkeypatch.setenv(config.CONTROL_MODE_ENV, value)
    assert config.control_mode() is False


@pytest.mark.parametrize(
    "value", ["", "   ", "true", "TRUE", "maybe", "flase", "1", "yes", "nope"]
)
def test_fail_safe_parsing_fr3(monkeypatch, value):
    """spec 013 FR-3 / AC-3: anything unrecognised leaves the gate ON.

    ``flase`` is the point of this test - a typo must not silently disarm the gate.
    """
    monkeypatch.setenv(config.CONTROL_MODE_ENV, value)
    assert config.control_mode() is True


def test_flag_is_env_only_fr4(monkeypatch):
    """spec 013 FR-4 / AC-7: no setter, and nothing persisted to the settings file."""
    assert not hasattr(config, "set_control_mode")
    monkeypatch.setenv(config.CONTROL_MODE_ENV, "false")
    assert config.control_mode() is False
    assert "control_mode" not in json.dumps(config._read_settings())


# --- layer 3: the judge ---------------------------------------------------------------

def test_judge_bypasses_without_model_call_fr5(monkeypatch):
    """spec 013 FR-5/FR-8 / AC-4: approve directly, and never consult the model."""
    monkeypatch.setenv(config.CONTROL_MODE_ENV, "false")
    calls = []

    async def must_not_run(_system, _prompt):
        calls.append(1)
        raise AssertionError("the model must not be consulted when control mode is off")

    checker = judge.Judge(
        trust=False,
        precedent_lookup=lambda _r: None,
        experience_empty=lambda: True,
        ask_model=must_not_run,
    )
    verdict = asyncio.run(checker.review(_report()))

    assert verdict.decision == "approve"
    assert verdict.source == "control-mode-off"
    assert calls == [], "control mode off must skip the LLM call, not discard its answer"


def test_judge_still_enforces_when_on(monkeypatch):
    """spec 013 AC-1: with the flag unset, spec 011's filter still governs (cold start -> ask)."""
    monkeypatch.delenv(config.CONTROL_MODE_ENV, raising=False)

    async def approving(_system, _prompt):
        return json.dumps({"decision": "approve", "reasoning": "looks fine", "confidence": 1.0})

    checker = judge.Judge(
        trust=True,
        precedent_lookup=lambda _r: None,
        experience_empty=lambda: True,  # cold start (011 FR-20) -> downgrade to ask
        ask_model=approving,
    )
    verdict = asyncio.run(checker.review(_report()))
    assert verdict.decision == "ask"


# --- layer 2 default checker ----------------------------------------------------------

def test_ask_checker_honours_bypass_fr5(monkeypatch):
    """spec 013 FR-5 / AC-5: the bypass must not depend on a judge being installed."""
    monkeypatch.setenv(config.CONTROL_MODE_ENV, "false")
    verdict = asyncio.run(workflow.AskChecker().review(_report()))
    assert (verdict.decision, verdict.source) == ("approve", "control-mode-off")


def test_ask_checker_asks_when_on(monkeypatch):
    """spec 011 FR-13 regression: the default checker still asks with control mode on."""
    monkeypatch.delenv(config.CONTROL_MODE_ENV, raising=False)
    verdict = asyncio.run(workflow.AskChecker().review(_report()))
    assert verdict.decision == "ask"
    assert verdict.source == "default"


# --- the constitutional guarantee -----------------------------------------------------

def test_audit_preserved_when_bypassed_fr6(monkeypatch):
    """spec 013 FR-6 / AC-6 - the criterion that keeps this feature constitutional.

    P8 requires that *in all cases* an executed mutation stay auditable and state who decided, and
    P12 that every mutation be evaluated. So a bypassed operation must still be scored, still carry
    its justification, and still appear in the run record as executed. Bypassing the ask is the
    feature; bypassing the audit would be the defect.
    """
    monkeypatch.setenv(config.CONTROL_MODE_ENV, "false")
    run = workflow.WorkflowRun(objective="tidy the scratch folder", workspace="w", threshold=1)

    permit = asyncio.run(run.permit(_operation()))

    assert permit.allow is True, "control mode off must let the gating operation through"
    assert run.awaiting is False, "the run must not pause"

    (recorded,) = run.operations
    assert recorded.status == "executed"
    assert recorded.score >= 1, "the operation must still be scored (P12)"
    assert recorded.justification, "the effect/undo justification must still be recorded"

    record = run.as_dict()
    assert record["verdict"]["source"] == "control-mode-off", "record must name who decided (P8)"
    assert record["operations"][0]["status"] == "executed"


def test_gate_still_pauses_when_on(monkeypatch):
    """spec 011 FR-12 regression: the same operation pauses with control mode on."""
    monkeypatch.delenv(config.CONTROL_MODE_ENV, raising=False)
    run = workflow.WorkflowRun(objective="tidy the scratch folder", workspace="w", threshold=1)

    permit = asyncio.run(run.permit(_operation()))

    assert permit.allow is False
    assert run.awaiting is True


# --- FR-7 startup warning -------------------------------------------------------------

def test_startup_warns_when_off_fr7(monkeypatch, capsys):
    """spec 013 FR-7 / AC-8: a disabled gate is never silent."""
    monkeypatch.setenv(config.CONTROL_MODE_ENV, "false")
    import app.__main__ as entry

    monkeypatch.setattr(entry.uvicorn, "run", lambda *_a, **_kw: None)
    entry.main()

    out = capsys.readouterr().out
    assert "CONTROL MODE OFF" in out
    assert "LEADER_CONTROL_MODE" in out


def test_startup_quiet_when_on(monkeypatch, capsys):
    """The warning must not appear in the default, governed configuration."""
    monkeypatch.delenv(config.CONTROL_MODE_ENV, raising=False)
    import app.__main__ as entry

    monkeypatch.setattr(entry.uvicorn, "run", lambda *_a, **_kw: None)
    entry.main()

    assert "CONTROL MODE OFF" not in capsys.readouterr().out
