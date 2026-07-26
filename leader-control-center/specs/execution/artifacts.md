# Artifact System

Artifacts are first-class business objects. Everything valuable produced by
execution becomes an Artifact.

> Artifacts are immutable. Updating an Artifact always creates a new version.

---

## Artifact Shape

```
Artifact {
  id
  type
  version
  owner
  executionId          # producing execution
  createdBy            # provider / user
  createdAt
  location             # storage reference
  metadata
  parentArtifactId     # lineage (previous version or source)
}
```

---

## Artifact Types

```
Markdown
Document
Specification
Presentation
Spreadsheet
Diagram
Image
PDF
Source Code
Test Report
Research
Architecture
JSON
```

---

## Versioning

Artifacts are immutable; updates create a new version.

```
Specification → v1 → v2 → v3
```

Planning references may pin to a version; the latest version is shown by default
in the UI.

---

## Lineage

Every Artifact records its provenance:

- Producer (Provider or Human)
- Execution
- Capability
- Timestamp
- Parent Artifact

This enables complete provenance and future execution replay.

---

## Review

An Artifact may require review before execution continues. Review is driven by
the **Human Review** execution strategy and resolves through a Decision — see
[human-requests.md](./human-requests.md) and
[execution-strategy.md](./execution-strategy.md). A rejected review produces a
Human Request (or a new version), never an in-place mutation.

---

## Rendering

The frontend selects a renderer by Artifact type; no workflow logic depends on
rendering.

```
Markdown      → Markdown Viewer
Presentation  → Slide Viewer
Diagram       → Diagram Renderer
Source Code   → Syntax Highlighting
PDF           → PDF Viewer
Spreadsheet   → Table Viewer
```

See [../frontend/frontend.md](../frontend/frontend.md).

---

## Invariants

1. Artifacts are immutable once published; updates create new versions.
2. Every Artifact is traceable to the execution and producer that created it.
3. Artifact storage locations are references; large blobs are not stored in the
   event log.
