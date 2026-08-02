"""Test isolation: force an in-memory SQLite database so every `create_app()`
starts from a fresh seed (the smoke tests assert the seeded shape). This must run
before app.config is imported, so it is set at conftest import time."""
from __future__ import annotations

import os

os.environ["SQLITE_PATH"] = ":memory:"
