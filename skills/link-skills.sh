#!/bin/bash

# link-skills.sh - Symlink Claude Code skills from this folder to the user's skills directory
#
# Usage:
#   ./link-skills.sh [SKILL_NAME_PATTERN] [TARGET_SKILLS_DIR]
#
# Arguments:
#   SKILL_NAME_PATTERN  - Name of skill(s) to link. Supports wildcards (e.g., "second-brain*")
#                         If not provided, shows usage and available skills.
#   TARGET_SKILLS_DIR   - (Optional) Target directory for symlinks.
#                         Defaults to ~/.claude/skills
#
# Examples:
#   ./link-skills.sh second-brain
#   ./link-skills.sh "second-brain*"
#   ./link-skills.sh lint-unformat ~/custom/skills
#   ./link-skills.sh "interview*" /tmp/skills

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_TARGET_DIR="${HOME}/.claude/skills"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions

usage() {
    cat << EOF
${BLUE}Claude Code Skills Linker${NC}

Link skills from this folder to your Claude Code skills directory.

${YELLOW}Usage:${NC}
  ./link-skills.sh [SKILL_NAME_PATTERN] [TARGET_SKILLS_DIR]

${YELLOW}Arguments:${NC}
  SKILL_NAME_PATTERN  - Name of skill(s) to link. Supports wildcards (e.g., "second-brain*")
                        If not provided, shows available skills.
  TARGET_SKILLS_DIR   - (Optional) Target directory for symlinks.
                        Defaults to: ${DEFAULT_TARGET_DIR}

${YELLOW}Examples:${NC}
  ./link-skills.sh second-brain
  ./link-skills.sh "second-brain*"
  ./link-skills.sh lint-unformat ~/custom/skills
  ./link-skills.sh "interview*" /tmp/skills

${YELLOW}Available Skills:${NC}
EOF
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
TARGET_DIR="${2:-$DEFAULT_TARGET_DIR}"

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
        ((success_count++))
    else
        ((failed_count++))
    fi
done

# Summary
echo ""
if [ $failed_count -eq 0 ]; then
    echo -e "${GREEN}✓ Success! Linked $success_count skill(s)${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Verify symlinks: ls -la $TARGET_DIR/"
    echo "  2. Restart Claude Code to reload skills"
    echo "  3. Skills will appear in /list or autocomplete"
    exit 0
else
    echo -e "${YELLOW}⚠ Completed with $success_count linked, $failed_count skipped${NC}"
    exit 1
fi
