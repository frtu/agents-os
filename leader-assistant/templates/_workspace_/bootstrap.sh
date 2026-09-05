#!/usr/bin/env bash
# Bootstrap script — links workspace skills into ~/.claude/skills

set -e

# Default configuration
SKILLS_LIB_DIR="../../../skills"
TARGET_DIR="./skills"

usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Options:
    -s, --skills-lib DIR   Skills library directory (default: ../../../skills)
    -t, --target DIR       Target skills directory (default: ./skills)
    --help                 Show this help message

Environment variables:
    CLAUDE_SKILLS_DIR   Target directory for skill symlinks

Examples:
    $0                                              # Use default paths
    $0 -s /path/to/skills                           # Use custom skills library
    $0 -s /path/to/skills -t /custom/target         # Custom source and target
EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--skills-lib)
            SKILLS_LIB_DIR="$2"
            shift 2
            ;;
        -t|--target)
            TARGET_DIR="$2"
            shift 2
            ;;
        --help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

if [[ ! -d "$SKILLS_LIB_DIR" ]]; then
    echo "Error: Skill library dir '$SKILLS_LIB_DIR' doesn't exist." >&2
    exit 1
fi

LINK_SKILLS="${SKILLS_LIB_DIR}/link-skills.sh"

cd "$(dirname "$0")"

# Load environment file if it exists
if [[ -f .env ]]; then
    set -a
    source .env
    set +a
fi

if [[ ! -f "$LINK_SKILLS" ]]; then
    echo "Error: link-skills.sh not found at $LINK_SKILLS" >&2
    exit 1
fi

echo "Bootstrapping skills into: $TARGET_DIR"
echo ""

# Link all change management with git
bash "$LINK_SKILLS" "change-management*" "$TARGET_DIR"

# Clean up skills
bash "$LINK_SKILLS" "lint-unformat" "$TARGET_DIR"

# Writing mgmt
bash "$LINK_SKILLS" "rewrite-clarity" "$TARGET_DIR"
bash "$LINK_SKILLS" "rewrite-*" "$TARGET_DIR"

# Second brain
bash "$LINK_SKILLS" "second-brain*" "$TARGET_DIR"
