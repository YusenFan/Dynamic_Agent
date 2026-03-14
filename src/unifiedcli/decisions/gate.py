"""DecisionGateEngine — build decision packets and prompt the user."""

from __future__ import annotations

import uuid

import click

from unifiedcli.decisions.triggers import evaluate_triggers
from unifiedcli.models.decision import (
    DecisionOption,
    DecisionPacket,
    DecisionTrigger,
    UserDecision,
)
from unifiedcli.models.task import TaskNode


class DecisionGateEngine:
    """Manages decision gates: builds packets, prompts user, returns decisions."""

    def build_packet(
        self,
        node: TaskNode,
        options: list[DecisionOption],
        recommended: str | None = None,
        confidence: float = 1.0,
    ) -> DecisionPacket:
        """Build a decision packet for a task node."""
        triggers = evaluate_triggers(node, confidence)
        trigger = triggers[0] if triggers else DecisionTrigger.MULTIPLE_TRADEOFFS
        return DecisionPacket(
            decision_id=f"dec_{uuid.uuid4().hex[:8]}",
            task_id=node.task_id,
            project_id=node.project_id,
            decision_topic=node.name,
            reason=node.description,
            trigger=trigger,
            options=options,
            recommended_option=recommended,
            reversibility="reversible" if node.reversible else "irreversible",
        )

    def prompt_user(self, packet: DecisionPacket) -> UserDecision:
        """Present the decision to the user via CLI and collect their choice."""
        click.echo(f"\n{'='*60}")
        click.echo(f"DECISION REQUIRED: {packet.decision_topic}")
        click.echo(f"Reason: {packet.reason}")
        click.echo(f"Trigger: {packet.trigger.value}")
        click.echo(f"{'='*60}")

        for i, opt in enumerate(packet.options, 1):
            marker = " (recommended)" if opt.option_id == packet.recommended_option else ""
            click.echo(f"\n  [{i}] {opt.label}{marker}")
            if opt.description:
                click.echo(f"      {opt.description}")
            if opt.pros:
                click.echo(f"      Pros: {', '.join(opt.pros)}")
            if opt.cons:
                click.echo(f"      Cons: {', '.join(opt.cons)}")

        click.echo()
        while True:
            choice = click.prompt("Choose an option (number)", type=int)
            if 1 <= choice <= len(packet.options):
                break
            click.echo(f"Please enter a number between 1 and {len(packet.options)}")

        selected = packet.options[choice - 1]
        notes = click.prompt("Any additional notes?", default="", show_default=False)

        return UserDecision(
            decision_id=packet.decision_id,
            chosen_option=selected.option_id,
            user_notes=notes,
        )
