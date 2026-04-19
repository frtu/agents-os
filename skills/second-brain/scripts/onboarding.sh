#!/bin/bash
set -e

# Second Brain — Onboarding Script
# Scaffolds vault directory structure and verifies CLI tooling.
#
# Usage: bash onboarding.sh <vault-path>
# Output: JSON summary to stdout. Progress messages to stderr.

VAULT_ROOT="${1:-.}"

echo "=== Second Brain Onboarding ===" >&2

# 1. Create directory structure
echo "Creating directory structure..." >&2

# raw/ — immutable source documents
mkdir -p "$VAULT_ROOT/raw/assets"      # Images and attachments from clipped articles
mkdir -p "$VAULT_ROOT/raw/clippings"   # Web articles captured with Obsidian Web Clipper
mkdir -p "$VAULT_ROOT/raw/docs"        # PDFs, papers, received files, reference documents
mkdir -p "$VAULT_ROOT/raw/notes"       # Handwritten notes, briefs, random ideas

# wiki/ — the LLM's workspace
mkdir -p "$VAULT_ROOT/wiki/product/persona"        # Categories of users with similar background & skills
mkdir -p "$VAULT_ROOT/wiki/product/entities"       # Product entities, models or logical concepts (e.g., users, accounts)
mkdir -p "$VAULT_ROOT/wiki/product/features"       # Product-level capabilities or value propositions
mkdir -p "$VAULT_ROOT/wiki/people/competencies"    # Hard or soft skills needed to achieve a step of a process
mkdir -p "$VAULT_ROOT/wiki/people/members"         # Individual persons from a squad/team
mkdir -p "$VAULT_ROOT/wiki/people/processes"       # Step of actions to achieve an outcome
mkdir -p "$VAULT_ROOT/wiki/people/steps"           # Particular step of a process (a particular action)
mkdir -p "$VAULT_ROOT/wiki/concepts/patterns"      # Development patterns (idempotency, reliability, security, ...)
mkdir -p "$VAULT_ROOT/wiki/concepts/technologies"  # Reusable technology (protocol, infra, etc.)
mkdir -p "$VAULT_ROOT/wiki/resources/artifacts"    # Things produced by the system (code, binaries)
mkdir -p "$VAULT_ROOT/wiki/resources/components"   # internal system components that deliver value to users, including UI components and legacy/deprecated systems
mkdir -p "$VAULT_ROOT/wiki/resources/dependencies" # Dependencies our application depends on
mkdir -p "$VAULT_ROOT/wiki/resources/tools"        # Systems human/AI can reuse out of the box
mkdir -p "$VAULT_ROOT/wiki/sources"
mkdir -p "$VAULT_ROOT/wiki/synthesis"
mkdir -p "$VAULT_ROOT/wiki/projects"           # Time-bounded development work

# output/ — reports, query results, generated artifacts
mkdir -p "$VAULT_ROOT/output"

# Create README files for each directory
cat > "$VAULT_ROOT/raw/assets/README.md" << 'EOF'
All images, audio or any resources that doesn't processing but can be used inside Markdown document using syntax `![[resource/path]]`.
EOF

cat > "$VAULT_ROOT/raw/clippings/README.md" << 'EOF'
Web articles captured with Obsidian Web Clipper or copied manually.

Example: a blog post, a saved Twitter thread, a documentation page.
EOF

cat > "$VAULT_ROOT/raw/docs/README.md" << 'EOF'
PDFs, papers, received files, reference documents.

Example: a white paper, a technical specification, a report.
EOF

cat > "$VAULT_ROOT/raw/notes/README.md" << 'EOF'
Handwritten notes, briefs, random ideas.

Example: a reflection on a project, a brief for a task, meeting notes.
EOF

cat > "$VAULT_ROOT/output/README.md" << 'EOF'
All reports, query results, and generated artifacts go here.
EOF

cat > "$VAULT_ROOT/wiki/product/README.md" << 'EOF'
All the content related to a product or part of the product this workspace is developing. Anything NOT developed by the team should be stored in `./resources/tools`

Always search the most specific subfolders to write into, or fallback to parent folder when not found.
EOF

cat > "$VAULT_ROOT/wiki/product/persona/README.md" << 'EOF'
All the content related to a category of users with similar background & skills.

Example :
- product-manager
- engineering-lead
- developer
EOF

cat > "$VAULT_ROOT/wiki/product/entities/README.md" << 'EOF'
All the content related to a product entities / resources, model or logical concepts.

Example :
- user
- account
EOF

cat > "$VAULT_ROOT/wiki/product/features/README.md" << 'EOF'
All the content related to a capability to interact with a certain [[resources]]

Example : in case of search
- create [[user]]
- delete [[account]]
* routing
* validation
EOF

cat > "$VAULT_ROOT/wiki/people/processes/README.md" << 'EOF'
All the content related to a process (step of actions to achieve an outcome).

Example: software engineering, regulatory audit, ...
EOF

cat > "$VAULT_ROOT/wiki/people/steps/README.md" << 'EOF'
All the content related to a particular step of a process (a particular action to a particular system).

Example: development, unit testing, deployment (generic), release management (toward prod), ..
EOF

cat > "$VAULT_ROOT/wiki/people/competencies/README.md" << 'EOF'
All the content related to a particular competency, hard or soft skill needed to achieve a step of a process.

Example: system design, leadership, ...
EOF

cat > "$VAULT_ROOT/wiki/people/members/README.md" << 'EOF'
All the content related to a particular person (name) from a squad (team)

Example: fred, ...
EOF

cat > "$VAULT_ROOT/wiki/concepts/README.md" << 'EOF'
All the content related to a certain concepts.

Always search the most specific subfolders to write into, or fallback to parent folder when not found.
EOF

cat > "$VAULT_ROOT/wiki/concepts/patterns/README.md" << 'EOF'
All the content related to a development patterns.

Example: idempotency, dead letter queue, reliability, security, deployment, canary, self healing, ...
EOF

cat > "$VAULT_ROOT/wiki/concepts/technologies/README.md" << 'EOF'
All the content related to a technology that we can reuse (protocol, infra, message queue, ...).

Example: database, kafka, ...
EOF

cat > "$VAULT_ROOT/wiki/resources/README.md" << 'EOF'
All the content related to a resource.

Always search the most specific subfolders to write into, or fallback to parent folder when not found.
EOF

cat > "$VAULT_ROOT/wiki/resources/artifacts/README.md" << 'EOF'
All the content related to something that is produce by the system or more physical concepts.

Example: code source, binary package, pipeline, ...
EOF

cat > "$VAULT_ROOT/wiki/resources/components/README.md" << 'EOF'
All the content related to the currently developed System or part of the System (modules, ..) that deliver value to our users, 
including UI components and legacy/deprecated systems (e.g., service-a, observability)

Example: service-a, observability, ...
EOF

cat > "$VAULT_ROOT/wiki/resources/dependencies/README.md" << 'EOF'
All the content related to dependencies : something our application depends on (PostgreSQL or Redis resources, ...).

Example: PVC, Pod, Checkpoint storage, Service discovery, Schema registry, ...
EOF

cat > "$VAULT_ROOT/wiki/resources/tools/README.md" << 'EOF'
All the content related to a runnable System or part of the System that human or AI can reuse out of the box. Could also be a product developed by another team that comes out-of-the-box.

Example: JIRA, bash commands, Google docs, IM (Instant Messaging), ...
EOF

cat > "$VAULT_ROOT/wiki/sources/README.md" << 'EOF'
One summary page per ingested source
EOF

cat > "$VAULT_ROOT/wiki/synthesis/README.md" << 'EOF'
One comparisons, analyses, cross-cutting themes.
EOF

cat > "$VAULT_ROOT/wiki/projects/README.md" << 'EOF'
All content related to time-bounded development work.

**Structure:**
- `wiki/projects/{initiative-name}/` — Transversal initiatives (e.g., kafka-migration, sso-enforcement)
- `wiki/projects/{product-name}/` — Product or platform (e.g., user service)
- `wiki/projects/{product-name}/{project-name}/` — Specific project to create or extend product capabilities

Always search the most specific subfolders to write into, or fallback to parent folder when not found.
EOF

echo "Created README files for all directories" >&2

# 2. Create wiki/portal.md if it doesn't exist
if [ ! -f "$VAULT_ROOT/wiki/portal.md" ]; then
  cat > "$VAULT_ROOT/wiki/portal.md" << 'EOF'
# Index

Master catalog of all wiki pages. Updated on every ingest.

## Product

### Persona

### Entities

### Features

## People

### Processes

### Steps

### Competencies

### Members

## Concepts

### Patterns

### Technologies

## Resources

### Artifacts

### Components

### Dependencies

### Tools

## Projects

## Sources

## Synthesis
EOF
  echo "Created wiki/portal.md" >&2
else
  echo "wiki/portal.md already exists, skipping" >&2
fi

# 3. Create wiki/log.md if it doesn't exist
if [ ! -f "$VAULT_ROOT/wiki/log.md" ]; then
  cat > "$VAULT_ROOT/wiki/log.md" << 'EOF'
# Log

Chronological record of all operations.

EOF
  echo "Created wiki/log.md" >&2
else
  echo "wiki/log.md already exists, skipping" >&2
fi

# 4. Check tooling
echo "" >&2
echo "Checking tooling..." >&2

TOOLS_JSON="[]"

check_tool() {
  local name="$1"
  local cmd="$2"
  local install_cmd="$3"
  local status="missing"

  if command -v "$cmd" &> /dev/null; then
    status="installed"
    echo "  [ok] $name" >&2
  else
    echo "  [missing] $name — install with: $install_cmd" >&2
  fi

  TOOLS_JSON=$(echo "$TOOLS_JSON" | python3 -c "
import sys, json
tools = json.load(sys.stdin)
tools.append({'name': '$name', 'status': '$status', 'install': '$install_cmd'})
print(json.dumps(tools))
" 2>/dev/null || echo "$TOOLS_JSON")
}

check_tool "summarize" "summarize" "npm i -g @steipete/summarize"
check_tool "qmd" "qmd" "npm i -g @tobilu/qmd"
check_tool "agent-browser" "agent-browser" "npm i -g agent-browser && agent-browser install"

echo "" >&2
echo "Onboarding complete." >&2

# 5. Output JSON result to stdout
VAULT_ABS=$(cd "$VAULT_ROOT" && pwd)
cat << JSONEOF
{
  "status": "complete",
  "vault_root": "$VAULT_ABS",
  "directories": [
    "raw/",
    "raw/assets/",
    "raw/clippings/",
    "raw/docs/",
    "raw/notes/",
    "wiki/",
    "wiki/sources/",
    "wiki/synthesis/",
    "wiki/projects/",
    "wiki/product/",
    "wiki/product/features/",
    "wiki/product/persona/",
    "wiki/product/entities/",
    "wiki/people/",
    "wiki/people/competencies/",
    "wiki/people/members/",
    "wiki/people/processes/",
    "wiki/people/steps/",
    "wiki/concepts/",
    "wiki/concepts/patterns/",
    "wiki/concepts/technologies/",
    "wiki/resources/",
    "wiki/resources/artifacts/",
    "wiki/resources/components/",
    "wiki/resources/dependencies/",
    "wiki/resources/tools/",
    "output/"
  ],
  "files": [
    "wiki/portal.md",
    "wiki/log.md"
  ],
  "tools": $TOOLS_JSON
}
JSONEOF
