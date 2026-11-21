---
concept: output-template
summary: Every output a skill generates (report, page, brief, file) follows a template file in references/templates/ that owns the format, so a human evolves the output by editing the template while the skill (process, compute, scripts) stays unchanged.
exemplars: [review-engineering-director, retrospective-3-report, interview-1-preparation, second-brain-ingest-advanced]
related: [case-studies, extensible-dictionary, script-layering]
---

# Output template

## Problem

A skill's output format is mixed into its process: headings, section order, tone and table columns are written inline in `SKILL.md` or as strings in a script. The symptoms:

- To add a section, rename a heading or change a table column, someone has to edit `SKILL.md` or code. The format can't evolve without touching the compute, and every format tweak risks breaking the process.
- The person who owns the deliverable (a manager, a reviewer, the user) can't change it themselves: the format is buried in agent instructions or Python.
- Each run interprets the format a little differently, because it is described in prose instead of shown as a skeleton.
- One skill grows `if the doc is a pitch… if it's a cost review…` branches instead of picking one of several formats.
- Real names and numbers from the first example end up in the format and get copied into every output.

## Pattern

Separate **what the output looks like** (format) from **how it is produced** (compute). Each output a skill generates has a template file in `references/templates/{artifact}.md`: the skeleton of the deliverable, plus, per section, the **insight to deliver**, the **style & format**, and the **questions to answer**. `SKILL.md` and scripts only **select** a template and **fill** it; they never restate its sections. Adding an output type adds a template file and a row in `SKILL.md`'s template table. Changing the format edits only the template. Two fill modes share the same rule: the **agent** fills a guided skeleton (judgement), or a **script** fills `{{PLACEHOLDER}}` slots (deterministic).

```text
skill-name/
├── SKILL.md                      # Template table (template → use when) + "read the template before producing"
├── references/
│   ├── templates/
│   │   ├── {artifact}.md         # Agent-filled: fenced skeleton + per-section insight / style / questions
│   │   ├── {artifact}.md         # Script-filled: text with {{PLACEHOLDER}} slots
│   │   └── {artifact}.example.*  # Optional: a filled, synthetic example of a structured output (JSON, YAML)
│   └── cases/                    # Specifics that pair with a template (see case-studies)
└── scripts/
    └── render_{artifact}.py      # Optional: fills a template; its --help lists the placeholders
```

## Use when / Don't use when

| Use when | Don't use when |
| --- | --- |
| The skill produces a document, page, report, brief or file someone reads or keeps | The output is a one-line answer or a status: a short fenced skeleton in `SKILL.md` is enough |
| The format will change over time, or someone other than the skill author owns it | The output is a **machine contract** (JSON keys, frontmatter fields another script reads, exit statuses): keep it in code and document it in `usage.md`, because changing it is a compute change |
| There are several output types for the same process (pitch, cost review, risk assessment) | The variation is in the **situation**, not the format: add a case ([`case-studies.md`](./case-studies.md)) |
| A script renders text a human may want to reword (briefs, notifications, page bodies) | The variation is a word-level lookup: use [`extensible-dictionary.md`](./extensible-dictionary.md) |

## Anatomy

| Part | Rule |
| --- | --- |
| **Template file** `references/templates/{artifact}.md` | One file per output type. Starts with a one-line *use for* and what it pairs with (cases, guides). Holds the skeleton exactly as the output should look (fenced block for agent-filled, raw text for script-filled) |
| **Per-section guidance** (agent-filled) | For each section: the **insight to deliver** (what the reader must learn), **style & format** (length, chart, table, bullets), and **questions to answer**. Placeholders in `[brackets]` say what goes there, not an example value |
| **Placeholders** (script-filled) | `{{UPPER_SNAKE}}` slots. The full list is in the rendering script's `--help` (and docstring). Unknown placeholders are left visible or fail loudly, never silently dropped |
| **Generic only** | No team names, internal systems, URLs or real numbers in a template. Those go in `references/cases/`. Synthetic examples only |
| **Template table in `SKILL.md`** | `template → use when the artifact is…`, plus *"read the matching template before producing or reviewing"*. `SKILL.md` never repeats a template's sections |
| **Self-review** (optional) | A short checklist at the end of the template (e.g. "one-minute self-review") so the agent checks the output against the format, not against memory |
| **Growth rule** | New output type → new template + one table row. A finding that recurs across cases → promote it to a generic rule in the template. Format change → edit the template only |

## Exemplar walkthrough

- **`review-engineering-director`** (several agent-filled formats): `references/templates/` holds `product-definition.md`, `vision-refresh.md`, `exec-cost-review.md`, `risk-assessment.md`, `mid-year-review.md`. `SKILL.md` has a template table ("start from it instead of the default") that pairs each template with its cases. Each template opens with *use for / pairs with*, then a fenced skeleton with `[bracketed]` guidance per section.
- **`retrospective-3-report`** (one format + a mapping): `references/templates/retrospective-report.md` holds structure, per-section insight, style, questions and a one-minute self-review; `SKILL.md` says *read it before producing or reviewing*. `retro-formats.md` maps each input board format onto the template's sections, so new input formats don't change the output format. It is also read by `retrospective-2-questions` (one owner, linked).
- **`interview-1-preparation`** (one template per page it writes): `candidate-page.md`, `question-guide.md`, `source-page.md`, `wiki-updates.md`.
- **`second-brain-ingest-advanced`** (script-filled): `references/templates/brief-atomic.md`, `brief-bubble-up.md`, `brief-deliverable.md` use `{{VAULT}}`, `{{SOURCES}}`, `{{WRITE_SCOPE}}`…; `scripts/render_briefs.py` fills them and lists every placeholder in its docstring. `SKILL.md` says *edit the templates only to change worker behaviour for every run*. `plan.example.json` shows a filled structured output.

What makes them succeed: the person who owns the deliverable can change it by editing one Markdown file, and the next run picks it up without anyone touching the process.

## Adoption checklist

1. List every output the skill generates. For each one, decide: **document** (template) or **machine contract** (code + `usage.md`).
2. For each document output, create `references/templates/{artifact}.md`: *use for / pairs with*, then the skeleton.
3. Agent-filled: add per-section insight, style & format, questions to answer, and an optional self-review. Script-filled: use `{{UPPER_SNAKE}}` placeholders and list them in the rendering script's `--help`.
4. Genericize: move names, systems, numbers and links from the source example into a case file.
5. In `SKILL.md`, replace the inline format with a template table and *"read the matching template before producing"*. Delete the prose that described the sections.
6. In a script, replace hard-coded output strings with a read of the template (path relative to the script, or passed with `--templates`).
7. Verify: change a heading in the template, run the skill once, and check that the output follows it with no other edit.

## Anti-patterns

- **Format in the process**: headings and section order written inline in `SKILL.md`. Every format tweak edits the skill.
- **Format in code**: a script builds the page with f-strings. A human can't reword it without editing Python and its tests.
- **Prose instead of a skeleton**: "write a summary, then the risks, then…". Each run reads it differently; show the skeleton.
- **Example values as placeholders**: `[e.g. "−12% by Q3"]` copied verbatim into outputs. Say what goes there, not a realistic value, or label it clearly as an example.
- **Specifics in the template**: real team names or numbers. They leak into every output; keep them in cases.
- **Branching formats**: one template with `if pitch… if cost review…`. Split into one template per output type.
- **Templating machine contracts**: putting JSON keys or frontmatter fields that a script reads into an editable template. A human edit then breaks the compute.
