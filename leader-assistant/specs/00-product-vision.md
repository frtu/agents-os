---
id: 202608152112-00
title: Product Vision
spec: 00-product-vision
layer: core
status: draft
lifecycle: draft
Category: spec
Tags: [vision, product, knowledge-vault, specification-assistant]
traceability:
  readme: ["§1 Vision", "§3 Primary Product Output", "§30 Long-Term Product Loop"]
  references: ["_references_/0-context/llm-wiki.md", "_references_/10-internal-storage/wiki-architecture.md"]
related:
  - "[[01-principles]]"
  - "[[02-domain-model]]"
  - "[[07-specification-model]]"
  - "[[12-assistant]]"
Created: 2026-08-15
Last Updated: 2026-08-15
---

# Product Vision

> This spec kit specifies **how to build** the AI Product Owner / Project Specification Assistant described in the project README. It is distinct from the *runtime* spec kit that the finished assistant itself maintains under `vault/wiki/product/specs/`.

## 1. Purpose

Build an **AI Product Owner / Project Specification Assistant** whose primary purpose is to continuously transform accumulated knowledge into **high-quality project specifications**. The assistant is itself the application being built.

## 2. Problem Statement

Conventional RAG systems rediscover knowledge from raw documents on every query — nothing accumulates. Teams abandon wikis because maintenance burden grows faster than value. This product instead maintains a **persistent, compounding knowledge artifact** (the Knowledge Vault) and derives specifications from it continuously, with the LLM doing all the bookkeeping.

## 3. Interfaces (must be equivalent)

The assistant is accessible through two equivalent interfaces:

- **Application Chat**
- **API**

Both expose the same underlying capabilities. See [[13-api]] and [[14-chat]] for parity requirements.

## 4. System Boundary

```text
                         ┌─────────────────────┐
                         │  Assistant (this    │
                         │      project)       │
                         └──────────┬──────────┘
                                    │
             ┌──────────────────────┼──────────────────────┐
             ▼                      ▼                      ▼
      Knowledge Vault          Specification          External PM
       (internal)                Generation              System
             │                      │                      │
       learns from               produces              invoked on
       raw sources              project specs          user demand
```

- The **Knowledge Vault** is an internal product capability, continuously built and maintained by the assistant. It is **not** the user's external PM system (Jira, Linear, Azure DevOps) and not a user-facing document-management system. See [[03-workspace]].
- An **external PM system** is accessed only when explicitly requested by the user (e.g. "Create a new story for XXX"). See [[15-integrations]].

## 5. Primary Output

The primary output is **project specifications** — a *collection of linked specification documents*, not one monolithic document. At runtime the assistant maintains these under `vault/wiki/product/specs/`. See [[07-specification-model]] for the model the assistant produces.

The assistant continuously generates and refines specifications from: accumulated knowledge, conversations, source documents, user requirements, project context, previous specifications, and user feedback.

**Secondary output** (on request): broader PO/PM artifacts — meeting summaries, document reviews, engineering tickets, strategy and status docs — produced by reusing externalized templates. This is a subordinate capability; see [[21-outputs]]. The scope choice (narrow "specification assistant" vs. broad PO/PM) is recorded in [[00-product-vision-contradiction]].

## 6. Long-Term Product Loop

```text
Raw Knowledge → Ingestion → Knowledge Vault → Specification Drafting
  → Human Review → Approved Specification → External PM Actions (on request)
  → Feedback / New Knowledge ──► Knowledge Vault
```

The ultimate objective is a **knowledge-compounding specification assistant**: the more it learns, the better its specifications become; the more specifications are reviewed and used, the more useful knowledge becomes available for future work.

## 7. Success Criteria

1. Adding a source to `vault/raw/` compounds the Vault (updates/creates concepts, links, contradictions) rather than being re-derived per query.
2. Specifications evolve continuously from knowledge changes without an explicit "generate the specification" command.
3. Every specification and knowledge mutation is captured in Git with preserved provenance.
4. Chat and API produce identical capabilities; neither bypasses the planning/risk/knowledge model.
5. Consequential work remains human-reviewable (plan → review → execute).

## 8. Scope of This Spec Kit

The numbered documents (00–20, plus the [[21-outputs]] extension) specify the domain model, the Vault, the knowledge pipeline, the specification model and lifecycle, planning, risk governance, Git workflow, the internal architecture, both interfaces, integrations, and the cross-cutting concerns (observability, security, non-functional, testing). Governance is ratified in [`memory/constitution.md`](../memory/constitution.md); the buildable layer lives in [[001-leader-assistant/plan|001-leader-assistant]]. See [[README]] for reading order and conventions.

## 9. Non-Goals

Enumerated in [[19-non-functional]] §Non-Goals and derived from README §29 (do not replace an external PM platform, do not autonomously execute arbitrary external actions, do not treat vector embeddings as the canonical knowledge model, etc.).
