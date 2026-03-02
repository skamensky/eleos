from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from eleos.db.engine import get_engine
from eleos.db.models import CaseRunRow
from eleos.logging.logger import get_logger
from eleos.models.enums import LogEvent
from eleos.settings.config import config

logger = get_logger(__name__)
_initialized = False


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def initialize() -> None:
    global _initialized
    if _initialized:
        return
    get_engine()
    logger.info(
        LogEvent.AUDIT_PERSISTENCE_INITIALIZED.value,
        backend="sqlalchemy",
        schema=config.persistence.db_schema,
    )
    _initialized = True


def lock_case_row(session: Session, case_id: str) -> None:
    locked = session.execute(
        select(CaseRunRow.case_id)
        .where(CaseRunRow.case_id == case_id)
        .with_for_update()
    ).scalar_one_or_none()
    if locked is None:
        raise KeyError(f"case not found: {case_id}")
