"""Aggregated project status derived from the statuses of its acts."""

from __future__ import annotations

from collections.abc import Iterable

from app.models import ActStatus, ProjectStatus


class ProjectStatusService:
    """Computes the project status from its current status and its acts' statuses.

    ``ON_HOLD`` is a manual-only state: if the project is currently on hold,
    aggregation leaves it alone — auto-pricing must never override an explicit
    pause set by the manager.

    For non-paused projects:

    * any act in ``ATTENTION`` → project is ``ATTENTION``
    * non-empty AND every act ``CLOSED`` → project is ``COMPLETED``
    * everything else → ``ACTIVE``
    """

    @staticmethod
    def aggregate(
        *,
        current_status: ProjectStatus,
        act_statuses: Iterable[ActStatus],
    ) -> ProjectStatus:
        if current_status is ProjectStatus.ON_HOLD:
            return ProjectStatus.ON_HOLD

        statuses = list(act_statuses)

        if any(s is ActStatus.ATTENTION for s in statuses):
            return ProjectStatus.ATTENTION

        if statuses and all(s is ActStatus.CLOSED for s in statuses):
            return ProjectStatus.COMPLETED

        return ProjectStatus.ACTIVE
