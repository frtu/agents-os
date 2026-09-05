"""Cross-layer tests for maker-checker approval (spec 011).

The per-layer suites already cover each layer in isolation:
``test_workflow_reporting.py`` (layer 2), ``test_judge.py`` (layer 3),
``test_experience.py`` (the store). What none of them can show is the properties that only exist
*between* layers — that the layers stay unaware of each other (AC-2), that the agent's **native**
tools land on the same gate as its capability tools (AC-3), that REST and chat converge because
they share one entry point (AC-17), and that the raw guard sits in front of all of it (AC-20).
"""

from __future__ import annotations

import ast
import asyncio
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parent.parent / "app"


# --- AC-2: the layers do not import each other (FR-34) -------------------------


def _imported_app_modules(path: Path) -> set[str]:
    """Every sibling `app.*` module a file imports, including function-local imports.

    Local imports matter more than top-level ones here: the layers break their cycles with
    deferred imports, so a scan that only walked module-level `import` statements would report a
    clean boundary that the code does not actually keep.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level:  # `from . import x` / `from .x import y`
                if node.module:
                    found.add(node.module.split(".")[0])
                found.update(a.name for a in node.names)
            elif node.module and node.module.startswith("app."):
                found.add(node.module.split(".")[1])
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("app."):
                    found.add(alias.name.split(".")[1])
    return found


@pytest.mark.parametrize("module", ["capabilities.py", "agent.py", "execution_gate.py"])
def test_ac2_layer_1_does_not_import_layers_2_or_3(module):
    # AC-2 (FR-34): layer 1 announces to a protocol, so it must not know who implements it. If it
    # imported workflow or judge it could reach past the gate — read a score, inspect a verdict —
    # and the "independently evolvable, layer 1 runs correctly alone" property (AC-1) would be a
    # claim rather than a fact.
    imported = _imported_app_modules(APP / module)
    assert "workflow" not in imported, f"{module} imports layer 2"
    assert "judge" not in imported, f"{module} imports layer 3"


def test_ac2_layer_2_does_not_import_layer_3():
    # AC-2 (FR-34): layer 2 scores and reports; whether a verdict comes from an LLM, a stub or
    # nothing at all is the caller's choice, injected as a `Checker`.
    imported = _imported_app_modules(APP / "workflow.py")
    assert "judge" not in imported
    assert "capabilities" not in imported, "layer 2 must not reach back into layer 1 either"


def test_ac2_the_gate_contract_depends_on_no_layer():
    # `execution_gate` is the shared vocabulary all three layers speak. It stays a leaf.
    imported = _imported_app_modules(APP / "execution_gate.py")
    assert imported <= {"config"}, f"the contract module grew dependencies: {imported}"


# --- AC-3: a native tool write is announced, scored and recorded (FR-4/6/7) ----


def _hook_verdict(workspace_path: Path, tool_name: str, tool_input: dict) -> dict:
    """Drive the PreToolUse hook the way the SDK does — the only enforcement point (spec 011 D2)."""
    from app import agent

    hook = agent._pretooluse_hook(workspace_path)
    return asyncio.run(hook({"tool_name": tool_name, "tool_input": tool_input}, "tool-1", None))


def test_ac3_native_write_to_wiki_is_announced_and_scored(isolated_workspace_root):
    # AC-3 (FR-4/FR-6/FR-7): the gate used to be derived from the words in the user's message, so a
    # native `Write` was invisible to it. Now the PreToolUse hook announces it, layer 2 scores it
    # from its declared tier, and it lands on the run's report — which is what makes the report a
    # record of the *whole* execution rather than of the capability calls only.
    from app import capabilities, concierge, execution_gate

    _name, wpath = capabilities.resolve_for_chat(None)
    run = concierge.build_run("write a wiki note", "_default_")
    target = wpath / "vault" / "wiki" / "note.md"

    with execution_gate.use_gate(run):
        verdict = _hook_verdict(wpath, "Write", {"file_path": str(target)})

    assert verdict == {}, "a reversible write inside the workspace should not be denied"
    assert len(run.operations) == 1
    scored = run.operations[0]
    assert scored.operation.kind == "tool"
    assert scored.operation.name == "Write"
    assert scored.operation.target == str(target)
    assert 1 <= scored.score <= 5
    assert scored.status == "executed"
    # Reconstructable after the fact (FR-14): the record carries the modifiers that produced it.
    assert "modifiers" in scored.as_dict()


# --- AC-22: a read is declared as a read, so routine inspection does not gate (FR-39/FR-40) ----


def _declared(command: str):
    """Layer 1's declaration for a shell command, plus layer 2's score for it."""
    from app import agent, workflow

    operation = agent._operation_for_tool(Path("/tmp/ws"), "Bash", {"command": command})
    return operation, workflow.score_operation(operation)


READ_ONLY_INVENTORY = (
    'echo "=== tree ==="; find vault -maxdepth 2 | sort; '
    "find vault/wiki -type f | sort; tail -20 vault/wiki/log.md 2>/dev/null"
)


def test_ac22_read_only_inventory_is_declared_auto_and_scores_one():
    # AC-22 (FR-39/FR-40): this exact shape of command used to score 5 and stall behind a card. One
    # blanket `Bash` declaration put "effects outside the repo are not undone" on every shell call,
    # which fired IRREVERSIBLE_OUTSIDE_GIT unconditionally; BREADTH then read the listed paths as a
    # sweep and SENSITIVE_TARGET read `tail`-ing the ledger as rewriting it.
    from app import config

    operation, scored = _declared(READ_ONLY_INVENTORY)
    assert operation.tier == "auto"
    assert operation.reversibility == "read-only — nothing to undo"
    assert scored.modifiers == ()
    assert scored.score == 1
    assert scored.score < config.gate_threshold()


@pytest.mark.parametrize(
    "command",
    [
        "rm -rf vault/wiki/concepts && find vault -type f | sort",
        "find vault -type f | xargs rm",  # the deletion is behind a wrapper
        'sed -i "s/a/b/" vault/wiki/portal.md',  # read-only program, mutating flag
        'find . -name "*.md" -delete',
        "echo $(rm -rf vault)",  # hidden by command substitution
        "curl -s https://example.com/x | tail -5",
        "git push origin master",  # read-only program, mutating subcommand
    ],
)
def test_ac22_mutating_commands_still_reach_the_gate(command):
    # AC-22 (FR-39): recognition is *positive*, so the downgrade reaches only known-safe reads and
    # every way of smuggling an effect past it keeps the pessimistic declaration.
    from app import config

    operation, scored = _declared(command)
    assert operation.tier == "reversible", command
    assert scored.score >= config.gate_threshold(), command


@pytest.mark.parametrize(
    "command",
    [
        "python3 script.py",  # unknown program
        "bash -c 'find vault'",  # a shell re-parses its argument, so the payload is not the command
        "sudo cat vault/wiki/portal.md",  # reading payload, but the privilege is the risk
    ],
)
def test_fr39_unrecognised_commands_keep_the_pessimistic_declaration(command):
    # FR-39: an unknown program, and the two wrapper kinds excluded from delegation, are never
    # classified read-only however harmless the payload looks.
    operation, _scored = _declared(command)
    assert operation.tier == "reversible", command


@pytest.mark.parametrize(
    "command",
    [
        r"find vault/raw -type f -exec wc -c {} \; | sort -rn",
        "find vault/raw -type f | xargs wc -l",
        "timeout 30 find vault -type f",
    ],
)
def test_ac25_a_read_that_delegates_to_a_reading_program_is_still_a_read(command):
    # AC-25 (FR-39): judging only the leading program mis-declared these — `-exec`/`xargs` were read
    # as mutating outright, so listing file sizes scored 4 and gated. The payload decides.
    operation, scored = _declared(command)
    assert operation.tier == "auto", command
    assert scored.score == 1, command


@pytest.mark.parametrize(
    "command",
    [r"find vault -type f -exec rm {} \;", "find vault -type f | xargs rm"],
)
def test_ac25_a_delegated_mutation_is_not_excused_by_its_wrapper(command):
    # AC-25 (FR-39): the other direction of the same rule — accepting the flag rather than the
    # payload would have let `-exec rm` through as a read.
    from app import config

    operation, scored = _declared(command)
    assert operation.tier == "reversible", command
    assert scored.score >= config.gate_threshold(), command


def test_ac26_a_shell_write_inside_the_workspace_is_priced_like_a_write(tmp_path):
    # AC-26 (FR-42): a shell mutation confined to the workspace must carry the same git-covered undo
    # path as `Write`, not the blanket "effects outside the repo are not undone" that `_escapes_git`
    # matches on text — otherwise the same effect scores 4 (gates) via a redirect and 2 via `Write`.
    # (`mkdir` moved to FR-50 `auto`, so this pins the general redirect-write case instead.)
    from app import agent, config, workflow

    redirect = "cat > vault/wiki/concepts/a.md <<'EOF'\nhi\nEOF"
    shell = agent._operation_for_tool(tmp_path, "Bash", {"command": redirect})
    written = agent._operation_for_tool(tmp_path, "Write", {"file_path": "vault/wiki/concepts/a.md"})

    assert shell.reversibility == written.reversibility
    assert "IRREVERSIBLE_OUTSIDE_GIT" not in workflow.score_operation(shell).modifiers
    assert workflow.score_operation(shell).score < config.gate_threshold()


@pytest.mark.parametrize(
    "command",
    [
        "cp vault/wiki/x /tmp/elsewhere/x",  # one escaping token is enough
        "cat > ~/elsewhere <<'EOF'\nhi\nEOF",  # unresolvable, so treated as outside
        'git commit -m "ingest"',  # names no path, so it earns no downgrade by saying nothing
    ],
)
def test_fr42_a_command_that_may_escape_keeps_the_pessimistic_declaration(command, tmp_path):
    # FR-42: confinement must be *proven* for every token, never inferred from the absence of one.
    # (Uses non-`mkdir` mutations, since `mkdir` is now FR-50 `auto` regardless of path.)
    from app import agent, workflow

    operation = agent._operation_for_tool(tmp_path, "Bash", {"command": command})
    assert "IRREVERSIBLE_OUTSIDE_GIT" in workflow.score_operation(operation).modifiers, command


@pytest.mark.parametrize(
    "command",
    ["rm -rf vault/wiki", 'sed -i "" s/a/b/ vault/wiki/portal.md'],
)
def test_ac26_a_destructive_command_still_gates_inside_the_workspace(command, tmp_path):
    # AC-26 (FR-42/FR-8): the downgrade removes a modifier that was firing on the wrong evidence, not
    # the ones that read the command itself — being inside the workspace excuses nothing destructive.
    from app import agent, config, workflow

    operation = agent._operation_for_tool(tmp_path, "Bash", {"command": command})
    scored = workflow.score_operation(operation)
    assert "DESTRUCTIVE_SHELL" in scored.modifiers, command
    assert scored.score >= config.gate_threshold(), command


@pytest.mark.parametrize(
    "command",
    [
        "cd /Users/x/library/skills/second-brain-ingest && wc -l SKILL.md && sed -n '1,200p' SKILL.md",
        "cd vault/wiki && ls -la && cat portal.md",
    ],
)
def test_ac27_cd_then_reads_is_declared_auto_and_scores_one(command):
    # AC-27 (FR-39): the session that motivated this stalled three times on `cd <path> && <reads>`.
    # `cd` writes nothing, so it belongs on the read-only allowlist; without it the whole && chain
    # kept the pessimistic `reversible` declaration and scored 5 via three false-positive modifiers.
    from app import config

    operation, scored = _declared(command)
    assert operation.tier == "auto", command
    assert operation.reversibility == "read-only — nothing to undo", command
    assert scored.modifiers == (), command
    assert scored.score == 1, command
    assert scored.score < config.gate_threshold(), command


@pytest.mark.parametrize(
    "command",
    [
        "R=vault; find $R -type f | sort",
        "R=/tmp/ws/vault; echo ===; find $R/wiki -type f | sed 's#.*/##' | sort | uniq",
        "A=1 B=2; find vault -name '*.md' | sort",
    ],
)
def test_ac27_assignment_prefixed_reads_are_declared_auto_and_score_one(command):
    # AC-27 (FR-39): a second session stalled on read-only recon written as `R=<path>; find $R …`.
    # The bare `R=<path>` segment named no program and was read as mutating, dragging the whole chain
    # to `reversible` where IRREVERSIBLE_OUTSIDE_GIT + BREADTH scored it 4-5. A pure assignment sets
    # shell state and writes nothing, so it is a read-only no-op.
    from app import config

    operation, scored = _declared(command)
    assert operation.tier == "auto", command
    assert scored.modifiers == (), command
    assert scored.score == 1, command
    assert scored.score < config.gate_threshold(), command


@pytest.mark.parametrize(
    "command",
    ["R=vault; rm -rf $R/wiki", "R=vault; echo hi > $R/x.md"],
)
def test_fr39_an_assignment_prefix_does_not_excuse_a_mutation(command):
    # FR-39: recognition stays positive — the assignment no-op is read-only, but a real mutation
    # behind it keeps the pessimistic declaration and reaches the gate.
    from app import config

    operation, scored = _declared(command)
    assert operation.tier == "reversible", command
    assert scored.score >= config.gate_threshold(), command


def test_ac28_bulk_knowledge_store_write_never_gates_on_count(tmp_path):
    # AC-28 (FR-43 / D11): an ingest writes one page per source by design, so breadth must not gate on
    # page count in vault/wiki/. Seventeen targets or one, the write stays below the gate; the same
    # count outside the store re-arms breadth and reaches it.
    from app import agent, config, workflow

    many = " ".join(f"vault/wiki/sources/docs/p{i}.md" for i in range(17))
    store = agent._operation_for_tool(tmp_path, "Edit", {"file_path": many})
    store_scored = workflow.score_operation(store)
    assert "BREADTH_MANY_TARGETS" not in store_scored.modifiers
    assert store_scored.score < config.gate_threshold()

    outside = agent._operation_for_tool(
        tmp_path, "Edit", {"file_path": "docs/a.md docs/b.md docs/c.md"}
    )
    assert "BREADTH_MANY_TARGETS" in workflow.score_operation(outside).modifiers


def test_ac3_a_write_outside_the_workspace_is_escalated(isolated_workspace_root, tmp_path):
    # AC-3 + FR-8: the same tool, scored differently because the *effect* differs. The workspace git
    # repo is what makes a write reversible, and it does not reach outside its own root, so an
    # outside write is approval-tier and gates where an inside one runs.
    from app import capabilities, concierge, execution_gate

    _name, wpath = capabilities.resolve_for_chat(None)
    run = concierge.build_run("write somewhere else", "_default_")
    outside = tmp_path / "elsewhere.md"

    with execution_gate.use_gate(run):
        inside_verdict = _hook_verdict(
            wpath, "Write", {"file_path": str(wpath / "vault" / "wiki" / "ok.md")}
        )
        outside_verdict = _hook_verdict(wpath, "Write", {"file_path": str(outside)})

    assert inside_verdict == {}
    assert outside_verdict.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"
    assert run.awaiting is True
    scores = {op.operation.target: op.score for op in run.operations}
    assert scores[str(outside)] > scores[str(wpath / "vault" / "wiki" / "ok.md")]


# --- AC-20: vault/raw/ is refused irrespective of score, verdict or trust ------


@pytest.mark.parametrize("trust", [True, False])
def test_ac20_raw_is_refused_under_any_gate_and_any_trust_mode(isolated_workspace_root, trust):
    # AC-20 (P2): the raw guard is checked *before* layer 2 is consulted, so there is no score to
    # fall under a threshold, no verdict to approve it and no trust mode to wave it through. Running
    # this under an allow-everything gate is the point: even a gate that permits all cannot permit
    # this one.
    from app import capabilities, execution_gate

    _name, wpath = capabilities.resolve_for_chat(None)
    raw_target = wpath / "vault" / "raw" / "source.md"

    with execution_gate.use_gate(execution_gate.AllowAllGate()):
        verdict = _hook_verdict(wpath, "Write", {"file_path": str(raw_target)})

    decision = verdict.get("hookSpecificOutput", {}).get("permissionDecision")
    assert decision == "deny", f"trust={trust}: vault/raw/ must stay refused"
    assert not raw_target.exists()


def test_ac20_raw_denial_never_reaches_layer_2(isolated_workspace_root):
    # AC-20: an absolute rule that consulted the risk layers would be negotiable in principle, and
    # would also pollute the run's report with an operation that was never a candidate. Nothing is
    # announced, so nothing is scored.
    from app import capabilities, concierge, execution_gate

    _name, wpath = capabilities.resolve_for_chat(None)
    run = concierge.build_run("overwrite a raw source", "_default_", trust=True)

    with execution_gate.use_gate(run):
        verdict = _hook_verdict(
            wpath, "Write", {"file_path": str(wpath / "vault" / "raw" / "x.md")}
        )

    assert verdict.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"
    assert run.operations == ()
    assert run.state == "running"


# --- FR-25: the approval card prompt stays a concise one-liner -----------------


def test_fr25_summarize_target_collapses_shell_commands():
    # spec 011 FR-25: a multi-line / long shell target must not fill the card prompt. The summary is
    # one scannable line, truncated, so the option buttons stay visible.
    from app import concierge

    assert concierge._summarize_target(None) == "(no target)"
    assert concierge._summarize_target("   \n  \n") == "(no target)"
    assert concierge._summarize_target("git status") == "git status"

    long_line = "echo " + "x" * 200
    summary = concierge._summarize_target(long_line)
    assert len(summary) <= 80
    assert summary.endswith("…")

    heredoc = "cat <<'EOF' > f.md\nline one\nline two\nEOF"
    multi = concierge._summarize_target(heredoc)
    assert "\n" not in multi
    assert multi.startswith("cat <<'EOF'")
    assert multi.endswith("…")  # a trailing marker signals there is more than the first line


def test_fr25_bash_gating_card_prompt_is_concise_full_command_preserved(isolated_workspace_root):
    # spec 011 FR-25: the reported bug — a long Bash command landed in the card's prompt and pushed the
    # options off-screen. The prompt must summarize the target, while the full command stays in the
    # persisted risk assessment for audit.
    from app import capabilities, concierge, conversation, models

    capabilities.create_workspace("fr25")
    run = concierge.build_run("run a big script", "fr25")
    full_command = "cat <<'EOF' > /tmp/out.md\n" + "\n".join(f"row {i}" for i in range(40)) + "\nEOF"
    gating = models.RiskOperation(
        op_id="op-1", kind="tool", name="Bash", target=full_command, tier="approval", score=4
    )
    assessment = models.RiskAssessment(
        run_id=run.run_id, objective=run.objective, gating=gating, accumulated=[gating]
    )

    card = concierge._ask_card("fr25", None, run, assessment, None)
    assert card is not None
    assert "\n" not in card.prompt
    assert len(card.prompt) <= 140
    assert card.prompt.startswith("Approve `Bash`")
    assert "row 39" not in card.prompt  # the body of the heredoc never reaches the prompt

    # The options survive alongside the concise prompt (not displaced by the payload).
    assert [o.id for o in card.options] == ["approve", "approve_all"]

    # The full command is still recoverable from the persisted record (spec 011 FR-25 audit clause).
    _name, wpath = capabilities.resolve_for_chat("fr25")
    conv = conversation.load(wpath, card.conversation_id)
    assert conv is not None
    assert conv.pending_interaction["risk"]["gating"]["target"] == full_command


# --- AC-17: REST and chat reach execution only via the concierge (FR-23) ------


def test_ac17_every_api_route_reaches_capabilities_through_the_concierge():
    """AC-17 (FR-23): parity is structural, not a promise.

    A route that awaited a capability itself would execute with no gate installed — the exact hole
    the concierge closes. So the check is on the *callee* of every ``await`` in a route body: it must
    be a ``concierge.*`` function. Capabilities may still appear as arguments (they are passed in as
    the thunk the concierge runs behind the gate), which is why matching on the callee rather than on
    the text of the expression is what makes this test mean anything.
    """
    tree = ast.parse((APP / "api.py").read_text(encoding="utf-8"), filename="api.py")
    routes, offenders = 0, []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        decorators = ast.unparse(ast.Module(body=list(node.decorator_list), type_ignores=[]))
        if "app.get" not in decorators and "app.post" not in decorators:
            continue
        routes += 1
        for inner in ast.walk(node):
            callee = ""
            if isinstance(inner, ast.Await) and isinstance(inner.value, ast.Call):
                callee = ast.unparse(inner.value.func)
            elif isinstance(inner, ast.AsyncFor) and isinstance(inner.iter, ast.Call):
                callee = ast.unparse(inner.iter.func)
            if callee.startswith("capabilities."):
                offenders.append(f"{node.name} -> {callee}")
    assert routes > 10, f"the route scan found only {routes} routes; the detector is broken"
    assert not offenders, f"routes bypassing the concierge: {offenders}"


def test_ac17_rest_and_chat_reach_the_same_verdict_for_the_same_request(
    client, isolated_workspace_root
):
    # AC-17 (FR-23, P9): the same consequential request, asked two ways. One entry point means one
    # verdict — REST pauses with 409 + the assessment, chat pauses with the 008 card, and neither
    # creates anything. If the surfaces had their own gating these would drift.
    rest = client.post("/api/workspaces", json={"name": "parity-rest"})
    assert rest.status_code == 409
    assessment = rest.json()
    assert assessment["decision"] == "ask"
    assert assessment["gating"]["name"] == "create_workspace"
    assert not (isolated_workspace_root / "parity-rest").exists()

    chat = client.post("/api/chat", json={"message": "create a workspace named parity-chat"}).json()
    assert chat["executed"] is False
    assert chat["interaction"]["kind"] == "approval"
    assert not (isolated_workspace_root / "parity-chat").exists()


def test_ac17_a_rest_pause_is_answerable_on_the_chat_interaction_route(
    client, isolated_workspace_root
):
    # AC-17 + FR-25: identical treatment means a REST pause is answered on the *same* route a chat
    # pause is — the 409 carries the card's address precisely so a machine caller has somewhere to
    # answer, instead of a refusal it can only retry.
    assessment = client.post("/api/workspaces", json={"name": "answerable"}).json()
    assert assessment["interaction_id"] and assessment["conversation_id"]

    answered = client.post("/api/chat/interaction", json={
        "workspace": assessment["workspace"] or None,
        "conversation_id": assessment["conversation_id"],
        "interaction_id": assessment["interaction_id"],
        "choice": "approve",
    })
    assert answered.status_code == 200
    assert answered.json()["executed"] is True
    assert (isolated_workspace_root / "answerable" / "vault" / "wiki").is_dir()


def test_ac17_a_read_runs_identically_on_both_surfaces(
    client, offline_agent, isolated_workspace_root
):
    # AC-17: parity has to hold for the *un*gated case too, or the concierge would be a gate that
    # only happens to sit in front of REST. An `auto`-tier read runs immediately on both surfaces —
    # 200 with no assessment, and a chat turn with no card — because the same effect declaration
    # scores below the threshold whichever door it came through.
    rest = client.get("/api/workspaces")
    assert rest.status_code == 200  # not 409: a listing is never an ask
    assert isinstance(rest.json()["workspaces"], list)

    chat = client.post("/api/chat", json={"message": "which workspaces exist?"}).json()
    assert chat["pending_plan"] is None
    assert chat.get("interaction") is None


# --- FR-26: a pause is answerable even after its card is gone -----------------


def test_fr26_approve_true_executes_the_plan_when_the_card_is_gone(
    client, isolated_workspace_root
):
    """FR-26: the card is the question; the durable plan is the answerable work behind it.

    A card can be resolved, superseded or expire, and none of those should strand work the operator
    already saw and still wants. Dropping the card and resending the turn with ``approve=true`` must
    therefore still execute — through a run pre-granted for *that plan's* operation only, which is
    why this also proves the fallback builds a well-formed announcement (it reads the tier from
    ``EFFECTS``, not from the stored plan).
    """
    from app import capabilities
    from app import conversation as convo

    first = client.post("/api/chat", json={"message": "create a workspace named fr26"}).json()
    cid = first["conversation_id"]
    assert first["executed"] is False
    assert first["pending_plan"] is not None

    _name, wpath = capabilities.resolve_for_chat(None)
    conv = convo.load(wpath, cid)
    assert conv is not None
    convo.clear_pending_interaction(conv)  # the card is gone; the plan is not

    again = client.post(
        "/api/chat", json={"message": "approve", "conversation_id": cid, "approve": True}
    ).json()
    assert again["executed"] is True
    assert (isolated_workspace_root / "fr26" / "vault" / "wiki").is_dir()


def test_ac17_a_pause_in_a_non_default_workspace_reports_where_its_card_lives(
    client, isolated_workspace_root
):
    """AC-17 + FR-25: the 409 must be an *address*, not just two ids.

    Cards live in a specific workspace's sessions, and the workspace a card lives in is not always
    the one the operation targets. A caller that answered `interaction_id` + `conversation_id`
    against the default workspace would silently miss a card raised in another one — the pause would
    look answered and nothing would run. So the assessment names the workspace too.
    """
    from app import capabilities

    capabilities.create_workspace("elsewhere")
    paused = client.post(
        "/api/skills/import", json={"workspace": "elsewhere", "name": "weekly-digest"}
    )
    assert paused.status_code == 409
    assessment = paused.json()
    assert assessment["workspace"] == "elsewhere"

    answered = client.post("/api/chat/interaction", json={
        "workspace": assessment["workspace"],
        "conversation_id": assessment["conversation_id"],
        "interaction_id": assessment["interaction_id"],
        "choice": "approve",
    }).json()
    assert answered["executed"] is True
    assert (isolated_workspace_root / "elsewhere" / "skills" / "weekly-digest").exists()


# --- AC-21 / FR-38: batch "approve all similar" ------------------------------


def test_ac21_approval_card_offers_a_batch_option_and_carries_the_shape_fr38(
    client, isolated_workspace_root
):
    """FR-38: the pause offers "approve all similar" and durably records the shape it would grant.

    The multi-operation semantics — one shape grant admitting N same-shape ops — are unit-tested at
    layer 2 (``test_shape_grant_lets_all_same_shape_ops_through_fr38``). This proves the door: the
    operator is actually *offered* the batch choice, the run's ``awaiting_shape`` is persisted on the
    card record, and answering with it completes the paused work through the seeded shape grant.
    """
    from app import capabilities
    from app import conversation as convo

    capabilities.create_workspace("bulk")
    paused = client.post("/api/skills/import", json={"workspace": "bulk", "name": "weekly-digest"})
    assert paused.status_code == 409  # weekly-digest declares high risk → gates
    assessment = paused.json()

    _name, wpath = capabilities.resolve_for_chat("bulk")
    conv = convo.load(wpath, assessment["conversation_id"])
    record = conv.pending_interaction
    assert [o["id"] for o in record["options"]] == ["approve", "approve_all"]
    assert record["granted_shape"] == "capability:import_skill"

    answered = client.post("/api/chat/interaction", json={
        "workspace": assessment["workspace"],
        "conversation_id": assessment["conversation_id"],
        "interaction_id": assessment["interaction_id"],
        "choice": "approve_all",
    }).json()
    assert answered["executed"] is True
    assert (isolated_workspace_root / "bulk" / "skills" / "weekly-digest").exists()
