# Implementation Plan: [FEATURE NAME]

**Feature ID:** `NNN-short-name` · **Spec:** [`spec.md`](spec.md)
**Status:** Draft | In Review | Approved
**Created:** YYYY-MM-DD · **Last Updated:** YYYY-MM-DD

> Describes **how**. Turns the spec into an architecture and technical approach. Do not restate requirements — reference them (FR-1, AC-2). Record open technical choices in a sibling `plan-tbd.md`, not inline as silent decisions.

## Constitution Check

Confirm alignment with each principle in [`memory/constitution.md`](../../memory/constitution.md). Note and justify any deviation.

- [ ] P1 Vault is source of truth
- [ ] P2 `vault/raw/` human-owned (pipeline never mutates)
- [ ] P3 Pipeline direction (vault/raw → sessions → dreaming → vault/wiki/sources → vault/wiki/category; vault/wiki + templates → vault/output)
- [ ] P4 Zettelkasten discipline
- [ ] P5 Concept lifecycle (evidence-based)
- [ ] P6 Traceability (bidirectional)
- [ ] P7 Reuse before create (externalized templates)
- [ ] P8 Human-in-the-loop
- [ ] P9 Interface parity
- [ ] P10 Portability
- [ ] P11 Continuous specification generation
- [ ] P12 Risk-governed mutations
- [ ] P13 Multi-workspace

## Technical Context

- **Language / runtime:** …
- **Key libraries / SDKs:** …
- **Dependencies on other features:** …

## Architecture Overview

How the pieces fit. Diagram or bullet flow. Reference the vault pipeline where relevant.

## Components

For each component: responsibility, inputs/outputs, where it reads/writes in the workspace.

## Data & File Contracts

Concrete on-disk shapes: frontmatter fields, folder paths, naming rules, log entry formats. Reference `wiki-schema.md` rather than duplicating it.

## Interfaces / Contracts

Capability-layer functions, API request/response shapes, chat commands. Endpoint URLs are illustrative, not binding.

## Alternatives Considered

Options weighed. Undecided options go to `plan-tbd.md`.

## Risks & Mitigations

- Risk → mitigation.

## Rollout / Sequencing

Incremental delivery; what an MVP slice looks like.
