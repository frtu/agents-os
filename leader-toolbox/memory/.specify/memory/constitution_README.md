# How the chat backend should use the Constitution

This short README explains the minimal, concrete rules the web chat backend should follow to honor the `constitution.md` for a chat backed by a knowledge base (KB).

## 1) Contract (inputs / outputs / errors)

- Input: {session_id, user_id (optional), message, metadata}
- Output: {text, citations[], used_kb_ids[], follow_up_suggestions[], error?}
- Errors: return friendly, actionable messages (e.g., "I couldn't find evidence in the knowledge base; try rephrasing or allow a broader search").

## 2) Retrieval defaults

- Default top-K: 5 (configurable).
- Similarity threshold: use a configurable float (example default: 0.7). Matches below threshold count as "no evidence."
- Return for each hit: {source_id, title, score, excerpt (short), url (if available)}.

## 3) Citation & response format

- If an answer uses KB material, include a citations array with items containing {title, source_id, excerpt, link (optional)}.
- Prepend or append a short "Evidence:" block listing used citations when factual claims are made.
- If KB evidence contradicts model knowledge, prefer KB and add a short note: "KB evidence indicates... — please verify."

## 4) Memory & session handling

- Use conversation history within the session for context; session history should be trimmed (token-window) before retrieval.
- Do not persist session history into long-term storage without explicit user consent.
- Long-term memory must be opt-in, tagged, and auditable. Provide an API to list and delete user-stored items.

## 5) No-fabrication & uncertainty

- Never invent citation sources. If unsure, respond: "I don't have confirmed information in the knowledge base about that." Offer to search broader or suggest follow-ups.

## 6) Privacy & PII

- Avoid including raw PII from user messages into the KB. Redact or transform sensitive fields before storing.
- Keep logs anonymized and follow the configured retention policy.

## 7) KB updates

- Re-index after source changes; track index version or timestamp with each search response (e.g., `kb_version: 2025-10-26T...`).
- On re-index, provide a short migration note to any long-term memory components if schema or source IDs change.

## 8) Safety filtering

- Apply content policy filters pre-generation and pre-return. Block and politely refuse illegal, harmful, or disallowed requests.

## 9) Testing checklist (minimal)

- Retrieval: assert top-K returns expected sources for representative queries.
- Citation: responses that claim facts include at least one KB citation.
- Privacy: verify PII is not persisted without consent.

## 10) Example minimal response payload


```json
{
  "text": "According to the project FAQ, the deployment step is 'run build then deploy'.",
  "citations": [
    {"title":"Project FAQ","source_id":"faq-2025","excerpt":"run build then deploy","link":"https://..."}
  ],
  "used_kb_ids": ["faq-2025"],
  "kb_version": "2025-10-26T12:00:00Z"
}
```

Replace or extend these defaults as your project requires. Below are concrete defaults chosen for this workspace:

- Backend: Python + FastAPI (examples provided in /examples/fastapi_chat.py)
- Local deployment: run with uvicorn on a developer machine
- Single-tenant: one KB per deployment
- Starter KB: single-file ingestion to an in-memory FAISS index (sentence-transformers embeddings)
- Upgrade path: switch vector_store to Elasticsearch or managed vector DB by changing `constitution_config.json` and updating the retrieval layer.

If you'd like, I can also create an alternative integration snippet for Node/Express or a ready-to-run Dockerfile.
---
Generated to accompany `.specify/memory/constitution.md` (Version 1.0)
