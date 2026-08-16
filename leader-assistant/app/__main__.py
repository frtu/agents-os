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


def main() -> None:
    host = os.getenv("LEADER_HOST", "127.0.0.1")
    port = int(os.getenv("LEADER_PORT", "8000"))
    display_host = "localhost" if host in ("0.0.0.0", "127.0.0.1") else host
    base = f"http://{display_host}:{port}"

    banner = (
        "\n"
        "  Leader Assistant — local service\n"
        "  --------------------------------\n"
        f"  API base   : {base}\n"
        f"  Swagger UI : {base}/docs\n"
        f"  ReDoc      : {base}/redoc\n"
        f"  OpenAPI    : {base}/openapi.json\n"
        f"  Health     : {base}/health\n"
        "\n"
        "  Press Ctrl+C to stop.\n"
    )
    print(banner, flush=True)

    uvicorn.run("app.api:app", host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
