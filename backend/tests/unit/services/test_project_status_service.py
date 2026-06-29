"""Pure-logic tests for project status aggregation.

Rules (when project is not ON_HOLD):
    any act ATTENTION         → ATTENTION
    non-empty AND all CLOSED  → COMPLETED
    otherwise                 → ACTIVE

ON_HOLD is manual-only: aggregation does not override it.
"""

from __future__ import annotations

import pytest

from app.models import ActStatus, ProjectStatus
from app.services.project_status_service import ProjectStatusService


@pytest.mark.parametrize(
    ("current", "act_statuses", "expected"),
    [
        # ON_HOLD is preserved regardless of acts
        (ProjectStatus.ON_HOLD, [], ProjectStatus.ON_HOLD),
        (ProjectStatus.ON_HOLD, [ActStatus.CLOSED, ActStatus.CLOSED], ProjectStatus.ON_HOLD),
        (ProjectStatus.ON_HOLD, [ActStatus.ATTENTION], ProjectStatus.ON_HOLD),
        # all closed → completed
        (ProjectStatus.ACTIVE, [ActStatus.CLOSED], ProjectStatus.COMPLETED),
        (ProjectStatus.ACTIVE, [ActStatus.CLOSED] * 5, ProjectStatus.COMPLETED),
        # any attention beats mixed
        (ProjectStatus.ACTIVE, [ActStatus.CLOSED, ActStatus.ATTENTION], ProjectStatus.ATTENTION),
        (ProjectStatus.ACTIVE, [ActStatus.ATTENTION], ProjectStatus.ATTENTION),
        (
            ProjectStatus.ACTIVE,
            [ActStatus.NOT_SENT, ActStatus.WAITING_SIGNATURE, ActStatus.ATTENTION],
            ProjectStatus.ATTENTION,
        ),
        # mixed in-flight without attention → active
        (
            ProjectStatus.ACTIVE,
            [ActStatus.WAITING_SIGNATURE, ActStatus.NOT_SENT],
            ProjectStatus.ACTIVE,
        ),
        (
            ProjectStatus.ACTIVE,
            [ActStatus.CLOSED, ActStatus.WAITING_SIGNATURE],
            ProjectStatus.ACTIVE,
        ),
        # empty list of acts → active (no acts is not "all closed")
        (ProjectStatus.ACTIVE, [], ProjectStatus.ACTIVE),
        # status flips back when acts change
        (ProjectStatus.COMPLETED, [ActStatus.WAITING_SIGNATURE], ProjectStatus.ACTIVE),
        (ProjectStatus.ATTENTION, [ActStatus.CLOSED, ActStatus.CLOSED], ProjectStatus.COMPLETED),
    ],
    ids=lambda v: repr(v),
)
def test_aggregate(
    current: ProjectStatus,
    act_statuses: list[ActStatus],
    expected: ProjectStatus,
) -> None:
    result = ProjectStatusService.aggregate(
        current_status=current,
        act_statuses=act_statuses,
    )
    assert result == expected
