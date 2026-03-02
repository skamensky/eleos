from __future__ import annotations

from eleos.db import state_cases, state_evidence, state_hypotheses, state_tasks
from eleos.db.views.mappers import to_hypothesis_view, to_task_view
from eleos.db.views.models import CriticInputView
from eleos.models.enums import Mode
from eleos.models.ids import CaseId


def build_critic_input(
    case_id: CaseId,
    *,
    max_iterations: int,
    novelty_floor: float,
) -> CriticInputView:
    case = state_cases.get_case_state(case_id)
    latest = state_evidence.latest_evidence(case_id)
    hypotheses = [to_hypothesis_view(row) for row in state_hypotheses.list_hypotheses(case_id)]
    tasks = [to_task_view(row) for row in state_tasks.list_tasks(case_id)]
    return CriticInputView(
        case_id=case_id,
        objective=case.objective,
        mode=Mode(case.mode),
        loop_count=case.loop_count,
        max_iterations=max_iterations,
        novelty_floor=novelty_floor * case.critic_depth_multiplier,
        last_novelty_signal=latest.novelty_signal if latest is not None else None,
        top_confidence=state_hypotheses.top_confidence_score(case_id),
        hypotheses=hypotheses,
        tasks=tasks,
    )
