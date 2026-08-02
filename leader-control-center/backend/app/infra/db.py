"""SQLite persistence for the MVP. State survives restarts; the Store's in-memory
dicts remain the working set and this module is the durable seam behind them.

Aggregates are persisted as JSON documents (one row per aggregate) in a single
`aggregates(collection, id, ord, data)` table — the pragmatic "aggregate
persistence" model, not the normalized schema in _specs_/database/data-model.md
(that is deferred; see ../../storage.md). Writes are full-snapshot rewrites in a
transaction, driven by the domain event bus, so no application/domain code
changes are needed."""
from __future__ import annotations

import json
import os
import sqlite3
import threading
from typing import TYPE_CHECKING

from app.domain.models import (
    Artifact,
    Capability,
    Decision,
    HumanRequest,
    Initiative,
    Notification,
    Provider,
    Story,
    StoryExecution,
    Task,
    TimelineEvent,
)

if TYPE_CHECKING:
    from app.infra.store import Store

_SCHEMA = """
CREATE TABLE IF NOT EXISTS aggregates (
    collection TEXT NOT NULL,
    id         TEXT NOT NULL,
    ord        INTEGER NOT NULL DEFAULT 0,
    data       TEXT NOT NULL,
    PRIMARY KEY (collection, id)
);
"""

# Plain dict[id, Model] collections: store attribute name -> (collection, model).
_MAPPED = (
    ("initiatives", "initiatives", Initiative),
    ("stories", "stories", Story),
    ("tasks", "tasks", Task),
    ("capabilities", "capabilities", Capability),
    ("providers", "providers", Provider),
    ("executions", "story_executions", StoryExecution),
    ("human_requests", "human_requests", HumanRequest),
    ("decisions", "decisions", Decision),
)


class Database:
    def __init__(self, path: str) -> None:
        self.path = path
        if path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        # check_same_thread=False: the tick loop (event loop thread) and sync
        # route handlers (threadpool) may both trigger a write-through save.
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)
        self._conn.commit()
        self._lock = threading.Lock()

    def has_data(self) -> bool:
        with self._lock:
            return (
                self._conn.execute("SELECT 1 FROM aggregates LIMIT 1").fetchone()
                is not None
            )

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # -- write-through -----------------------------------------------------
    def save(self, store: "Store") -> None:
        rows = list(self._rows(store))
        with self._lock, self._conn:  # single transaction
            self._conn.execute("DELETE FROM aggregates")
            self._conn.executemany(
                "INSERT INTO aggregates(collection, id, ord, data) VALUES (?, ?, ?, ?)",
                rows,
            )

    @staticmethod
    def _rows(store: "Store"):
        for attr, collection, _model in _MAPPED:
            for id_, model in getattr(store, attr).items():
                yield (collection, id_, 0, model.model_dump_json())
        for id_, epic in store.epics.items():
            yield (
                "epics",
                id_,
                0,
                json.dumps(
                    {"id": epic.id, "initiative_id": epic.initiative_id, "title": epic.title}
                ),
            )
        # list-per-key collections: `ord` preserves in-list order.
        for artifacts in store.artifacts_by_story.values():
            for ord_, art in enumerate(artifacts):
                yield ("artifacts", art.id, ord_, art.model_dump_json())
        for events in store.timelines.values():
            for ord_, ev in enumerate(events):
                yield ("timeline", ev.id, ord_, ev.model_dump_json())
        for ord_, n in enumerate(store.notifications):
            yield ("notifications", n.id, ord_, n.model_dump_json())

    # -- load --------------------------------------------------------------
    def load_into(self, store: "Store") -> None:
        from app.infra.store import EpicRow

        with self._lock:
            rows = self._conn.execute(
                "SELECT collection, id, ord, data FROM aggregates ORDER BY ord"
            ).fetchall()

        buckets: dict[str, list[tuple[str, str]]] = {}
        for collection, id_, _ord, data in rows:
            buckets.setdefault(collection, []).append((id_, data))

        for attr, collection, model in _MAPPED:
            target = getattr(store, attr)
            for id_, data in buckets.get(collection, []):
                target[id_] = model.model_validate_json(data)

        for id_, data in buckets.get("epics", []):
            d = json.loads(data)
            store.epics[id_] = EpicRow(d["id"], d["initiative_id"], d["title"])

        for _id, data in buckets.get("artifacts", []):
            art = Artifact.model_validate_json(data)
            store.artifacts_by_story.setdefault(art.story_id, []).append(art)

        for _id, data in buckets.get("timeline", []):
            ev = TimelineEvent.model_validate_json(data)
            store.timelines.setdefault(ev.execution_id, []).append(ev)

        for _id, data in buckets.get("notifications", []):
            store.notifications.append(Notification.model_validate_json(data))

        # Derived indexes, rebuilt from the loaded aggregates.
        store.execution_by_story = {
            ex.story_id: ex.id for ex in store.executions.values()
        }
        store.seeded = True
