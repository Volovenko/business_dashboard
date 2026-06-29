"""Pure-logic tests for act status computation.

Status truth table (first match wins):
    is_signed                                     → CLOSED
    is_sent (and not signed)                      → WAITING_SIGNATURE
    not sent AND age ≥ threshold_days             → ATTENTION
    otherwise                                     → NOT_SENT
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.models import ActStatus
from app.services.act_status_service import ActStatusService

THRESHOLD = 30
TODAY = date(2026, 6, 25)


def _days_before(n: int) -> date:
    return TODAY - timedelta(days=n)


@pytest.mark.parametrize(
    ("is_sent", "is_signed", "days_old", "expected"),
    [
        # closed wins regardless of age
        (True, True, 0, ActStatus.CLOSED),
        (True, True, 365, ActStatus.CLOSED),
        # signed without sent is an invariant violation but we treat signed=True as closed
        (False, True, 0, ActStatus.CLOSED),
        # sent but not signed → waiting_signature regardless of age
        (True, False, 0, ActStatus.WAITING_SIGNATURE),
        (True, False, 29, ActStatus.WAITING_SIGNATURE),
        (True, False, 30, ActStatus.WAITING_SIGNATURE),
        (True, False, 365, ActStatus.WAITING_SIGNATURE),
        # fresh not_sent
        (False, False, 0, ActStatus.NOT_SENT),
        (False, False, 29, ActStatus.NOT_SENT),
        # stale not_sent → attention
        (False, False, 30, ActStatus.ATTENTION),
        (False, False, 365, ActStatus.ATTENTION),
    ],
    ids=lambda v: repr(v),
)
def test_compute_status(
    is_sent: bool,
    is_signed: bool,
    days_old: int,
    expected: ActStatus,
) -> None:
    status = ActStatusService.compute(
        is_sent=is_sent,
        is_signed=is_signed,
        payment_date=_days_before(days_old),
        today=TODAY,
        threshold_days=THRESHOLD,
    )
    assert status == expected


def test_threshold_is_inclusive_lower_bound() -> None:
    """30 days before today → exactly at threshold → attention; 29 days → not attention."""
    at_threshold = ActStatusService.compute(
        is_sent=False,
        is_signed=False,
        payment_date=_days_before(THRESHOLD),
        today=TODAY,
        threshold_days=THRESHOLD,
    )
    just_below = ActStatusService.compute(
        is_sent=False,
        is_signed=False,
        payment_date=_days_before(THRESHOLD - 1),
        today=TODAY,
        threshold_days=THRESHOLD,
    )
    assert at_threshold is ActStatus.ATTENTION
    assert just_below is ActStatus.NOT_SENT


def test_custom_threshold_is_respected() -> None:
    status = ActStatusService.compute(
        is_sent=False,
        is_signed=False,
        payment_date=_days_before(10),
        today=TODAY,
        threshold_days=7,
    )
    assert status is ActStatus.ATTENTION
