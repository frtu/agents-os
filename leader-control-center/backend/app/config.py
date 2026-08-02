"""Runtime configuration, read from the environment (see .env.example)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field


def _origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    return [o.strip() for o in raw.split(",") if o.strip()]


@dataclass(frozen=True)
class Settings:
    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    sqlite_path: str = field(
        default_factory=lambda: os.getenv(
            "SQLITE_PATH", "../data/leader-control-center.db"
        )
    )
    simulation_tick_seconds: float = field(
        default_factory=lambda: float(os.getenv("SIMULATION_TICK_SECONDS", "2.5"))
    )
    cors_origins: list[str] = field(default_factory=_origins)


settings = Settings()
