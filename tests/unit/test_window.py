from datetime import date, datetime, timezone

import pytest

from ai_release_notes.window import (
    WindowError,
    WindowKind,
    apply_resolved_refs,
    derive_identity_string,
    resolve_window,
)


def test_date_range_resolves_start_and_end():
    window = resolve_window(since=date(2026, 8, 1), until=date(2026, 8, 31))

    assert window.kind == WindowKind.DATES
    assert window.resolved_start is not None
    assert window.resolved_end is not None
    assert window.resolved_end > window.resolved_start


def test_no_input_defaults_to_last_one_month_ending_now():
    now = datetime(2026, 9, 12, tzinfo=timezone.utc)

    window = resolve_window(now=now)

    assert window.kind == WindowKind.DEFAULT
    assert window.resolved_end == now
    assert window.resolved_start == datetime(2026, 8, 13, tzinfo=timezone.utc)


def test_ref_pair_is_accepted_but_not_yet_resolved():
    window = resolve_window(from_ref="v1.2.0", to_ref="v1.3.0")

    assert window.kind == WindowKind.REFS
    assert window.start_ref == "v1.2.0"
    assert window.end_ref == "v1.3.0"
    # Refs can't be turned into dates without calling GitHub -- that happens
    # later (US2), not inside window.py itself.
    assert window.resolved_start is None
    assert window.resolved_end is None


def test_both_dates_and_refs_together_is_an_error():
    with pytest.raises(WindowError):
        resolve_window(since=date(2026, 8, 1), until=date(2026, 8, 31), from_ref="v1.2.0", to_ref="v1.3.0")


def test_only_since_without_until_is_an_error():
    with pytest.raises(WindowError):
        resolve_window(since=date(2026, 8, 1))


def test_only_from_ref_without_to_ref_is_an_error():
    with pytest.raises(WindowError):
        resolve_window(from_ref="v1.2.0")


def test_apply_resolved_refs_fills_in_resolved_dates():
    window = resolve_window(from_ref="v1.2.0", to_ref="v1.3.0")
    start = datetime(2026, 7, 1, tzinfo=timezone.utc)
    end = datetime(2026, 8, 1, tzinfo=timezone.utc)

    resolved = apply_resolved_refs(window, resolved_start=start, resolved_end=end)

    assert resolved.resolved_start == start
    assert resolved.resolved_end == end


def test_apply_resolved_refs_rejects_end_before_start():
    window = resolve_window(from_ref="v1.2.0", to_ref="v1.3.0")
    start = datetime(2026, 8, 1, tzinfo=timezone.utc)
    end = datetime(2026, 7, 1, tzinfo=timezone.utc)

    with pytest.raises(WindowError):
        apply_resolved_refs(window, resolved_start=start, resolved_end=end)


def test_derive_identity_string_for_dates():
    window = resolve_window(since=date(2026, 8, 1), until=date(2026, 8, 31))
    assert derive_identity_string(window) == "2026-08-01_to_2026-08-31"


def test_derive_identity_string_for_refs():
    window = resolve_window(from_ref="v1.2.0", to_ref="v1.3.0")
    assert derive_identity_string(window) == "v1.2.0_to_v1.3.0"


def test_derive_identity_string_for_default():
    now = datetime(2026, 9, 12, tzinfo=timezone.utc)
    window = resolve_window(now=now)
    assert derive_identity_string(window) == "2026-08-13_to_2026-09-12"
