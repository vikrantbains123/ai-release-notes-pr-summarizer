"""Resolves the Time Window entity: a date range, a ref pair, or the
default of the last 1 month (FR-001, FR-015).
"""
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import Optional


class WindowError(Exception):
    """Raised for an invalid or incomplete window specification."""


class WindowKind(str, Enum):
    DATES = "dates"
    REFS = "refs"
    DEFAULT = "default"


DEFAULT_WINDOW_DAYS = 30


@dataclass
class TimeWindow:
    kind: WindowKind
    start: Optional[date] = None
    end: Optional[date] = None
    start_ref: Optional[str] = None
    end_ref: Optional[str] = None
    resolved_start: Optional[datetime] = None
    resolved_end: Optional[datetime] = None


def resolve_window(
    since: Optional[date] = None,
    until: Optional[date] = None,
    from_ref: Optional[str] = None,
    to_ref: Optional[str] = None,
    now: Optional[datetime] = None,
) -> TimeWindow:
    has_dates = since is not None or until is not None
    has_refs = from_ref is not None or to_ref is not None

    if has_dates and has_refs:
        raise WindowError(
            "Cannot combine a date range (--since/--until) with a reference "
            "pair (--from-ref/--to-ref); use one or the other"
        )

    if has_dates:
        if since is None or until is None:
            raise WindowError("Both --since and --until are required together")
        resolved_start = datetime.combine(since, datetime.min.time(), tzinfo=timezone.utc)
        resolved_end = datetime.combine(until, datetime.min.time(), tzinfo=timezone.utc)
        if resolved_end <= resolved_start:
            raise WindowError("--until must be after --since")
        return TimeWindow(
            kind=WindowKind.DATES,
            start=since,
            end=until,
            resolved_start=resolved_start,
            resolved_end=resolved_end,
        )

    if has_refs:
        if from_ref is None or to_ref is None:
            raise WindowError("Both --from-ref and --to-ref are required together")
        return TimeWindow(kind=WindowKind.REFS, start_ref=from_ref, end_ref=to_ref)

    resolved_end = now or datetime.now(timezone.utc)
    resolved_start = resolved_end - timedelta(days=DEFAULT_WINDOW_DAYS)
    return TimeWindow(kind=WindowKind.DEFAULT, resolved_start=resolved_start, resolved_end=resolved_end)


def derive_identity_string(window: TimeWindow) -> str:
    """Builds a default version/release-name string from the window, used
    (FR-019) when the user hasn't supplied --version/--release-name and
    isn't publishing.
    """
    if window.kind == WindowKind.REFS:
        return f"{window.start_ref}_to_{window.end_ref}"
    if window.kind == WindowKind.DATES:
        return f"{window.start.isoformat()}_to_{window.end.isoformat()}"
    return f"{window.resolved_start.date().isoformat()}_to_{window.resolved_end.date().isoformat()}"


def apply_resolved_refs(window: TimeWindow, resolved_start: datetime, resolved_end: datetime) -> TimeWindow:
    """Fills in resolved_start/resolved_end for a `refs`-kind window, once
    the caller has resolved both refs to commit dates via GitHub (US2).
    """
    if resolved_end <= resolved_start:
        raise WindowError("--to-ref must resolve to a later commit than --from-ref")
    window.resolved_start = resolved_start
    window.resolved_end = resolved_end
    return window
