---
name: interview-eval
description: >
  Main interview evaluation workflow. Routes to preparation (pre-interview) or
  post-review (post-interview) sub-skills. Use when the user says "evaluate candidate",
  "interview {name}", "bar raiser for {name}", or works with candidate materials.
allowed-tools: Bash Read Glob Grep AskUserQuestion Skill
---

# Interview Evaluation

Orchestrate candidate evaluation through the interview pipeline by routing to the appropriate sub-skill.

## Input

`{Raw Candidates Folder}`: `raw/People/Candidates`
`{Raw Candidate Materials}`: `{Raw Candidates Folder}/{Candidate Name}/`

Typical files:
- Resume (PDF)
- Interview briefing (Export)
- LinkedIn profile
- Recruiting intake form
- Interview transcript (closed captions or notes)

## Workflow

### 1. Select or Create Candidate

**Step 1a: List existing candidates**

```bash
ls -1 {Raw Candidates Folder}/ 2>/dev/null | grep -v "^\." | grep -v "\.md$"
```

**Step 1b: Ask user to select or create**

Present a question with options:
- **Existing candidates** — list each folder as an option
- **Create new** — user provides a name

Example question format:
> "Select an existing candidate or create a new one:"
> - `Fred Tu`
> - `Korben Dallas`
> - **Create new candidate...**

**Step 1c: If creating new candidate**

If user selects "Create new", ask for the full name:
> "Enter the candidate's full name (e.g., Korben Dallas):"

Create the folder and placeholder file:
```bash
mkdir -p "{Raw Candidate Materials}"
touch "{Raw Candidate Materials}/{Candidate Name}.md"
open "{Raw Candidate Materials}"
```

Then **STOP**, prompt user to add content AND press Enter to run to continue to step 2:

> **Folder created:** `{Raw Candidate Materials}`
> **Placeholder:** `{Candidate Name}.md`
>
> Please add the candidate materials to this folder:
> - Resume (PDF or markdown)
> - Interview briefing (from ATS export)
> - LinkedIn profile
> - Previous feedback (if any)
> - Interview transcript (if post-interview)
>
> **When ready**, press Enter to continue.

Pause the skill after folder creation — the user must populate the folder first & press Enter to resume.

### 2. Detect Interview Phase

**Auto-detect based on folder contents.** Scan the candidate folder for file patterns:

```bash
ls -1 "{Raw Candidate Materials}"
```

**Detection rules:**

| File Pattern | Indicates |
|--------------|-----------|
| `*[Ii]nterview*.md` (not "Interview Briefing") | Post-interview transcript |
| `*closed_caption*.md` | Post-interview transcript |
| `*transcript*.md` | Post-interview transcript |
| `*REVIEW*.md` or `*[Rr]eview*.md` | Post-interview feedback |
| `*[Mm]y [Ff]eedback*.md` | Post-interview feedback |
| `*[Ss]ummary*.md` or `*[Nn]otes*.png` | Interview Q&A notes (AI summary) |
| Only briefing/resume/feedback files | Pre-interview |

**Detection logic:**

```bash
# Check for post-interview indicators
POST_INTERVIEW=$(ls -1 "{Raw Candidate Materials}/" 2>/dev/null | \
  grep -iE "(interview.*\.md|closed_caption|transcript|review|my.*feedback)" | \
  grep -viE "^Interview Briefing" | head -1)

if [ -n "$POST_INTERVIEW" ]; then
  echo "post-interview"
else
  echo "pre-interview"
fi
```

**If detection is ambiguous**, present the detected phase with option to override:
> "Detected: **pre-interview** (no transcript found). Continue with pre-interview, or override?"

### 3. Detect Untracked Files

Check for new files not yet captured in git or referenced in portal.md:

```bash
# Find untracked or modified files in candidate folder
NEW_FILES=$(git -C "$VAULT_ROOT" status --porcelain "{Raw Candidate Materials}/" 2>/dev/null | \
  grep -E "^\?\?|^.M|^A " | awk '{print $2}')

# Check if any candidate files are missing from portal.md
PORTAL_REFS=$(grep -o "candidate-{slug}[^]|]*" "$VAULT_ROOT/wiki/portal.md" 2>/dev/null)
```

**If new/untracked files detected**, ask user which workflow to run:

> "Found new files not yet processed:"
> - `{file1}`
> - `{file2}`
>
> "Which workflow should I run?"
> - **Capture Q&A Notes** — Extract structured Q&A from transcript/summary
> - **Post-Interview Review** — Create full evaluation with scores

### 4. Route to Sub-Skill

Based on the detected/confirmed phase and user choice:

**Pre-Interview:**
> Invoke `/interview-1-preparation {candidate-name}`

**Post-Interview (Capture Q&A):**
> Invoke `/interview-2-capture-interview-q-a {candidate-name}`

**Post-Interview (Full Review):**
> Invoke `/interview-3-post-review {candidate-name}`

When AI summaries or interview notes are detected, offer to generate structured Q&A notes with dual-layer formatting (bullet points + prose) before or instead of a full review.

## Quick Reference

| User Says | Route To |
|-----------|----------|
| "pre-interview {name}" | `/interview-1-preparation` |
| "prepare for interview with {name}" | `/interview-1-preparation` |
| "capture notes for {name}" | `/interview-2-capture-interview-q-a` |
| "format interview notes for {name}" | `/interview-2-capture-interview-q-a` |
| "create interview Q&A for {name}" | `/interview-2-capture-interview-q-a` |
| "evaluate {name} post-interview" | `/interview-3-post-review` |
| "post interview for {name}" | `/interview-3-post-review` |
| "complete evaluation for {name}" | `/interview-3-post-review` |

## Example: New Candidate

**User:** /interview-eval

**Assistant:** Select an existing candidate or create a new one:
- `Fred T`
- `Korben Dallas`
- **Create new candidate...**

**User:** Create new candidate...

**Assistant:** Enter the candidate's full name:

**User:** Korben Dallas

**Assistant:** Created `{Raw Candidates Folder}/Korben Dallas/`
Placeholder: `Korben Dallas.md`
*(Folder opened in Finder)*

Please add the candidate materials to this folder:
- Resume (PDF or markdown)
- Interview briefing (from ATS export)
- LinkedIn profile
- Previous feedback (if any)
- Interview transcript (if post-interview)

**When ready**, press Enter to continue.

## Example: Existing Candidate with Auto-Detection

**User:** /interview-eval

**Assistant:** Select an existing candidate or create a new one:
- `Fred T`
- `Korben Dallas`

**User:** Fred T

**Assistant:** Found `{Raw Candidates Folder}/Fred T/` with:
- `Interview xx - 1-Resume.md`
- `Interview xx - 2-Previous feedback.md`
- `2026-06-05 T Interview.md` ← transcript detected

Detected: **post-interview** (interview transcript found)

Which workflow should I run?
- **Capture Q&A Notes** — Extract structured Q&A from transcript
- **Post-Interview Review** — Create full evaluation with scores

**User:** Post-Interview Review

**Assistant:** Routing to `/interview-3-post-review Fred T`...
