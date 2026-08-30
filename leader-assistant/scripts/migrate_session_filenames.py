#!/usr/bin/env python
"""One-off migration of session filenames to the spec 012 FR-1 form.

Renames `<workspace>/sessions/<conversation-id>.md` to
`<workspace>/sessions/YYYY-MM-DD-<conversation-id>-<slug>.md` and rewrites the header from
`templates/template-conversation.md`, leaving the turn blocks **byte-for-byte** unchanged.

A script rather than a capability (spec 012 FR-11): it operates on git-ignored `Workspaces/`, is run
once by a human, and has no business joining the app's runtime surface or the agent's tool set.
Idempotent — a file already in the FR-1 form is skipped, so re-running is a no-op.

    uv run python scripts/migrate_session_filenames.py            # dry run: print old -> new
    uv run python scripts/migrate_session_filenames.py --apply    # rename and commit
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import conversation  # noqa: E402

# Already migrated: `YYYY-MM-DD-<12 hex>-…`. Matching on the shape (not on a manifest) is what makes
# a second run a no-op.
MIGRATED = re.compile(r"^\d{4}-\d{2}-\d{2}-[0-9a-f]{12}-")

_COMMIT_MESSAGE = "migrate: session filenames to YYYY-MM-DD-<id>-<slug> (spec 012 FR-11)"


def _split_frontmatter(text: str) -> str:
    """Everything after the frontmatter block, verbatim — the bytes that must not change."""
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    return text if end == -1 else text[end + 4:]


def _prepare(workspace: Path, path: Path) -> conversation.Conversation | None:
    """Load a record and fill in the fields the new filename needs, or `None` if it is not one.

    Both the plan and the apply go through here, so a dry run cannot name a file differently from
    the rename that follows it.
    """
    conv = conversation.load_path(workspace, path)
    if conv is None:  # a stray note, not a conversation (FR-9)
        return None
    if not conv.name:
        # The record's own name if it has one, else its first turn — `user` for a conversation the
        # human opened, any role for one an agent card opened.
        first = next((t.text for t in conv.turns if t.role == "user"), "")
        conv.name = conversation.fallback_name(first or (conv.turns[0].text if conv.turns else ""))
    return conv


def _target_for(conv: conversation.Conversation, sessions: Path) -> Path:
    slug = conversation.slugify(conv.name)
    return sessions / f"{conv.created}-{conv.conversation_id}-{slug}.md"


def plan_migration(workspace: Path) -> list[tuple[Path, Path]]:
    """The (old, new) pairs this workspace needs — pure, so `--apply` reveals no surprises."""
    sessions = workspace / "sessions"
    if not sessions.is_dir():
        return []
    pairs: list[tuple[Path, Path]] = []
    for path in sorted(sessions.glob("*.md")):
        if MIGRATED.match(path.stem):
            continue
        conv = _prepare(workspace, path)
        if conv is None:
            continue
        target = _target_for(conv, sessions)
        if target != path:
            pairs.append((path, target))
    return pairs


def migrate_workspace(workspace: Path, *, dry_run: bool = True) -> list[tuple[Path, Path]]:
    """Rewrite each record's header and rename it; commit once in the workspace's own repo."""
    pairs = plan_migration(workspace)
    if dry_run or not pairs:
        return pairs
    for old, new in pairs:
        conv = _prepare(workspace, old)
        body = _split_frontmatter(old.read_text(encoding="utf-8")).lstrip("\n")
        header = conversation._render_header(conv).rstrip("\n")
        new.write_text(header + "\n\n" + body, encoding="utf-8")
        old.unlink()

    from app import capabilities

    capabilities._git_commit(workspace, _COMMIT_MESSAGE)
    return pairs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="Workspaces", help="directory holding <workspace>/ dirs")
    parser.add_argument("--apply", action="store_true", help="perform the renames (default: dry run)")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"no such workspace root: {root}")
        return 1

    total = 0
    for workspace in sorted(p for p in root.iterdir() if p.is_dir()):
        pairs = migrate_workspace(workspace, dry_run=not args.apply)
        for old, new in pairs:
            print(f"{'renamed' if args.apply else 'would rename'} {old.name} -> {new.name}")
        total += len(pairs)
    print(f"{total} file(s) {'migrated' if args.apply else 'to migrate'} under {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
