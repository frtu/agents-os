#!/bin/bash

# link-skills.sh - Symlink agent skills from this folder into an agent's skills directory
#
# Usage:
#   ./link-skills.sh [SKILL_NAME_PATTERN] [HARNESS | TARGET_SKILLS_DIR]
#
# Arguments:
#   SKILL_NAME_PATTERN  - Name of skill(s) to link. Supports wildcards (e.g., "second-brain*")
#                         If not provided, shows usage, harnesses and available skills.
#   HARNESS | TARGET_SKILLS_DIR
#                       - (Optional) Where to link the skills:
#                         * a directory path (contains "/", starts with "~" or ".",
#                           or already exists) → linked there, as before
#                         * a known harness name (claude, opencode, codex, gemini,
#                           cursor, agents) → linked into that harness's skills dir
#                         Defaults to the "claude" harness dir (DEFAULT_HARNESS).
#
# Examples:
#   ./link-skills.sh second-brain
#   ./link-skills.sh "second-brain*" opencode
#   ./link-skills.sh lint-unformat ~/custom/skills
#   ./link-skills.sh "interview*" ./my-skills

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_HARNESS="${LINK_SKILLS_DEFAULT_HARNESS:-claude}"
KNOWN_HARNESSES="claude opencode codex gemini cursor agents"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions

# Print the user-level skills directory of a known harness, or fail.
# Keep in sync with README → "Agent-Specific Setup".
harness_dir() {
    case "$1" in
        claude)   echo "${HOME}/.claude/skills" ;;
        opencode) echo "${XDG_CONFIG_HOME:-${HOME}/.config}/opencode/skills" ;;
        codex)    echo "${CODEX_HOME:-${HOME}/.codex}/skills" ;;
        gemini)   echo "${HOME}/.gemini/skills" ;;
        cursor)   echo "${HOME}/.cursor/skills" ;;
        agents)   echo "${HOME}/.agents/skills" ;;
        *)        return 1 ;;
    esac
}

# Resolve the 2nd argument to a target directory.
# Path-like or existing directory → path; known harness → its dir; else error.
resolve_target() {
    local arg="$1"

    if [ -z "$arg" ]; then
        harness_dir "$DEFAULT_HARNESS"
        return
    fi

    case "$arg" in
        */* | "~"* | .*)
            echo "${arg/#\~/$HOME}"
            return
            ;;
    esac

    if [ -d "$arg" ]; then
        echo "$arg"
        return
    fi

    if harness_dir "$arg"; then
        return
    fi

    echo -e "${RED}✗ Unknown harness or directory: $arg${NC}" >&2
    echo "  Known harnesses: $KNOWN_HARNESSES" >&2
    echo "  To use a new directory with that name, pass it as a path: ./$arg" >&2
    return 1
}

list_harnesses() {
    echo ""
    for h in $KNOWN_HARNESSES; do
        local marker=""
        [ "$h" = "$DEFAULT_HARNESS" ] && marker=" (default)"
        printf "  • %-9s → %s%s\n" "$h" "$(harness_dir "$h")" "$marker"
    done
    echo ""
}

usage() {
    cat << EOF
$(echo -e "${BLUE}Agent Skills Linker${NC}")

Link skills from this folder into an agent's skills directory.

$(echo -e "${YELLOW}Usage:${NC}")
  ./link-skills.sh [SKILL_NAME_PATTERN] [HARNESS | TARGET_SKILLS_DIR]

$(echo -e "${YELLOW}Arguments:${NC}")
  SKILL_NAME_PATTERN  - Name of skill(s) to link. Supports wildcards (e.g., "second-brain*")
                        If not provided, shows available skills.
  HARNESS | TARGET_SKILLS_DIR
                      - (Optional) A known harness name (see below) or a directory path.
                        A path contains "/", starts with "~" or ".", or already exists.
                        Defaults to the "${DEFAULT_HARNESS}" harness
                        (override with LINK_SKILLS_DEFAULT_HARNESS).

$(echo -e "${YELLOW}Examples:${NC}")
  ./link-skills.sh second-brain
  ./link-skills.sh "second-brain*" opencode
  ./link-skills.sh lint-unformat ~/custom/skills
  ./link-skills.sh "interview*" ./my-skills

$(echo -e "${YELLOW}Known Harnesses:${NC}")
EOF
    list_harnesses
    echo -e "${YELLOW}Available Skills:${NC}"
    list_skills
}

list_skills() {
    echo ""
    for skill_dir in "$SCRIPT_DIR"/*/; do
        if [ -f "$skill_dir/SKILL.md" ]; then
            skill_name=$(basename "$skill_dir")
            echo "  • $skill_name"
        fi
    done
    echo ""
}

validate_skill_dir() {
    local skill_path="$1"

    if [ ! -d "$skill_path" ]; then
        echo -e "${RED}✗ Error: Skill directory not found: $skill_path${NC}" >&2
        return 1
    fi

    if [ ! -f "$skill_path/SKILL.md" ]; then
        echo -e "${RED}✗ Error: Missing SKILL.md in $skill_path${NC}" >&2
        return 1
    fi

    return 0
}

create_symlink() {
    local skill_dir="$1"
    local target_dir="$2"
    local skill_name=$(basename "$skill_dir")
    local target_link="$target_dir/$skill_name"

    # Ensure target directory exists
    if [ ! -d "$target_dir" ]; then
        echo -e "${YELLOW}→ Creating target directory: $target_dir${NC}"
        mkdir -p "$target_dir"
    fi

    # Remove existing symlink or file if it exists
    if [ -e "$target_link" ] || [ -L "$target_link" ]; then
        # Check if it's already a symlink pointing to the correct location
        if [ -L "$target_link" ] && [ "$(readlink "$target_link")" = "$skill_dir" ]; then
            echo -e "${GREEN}✓ Already linked: $skill_name${NC}"
            return 0
        fi

        # If it exists and is different, ask for confirmation
        echo -e "${YELLOW}⚠ Skill already exists at: $target_link${NC}"
        echo "  Current target: $(readlink -f "$target_link" 2>/dev/null || echo 'not a symlink')"
        echo "  New target: $skill_dir"

        read -p "  Replace? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}✗ Skipped: $skill_name${NC}"
            return 1
        fi

        rm -f "$target_link"
    fi

    # Create the symlink
    ln -s "$skill_dir" "$target_link"
    echo -e "${GREEN}✓ Linked: $skill_name${NC}"
    return 0
}

# Main script

# Check if no arguments provided
if [ $# -eq 0 ]; then
    usage
    exit 0
fi

# Parse arguments
SKILL_PATTERN="$1"
TARGET_DIR="$(resolve_target "${2:-}")" || exit 1

# Expand the pattern to find matching skills
matching_skills=()
for skill_dir in "$SCRIPT_DIR"/*/; do
    skill_name=$(basename "$skill_dir")

    # Check if this skill matches the pattern (simple glob matching)
    if [[ "$skill_name" == $SKILL_PATTERN ]]; then
        if validate_skill_dir "$skill_dir"; then
            matching_skills+=("$skill_dir")
        fi
    fi
done

# Check if any skills matched
if [ ${#matching_skills[@]} -eq 0 ]; then
    echo -e "${RED}✗ No skills found matching: $SKILL_PATTERN${NC}" >&2
    echo ""
    usage
    exit 1
fi

# Process each matching skill
echo -e "${BLUE}Linking ${#matching_skills[@]} skill(s) to: $TARGET_DIR${NC}"
echo ""

success_count=0
failed_count=0

for skill_dir in "${matching_skills[@]}"; do
    if create_symlink "$skill_dir" "$TARGET_DIR"; then
        success_count=$((success_count + 1))
    else
        failed_count=$((failed_count + 1))
    fi
done

# Summary
echo ""
if [ $failed_count -eq 0 ]; then
    echo -e "${GREEN}✓ Success! Linked $success_count skill(s)${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Verify symlinks: ls -la $TARGET_DIR/"
    echo "  2. Restart your agent session to reload skills"
    echo "  3. Invoke a skill (e.g. /skill-name) or point the agent at its SKILL.md"
    exit 0
else
    echo -e "${YELLOW}⚠ Completed with $success_count linked, $failed_count skipped${NC}"
    exit 1
fi
