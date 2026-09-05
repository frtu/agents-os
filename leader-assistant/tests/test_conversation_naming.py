"""Feature 012 — conversation naming & lazy session creation (AC-1..AC-12).

Two properties are under test, and they pull against each other:

* a session record is **named and timestamped** (`YYYY-MM-DD-HH-MM-SS-<id>-<slug>.md`), with the name
  chosen by the assistant during the turn that was already running; and
* the record **does not exist** until the user's first message is durably recorded — so no read,
  probe or listing may create one.

The tension is that the name must be decided *before* the only write that creates the file, which is
why several tests here assert on ordering rather than on content.
"""

from __future__ import annotations

import asyncio
import re
from datetime import date, datetime
from pathlib import Path

import pytest

from app import capabilities, conversation

# AC-1: the shape a record's filename must have once a turn has landed.
FILENAME = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}-[0-9a-f]{12}-[a-z0-9-]+\.md$")

TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "template-conversation.md"


def _sessions(workspace: Path) -> list[Path]:
    return sorted((workspace / "sessions").glob("*.md"))


@pytest.fixture
def pausing_agent(monkeypatch):
    """An agent runtime that raises a blocking approval card before the turn is appended.

    Uses the real `request_approval` handler, so the card is persisted the way it is in production —
    which is what materializes the record early and makes AC-7 a real test rather than a mock.
    """
    from app import agent

    async def fake_run_stream(
        _prompt, _message, selector, _wpath, resume_sid, citations,
        conversation_id=None, interactions=None, trust=False, naming=None,
    ):
        specs = agent._capability_tool_specs(
            selector, citations, conversation_id, interactions, trust, naming
        )
        handler = next(s for s in specs if s.name == "request_approval").handler
        await handler({"prompt": "Rewrite 9 wiki pages", "detail": "reversible"})
        yield "Waiting for your decision.", resume_sid

    monkeypatch.setattr(agent, "run_stream", fake_run_stream)


def _naming_agent(monkeypatch, title: str, tags: str = "pricing, catalog"):
    """An agent runtime that titles the conversation through the real `name_conversation` handler."""
    from app import agent

    async def fake_run_stream(
        _prompt, _message, selector, _wpath, resume_sid, citations,
        conversation_id=None, interactions=None, trust=False, naming=None,
    ):
        specs = agent._capability_tool_specs(
            selector, citations, conversation_id, interactions, trust, naming
        )
        handler = next(s for s in specs if s.name == "name_conversation").handler
        await handler({"title": title, "tags": tags})
        yield "Here is my answer.", resume_sid

    monkeypatch.setattr(agent, "run_stream", fake_run_stream)


# --- FR-1: the filename ------------------------------------------------------


def test_fr1_session_filename_is_timestamp_id_slug(client, offline_agent, isolated_workspace_root):
    # AC-1: one turn leaves exactly one record, timestamped to the second, carrying the id, with a
    # readable slug.
    cid = client.post("/api/chat", json={"message": "How do we price the catalog?"}).json()[
        "conversation_id"
    ]
    files = _sessions(isolated_workspace_root / "_default_")
    assert len(files) == 1
    assert FILENAME.match(files[0].name), files[0].name
    assert cid in files[0].name


def test_fr12_created_timestamp_is_the_filename_prefix(client, offline_agent, isolated_workspace_root):
    # AC-13: `Created` is a full ISO timestamp and is the SINGLE value the prefix derives from, so
    # the name and the record cannot disagree about when the conversation started.
    client.post("/api/chat", json={"message": "when did this start?"})
    path = _sessions(isolated_workspace_root / "_default_")[0]

    created = next(
        line.split(":", 1)[1].strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith("Created:")
    )
    # A full second-precision timestamp, not a bare date: it round-trips through datetime unchanged.
    assert datetime.fromisoformat(created).isoformat(timespec="seconds") == created
    assert path.name.startswith(created.replace("T", "-").replace(":", "-") + "-")


def test_fr1_same_day_conversations_sort_by_start_time(isolated_workspace_root):
    # AC-14: second precision exists so a day's conversations read in the order they happened —
    # the property the date-only name could not give.
    capabilities.create_workspace("demo")
    workspace = isolated_workspace_root / "demo"
    for stamp, name in (("2026-08-30T09:12:04", "Earlier talk"), ("2026-08-30T14:23:05", "Later talk")):
        conv = conversation.Conversation(
            conversation_id=conversation.new_id(), workspace=workspace, created=stamp, name=name
        )
        conversation.append_turn(conv, "q", "a")

    assert [conversation.load_path(workspace, p).name for p in _sessions(workspace)] == [
        "Earlier talk",
        "Later talk",
    ]


# --- FR-2: nothing is created by reading ------------------------------------


def test_fr2_nothing_is_created_before_the_first_message(client, isolated_workspace_root):
    # AC-2: a status probe and a sessions listing against a never-used id leave sessions/ empty.
    capabilities.create_workspace("demo")
    workspace = isolated_workspace_root / "demo"

    probe = client.get(
        "/api/chat/status", params={"conversation_id": "abcdef123456", "workspace": "demo"}
    )
    listed = client.get("/api/sessions", params={"workspace": "demo"})

    assert probe.status_code == 200 and probe.json()["exists"] is False
    assert listed.status_code == 200 and listed.json()["conversations"] == []
    assert _sessions(workspace) == []


def test_fr2_pending_lookup_creates_nothing(isolated_workspace_root):
    # AC-2 / FR-2: resolving "is anything pending?" for an unknown id is a pure read. This is the
    # regression the feature exists for — both lookups used to call load_or_create.
    from app import concierge

    capabilities.create_workspace("demo")
    workspace = isolated_workspace_root / "demo"

    assert concierge._pending_record("demo", "abcdef123456") == ("", {})
    assert concierge._pending_plan_record("demo", "abcdef123456") == {}
    assert _sessions(workspace) == []


def test_fr2_pause_before_first_turn_creates_exactly_one_named_file(
    client, pausing_agent, isolated_workspace_root
):
    # AC-7: a card is durable state, so raising one materializes the record before the turn is
    # appended. Exactly one file, and it is named — not an anonymous `…-conversation.md`.
    capabilities.create_workspace("demo")
    body = client.post(
        "/api/chat", json={"workspace": "demo", "message": "tidy up the whole knowledge base"}
    ).json()
    assert body["interaction"] is not None  # the turn really did pause

    files = _sessions(isolated_workspace_root / "demo")
    assert len(files) == 1
    assert FILENAME.match(files[0].name)
    assert files[0].name.endswith("-tidy-up-the-whole-knowledge-base.md")


# --- FR-3: the header comes from the template -------------------------------


def test_fr3_header_is_rendered_from_the_template(client, offline_agent, isolated_workspace_root):
    # AC-3: every literal frontmatter key in the human-owned template appears in a fresh record,
    # in the template's own capitalization, plus the `# Conversation — ` H1.
    client.post("/api/chat", json={"message": "What did we decide about pricing?"})
    text = _sessions(isolated_workspace_root / "_default_")[0].read_text(encoding="utf-8")

    keys = [
        line.split(":", 1)[0]
        for line in TEMPLATE.read_text(encoding="utf-8").splitlines()
        if ":" in line and not line.startswith("#") and "{{logs}}" not in line
    ]
    unconditional = [k for k in keys if k not in ("Sdk-session-id", "Pending-plan", "Pending-interaction")]
    assert unconditional, "the template should declare at least Category/Id/Created/Tags"
    for key in unconditional:
        assert f"\n{key}:" in text, f"missing template key {key!r}"
    assert "# Conversation — " in text


def test_fr3_unset_placeholder_lines_are_omitted(isolated_workspace_root):
    # AC-3: a placeholder with no value leaves no empty line behind — that single rule is what lets
    # a static template carry the app's conditional fields.
    capabilities.create_workspace("demo")
    workspace = isolated_workspace_root / "demo"
    conv = conversation.load_or_new(workspace, None)
    conversation.set_name(conv, "Pricing review", ["pricing"])
    conversation.append_turn(conv, "hello", "hi")

    text = conv.path.read_text(encoding="utf-8")
    assert "Pending-plan:" not in text
    assert "Pending-interaction:" not in text
    assert "Sdk-session-id:" not in text
    assert "Tags: [pricing]" in text  # an empty *list* is a value, and is kept

    conversation.set_pending_plan(conv, "do the thing", {"risk": "safe"})
    text = conv.path.read_text(encoding="utf-8")
    assert "Pending-plan: {" in text
    assert "Pending-interaction:" not in text  # still unset — one field appearing is not all of them


def test_fr3_h1_heading_does_not_become_a_turn(isolated_workspace_root):
    # AC-3 / FR-7: the name lives in the body, so the turn parser must not mistake it for a turn.
    capabilities.create_workspace("demo")
    workspace = isolated_workspace_root / "demo"
    conv = conversation.load_or_new(workspace, None)
    conversation.set_name(conv, "Pricing review")
    conversation.append_turn(conv, "hello", "hi")

    reloaded = conversation.load(workspace, conv.conversation_id)
    assert [t.role for t in reloaded.turns] == ["user", "assistant"]
    assert reloaded.name == "Pricing review"


# --- FR-13/FR-14: event-message log format + back-compat parsing -----------


def test_fr13_append_writes_new_role_time_block(isolated_workspace_root):
    # spec 012 FR-13: a message is appended via the {{#event-message}} loop, one iteration per
    # message, producing `## <role> - <event-time>` blocks (not the legacy `## [<time>] <role>`).
    capabilities.create_workspace("demo")
    workspace = isolated_workspace_root / "demo"
    conv = conversation.load_or_new(workspace, None)
    conversation.append_message_block(conv, "user", "2026-09-02 14:30", "hello")
    conversation.append_message_block(conv, "assistant", "2026-09-02 14:30", "hi there")

    text = conv.path.read_text(encoding="utf-8")
    assert "## user - 2026-09-02 14:30" in text
    assert "## assistant - 2026-09-02 14:30" in text
    assert "## [" not in text  # never the legacy header


def test_fr13_render_message_block_uses_the_template_loop(isolated_workspace_root):
    # spec 012 FR-13: the minimal mustache renderer substitutes one block from the template's
    # {{#event-message}} section per event-message (role / event-time / message).
    block = conversation.render_message_block("assistant", "2026-09-02 14:30", "  hi  ")
    assert block == "## assistant - 2026-09-02 14:30\nhi"


def test_fr14_parser_reads_new_and_legacy_formats(isolated_workspace_root):
    # spec 012 FR-14: the parser reads the new `## <role> - <time>` AND the legacy
    # `## [<time>] <role>` header — a mixed file (an old thread continued after the format change)
    # round-trips both, so no session is orphaned by the change.
    capabilities.create_workspace("demo")
    workspace = isolated_workspace_root / "demo"
    sessions = workspace / "sessions"
    sessions.mkdir(exist_ok=True)
    (sessions / "mixedformat00.md").write_text(
        "---\nId: mixedformat00\nCreated: 2026-08-01\n---\n\n"
        "## [2026-08-01 09:00] user\nold question\n\n"
        "## [2026-08-01 09:00] assistant\nold answer\n\n"
        "## user - 2026-09-02 14:30\nnew question\n\n"
        "## assistant - 2026-09-02 14:30\nnew answer\n",
        encoding="utf-8",
    )

    conv = conversation.load(workspace, "mixedformat00")
    assert [(t.role, t.text) for t in conv.turns] == [
        ("user", "old question"), ("assistant", "old answer"),
        ("user", "new question"), ("assistant", "new answer"),
    ]


def test_fr14_markdown_heading_in_body_is_not_a_turn(isolated_workspace_root):
    # spec 012 FR-14: the new-header regex is anchored to a `## <role> - <timestamp>` shape, so a
    # `## Something` heading inside a message body is content, not a turn boundary.
    capabilities.create_workspace("demo")
    workspace = isolated_workspace_root / "demo"
    conv = conversation.load_or_new(workspace, None)
    conversation.append_message_block(conv, "assistant", "2026-09-02 14:30", "See:\n## Summary\ndetails")

    reloaded = conversation.load(workspace, conv.conversation_id)
    assert [t.role for t in reloaded.turns] == ["assistant"]
    assert "## Summary" in reloaded.turns[0].text


# --- FR-4: the assistant names the conversation it is answering -------------


def test_fr4_agent_supplied_title_lands_in_the_filename(
    client, monkeypatch, isolated_workspace_root
):
    # AC-4: the title the agent chose during the turn becomes the slug, the H1 and the tags —
    # with no second agent invocation (the fake runtime is called exactly once).
    _naming_agent(monkeypatch, "Search catalog pricing model")
    client.post("/api/chat", json={"message": "how should we price the search catalog?"})

    files = _sessions(isolated_workspace_root / "_default_")
    assert len(files) == 1
    assert files[0].name.endswith("-search-catalog-pricing-model.md")
    text = files[0].read_text(encoding="utf-8")
    assert "# Conversation — Search catalog pricing model" in text
    assert "Tags: [pricing, catalog]" in text


def test_fr4_naming_tool_is_registered_and_only_collects_a_proposal(isolated_workspace_root):
    # AC-4 / FR-4: the tool is turn-local — it appends to the caller's list and touches no
    # workspace, hence the `auto` effect tier (spec 006 FR-5a).
    from app import agent

    naming: list[tuple[str, list[str]]] = []
    specs = agent._capability_tool_specs("demo", [], "cid", None, False, naming)
    handler = next(s for s in specs if s.name == "name_conversation").handler

    result = asyncio.run(handler({"title": "Onboarding interview questions", "tags": "Hiring, ux"}))
    assert naming == [("Onboarding interview questions", ["hiring", "ux"])]
    assert "onboarding-interview-questions" in result["content"][0]["text"]

    # An unusable title is refused rather than recorded, leaving the fallback in place (FR-5).
    asyncio.run(handler({"title": "   ", "tags": ""}))
    assert len(naming) == 1
    assert capabilities.EFFECTS["name_conversation"].tier == "auto"


# --- FR-5: the deterministic fallback ---------------------------------------


def test_fr5_fallback_slug_from_first_message(client, offline_agent, isolated_workspace_root):
    # AC-5: offline, the name is still meaningful — a slug of the first message, not a hex id.
    client.post("/api/chat", json={"message": "How do we price the catalog?"})
    assert _sessions(isolated_workspace_root / "_default_")[0].name.endswith(
        "-how-do-we-price-the-catalog.md"
    )


def test_fr5_unslugifiable_message_falls_back_to_conversation(
    client, offline_agent, isolated_workspace_root
):
    # AC-5: a name that slugifies to nothing still needs a filename.
    client.post("/api/chat", json={"message": "🎉🎉🎉"})
    assert _sessions(isolated_workspace_root / "_default_")[0].name.endswith("-conversation.md")


@pytest.mark.parametrize(
    "text,expected",
    [
        ("", "conversation"),
        ("🎉🎉", "conversation"),
        ("日本語", "conversation"),
        ("...!!!", "conversation"),
        ("Résumé review", "resume-review"),
        ("  Mixed CASE / punctuation!  ", "mixed-case-punctuation"),
        ("../../etc/passwd", "etc-passwd"),  # a slug can never carry a path separator
    ],
)
def test_fr5_slugify_edge_cases(text, expected):
    # AC-5 / FR-5: the fallback is deterministic and total — every input yields a usable slug.
    assert conversation.slugify(text) == expected


def test_fr5_slugify_truncates_at_a_word_boundary():
    # FR-5: a long first message must not produce an unbounded filename, nor a trailing dash.
    slug = conversation.slugify("word " * 60)
    assert len(slug) <= 48
    assert not slug.endswith("-") and not slug.startswith("-")


# --- FR-6: the name is fixed at creation ------------------------------------


def test_fr6_name_is_frozen_and_the_second_turn_reuses_one_file(
    client, monkeypatch, isolated_workspace_root
):
    # AC-6: a second turn appends to the same file and does not rename it, even when the agent
    # proposes a different title.
    _naming_agent(monkeypatch, "First chosen title")
    cid = client.post("/api/chat", json={"message": "first question"}).json()["conversation_id"]
    first = _sessions(isolated_workspace_root / "_default_")
    assert len(first) == 1

    _naming_agent(monkeypatch, "Completely different title")
    client.post("/api/chat", json={"message": "second question", "conversation_id": cid})

    after = _sessions(isolated_workspace_root / "_default_")
    assert after == first  # same single path, not renamed
    text = after[0].read_text(encoding="utf-8")
    assert "# Conversation — First chosen title" in text
    assert "Completely different title" not in text
    # spec 012 FR-13: two turns → two `## user - <time>` message blocks.
    assert text.count("## user - ") == 2


def test_fr6_set_name_is_a_no_op_once_materialized(isolated_workspace_root):
    # FR-6: enforcement is structural — there is no code path that renames a written record.
    capabilities.create_workspace("demo")
    workspace = isolated_workspace_root / "demo"
    conv = conversation.load_or_new(workspace, None)
    conversation.set_name(conv, "Original name")
    conversation.append_turn(conv, "hi", "hello")
    path = conv.path

    conversation.set_name(conv, "Renamed", ["nope"])
    assert conv.name == "Original name"
    assert conv.path == path and path.is_file()
    assert _sessions(workspace) == [path]


# --- FR-7 / FR-8: resolution and parsing ------------------------------------


def test_fr7_load_resolves_by_scanning_sessions(client, offline_agent, isolated_workspace_root):
    # AC-8: the id is no longer the whole filename, so lookup is a scan.
    cid = client.post("/api/chat", json={"message": "resolve me"}).json()["conversation_id"]
    workspace = isolated_workspace_root / "_default_"

    resolved = conversation.path_for(workspace, cid)
    assert resolved == _sessions(workspace)[0]
    conv = conversation.load(workspace, cid)
    assert conv is not None and conv.conversation_id == cid


def test_fr7_legacy_flat_file_still_loads(isolated_workspace_root):
    # AC-8 / D6: a pre-012 `<id>.md` with lowercase keys resumes without migration.
    capabilities.create_workspace("demo")
    workspace = isolated_workspace_root / "demo"
    (workspace / "sessions").mkdir(exist_ok=True)
    (workspace / "sessions" / "aabbccddeeff.md").write_text(
        "---\nconversation-id: aabbccddeeff\ncreated: 2026-08-01\n---\n\n"
        "## [2026-08-01 09:00] user\nold question\n\n"
        "## [2026-08-01 09:00] assistant\nold answer\n",
        encoding="utf-8",
    )

    conv = conversation.load(workspace, "aabbccddeeff")
    assert conv is not None
    assert conv.created == "2026-08-01"
    assert [t.text for t in conv.turns] == ["old question", "old answer"]


def test_fr7_date_only_name_and_created_still_load(isolated_workspace_root):
    # AC-15 / FR-7/FR-12: a record written before the timestamp requirement resolves by id, keeps
    # its bare `Created` date, and still buckets — the id is matched in the name, never counted to.
    from app import ui

    capabilities.create_workspace("demo")
    workspace = isolated_workspace_root / "demo"
    sessions = workspace / "sessions"
    sessions.mkdir(exist_ok=True)
    (sessions / "2026-08-01-aabbccddeeff-pricing-the-catalog.md").write_text(
        "---\nId: aabbccddeeff\nCreated: 2026-08-01\n---\n\n"
        "# Conversation — Pricing the catalog\n\n"
        "## [2026-08-01 09:00] user\nold question\n",
        encoding="utf-8",
    )

    conv = conversation.load(workspace, "aabbccddeeff")
    assert conv is not None and conv.conversation_id == "aabbccddeeff"
    assert conv.created == "2026-08-01"
    assert ui._bucket_for(conv.created, date(2026, 8, 1)) == "Today"


def test_fr7_duplicate_matches_resolve_by_frontmatter_id(isolated_workspace_root):
    # AC-8: two files can glob one id; the `Id:` field breaks the tie and nothing raises — a chat
    # turn must not die on a duplicate.
    capabilities.create_workspace("demo")
    sessions = isolated_workspace_root / "demo" / "sessions"
    sessions.mkdir(exist_ok=True)
    cid = "aabbccddeeff"
    right = sessions / f"2026-08-01-{cid}-real-record.md"
    wrong = sessions / f"2026-08-02-{cid}-imposter.md"
    right.write_text(f"---\nId: {cid}\nCreated: 2026-08-01\n---\n\n# Conversation — Real\n", encoding="utf-8")
    wrong.write_text("---\nId: 000000000000\nCreated: 2026-08-02\n---\n\n# Conversation — Nope\n", encoding="utf-8")

    assert conversation.path_for(isolated_workspace_root / "demo", cid) == right


def test_fr8_frontmatter_parsing_is_case_insensitive(isolated_workspace_root):
    # AC-9: the template's capitalized keys and the legacy lowercase keys parse identically.
    capabilities.create_workspace("demo")
    workspace = isolated_workspace_root / "demo"
    sessions = workspace / "sessions"
    sessions.mkdir(exist_ok=True)
    body = "\n\n# Conversation — Same\n\n## [2026-08-01 09:00] user\nq\n"
    upper = sessions / "2026-08-01-aaaaaaaaaaaa-upper.md"
    lower = sessions / "2026-08-01-bbbbbbbbbbbb-lower.md"
    upper.write_text(f"---\nId: aaaaaaaaaaaa\nCreated: 2026-08-01\nTags: [x, y]\n---{body}", encoding="utf-8")
    lower.write_text(f"---\nid: bbbbbbbbbbbb\ncreated: 2026-08-01\ntags: [x, y]\n---{body}", encoding="utf-8")

    a = conversation.load_path(workspace, upper)
    b = conversation.load_path(workspace, lower)
    assert (a.created, a.tags, a.name) == (b.created, b.tags, b.name)
    assert a.tags == ["x", "y"]


# --- FR-9 / FR-10: the listing ----------------------------------------------


def test_fr9_list_conversations_skips_a_stray_markdown_file(
    client, offline_agent, isolated_workspace_root
):
    # AC-10: listing parses files instead of decoding ids out of filenames, so a stray note is
    # skipped rather than crashing the Sessions panel.
    cid = client.post("/api/chat", json={"message": "a real conversation"}).json()["conversation_id"]
    (isolated_workspace_root / "_default_" / "sessions" / "notes.md").write_text(
        "just a note someone dropped in here\n", encoding="utf-8"
    )

    listed = client.get("/api/sessions")
    assert listed.status_code == 200
    ids = [c["conversation_id"] for c in listed.json()["conversations"]]
    assert ids == [cid]


def test_fr10_sidebar_title_is_the_conversation_name(client, monkeypatch):
    # AC-11: the Sessions panel shows the chosen name, not the raw first message.
    _naming_agent(monkeypatch, "Search catalog pricing model")
    cid = client.post(
        "/api/chat", json={"message": "how should we price the search catalog? asking for the board"}
    ).json()["conversation_id"]

    summary = client.get("/api/sessions").json()["conversations"][0]
    assert summary["conversation_id"] == cid
    assert summary["title"] == "Search catalog pricing model"
    assert client.get(f"/api/sessions/{cid}").json()["title"] == summary["title"]


def test_fr10_title_falls_back_to_the_first_user_line(isolated_workspace_root):
    # AC-11 / FR-10: a pre-migration record has no name, so the first user line stands in.
    capabilities.create_workspace("demo")
    sessions = isolated_workspace_root / "demo" / "sessions"
    sessions.mkdir(exist_ok=True)
    (sessions / "aabbccddeeff.md").write_text(
        "---\nconversation-id: aabbccddeeff\ncreated: 2026-08-01\n---\n\n"
        "## [2026-08-01 09:00] user\nwhat did we decide?\n",
        encoding="utf-8",
    )

    summary = capabilities.list_conversations("demo").conversations[0]
    assert summary.title == "what did we decide?"


def test_fr11_migration_is_idempotent_and_preserves_turns(isolated_workspace_root):
    # AC-12: the one-off script renames the legacy flat files without touching a turn byte, and a
    # second run finds nothing left to do.
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from scripts import migrate_session_filenames as migrate

    capabilities.create_workspace("demo")
    workspace = isolated_workspace_root / "demo"
    sessions = workspace / "sessions"
    sessions.mkdir(exist_ok=True)
    legacy = sessions / "aabbccddeeff.md"
    body = (
        "## [2026-08-01 09:00] user\nhow should we price the search catalog?\n\n"
        "## [2026-08-01 09:00] assistant\nStart from the cost floor.\n"
    )
    legacy.write_text(
        f"---\nconversation-id: aabbccddeeff\ncreated: 2026-08-01\n---\n\n{body}", encoding="utf-8"
    )
    before = conversation.load(workspace, "aabbccddeeff")

    # The time comes from the record's own first turn (09:00), never from the clock at migration
    # time — that is what lets the dry run predict the apply and a re-run find nothing.
    expected = "2026-08-01-09-00-00-aabbccddeeff-how-should-we-price-the-search-catalog.md"
    assert [(o.name, n.name) for o, n in migrate.plan_migration(workspace)] == [
        ("aabbccddeeff.md", expected)
    ]
    assert legacy.exists(), "a dry run must not move anything"

    migrated = migrate.migrate_workspace(workspace, dry_run=False)
    assert len(migrated) == 1
    assert not legacy.exists()
    new = sessions / expected
    assert FILENAME.match(new.name)
    assert body in new.read_text(encoding="utf-8"), "turn blocks must survive byte-for-byte"

    after = conversation.load(workspace, "aabbccddeeff")
    assert [(t.role, t.text) for t in after.turns] == [(t.role, t.text) for t in before.turns]
    assert after.created == "2026-08-01T09:00:00"
    assert after.name == "how should we price the search catalog?"

    assert migrate.plan_migration(workspace) == [], "a second run is a no-op"


def test_fr11_migration_upgrades_a_date_only_name(isolated_workspace_root):
    # AC-12: the earlier date-only name is a migration input too — it keeps its slug and gains the
    # time of its first turn, so the whole sessions/ folder ends up in one shape.
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from scripts import migrate_session_filenames as migrate

    capabilities.create_workspace("demo")
    workspace = isolated_workspace_root / "demo"
    sessions = workspace / "sessions"
    sessions.mkdir(exist_ok=True)
    body = "## [2026-08-02 16:45] user\nwhat next?\n\n## [2026-08-02 16:45] assistant\nShip it.\n"
    (sessions / "2026-08-02-aabbccddeeff-pricing-the-catalog.md").write_text(
        f"---\nId: aabbccddeeff\nCreated: 2026-08-02\n---\n\n"
        f"# Conversation — Pricing the catalog\n\n{body}",
        encoding="utf-8",
    )

    migrated = migrate.migrate_workspace(workspace, dry_run=False)
    assert [n.name for _o, n in migrated] == [
        "2026-08-02-16-45-00-aabbccddeeff-pricing-the-catalog.md"
    ]
    after = conversation.load(workspace, "aabbccddeeff")
    assert after.created == "2026-08-02T16:45:00"
    assert after.name == "Pricing the catalog"
    assert body in after.path.read_text(encoding="utf-8")
    assert migrate.plan_migration(workspace) == [], "a second run is a no-op"
