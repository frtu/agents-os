"""Feature 011 — the past-experience store (spec 011 FR-17…FR-20, FR-29…FR-32).

One test per requirement, each citing the spec id it covers. Every test writes only under the
pytest ``tmp_path``: the autouse ``isolated_workspace_root`` fixture in ``conftest.py`` already
repoints ``LEADER_WORKSPACE_ROOT``, and ``experience_path`` fixture below pins
``LEADER_EXPERIENCE_PATH`` / ``LEADER_RISK_WEIGHTS_PATH`` explicitly so the real workspace root is
never touched even if a default changes.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone

import pytest

from app import config, experience
from app.execution_gate import Operation


@pytest.fixture(autouse=True)
def experience_paths(tmp_path, monkeypatch):
    """Pin both feature-011 files inside tmp_path (nothing here may touch a real workspace)."""
    store = tmp_path / "experience" / ".leader-experience.jsonl"
    weights = tmp_path / "experience" / ".leader-risk-weights.json"
    monkeypatch.setenv("LEADER_EXPERIENCE_PATH", str(store))
    monkeypatch.setenv("LEADER_RISK_WEIGHTS_PATH", str(weights))
    return store, weights


def _op(name="import_skill", target="second-brain-ingest", kind="capability", tier="approval"):
    return Operation(
        kind=kind,
        name=name,
        target=target,
        tier=tier,
        reversibility="unlink skills/<name>",
    )


def _write(store, records):
    """Hand-write records with controlled timestamps/sources (the store is plain JSONL by design)."""
    store.parent.mkdir(parents=True, exist_ok=True)
    with store.open("a", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")


def _record(
    fingerprint,
    decision="approve",
    source="user",
    age_days=1,
    score=4,
    record_id="r1",
):
    when = datetime.now(timezone.utc) - timedelta(days=age_days)
    return {
        "schema": 1,
        "record_id": record_id,
        "timestamp": when.isoformat(),
        "run_id": "run-1",
        "workspace": "demo",
        "objective_fingerprint": "obj:import-skill",
        "operation_fingerprint": fingerprint,
        "score": score,
        "band": experience.band(score),
        "decision": decision,
        "source": source,
        "matched_precedent": None,
        "outcome": "executed",
        "reasoning": "",
    }


# --- recording -------------------------------------------------------------------------------


def test_one_record_per_decision_appends_without_rewriting_fr29(experience_paths):
    """spec 011 FR-29/FR-30, AC-16: one line per decision, and the first line is never touched."""
    store, _ = experience_paths

    assert experience.record(run_id="run-1", operation=_op(), decision="approve", source="user")
    first_line = store.read_text(encoding="utf-8").splitlines()[0]

    assert experience.record(
        run_id="run-1", operation=_op(target="triage"), decision="decline", source="user"
    )

    lines = store.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert lines[0] == first_line  # append-only: the earlier record is byte-identical

    parsed = [json.loads(line) for line in lines]
    assert [p["decision"] for p in parsed] == ["approve", "decline"]
    for p in parsed:
        # FR-29's required fields, plus the schema version the append-only file needs to outlive
        # this shape.
        for key in (
            "schema",
            "timestamp",
            "run_id",
            "objective_fingerprint",
            "operation_fingerprint",
            "score",
            "band",
            "decision",
            "source",
            "matched_precedent",
            "outcome",
        ):
            assert key in p, key
        datetime.fromisoformat(p["timestamp"])  # a real ISO timestamp


def test_write_failure_does_not_raise_fr30(tmp_path, monkeypatch):
    """spec 011 FR-30, AC-16: a failure to write must never fail the response."""
    blocker = tmp_path / "not-a-directory"
    blocker.write_text("i am a file", encoding="utf-8")
    monkeypatch.setenv("LEADER_EXPERIENCE_PATH", str(blocker / "nested" / "exp.jsonl"))

    assert experience.record(run_id="r", operation=_op(), decision="approve", source="user") is False
    assert experience.is_empty() is True


def test_record_async_is_off_the_response_path_and_swallows_fr30(experience_paths):
    """spec 011 FR-30, AC-16: the async entry point lands the record and never raises."""
    store, _ = experience_paths

    async def _turn():
        # Fire and forget: the caller does not await the write itself.
        experience.record_async(
            run_id="run-async", operation=_op(), decision="approve", source="user"
        )
        assert experience.pending_count() >= 1
        await experience.drain()

    asyncio.run(_turn())

    lines = store.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["run_id"] == "run-async"


def test_record_async_survives_an_unwritable_store_fr30(tmp_path, monkeypatch):
    """spec 011 FR-30, AC-16: the async path swallows too — a full disk is not a chat failure."""
    blocker = tmp_path / "blocker"
    blocker.write_text("x", encoding="utf-8")
    monkeypatch.setenv("LEADER_EXPERIENCE_PATH", str(blocker / "exp.jsonl"))

    async def _turn():
        experience.record_async(run_id="r", operation=_op(), decision="approve", source="user")
        await experience.drain()

    asyncio.run(_turn())  # no exception is the assertion


# --- fingerprints ----------------------------------------------------------------------------


def test_fingerprints_are_deterministic_and_shape_scoped_fr31():
    """spec 011 FR-31: the same shape matches; a different shape does not."""
    a = experience.operation_fingerprint(_op())
    b = experience.operation_fingerprint(_op())
    assert a == b  # deterministic across calls
    assert a != experience.operation_fingerprint(_op(target="triage"))

    # op_id is per-occurrence and must not enter the fingerprint.
    one, two = _op(), _op()
    assert one.op_id != two.op_id
    assert experience.operation_fingerprint(one) == experience.operation_fingerprint(two)

    # Same directory, different filename = one shape. Different directory = a different shape.
    write_a = _op(kind="tool", name="Write", target="vault/wiki/concepts/widgets.md", tier="reversible")
    write_b = _op(kind="tool", name="Write", target="vault/wiki/concepts/gadgets.md", tier="reversible")
    write_c = _op(kind="tool", name="Write", target="vault/wiki/product/specs/x.md", tier="reversible")
    assert experience.operation_fingerprint(write_a) == experience.operation_fingerprint(write_b)
    assert experience.operation_fingerprint(write_a) != experience.operation_fingerprint(write_c)

    # Absolute paths are made workspace-relative so experience is global (FR-33).
    absolute = _op(
        kind="tool",
        name="Write",
        target="/Users/someone/Workspaces/demo/vault/wiki/concepts/widgets.md",
        tier="reversible",
    )
    assert experience.operation_fingerprint(absolute) == experience.operation_fingerprint(write_a)


def test_fingerprints_are_human_readable_fr31():
    """spec 011 FR-31, D5: a precedent must be explainable without running the judge."""
    fp = experience.operation_fingerprint(_op())
    assert "import_skill" in fp
    assert "second-brain-ingest" in fp
    assert fp == "capability:import_skill:second-brain-ingest"

    tool_fp = experience.operation_fingerprint(
        _op(kind="tool", name="Write", target="vault/wiki/concepts/widgets.md", tier="reversible")
    )
    assert "Write" in tool_fp  # the SDK tool name survives verbatim
    assert tool_fp == "tool:Write:vault/wiki/concepts/*"

    # FR-41 supersedes the earlier "first three program names in order" rule: the class is the
    # effect-bearing programs only, so the read-only `git status` helper drops out.
    bash_fp = experience.operation_fingerprint(
        _op(kind="tool", name="Bash", target="rm -rf build && git status", tier="approval")
    )
    assert "Bash" in bash_fp
    assert bash_fp == "tool:Bash:rm"


def test_read_only_commands_share_one_fingerprint_fr41_ac24():
    """spec 011 FR-41 / AC-24: slight variations of one read must canonicalise to one shape.

    The earlier rule keyed on the ordered first three program names, so every phrasing of an
    inventory was a new shape at zero approvals and precedent could never reach FR-17's sample count.
    """
    variants = [
        'echo "=== tree ==="; find vault/raw -type f | head -200; wc -l',
        'pwd; ls -la | head -30; find vault -maxdepth 3 2>/dev/null | sort',
        "tail -20 vault/wiki/log.md 2>/dev/null",
        "git status --short && git log --oneline | head -5",
        "cat vault/wiki/portal.md 2>&1 | grep -i concept",
    ]
    fingerprints = {
        experience.operation_fingerprint(
            _op(kind="tool", name="Bash", target=command, tier="auto")
        )
        for command in variants
    }
    assert fingerprints == {"tool:Bash:read-only"}


def test_mutating_commands_fingerprint_on_their_effect_fr41_ac24():
    """spec 011 FR-41 / AC-24: order and read-only helpers are not part of a mutating identity."""
    fp = lambda command: experience.operation_fingerprint(  # noqa: E731
        _op(kind="tool", name="Bash", target=command, tier="reversible")
    )
    # Order-independent, and the `ls`/`find` helpers drop out.
    assert fp("ls -la && rm -rf vault/wiki/x") == fp("rm vault/wiki/x; ls") == "tool:Bash:rm"
    # A wrapper is unwrapped, so the deletion is named rather than hidden behind `xargs`.
    assert fp("find vault -type f | xargs rm") == "tool:Bash:rm+xargs"
    # Conditionally read-only programs are judged on how they were called, not by name.
    assert fp("git push origin master") == "tool:Bash:git"
    assert fp('sed -i "s/a/b/" vault/wiki/portal.md') == "tool:Bash:sed"
    # Only read programs, yet writing: no program name names the effect, so the class does.
    assert fp("echo hi > vault/wiki/note.md") == "tool:Bash:write"
    # No mutating command may collide with the read-only class.
    assert experience.READ_ONLY_COMMAND_CLASS not in fp("rm -rf vault")


def test_volatile_parts_collapse_so_precedent_can_form_fr31():
    """spec 011 FR-31: uuids/timestamps must not make every occurrence a brand-new shape."""
    a = _op(kind="tool", name="Read", target="sessions/2026-08-29T10:00:00-thread", tier="auto")
    b = _op(kind="tool", name="Read", target="sessions/2026-08-30T11:30:00-thread", tier="auto")
    assert experience.operation_fingerprint(a) == experience.operation_fingerprint(b)


def test_objective_fingerprint_is_a_stable_token_signature_fr31():
    """spec 011 FR-31: word order and filler must not change an objective's signature."""
    one = experience.objective_fingerprint("Please import the second brain skill")
    two = experience.objective_fingerprint("import   SECOND brain skill, please")
    assert one == two
    assert one.startswith("obj:")
    assert experience.objective_fingerprint("delete the whole wiki") != one
    assert experience.objective_fingerprint("") == "obj:-"


# --- precedent lookup ------------------------------------------------------------------------


def test_precedent_counts_only_operator_decisions_fr17(experience_paths):
    """spec 011 FR-17: a judge's own approvals MUST NOT become the precedent for the next one.

    This is the anti-bootstrap rule. A store stuffed with `source="judge"` (and `trust`, and
    `precedent`) approvals yields no unlocking precedent at all.
    """
    store, _ = experience_paths
    fp = experience.operation_fingerprint(_op())
    _write(
        store,
        [_record(fp, source="judge", record_id=f"j{i}") for i in range(6)]
        + [_record(fp, source="trust", record_id="t1"), _record(fp, source="precedent", record_id="p1")],
    )

    assert experience.is_empty() is False  # the records exist...
    assert experience.lookup(fp) is None  # ...but none of them is a human decision

    # One genuine operator approval is what creates precedent.
    _write(store, [_record(fp, source="user", record_id="u1")])
    summary = experience.lookup(fp)
    assert summary is not None
    assert summary.approvals == 1
    assert summary.declines == 0
    assert summary.last_decision == "approve"
    assert summary.fingerprint == fp
    assert summary.precedent_id == f"prec:{fp}"


def test_precedent_reflects_a_decline_in_the_window_fr19(experience_paths):
    """spec 011 FR-17/FR-19: an operator decline is visible so it can only ever narrow automation."""
    store, _ = experience_paths
    fp = experience.operation_fingerprint(_op())
    _write(
        store,
        [
            _record(fp, decision="approve", age_days=5, record_id="u1"),
            _record(fp, decision="approve", age_days=4, record_id="u2"),
            _record(fp, decision="decline", age_days=1, record_id="u3"),
        ],
    )

    summary = experience.lookup(fp)
    assert summary.approvals == 2
    assert summary.declines == 1
    assert summary.last_decision == "decline"
    assert summary.samples == 3


def test_records_outside_the_window_are_excluded_fr17(experience_paths, monkeypatch):
    """spec 011 FR-17: precedent counting looks back only as far as the configured window."""
    store, _ = experience_paths
    fp = experience.operation_fingerprint(_op())
    monkeypatch.setenv("LEADER_PRECEDENT_WINDOW_DAYS", "30")
    assert config.precedent_window_days() == 30

    _write(store, [_record(fp, age_days=200, record_id="old")])
    assert experience.lookup(fp) is None

    _write(store, [_record(fp, age_days=2, record_id="new")])
    summary = experience.lookup(fp)
    assert summary.approvals == 1
    assert summary.window_days == 30
    assert summary.contributing == ("new",)


def test_lookup_ignores_other_fingerprints_fr17(experience_paths):
    """spec 011 FR-17, D5: precedent is exact-fingerprint, never fuzzy."""
    store, _ = experience_paths
    _write(store, [_record("capability:import_skill:triage", record_id="u1")])
    assert experience.lookup("capability:import_skill:second-brain-ingest") is None


# --- cold start ------------------------------------------------------------------------------


def test_is_empty_on_missing_file_then_false_after_one_record_fr20(experience_paths):
    """spec 011 FR-20, AC-9: the cold-start check that forces every gated operation to ask."""
    store, _ = experience_paths
    assert not store.exists()
    assert experience.is_empty() is True

    experience.record(run_id="r", operation=_op(), decision="ask", source="judge")
    assert experience.is_empty() is False


# --- suggest-only analysis -------------------------------------------------------------------


def test_analyze_reports_no_records_on_cold_start_fr32(experience_paths):
    """spec 011 FR-32, D7: a cold start says so explicitly rather than guessing."""
    result = experience.analyze()
    assert result["error"] == experience.NO_RECORDS
    assert result["total_records"] == 0
    assert "suggested_gate" not in result


def test_analyze_suggests_and_writes_nothing_fr32(experience_paths, monkeypatch):
    """spec 011 FR-32, AC-18, D7: suggestions are computed; the weights file stays untouched."""
    store, weights = experience_paths
    weights.parent.mkdir(parents=True, exist_ok=True)
    original = json.dumps({"thresholds": {"gate": 4}}, indent=2)
    weights.write_text(original, encoding="utf-8")

    monkeypatch.setenv("LEADER_PRECEDENT_MIN_SAMPLES", "3")
    trusted = experience.operation_fingerprint(_op())
    refused = experience.operation_fingerprint(_op(name="create_workspace", target="prod"))
    _write(
        store,
        [_record(trusted, score=4, age_days=i + 1, record_id=f"u{i}") for i in range(4)]
        + [_record(refused, decision="decline", score=5, record_id="d1")]
        # A judge approval must not lift a shape into the trusted set.
        + [_record("capability:ingest:notes", source="judge", record_id="j1")],
    )

    result = experience.analyze()

    assert result["total_records"] == 6
    assert result["distinct_shapes"] == 3
    assert trusted in result["suggested_trusted_shapes"]
    assert refused in result["suggested_always_ask_shapes"]
    assert "capability:ingest:notes" not in result["suggested_trusted_shapes"]
    # Mirrors the reference pattern's suggested_* naming (D7).
    assert result["suggested_gate"] == 5
    assert result["suggested_precedent_free_ceiling"] == 4
    assert "Suggestions only" in result["note"]

    by_fp = {s["fingerprint"]: s for s in result["shapes"]}
    assert by_fp[trusted]["operator_approvals"] == 4
    assert by_fp[trusted]["approval_rate"] == 1.0
    assert by_fp[refused]["operator_declines"] == 1
    assert by_fp["capability:ingest:notes"]["judge_approvals"] == 1

    # AC-18: the analysis routine never writes the weights file (or creates the store's siblings).
    assert weights.read_text(encoding="utf-8") == original


def test_analyze_disqualifies_a_shape_with_any_decline_fr32(experience_paths, monkeypatch):
    """spec 011 FR-32, D8: the system may learn to stop asking, never to start refusing."""
    store, _ = experience_paths
    monkeypatch.setenv("LEADER_PRECEDENT_MIN_SAMPLES", "2")
    fp = experience.operation_fingerprint(_op())
    _write(
        store,
        [
            _record(fp, record_id="u1"),
            _record(fp, record_id="u2"),
            _record(fp, record_id="u3"),
            _record(fp, decision="decline", record_id="u4"),
        ],
    )
    result = experience.analyze()
    assert fp not in result["suggested_trusted_shapes"]
    assert fp in result["suggested_always_ask_shapes"]


# --- robustness ------------------------------------------------------------------------------


def test_malformed_lines_are_skipped_not_fatal_fr29(experience_paths):
    """spec 011 FR-29: the store is hand-inspectable, so it is hand-corruptible. Skip, don't die."""
    store, _ = experience_paths
    store.parent.mkdir(parents=True, exist_ok=True)
    fp = experience.operation_fingerprint(_op())
    good = json.dumps(_record(fp, record_id="u1"))
    store.write_text(
        "\n".join(
            [
                "{ this is not json",
                good,
                "[1, 2, 3]",  # valid JSON, wrong shape
                "",
                json.dumps(_record(fp, record_id="u2"))[:-8],  # truncated final line
            ]
        ),
        encoding="utf-8",
    )

    records = experience.load()
    assert len(records) == 1
    assert records[0]["record_id"] == "u1"
    assert experience.is_empty() is False
    assert experience.lookup(fp).approvals == 1
    assert experience.analyze()["total_records"] == 1


def test_unparseable_timestamp_is_excluded_from_precedent_fr17(experience_paths):
    """spec 011 FR-17/FR-19: unverifiable window membership justifies neither a skip nor a refusal."""
    store, _ = experience_paths
    fp = experience.operation_fingerprint(_op())
    broken = _record(fp, record_id="u1")
    broken["timestamp"] = "last Tuesday"
    _write(store, [broken])

    assert experience.load()  # the record is still readable for audit
    assert experience.lookup(fp) is None


def test_unknown_fields_are_tolerated_fr29(experience_paths):
    """spec 011 FR-29: an append-only file must stay readable across schema versions."""
    store, _ = experience_paths
    fp = experience.operation_fingerprint(_op())
    future = _record(fp, record_id="u1")
    future["schema"] = 99
    future["some_future_field"] = {"nested": True}
    _write(store, [future])

    assert experience.lookup(fp).approvals == 1


def test_band_is_module_data_derived_from_the_score_fr29():
    """spec 011 FR-29: the band is a coarse label for the 1-5 score, declared as data."""
    assert experience.SCORE_BANDS[1] == "routine"
    assert experience.band(1) == "routine"
    assert experience.band(5) == "critical"
    assert experience.band(9) == "critical"  # clamped, never a KeyError on the write path
    assert experience.band(0) == "routine"
