from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import numpy as np
import uuid
from typing import List, Dict, Any

try:
    import faiss
    _has_faiss = True
except Exception:
    faiss = None
    _has_faiss = False

app = FastAPI(title="Minimal KB-backed Chat (FastAPI)")

# Simple in-memory store for chunks and metadata
VECTOR_DIM = 384  # default for all-MiniLM-L6-v2
index = None
embeddings_store: List[np.ndarray] = []
metadatas: List[Dict[str, Any]] = []

model = SentenceTransformer("all-MiniLM-L6-v2")


def chunk_text(text: str, size_chars: int = 1000, overlap: int = 200) -> List[str]:
    chunks = []
    start = 0
    length = len(text)
    while start < length:
        end = start + size_chars
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
        if start < 0:
            start = 0
    return chunks


def ensure_index(dim: int):
    global index
    if index is None:
        if _has_faiss:
            index = faiss.IndexFlatL2(dim)
        else:
            index = None


def add_embeddings(embs: np.ndarray):
    global index, embeddings_store
    if _has_faiss and index is not None:
        index.add(embs)
    embeddings_store.extend(list(embs))


def search_vector(query_emb: np.ndarray, top_k: int = 5):
    # Returns list of (score, metadata)
    if _has_faiss and index is not None and len(embeddings_store) >= top_k:
        D, I = index.search(np.array([query_emb]).astype('float32'), top_k)
        results = []
        for dist, idx in zip(D[0], I[0]):
            if idx < 0 or idx >= len(metadatas):
                continue
            results.append((float(dist), metadatas[idx]))
        return results
    # Fallback brute-force
    if len(embeddings_store) == 0:
        return []
    embs = np.stack(embeddings_store)
    # cosine similarity
    q = query_emb / np.linalg.norm(query_emb)
    embs_n = embs / np.linalg.norm(embs, axis=1, keepdims=True)
    sims = (embs_n @ q).astype(float)
    idxs = np.argsort(-sims)[:top_k]
    results = []
    for i in idxs:
        results.append((float(sims[i]), metadatas[i]))
    return results


class ChatRequest(BaseModel):
    session_id: str = None
    user_id: str = None
    message: str


class ChatResponse(BaseModel):
    text: str
    citations: List[Dict[str, Any]]
    used_kb_ids: List[str]
    kb_version: str = "local-1"


@app.post("/ingest_text")
async def ingest_text(name: str, content: str):
    """Ingest a text string as a KB document (starts local index)."""
    global metadatas
    chunks = chunk_text(content, size_chars=1000, overlap=200)
    embs = model.encode(chunks, convert_to_numpy=True, show_progress_bar=False)
    dim = embs.shape[1]
    ensure_index(dim)
    # add to faiss if available
    if _has_faiss and index is not None:
        index.add(embs.astype('float32'))
    for c, e in zip(chunks, embs):
        meta = {
            "source_id": str(uuid.uuid4()),
            "title": name,
            "excerpt": c[:400],
            "full": c
        }
        metadatas.append(meta)
        embeddings_store.append(e)
    return {"status": "ok", "chunks_indexed": len(chunks)}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    q_emb = model.encode([req.message], convert_to_numpy=True)[0]
    results = search_vector(q_emb, top_k=5)
    citations = []
    used_ids = []
    combined = []
    for score, meta in results:
        citations.append({
            "title": meta.get("title"),
            "source_id": meta.get("source_id"),
            "excerpt": meta.get("excerpt"),
            "score": score
        })
        used_ids.append(meta.get("source_id"))
        combined.append(meta.get("excerpt"))

    if len(combined) == 0:
        answer = "I don't have confirmed information in the knowledge base about that. Would you like me to ingest a document or allow a broader search?"
    else:
        # simple composition: join excerpts and respond
        context = "\n---\n".join(combined)
        answer = f"Based on the knowledge base excerpts:\n{context}\n\nAnswer (synthesized): {combined[0][:400]}"

    return ChatResponse(text=answer, citations=citations, used_kb_ids=used_ids)


@app.get("/status")
def status():
    return {"indexed_chunks": len(metadatas), "faiss_available": _has_faiss}
