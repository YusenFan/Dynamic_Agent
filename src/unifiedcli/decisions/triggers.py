"""Evaluate decision gate trigger conditions."""

from __future__ import annotations

from unifiedcli.models.decision import DecisionTrigger
from unifiedcli.models.task import TaskNode, TaskType


def evaluate_triggers(node: TaskNode, confidence: float = 1.0) -> list[DecisionTrigger]:
    """Determine which decision triggers apply to a task node."""
    triggers: list[DecisionTrigger] = []

    if node.decision_gate:
        triggers.append(DecisionTrigger.IRREVERSIBLE_ACTION)

    if not node.reversible:
        triggers.append(DecisionTrigger.IRREVERSIBLE_ACTION)

    if node.task_type == TaskType.DECISION:
        triggers.append(DecisionTrigger.MULTIPLE_TRADEOFFS)

    if node.task_type == TaskType.DEPLOY:
        triggers.append(DecisionTrigger.PUBLIC_EXPOSURE)

    # Check for auth-related inputs
    if any("vault://" in inp for inp in node.inputs):
        triggers.append(DecisionTrigger.EXTERNAL_AUTHORIZATION)

    if confidence < 0.6:
        triggers.append(DecisionTrigger.LOW_CONFIDENCE)

    # Deduplicate
    return list(set(triggers))
