"""Architecture checks for the constitution invariants (_specs_/constitution.md,
matrix in _specs_/testing/testing.md §1). Static: parses imports with `ast`, so
nothing is executed and no engine is needed."""
from __future__ import annotations

import ast
from pathlib import Path

from pydantic import BaseModel

from app.domain import models

APP = Path(__file__).resolve().parent.parent / "app"

# Business code may reach the engine through these ports only (P4).
ENGINE_PORTS = {"app.workflow.port", "app.workflow.scheduler_port"}

# Code lags spec: tracked as KD-1 in _specs_/clarification.md. Remove an entry
# when the import moves behind a port; never add one without a KD row.
KNOWN_ENGINE_IMPORTS = {
    ("application/service.py", "app.workflow.simulation"),
    ("application/service.py", "app.workflow.in_process_scheduler"),
}


def _imports(package: str) -> list[tuple[str, str]]:
    """(file relative to app/, imported module) for every import in a package."""
    found: list[tuple[str, str]] = []
    for path in sorted((APP / package).rglob("*.py")):
        rel = path.relative_to(APP).as_posix()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                found.extend((rel, alias.name) for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                found.append((rel, node.module))
    return found


def test_engine_concepts_stay_in_workflow_p4() -> None:
    # P4: the Temporal SDK is only ever imported inside app/workflow/.
    offenders = [
        (rel, mod)
        for package in ("api", "application", "domain", "infra")
        for rel, mod in _imports(package)
        if mod.split(".")[0] == "temporalio"
    ]
    assert offenders == []


def test_business_code_depends_on_ports_only_p4() -> None:
    # P4: application/domain/api import from app.workflow only through the ports.
    offenders = {
        (rel, mod)
        for package in ("api", "application", "domain")
        for rel, mod in _imports(package)
        if mod.startswith("app.workflow") and mod not in ENGINE_PORTS
    }
    assert offenders - KNOWN_ENGINE_IMPORTS == set(), "new engine coupling; go through workflow/port.py"
    assert KNOWN_ENGINE_IMPORTS - offenders == set(), "deviation fixed; drop it here and from clarification.md"


def test_routers_only_reach_the_application_layer_p3() -> None:
    # P3: thin routers — the API layer never touches infra or the engine directly.
    offenders = [
        (rel, mod)
        for rel, mod in _imports("api")
        if mod.startswith(("app.infra", "app.workflow"))
    ]
    assert offenders == []


def test_domain_models_serialize_camel_case_p6() -> None:
    # P6: every wire model inherits the camelCase base, so JSON matches domain.ts.
    wire_models = [
        obj
        for obj in vars(models).values()
        if isinstance(obj, type)
        and issubclass(obj, BaseModel)
        and obj.__module__ == models.__name__
        and obj is not models.Schema
    ]
    assert wire_models
    assert [m.__name__ for m in wire_models if not issubclass(m, models.Schema)] == []
