from __future__ import annotations

from eleos.db import state_cases
from eleos.db.views.critic import build_critic_input
from eleos.db.views.models import CriticInputView
from eleos.llm.agents.base.structured_agent import StructuredAgent
from eleos.llm.agents.critic.agent import critic_agent
from eleos.models.agents.critic.models import CriticAssessment
from eleos.models.ids import CaseId
from eleos.settings.config import config

_critic_agent: StructuredAgent[CriticInputView, CriticAssessment] = critic_agent


def evaluate_critic(case_id: CaseId) -> CriticAssessment:
    payload: CriticInputView = build_critic_input(
        case_id,
        max_iterations=config.runtime.max_iterations,
        novelty_floor=config.runtime.thresholds.no_novelty_floor,
    )
    assessment = _critic_agent.run(payload)
    if payload.loop_count > config.runtime.max_iterations:
        return CriticAssessment(
            requires_replan=False,
            reason="loop_guard_exceeded",
            drift_score=assessment.drift_score,
            novelty_score=assessment.novelty_score,
        )
    return assessment


def reduce_critic_depth(case_id: CaseId) -> None:
    case = state_cases.get_case_state(case_id)
    case.critic_depth_multiplier = 1.5
    state_cases.save_case(case)
