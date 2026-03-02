from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from eleos.db.engine import session_scope
from eleos.db.models import PlaybookRow
from eleos.models.enums import PlaybookStatus


def resolve_latest_effective(case_class: str) -> PlaybookRow:
    with session_scope() as session:
        stmt = (
            select(PlaybookRow)
            .options(selectinload(PlaybookRow.steps))
            .where(
                PlaybookRow.status == PlaybookStatus.ACTIVE.value,
                PlaybookRow.applicable_case_classes.contains([case_class]),
            )
            .order_by(PlaybookRow.updated_at.desc())
        )
        row = session.scalars(stmt).first()

    if row is None:
        raise LookupError(f"no active playbook found for case_class={case_class}")
    return row
