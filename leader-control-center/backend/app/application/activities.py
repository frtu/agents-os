"""Activity Definitions: reusable bash/webhook building blocks for Temporal
workflows (specs/execution/activity-definitions.md). Catalog data edited
directly (CRUD), plus a side-effect-free render and a one-off webhook test.
Bash scripts are syntax-checked only (`bash -n`); they never run in the API
process (decision A2)."""
from __future__ import annotations

import os
import shutil
import subprocess
import time
from typing import Callable

import httpx

from app.application.errors import InvariantError, NotFoundError
from app.domain import activity_template as tpl
from app.domain.activity_template import TemplateError
from app.domain.enums import ActivityKind, WebhookMethod
from app.domain.models import ActivityDefinition, RenderedActivity, WebhookTestResult
from app.infra.store import Store, now, uid

_DEFAULT_TIMEOUT = {ActivityKind.BASH: 300, ActivityKind.WEBHOOK: 30}
_TEST_TIMEOUT_CAP = 30.0
_RESPONSE_LIMIT = 4096

# Fields a caller may set; everything else is server-managed.
EDITABLE = (
    "name", "description", "kind", "input", "timeout_seconds", "script",
    "method", "url", "headers", "content_type", "body_template",
)


class ActivityDefinitionService:
    def __init__(
        self, store: Store,
        http: Callable[[], httpx.Client] | None = None,
        env: Callable[[str], str | None] = os.environ.get,
    ) -> None:
        self.store = store
        self._http = http or (lambda: httpx.Client(follow_redirects=False))
        self._env = env

    # -- queries -----------------------------------------------------------
    def list_definitions(self) -> list[ActivityDefinition]:
        return sorted(self.store.activity_definitions.values(), key=lambda d: d.name.lower())

    def get(self, definition_id: str) -> ActivityDefinition:
        definition = self.store.activity_definitions.get(definition_id)
        if definition is None:
            raise NotFoundError(f"Activity definition not found: {definition_id}")
        return definition

    # -- commands ------------------------------------------------------------
    def create(self, **fields) -> ActivityDefinition:
        kind = fields.get("kind")
        if kind is None:
            raise InvariantError("kind is required (Bash or Webhook)")
        fields.setdefault("timeout_seconds", _DEFAULT_TIMEOUT[ActivityKind(kind)])
        definition = ActivityDefinition(
            id=uid("act"), portfolio_id="portfolio_default",
            created_at=now(), updated_at=now(),
            **{k: v for k, v in fields.items() if k in EDITABLE and v is not None},
        )
        self._validate(definition)
        return self.store.put_activity_definition(definition)

    def update(self, definition_id: str, **changes) -> ActivityDefinition:
        existing = self.get(definition_id)
        updates = {k: v for k, v in changes.items() if k in EDITABLE and v is not None}
        merged = ActivityDefinition.model_validate({
            **existing.model_dump(), **updates,
            "version": existing.version + 1, "updated_at": now(),
        })
        self._validate(merged)
        return self.store.put_activity_definition(merged)

    def delete(self, definition_id: str) -> None:
        self.get(definition_id)
        self.store.delete_activity_definition(definition_id)

    # -- render / test -------------------------------------------------------
    def render(self, definition_id: str, values: dict | None) -> RenderedActivity:
        """Apply parameters without side effects; header secrets stay masked."""
        definition = self.get(definition_id)
        try:
            return self._render(definition, values, env=None)
        except TemplateError as e:
            raise InvariantError(str(e)) from e

    def test_webhook(self, definition_id: str, values: dict | None) -> WebhookTestResult:
        """Send the webhook once. Transport failures are reported in the result
        (the test ran); template/secret problems are 422s."""
        definition = self.get(definition_id)
        if definition.kind != ActivityKind.WEBHOOK:
            raise InvariantError("Only Webhook definitions can be test-sent; bash runs on a worker")
        try:
            masked = self._render(definition, values, env=None)
            sent = self._render(definition, values, env=self._env)
        except TemplateError as e:
            raise InvariantError(str(e)) from e

        timeout = min(float(definition.timeout_seconds), _TEST_TIMEOUT_CAP)
        started = time.monotonic()
        try:
            with self._http() as client:
                response = client.request(
                    str(sent.method), sent.url or "", headers=sent.headers,
                    content=(sent.body or "").encode(), timeout=timeout,
                )
        except httpx.HTTPError as e:
            return WebhookTestResult(
                request=masked, duration_ms=_elapsed(started),
                error=f"{type(e).__name__}: {e}" if str(e) else type(e).__name__,
            )
        body = response.text
        return WebhookTestResult(
            request=masked, status=response.status_code, duration_ms=_elapsed(started),
            response_headers=dict(response.headers),
            response_body=body[:_RESPONSE_LIMIT] + ("…[truncated]" if len(body) > _RESPONSE_LIMIT else ""),
        )

    # -- internals -----------------------------------------------------------
    @staticmethod
    def _render(
        definition: ActivityDefinition, values: dict | None,
        env: Callable[[str], str | None] | None,
    ) -> RenderedActivity:
        resolved = tpl.resolve_values(definition.input, values)
        if definition.kind == ActivityKind.BASH:
            return RenderedActivity(
                kind=definition.kind, script=tpl.render_script(definition.script or "", resolved),
            )
        headers = dict(definition.headers)
        if not any(k.lower() == "content-type" for k in headers):
            headers["Content-Type"] = definition.content_type
        return RenderedActivity(
            kind=definition.kind, method=definition.method,
            url=tpl.render_url(definition.url or "", resolved),
            headers=tpl.render_headers(headers, resolved, env),
            body=tpl.render_body(definition.body_template or "", definition.content_type, resolved),
        )

    def _validate(self, d: ActivityDefinition) -> None:
        if not d.name.strip():
            raise InvariantError("Name is required")
        if not isinstance(d.input, dict) or d.input.get("type", "object") != "object":
            raise InvariantError("input must be a JSON Schema object")
        if d.timeout_seconds <= 0:
            raise InvariantError("timeoutSeconds must be positive")
        try:
            if d.kind == ActivityKind.BASH:
                if not (d.script or "").strip():
                    raise InvariantError("A Bash definition needs a script")
                tpl.check_placeholders({"script": d.script}, d.input)
                _bash_syntax_check(d.script or "")
            else:
                self._validate_webhook(d)
        except TemplateError as e:
            raise InvariantError(str(e)) from e

    @staticmethod
    def _validate_webhook(d: ActivityDefinition) -> None:
        url = (d.url or "").strip()
        if not url.lower().startswith(("http://", "https://")):
            raise InvariantError("Webhook URL must start with http:// or https://")
        if d.method not in tuple(WebhookMethod):
            raise InvariantError("Webhook method must be POST, PUT or PATCH")
        for name, value in d.headers.items():
            if not name.strip():
                raise InvariantError("Header names cannot be empty")
            if tpl.ENV_REF.search(name):
                raise InvariantError("${env:...} is only allowed in header values")
        if tpl.ENV_REF.search(url) or tpl.ENV_REF.search(d.body_template or ""):
            raise InvariantError("${env:...} secrets are only allowed in header values")
        tpl.check_placeholders(
            {"url": url, "body": d.body_template, **{f"header {k}": v for k, v in d.headers.items()}},
            d.input,
        )
        if tpl.is_json(d.content_type) and (d.body_template or "").strip():
            # Placeholders must stand as whole JSON values: render with sample
            # strings, which breaks if a placeholder sits inside a "string".
            sample = {name: "sample" for name in tpl.placeholders(d.body_template)}
            tpl.render_body(d.body_template or "", d.content_type, sample)


def _bash_syntax_check(script: str) -> None:
    """Parse only (`bash -n`); nothing is executed."""
    bash = shutil.which("bash")
    if bash is None:
        return  # no bash on this host: skip the check rather than block saving
    result = subprocess.run(
        [bash, "-n"], input=script, capture_output=True, text=True, timeout=5,
    )
    if result.returncode != 0:
        message = result.stderr.strip().replace("bash: ", "")
        raise InvariantError(f"Bash syntax error: {message}")


def _elapsed(started: float) -> int:
    return int((time.monotonic() - started) * 1000)
