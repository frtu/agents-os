"""Template rendering for Activity Definitions (specs/execution/activity-definitions.md
§Templates). `{{name}}` placeholders are encoded for the place they land in
(shell-quoted, URL-encoded, JSON-encoded, or text), so a parameter value can
never break out of its slot. `${env:NAME}` secret references are allowed in
header values only. Pure functions; env lookup is injected."""
from __future__ import annotations

import json
import re
import shlex
from typing import Callable, Mapping
from urllib.parse import quote

PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")
ENV_REF = re.compile(r"\$\{env:([A-Za-z_][A-Za-z0-9_]*)\}")


class TemplateError(ValueError):
    """Invalid template or input (maps to HTTP 422)."""


def placeholders(text: str | None) -> set[str]:
    return set(PLACEHOLDER.findall(text or ""))


def check_placeholders(sources: Mapping[str, str | None], schema: dict) -> None:
    """Every placeholder must name a property declared in the JSON Schema."""
    declared = set((schema.get("properties") or {}).keys())
    for where, text in sources.items():
        unknown = placeholders(text) - declared
        if unknown:
            raise TemplateError(
                f"{where} uses undeclared parameter(s): {', '.join(sorted(unknown))}"
            )


def resolve_values(schema: dict, values: dict | None) -> dict:
    """Apply schema defaults and enforce `required` (lightweight JSON Schema)."""
    values = dict(values or {})
    missing = [k for k in schema.get("required", []) if k not in values]
    if missing:
        raise TemplateError(f"Missing required parameter(s): {', '.join(missing)}")
    for name, prop in (schema.get("properties") or {}).items():
        if name not in values and isinstance(prop, dict) and "default" in prop:
            values[name] = prop["default"]
    return values


def _text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    return str(value)


def _sub(text: str, encode: Callable[[object], str], values: dict) -> str:
    return PLACEHOLDER.sub(lambda m: encode(values.get(m.group(1))), text)


def render_script(script: str, values: dict) -> str:
    return _sub(script, lambda v: shlex.quote(_text(v)), values)


def render_url(url: str, values: dict) -> str:
    return _sub(url, lambda v: quote(_text(v), safe=""), values)


def render_body(template: str, content_type: str, values: dict) -> str:
    if is_json(content_type):
        body = _sub(template, lambda v: json.dumps(v), values)
        try:
            json.loads(body) if body.strip() else None
        except json.JSONDecodeError as e:
            raise TemplateError(f"Body is not valid JSON after rendering: {e.msg}") from e
        return body
    return _sub(template, _text, values)


def render_headers(
    headers: dict[str, str], values: dict,
    env: Callable[[str], str | None] | None = None,
) -> dict[str, str]:
    """Render header values. With `env`, resolve ${env:NAME} (missing → error);
    without it, leave references as-is (masked preview)."""
    rendered: dict[str, str] = {}
    for name, raw in headers.items():
        value = _sub(raw, _text, values)
        if env is not None:
            def lookup(m: re.Match) -> str:
                secret = env(m.group(1))
                if secret is None:
                    raise TemplateError(f"Secret env var not set: {m.group(1)}")
                return secret
            value = ENV_REF.sub(lookup, value)
        rendered[name] = value
    return rendered


def is_json(content_type: str) -> bool:
    return content_type.split(";")[0].strip().lower().endswith("json")
