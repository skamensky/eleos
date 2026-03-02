from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from eleos.settings.config import config

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def _require_dsn() -> str:
    dsn = config.persistence.dsn
    if not dsn:
        raise ValueError("Postgres DSN is required (ELEOS_PERSISTENCE__DSN)")
    return dsn


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(
            _require_dsn(),
            connect_args={"connect_timeout": config.persistence.connect_timeout_seconds},
            pool_pre_ping=True,
        )
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _session_factory


@contextmanager
def session_scope() -> Iterator[Session]:
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
