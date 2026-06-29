"""Pure computation of an act's status from its boolean flags and age."""

from __future__ import annotations

from datetime import date

from app.models import ActStatus


class ActStatusService:
    """Computes :class:`ActStatus` from the act's flags and payment age.

    The rules are applied in priority order (first match wins):

    * ``is_signed`` → ``CLOSED``
    * ``is_sent`` → ``WAITING_SIGNATURE``
    * ``age >= threshold_days`` (not sent, not signed) → ``ATTENTION``
    * otherwise → ``NOT_SENT``

    The function is pure: no I/O, no clock — ``today`` is injected. This makes
    it trivial to test and to call from any layer (services, seed, reports).
    """

    @staticmethod
    def compute(
        *,
        is_sent: bool,
        is_signed: bool,
        payment_date: date,
        today: date,
        threshold_days: int,
    ) -> ActStatus:
        if is_signed:
            return ActStatus.CLOSED

        if is_sent:
            return ActStatus.WAITING_SIGNATURE

        if ActStatusService._is_stale(payment_date, today, threshold_days):
            return ActStatus.ATTENTION

        return ActStatus.NOT_SENT

    @staticmethod
    def _is_stale(payment_date: date, today: date, threshold_days: int) -> bool:
        return (today - payment_date).days >= threshold_days
