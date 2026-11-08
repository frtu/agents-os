#!/bin/bash

# test-link-skills.sh - Tests for link-skills.sh target resolution (harness vs path).
# Runs against a throwaway HOME, so real skills directories are never touched.
#
# Usage: ./test-link-skills.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LINKER="$SCRIPT_DIR/link-skills.sh"
SKILL="change-management-1-stage"   # any skill folder with a SKILL.md

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export HOME="$TMP/home"
unset XDG_CONFIG_HOME CODEX_HOME LINK_SKILLS_DEFAULT_HARNESS
mkdir -p "$HOME"

pass=0
fail=0

check() { # description, condition...
    local desc="$1"; shift
    if "$@"; then
        echo "✓ $desc"; pass=$((pass + 1))
    else
        echo "✗ $desc"; fail=$((fail + 1))
    fi
}

link() { "$LINKER" "$@" > "$TMP/out.log" 2>&1; }

is_link() { [ -L "$1/$SKILL" ]; }

# Default → claude harness
link "$SKILL"
check "default links into ~/.claude/skills" is_link "$HOME/.claude/skills"

# Each known harness → its pre-configured dir
link "$SKILL" claude;   check "claude   → ~/.claude/skills"          is_link "$HOME/.claude/skills"
link "$SKILL" opencode; check "opencode → ~/.config/opencode/skills" is_link "$HOME/.config/opencode/skills"
link "$SKILL" codex;    check "codex    → ~/.codex/skills"           is_link "$HOME/.codex/skills"
link "$SKILL" gemini;   check "gemini   → ~/.gemini/skills"          is_link "$HOME/.gemini/skills"
link "$SKILL" cursor;   check "cursor   → ~/.cursor/skills"          is_link "$HOME/.cursor/skills"
link "$SKILL" agents;   check "agents   → ~/.agents/skills"          is_link "$HOME/.agents/skills"

# Env overrides for harness dirs
XDG_CONFIG_HOME="$TMP/xdg" link "$SKILL" opencode
check "opencode honours XDG_CONFIG_HOME" is_link "$TMP/xdg/opencode/skills"
CODEX_HOME="$TMP/codexhome" link "$SKILL" codex
check "codex honours CODEX_HOME" is_link "$TMP/codexhome/skills"

# Default harness override
LINK_SKILLS_DEFAULT_HARNESS=agents link "$SKILL"
check "LINK_SKILLS_DEFAULT_HARNESS changes the default" is_link "$HOME/.agents/skills"

# Paths behave as before
link "$SKILL" "$TMP/abs/skills";  check "absolute path is used as-is" is_link "$TMP/abs/skills"
(cd "$TMP" && "$LINKER" "$SKILL" ./rel > /dev/null 2>&1)
check "relative ./path is used as-is" is_link "$TMP/rel"
mkdir -p "$TMP/claude"
(cd "$TMP" && "$LINKER" "$SKILL" claude > /dev/null 2>&1)
check "existing dir named like a harness wins over the harness" is_link "$TMP/claude"

# Unknown bare word → error, nothing created
(cd "$TMP" && "$LINKER" "$SKILL" claud > "$TMP/out.log" 2>&1); rc=$?
check "unknown harness exits non-zero" [ "$rc" -ne 0 ]
check "unknown harness creates no directory" [ ! -e "$TMP/claud" ]
check "unknown harness lists known harnesses" grep -q "Known harnesses" "$TMP/out.log"

# Re-running is idempotent
link "$SKILL" opencode; rc=$?
check "re-link reports already linked and exits 0" [ "$rc" -eq 0 ]

echo ""
echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ]
