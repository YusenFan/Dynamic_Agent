"""Tests for decision trigger evaluation."""

from unifiedcli.decisions.triggers import evaluate_triggers
from unifiedcli.models.decision import DecisionTrigger
from unifiedcli.models.task import TaskNode, TaskType


class TestTriggers:
    def test_decision_gate_flag(self) -> None:
        node = TaskNode(
            task_id="t1", project_id="p", name="Test",
            task_type=TaskType.BUILD, decision_gate=True,
        )
        triggers = evaluate_triggers(node)
        assert DecisionTrigger.IRREVERSIBLE_ACTION in triggers

    def test_irreversible(self) -> None:
        node = TaskNode(
            task_id="t1", project_id="p", name="Test",
            task_type=TaskType.DEPLOY, reversible=False,
        )
        triggers = evaluate_triggers(node)
        assert DecisionTrigger.IRREVERSIBLE_ACTION in triggers
        assert DecisionTrigger.PUBLIC_EXPOSURE in triggers

    def test_low_confidence(self) -> None:
        node = TaskNode(
            task_id="t1", project_id="p", name="Test",
            task_type=TaskType.BUILD,
        )
        triggers = evaluate_triggers(node, confidence=0.3)
        assert DecisionTrigger.LOW_CONFIDENCE in triggers

    def test_vault_auth(self) -> None:
        node = TaskNode(
            task_id="t1", project_id="p", name="Test",
            task_type=TaskType.CONFIGURE,
            inputs=["vault://vercel/token"],
        )
        triggers = evaluate_triggers(node)
        assert DecisionTrigger.EXTERNAL_AUTHORIZATION in triggers
