import sys
import os
import asyncio
import numpy as np
import types

# Ensure the project root is on sys.path so 'examples' can be imported when
# pytest is run from the repository root or from the workspace.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import backend.fastapi_chat as appmod


class DummyModel:
    """Deterministic dummy embedding model for tests.

    It maps a text to a small vector based on its length so tests are fast
    and don't require real models.
    """

    def encode(self, texts, convert_to_numpy=True, show_progress_bar=False):
        vecs = []
        for t in texts:
            # simple 3-d embedding: [len%10, (len//10)%10, 1]
            l = len(t)
            v = np.array([l % 10, (l // 10) % 10, 1.0], dtype=float)
            # normalize
            v = v / np.linalg.norm(v)
            vecs.append(v)
        return np.stack(vecs)


def reset_state():
    appmod.metadatas.clear()
    appmod.embeddings_store.clear()
    # reset faiss index if present
    appmod.index = None


def test_chunk_text_basic():
    text = "a" * 2500
    chunks = appmod.chunk_text(text, size_chars=1000, overlap=200)
    # Expect at least 3 chunks for 2500 chars with overlap
    assert len(chunks) >= 3


def test_ingest_and_chat():
    reset_state()
    # patch model
    appmod.model = DummyModel()

    # ingest a small document synchronously via asyncio.run
    resp = asyncio.run(appmod.ingest_text(name="doc1", content="Hello world. This is a test document."))
    assert resp.get("status") == "ok"
    assert resp.get("chunks_indexed", 0) > 0

    # chat with the same text to ensure high similarity
    req = appmod.ChatRequest(message="Hello world. This is a test document.")
    res = asyncio.run(appmod.chat(req))
    assert isinstance(res.text, str)
    # should have at least one citation
    assert len(res.citations) >= 1
    assert len(res.used_kb_ids) >= 1


def test_status_reflects_indexed_chunks():
    # status should reflect the number of metadata entries
    s = appmod.status()
    assert s["indexed_chunks"] == len(appmod.metadatas)
