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
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8010")))
    sqlite_path: str = field(
        default_factory=lambda: os.getenv(
            "SQLITE_PATH", "../data/leader-control-center.db"
        )
    )
    simulation_tick_seconds: float = field(
        default_factory=lambda: float(os.getenv("SIMULATION_TICK_SECONDS", "2.5"))
    )
    scheduler_tick_seconds: float = field(
        default_factory=lambda: float(os.getenv("SCHEDULER_TICK_SECONDS", "5"))
    )
    cors_origins: list[str] = field(default_factory=_origins)
    # spec 002 FR-1: the Gradio console at /ui, and the base URL it reads the API
    # from (defaults to this process on loopback).
    console_ui_enabled: bool = field(
        default_factory=lambda: os.getenv("CONSOLE_UI_ENABLED", "true").lower() not in ("0", "false", "no")
    )
    console_api_base: str = field(default_factory=lambda: os.getenv("CONSOLE_API_BASE", ""))

    def console_base_url(self) -> str:
        if self.console_api_base:
            return self.console_api_base.rstrip("/")
        host = "127.0.0.1" if self.host in ("0.0.0.0", "") else self.host
        return f"http://{host}:{self.port}"


settings = Settings()
