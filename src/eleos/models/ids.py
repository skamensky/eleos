from typing import NewType
from uuid import uuid4

CaseId = NewType("CaseId", str)
HypothesisId = NewType("HypothesisId", str)


def new_case_id() -> CaseId:
    return CaseId(str(uuid4()))


def as_case_id(value: str) -> CaseId:
    return CaseId(value)


def as_hypothesis_id(value: str) -> HypothesisId:
    return HypothesisId(value)
