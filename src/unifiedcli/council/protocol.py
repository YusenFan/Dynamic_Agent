"""5-step deliberation protocol: plan → critique → respond → balance → update memory."""

from __future__ import annotations

import uuid

from unifiedcli.council.providers import LLMProvider
from unifiedcli.models.council import (
    ConsensusResult,
    CouncilRole,
    DeliberationRound,
    DeliberationStep,
    StepResult,
)


class DeliberationProtocol:
    """Executes the 5-step deliberation protocol across 3 LLM providers."""

    def __init__(
        self,
        planner: LLMProvider,
        critic: LLMProvider,
        balancer: LLMProvider,
    ) -> None:
        self.planner = planner
        self.critic = critic
        self.balancer = balancer

    async def run(self, topic: str, context: str = "") -> DeliberationRound:
        """Run a full deliberation round on the given topic."""
        round_id = f"round_{uuid.uuid4().hex[:8]}"
        dround = DeliberationRound(round_id=round_id, topic=topic)

        base_context = f"Topic: {topic}\n\nContext:\n{context}" if context else f"Topic: {topic}"

        # Step 1: Planner proposes
        plan_prompt = (
            f"{base_context}\n\n"
            "You are the Planner. Propose a detailed plan including task breakdown, "
            "dependencies, agent requirements, and execution strategy."
        )
        plan_response = await self.planner.generate(plan_prompt)
        dround.steps.append(StepResult(
            step=DeliberationStep.PLAN,
            role=CouncilRole.PLANNER,
            content=plan_response,
        ))

        # Step 2: Critic evaluates
        critique_prompt = (
            f"{base_context}\n\n"
            f"Planner's proposal:\n{plan_response}\n\n"
            "You are the Critic. Evaluate this plan. Identify missing dependencies, "
            "risks, unreasonable ordering, and potential failure points."
        )
        critique_response = await self.critic.generate(critique_prompt)
        dround.steps.append(StepResult(
            step=DeliberationStep.CRITIQUE,
            role=CouncilRole.CRITIC,
            content=critique_response,
        ))

        # Step 3: Planner responds to critique
        respond_prompt = (
            f"{base_context}\n\n"
            f"Your original plan:\n{plan_response}\n\n"
            f"Critic's feedback:\n{critique_response}\n\n"
            "You are the Planner. Respond to the critique — accept, reject, or modify "
            "your plan based on the feedback."
        )
        respond_response = await self.planner.generate(respond_prompt)
        dround.steps.append(StepResult(
            step=DeliberationStep.RESPOND,
            role=CouncilRole.PLANNER,
            content=respond_response,
        ))

        # Step 4: Balancer produces final consensus
        balance_prompt = (
            f"{base_context}\n\n"
            f"Planner's proposal:\n{plan_response}\n\n"
            f"Critic's feedback:\n{critique_response}\n\n"
            f"Planner's response:\n{respond_response}\n\n"
            "You are the Balancer. Synthesize the above into a final decision. "
            "Output a JSON object with keys: chosen_plan, rejected_plans, "
            "reasoning_summary, risks, agents_to_spawn, decision_gate_required, confidence."
        )
        balance_response = await self.balancer.generate(balance_prompt)
        dround.steps.append(StepResult(
            step=DeliberationStep.BALANCE,
            role=CouncilRole.BALANCER,
            content=balance_response,
        ))

        # Step 5: Parse consensus (best-effort JSON extraction)
        consensus = self._parse_consensus(balance_response)
        dround.consensus = consensus

        dround.steps.append(StepResult(
            step=DeliberationStep.UPDATE_MEMORY,
            role=CouncilRole.BALANCER,
            content="Memory update pending.",
        ))

        return dround

    def _parse_consensus(self, response: str) -> ConsensusResult:
        """Best-effort parse of balancer output into ConsensusResult."""
        import json
        # Try to extract JSON from the response
        try:
            # Look for JSON block
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(response[start:end])
                return ConsensusResult.model_validate(data)
        except (json.JSONDecodeError, Exception):
            pass
        # Fallback: treat entire response as the plan
        return ConsensusResult(
            chosen_plan=response,
            reasoning_summary="Could not parse structured consensus.",
            confidence=0.5,
        )
