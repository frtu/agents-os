# Chat + Knowledge Base: Minimal Constitution

## Purpose

Provide a concise, accurate, and evidence-backed interactive web chat experience using a maintained knowledge base (KB).

## Scope

- User-facing web chat UI and backend that: accepts user messages, retrieves KB evidence, and synthesizes responses.
- Not intended for regulated professional advice (legal/medical/financial) unless explicitly validated and disclosed.

## Knowledge base usage

- Primary source of truth: the KB (document store / vector index). All factual claims should be grounded with KB citations when available.
- Retrieval policy: retrieve top-K documents (configurable, default K=5); include source identifiers and short excerpts in the answer when used.
- If retrieved evidence contradicts the LLM's prior knowledge, prefer KB evidence and flag potential inconsistencies.

## Memory and session state

- Short-term: session messages (conversation history) are used for context and forgotten at session end unless user opts-in.
- Long-term memory: only stored when explicitly enabled and when user consents; stored items must be tagged and auditable.

## Privacy & data handling

- Avoid storing or indexing sensitive personal data in the KB. If such data is present, redact or remove per policy.
- Logs and analytics must be anonymized; retention default: 30 days (configurable).
- Provide a clear mechanism for users to request deletion of their long-term data.

## Response rules

- Always try to cite KB evidence for factual answers. Format citations clearly (title, source id, optional link, excerpt).
- If no relevant KB evidence is found, respond honestly: "I don't have confirmed information in the knowledge base about that; would you like me to search broadly or give a general answer?"
- Do not fabricate sources. If the model is uncertain, explicitly say so and offer next steps.

## Safety & content policy

- Block requests that facilitate illegal activity, hate, or explicit harm. Follow the project's content policy for disallowed content.

## KB updates & governance

- Re-index or update KB whenever source documents change; record a KB version or timestamp with each index snapshot.
- Constitution amendments: change via repository PR with a short rationale and a version/date update.

## Operational notes (minimal)

- Retrieval pipeline should support similarity thresholds; below-threshold matches count as "no evidence."
- Default user-facing errors: friendly, actionable (e.g., retry, refine question).

## Contact & metadata

- Maintainer: Fred TU <PRIVATE> (replace before release).

**Version**: 1.0 | **Ratified**: 2025-10-26 | **Last Amended**: 2025-10-26
