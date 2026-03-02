from datetime import datetime, timedelta, timezone

from pydantic import BaseModel

from eleos.models.enums import Mode, PlaybookPolicy


class InvestigationRequest(BaseModel):
    objective: str
    mode: Mode = Mode.DEEP_INVESTIGATION
    playbook_policy: PlaybookPolicy = PlaybookPolicy.SUGGESTIVE
    timeout_minutes: int = 120


def build_timeout(timeout_minutes: int) -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=timeout_minutes)
