"""Entry point: start the local service and print the Swagger UI URL.

Run with:
    uv run leader-assistant
    uv run python -m app
Environment:
    LEADER_HOST (default 127.0.0.1), LEADER_PORT (default 8000)
"""

from __future__ import annotations

import os

import uvicorn

# Support both `python -m app` / the console script (package context) and a direct
# `python app/__main__.py` run, which has no parent package for a relative import.
if __package__:
    from . import config
else:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from app import config


def main() -> None:
    # Load repo-root .env before reading any config so operators can set LEADER_* there
    # (spec 03-workspace §0). override=False keeps a real shell/CLI value winning.
    config.load_env_file()

    host = os.getenv("LEADER_HOST", "127.0.0.1")
    port = int(os.getenv("LEADER_PORT", "8000"))
    display_host = "localhost" if host in ("0.0.0.0", "127.0.0.1") else host
    base = f"http://{display_host}:{port}"

    banner = (
        "\n"
        "  Leader Assistant — local service\n"
        "  --------------------------------\n"
        f"  Web UI     : {base}/\n"
        f"  Swagger UI : {base}/api/\n"
        f"  ReDoc      : {base}/redoc\n"
        f"  OpenAPI    : {base}/openapi.json\n"
        f"  Health     : {base}/health\n"
        "\n"
        "  Press Ctrl+C to stop.\n"
    )
    # spec 013 FR-7: a disabled gate must never be silent. An operator who forgot the flag is
    # set in `.env` would otherwise get an unguarded process that looks exactly like a guarded one.
    if not config.control_mode():
        banner += (
            "  !!  CONTROL MODE OFF - every approval and risk check is bypassed.\n"
            "      Operations are still scored, logged to log.md and git-committed;\n"
            "      nothing will be asked. Set LEADER_CONTROL_MODE=true to restore the gate.\n"
            "\n"
        )

    print(banner, flush=True)

    uvicorn.run("app.api:app", host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
