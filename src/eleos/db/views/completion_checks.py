from __future__ import annotations

from eleos.db import state_cases, state_evidence
from eleos.db.views.mappers import to_evidence_view, to_mandatory_check_view
from eleos.db.views.models import CompletionCheckInputView
from eleos.models.ids import CaseId


def list_completion_check_inputs(case_id: CaseId) -> list[CompletionCheckInputView]:
    checks = state_cases.list_mandatory_checks(case_id)
    evidence_views = [to_evidence_view(row) for row in state_evidence.list_evidence(case_id)]
    return [
        CompletionCheckInputView(
            check=to_mandatory_check_view(check),
            evidence_records=list(evidence_views),
        )
        for check in checks
    ]
