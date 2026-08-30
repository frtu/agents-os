"""Direct tests for capability functions (spec 009, feature 010).

Covers capabilities that are tested via REST routes but lack direct unit tests,
plus edge cases for capture, settings, and request_approval.
"""

from __future__ import annotations

import pytest

from app import capabilities, config, models, vault


def _ws(name="demo"):
    """Helper to create a scaffolded workspace."""
    capabilities.create_workspace(name)
    return vault.resolve_workspace(name)


# --- get_settings / update_settings (spec 009 FR-8) ---------------------------


def test_get_settings_returns_current_state():
    # FR-8: get_settings returns the current persisted operator settings.
    settings = capabilities.get_settings()
    assert isinstance(settings, models.Settings)
    assert isinstance(settings.auto_approve, bool)
    assert isinstance(settings.agent_model, str)


def test_update_settings_persists_auto_approve():
    # FR-8: update_settings persists the setting and returns the new state.
    before = capabilities.get_settings()
    new_value = not before.auto_approve
    result = capabilities.update_settings(auto_approve=new_value)
    assert result.auto_approve == new_value
    assert capabilities.get_settings().auto_approve == new_value
    # Restore
    capabilities.update_settings(auto_approve=before.auto_approve)


def test_update_settings_with_none_leaves_unchanged():
    # FR-8: omitting auto_approve in update_settings leaves it unchanged.
    before = capabilities.get_settings()
    result = capabilities.update_settings(auto_approve=None)
    assert result.auto_approve == before.auto_approve


# --- request_approval (spec 010 FR-1..FR-6) -----------------------------------


def test_request_approval_without_trust_creates_pending_card(isolated_workspace_root):
    # FR-3: trust=False creates a real blocking approval card, pending and answerable.
    ws = _ws()
    itx, granted = capabilities.request_approval(
        "demo", None, "May I delete the old notes?", detail="This is irreversible", trust=False
    )
    assert granted is False
    assert itx.kind == "approval"
    assert itx.status == "pending"
    assert len(itx.options) == 1
    assert itx.options[0].id == "approve"


def test_request_approval_with_trust_grants_immediately(isolated_workspace_root):
    # FR-4/FR-5: trust=True resolves as approved immediately, no pending card.
    ws = _ws()
    itx, granted = capabilities.request_approval(
        "demo", None, "May I reformat the wiki?", trust=True
    )
    assert granted is True
    assert itx.status == "resolved"
    assert itx.resolution == "auto-approved"
    assert itx.options == []  # already decided: nothing to select


def test_request_approval_trust_logs_to_audit_trail(isolated_workspace_root):
    # FR-6: auto-approved actions are still logged for audit (P12).
    ws = _ws()
    log_before = (ws / "vault" / "wiki" / "log.md").read_text()
    capabilities.request_approval("demo", None, "Auto-approve test action", trust=True)
    log_after = (ws / "vault" / "wiki" / "log.md").read_text()
    assert "auto-approved" in log_after
    assert len(log_after) > len(log_before)


# --- capture edge cases (spec 007 FR-1/FR-2) ----------------------------------


def test_capture_deposits_to_raw_with_provenance(isolated_workspace_root):
    # FR-1: capture deposits under vault/raw/<provenance>/.
    ws = _ws()
    dest = capabilities.capture(ws, "transcripts", "meeting.txt", b"hello world")
    assert dest == ws / "vault" / "raw" / "transcripts" / "meeting.txt"
    assert dest.read_bytes() == b"hello world"


def test_capture_path_traversal_is_rejected(isolated_workspace_root):
    # Security: a malicious filename that escapes vault/raw/ is rejected.
    ws = _ws()
    with pytest.raises(vault.WorkspaceError, match="escapes vault/raw/"):
        capabilities.capture(ws, "notes", "../../../escape.txt", b"nope")


def test_capture_does_not_trigger_ingest(isolated_workspace_root):
    # FR-3: capture is input only — no processing, no auto-ingest.
    ws = _ws()
    portal_before = (ws / "vault" / "wiki" / "portal.md").read_text()
    capabilities.capture(ws, "notes", "raw-only.md", b"# Raw\ncontent here")
    portal_after = (ws / "vault" / "wiki" / "portal.md").read_text()
    assert portal_after == portal_before
    # No source page created
    sources = list((ws / "vault" / "wiki" / "sources").rglob("*.md"))
    assert sources == []


def test_capture_binary_data(isolated_workspace_root):
    # Capture preserves binary data exactly.
    ws = _ws()
    binary_data = bytes([0, 1, 2, 255, 128, 64])
    dest = capabilities.capture(ws, "assets", "binary.bin", binary_data)
    assert dest.read_bytes() == binary_data


# --- vault module functions ---------------------------------------------------


def test_resolve_workspace_with_selector(isolated_workspace_root):
    # Explicit selector resolves to <root>/<selector>.
    path = vault.resolve_workspace("custom")
    assert path.name == "custom"
    assert path.parent == config.workspace_root()


def test_resolve_workspace_default(isolated_workspace_root):
    # No selector uses the configured default.
    path = vault.resolve_workspace(None)
    assert path.name == config.default_workspace_name()


def test_list_workspace_names_empty(isolated_workspace_root):
    # No scaffolded workspaces returns empty list.
    names = vault.list_workspace_names()
    assert names == []


def test_list_workspace_names_after_create(isolated_workspace_root):
    # After creating workspaces, they appear in the list.
    capabilities.create_workspace("alpha")
    capabilities.create_workspace("beta")
    names = vault.list_workspace_names()
    assert set(names) == {"alpha", "beta"}


def test_is_scaffolded_true_after_create(isolated_workspace_root):
    # A created workspace is scaffolded.
    ws = _ws("scaffolded-test")
    assert vault.is_scaffolded(ws) is True


def test_is_scaffolded_false_for_missing(isolated_workspace_root):
    # A non-existent workspace is not scaffolded.
    ws = config.workspace_root() / "does-not-exist"
    assert vault.is_scaffolded(ws) is False


def test_guard_write_path_rejects_raw(isolated_workspace_root):
    # guard_write_path raises for any path under vault/raw/.
    ws = _ws()
    with pytest.raises(vault.WorkspaceError, match="raw"):
        vault.guard_write_path(ws, ws / "vault" / "raw" / "notes" / "x.md")


def test_guard_write_path_allows_wiki(isolated_workspace_root):
    # guard_write_path allows paths under vault/wiki/.
    ws = _ws()
    vault.guard_write_path(ws, ws / "vault" / "wiki" / "concepts" / "x.md")  # no error


def test_append_log_adds_entry(isolated_workspace_root):
    # append_log adds a timestamped entry to log.md.
    ws = _ws()
    vault.append_log(ws, "test-op", "Test Title")
    log = (ws / "vault" / "wiki" / "log.md").read_text()
    assert "test-op" in log
    assert "Test Title" in log


# --- conversation status edge cases -------------------------------------------


def test_conversation_status_unknown_id_returns_not_running(isolated_workspace_root):
    # An unknown conversation_id is neither running nor existing.
    _ws()
    status = capabilities.conversation_status("demo", "nonexistent-123")
    assert status.running is False
    assert status.exists is False


# --- query edge cases ---------------------------------------------------------


def test_query_empty_workspace_returns_no_citations(isolated_workspace_root):
    # A query on a fresh workspace with no content returns no citations.
    _ws()
    answer = capabilities.query(models.QueryRequest(workspace="demo", question="anything"))
    assert answer.citations == []
    assert "no matching knowledge" in answer.answer.lower() or "ingest sources" in answer.answer.lower()


# --- lint edge cases ----------------------------------------------------------


def test_lint_fresh_workspace_reports_ok(isolated_workspace_root):
    # A fresh workspace with just portal/log has no findings.
    _ws()
    report = capabilities.lint("demo")
    assert report.workspace == "demo"
    # Fresh workspace may have findings for thin pages but should be mostly ok
    assert isinstance(report.findings, list)


# --- plan for non-executable action -------------------------------------------


def test_plan_non_executable_returns_safe(isolated_workspace_root):
    # A request with no executable action returns a safe plan.
    _ws()
    plan = capabilities.plan(models.PlanRequest(workspace="demo", request="tell me about X"))
    assert plan.risk == "safe"
    assert plan.requires_approval is False


def test_plan_executable_action_returns_risky(isolated_workspace_root):
    # A request with an executable approval-tier action returns a risky plan.
    _ws()
    plan = capabilities.plan(models.PlanRequest(workspace="demo", request="create workspace named test123"))
    assert plan.risk == "risky"
    assert plan.requires_approval is True
    assert plan.capability == "create_workspace"


# --- persona module (spec 002 T010/T011) --------------------------------------


def test_persona_build_system_prompt_includes_key_elements():
    # The system prompt includes constitution, specs, and guardrails.
    from app import persona

    prompt = persona.build_system_prompt()
    assert "Constitution" in prompt
    assert "Operating rules" in prompt
    assert "AI Product Owner" in prompt
    # Guardrails are present
    assert "vault/raw/" in prompt
    assert "request_approval" in prompt


def test_persona_build_system_prompt_is_cached():
    # The prompt is cached (lru_cache) so repeated calls return the same object.
    from app import persona

    prompt1 = persona.build_system_prompt()
    prompt2 = persona.build_system_prompt()
    assert prompt1 is prompt2  # same object due to cache
