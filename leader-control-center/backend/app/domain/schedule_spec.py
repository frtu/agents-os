"""Pure time math for Schedule specs (specs/planning/schedules.md): validation,
next occurrences, the latest occurrence at or before an instant, and the
plain-language sentence a leader confirms. No I/O; datetimes are timezone-aware."""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from cronsim import CronSim, CronSimError

from app.domain.enums import OverlapPolicy, ScheduleSpecKind
from app.domain.models import ScheduleSpec

MIN_INTERVAL = timedelta(minutes=5)

_DURATION = re.compile(
    r"^P(?:(?P<w>\d+)W)?(?:(?P<d>\d+)D)?"
    r"(?:T(?:(?P<h>\d+)H)?(?:(?P<m>\d+)M)?(?:(?P<s>\d+)S)?)?$"
)


class SpecError(ValueError):
    """An invalid schedule spec (maps to HTTP 422)."""


def parse_duration(value: str) -> timedelta:
    """ISO 8601 duration subset: PnW, PnD, PTnHnMnS (no months/years)."""
    match = _DURATION.match(value or "")
    if not match or value in ("P", "PT") or value.endswith("T"):
        raise SpecError(f"Invalid ISO 8601 duration: {value!r} (use e.g. PT1H, P1D)")
    parts = {k: int(v) for k, v in match.groupdict().items() if v}
    return timedelta(
        weeks=parts.get("w", 0), days=parts.get("d", 0), hours=parts.get("h", 0),
        minutes=parts.get("m", 0), seconds=parts.get("s", 0),
    )


def parse_instant(value: str) -> datetime:
    """ISO 8601 instant that must carry an offset (or Z)."""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as e:
        raise SpecError(f"Invalid ISO 8601 instant: {value!r}") from e
    if dt.tzinfo is None:
        raise SpecError(f"Instant needs a UTC offset or Z: {value!r}")
    return dt


def to_iso(dt: datetime) -> str:
    """UTC, millisecond precision, trailing Z (the store's timestamp format)."""
    return (
        dt.astimezone(timezone.utc).isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def _zone(spec: ScheduleSpec) -> ZoneInfo:
    try:
        return ZoneInfo(spec.timezone or "UTC")
    except (ZoneInfoNotFoundError, ValueError) as e:
        raise SpecError(f"Unknown IANA timezone: {spec.timezone!r}") from e


def validate(spec: ScheduleSpec) -> None:
    """Raise SpecError unless the spec is complete and well-formed."""
    if spec.kind == ScheduleSpecKind.ONCE:
        if not spec.at:
            raise SpecError("Once schedules need `at`")
        parse_instant(spec.at)
    elif spec.kind == ScheduleSpecKind.INTERVAL:
        if not spec.every:
            raise SpecError("Interval schedules need `every`")
        if parse_duration(spec.every) < MIN_INTERVAL:
            raise SpecError("Interval must be at least PT5M")
        if spec.anchor:
            parse_instant(spec.anchor)
    elif spec.kind == ScheduleSpecKind.CRON:
        if not spec.expression:
            raise SpecError("Cron schedules need `expression`")
        if not spec.timezone:
            raise SpecError("Cron schedules need an IANA `timezone`")
        zone = _zone(spec)
        if len(spec.expression.split()) != 5:
            raise SpecError("Cron expression must have 5 fields")
        try:
            CronSim(spec.expression, datetime.now(zone))
        except CronSimError as e:
            raise SpecError(f"Invalid cron expression: {e}") from e


def _anchor(spec: ScheduleSpec, default_anchor: datetime) -> datetime:
    return parse_instant(spec.anchor) if spec.anchor else default_anchor


def next_occurrences(
    spec: ScheduleSpec, after: datetime, n: int, default_anchor: datetime,
) -> list[datetime]:
    """Up to `n` occurrences strictly after `after`."""
    if spec.kind == ScheduleSpecKind.ONCE:
        at = parse_instant(spec.at or "")
        return [at] if at > after else []
    if spec.kind == ScheduleSpecKind.INTERVAL:
        every = parse_duration(spec.every or "")
        anchor = _anchor(spec, default_anchor)
        k = 0 if after < anchor else (after - anchor) // every + 1
        return [anchor + every * (k + i) for i in range(n)]
    it = CronSim(spec.expression or "", after.astimezone(_zone(spec)))
    return [next(it) for _ in range(n)]


def latest_at_or_before(
    spec: ScheduleSpec, instant: datetime, default_anchor: datetime,
) -> datetime | None:
    """The most recent occurrence <= `instant`, or None if there is none."""
    if spec.kind == ScheduleSpecKind.ONCE:
        at = parse_instant(spec.at or "")
        return at if at <= instant else None
    if spec.kind == ScheduleSpecKind.INTERVAL:
        every = parse_duration(spec.every or "")
        anchor = _anchor(spec, default_anchor)
        if instant < anchor:
            return None
        return anchor + every * ((instant - anchor) // every)
    # CronSim's reverse search excludes its start, so start one second later.
    start = (instant + timedelta(seconds=1)).astimezone(_zone(spec))
    return next(CronSim(spec.expression or "", start, reverse=True), None)


_OVERLAP_TEXT = {
    OverlapPolicy.SKIP: "If the previous run is still active, skip this one.",
    OverlapPolicy.BUFFER_ONE: (
        "If the previous run is still active, queue one run for when it ends."
    ),
    OverlapPolicy.ALLOW_PARALLEL: "Start a new run even if the previous one is still active.",
}


def describe_spec(spec: ScheduleSpec) -> str:
    if spec.kind == ScheduleSpecKind.ONCE:
        return f"Once at {parse_instant(spec.at or '').isoformat(timespec='minutes')}"
    if spec.kind == ScheduleSpecKind.INTERVAL:
        text = f"Every {_humanize(parse_duration(spec.every or ''))}"
        return f"{text}, starting {spec.anchor}" if spec.anchor else text
    return f"On cron `{spec.expression}` ({spec.timezone})"


def describe(
    spec: ScheduleSpec, overlap: OverlapPolicy, story_title: str, initiative_title: str,
) -> str:
    return (
        f"{describe_spec(spec)}, create and start '{story_title}' in "
        f"{initiative_title}. {_OVERLAP_TEXT[overlap]}"
    )


def _humanize(delta: timedelta) -> str:
    seconds = int(delta.total_seconds())
    for unit, size in (("week", 604800), ("day", 86400), ("hour", 3600), ("minute", 60)):
        if seconds % size == 0:
            count = seconds // size
            return f"{count} {unit}" + ("s" if count != 1 else "")
    return f"{seconds} seconds"


def render_title(template: str, name: str, scheduled_for: datetime, n: int) -> str:
    """Fill {name} {date} {datetime} {n} in a story title template."""
    return (
        template.replace("{name}", name)
        .replace("{datetime}", scheduled_for.strftime("%Y-%m-%d %H:%M"))
        .replace("{date}", scheduled_for.strftime("%Y-%m-%d"))
        .replace("{n}", str(n))
    )


def zone_for(spec: ScheduleSpec) -> ZoneInfo:
    """Timezone used to render occurrence dates (Cron: its zone; else UTC)."""
    return _zone(spec) if spec.kind == ScheduleSpecKind.CRON else ZoneInfo("UTC")
