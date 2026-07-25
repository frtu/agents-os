# /specs/artifact-system.md

# Artifact System

Artifacts are first-class domain objects.

Everything valuable produced by AI becomes an Artifact.

---

# Artifact Types

Markdown

Document

Presentation

Spreadsheet

Diagram

Image

Source Code

Research

Architecture

JSON

---

# Versioning

Artifacts are immutable.

Updating creates

Version 2

```
Specification

↓

v1

↓

v2

↓

v3
```

---

# Lineage

Every Artifact records

Producer

Execution

Agent

Timestamp

Parent Artifact

This enables complete provenance.

---

# Review

Artifacts may require review before execution continues.

Review results become Decisions.

---

# Rendering

Frontend selects renderer by Artifact type.

Markdown

↓

Markdown Viewer

Presentation

↓

Slide Viewer

Diagram

↓

Diagram Renderer

Code

↓

Syntax Highlighting

No workflow logic depends on rendering.
