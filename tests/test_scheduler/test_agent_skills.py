"""Tests for skill-based agent spawning.

When a subagent is dynamically created, it should:
1. Always receive the 3 basic skills (find-skills, browser-use, skill-creator)
2. Get additional skills matched by task description and spawn reason
3. Have a descriptive spawn_reason (not just a task_id reference)
"""

import pytest
from pathlib import Path

from unifiedcli.agents.runtime import AgentLifecycleManager
from unifiedcli.agents.skills import SkillManager, SkillInfo, _parse_skill_md
from unifiedcli.graph.engine import TaskGraphEngine
from unifiedcli.models.task import (
    TaskNode, TaskType, TaskStatus,
    ExecutorRequirement, SpawnPolicy, ArtifactContract,
)
from unifiedcli.scheduler.scheduler import Scheduler, _build_spawn_reason

# Path to the real skills directory in the project
SKILLS_DIR = Path(__file__).resolve().parents[2] / "src" / "unifiedcli" / ".agents" / "skills"


class TestSkillManager:
    def test_scan_finds_basic_skills(self) -> None:
        sm = SkillManager(SKILLS_DIR)
        basic = sm.get_basic_skills()
        names = [s.name for s in basic]
        assert "find-skills" in names
        assert "browser-use" in names
        assert "skill-creator" in names

    def test_get_skill(self) -> None:
        sm = SkillManager(SKILLS_DIR)
        skill = sm.get_skill("find-skills")
        assert skill is not None
        assert skill.is_basic is True
        assert "discover" in skill.description.lower()

    def test_list_all(self) -> None:
        sm = SkillManager(SKILLS_DIR)
        all_skills = sm.list_all()
        assert len(all_skills) >= 3

    def test_install_for_agent_always_includes_basic(self) -> None:
        sm = SkillManager(SKILLS_DIR)
        installed = sm.install_for_agent(
            task_description="do something random",
            spawn_reason="just testing",
        )
        assert "find-skills" in installed
        assert "browser-use" in installed
        assert "skill-creator" in installed

    def test_match_skills_no_false_positives(self) -> None:
        sm = SkillManager(SKILLS_DIR)
        # A task with no meaningful overlap should not match non-basic skills
        matched = sm.match_skills(
            task_description="cook dinner",
            spawn_reason="hungry agent",
        )
        assert len(matched) == 0

    def test_nonexistent_dir(self) -> None:
        sm = SkillManager(Path("/nonexistent/skills"))
        assert sm.get_basic_skills() == []
        assert sm.list_all() == []


class TestSkillMdParsing:
    def test_parse_valid(self) -> None:
        info = _parse_skill_md(SKILLS_DIR / "find-skills" / "SKILL.md")
        assert info is not None
        assert info.name == "find-skills"
        assert info.description != ""

    def test_parse_browser_use(self) -> None:
        info = _parse_skill_md(SKILLS_DIR / "browser-use" / "SKILL.md")
        assert info is not None
        assert info.name == "browser-use"
        assert "browse" in info.description.lower()


class TestBuildSpawnReason:
    def test_includes_task_name_and_type(self) -> None:
        task = TaskNode(
            task_id="task_deploy_01",
            project_id="p",
            name="Deploy Demo to Vercel",
            task_type=TaskType.DEPLOY,
            description="Deploy the generated web demo to Vercel hosting platform",
            executor_requirement=ExecutorRequirement(
                agent_type="hosting_agent",
                capability_tags=["hosting", "deployment"],
            ),
            artifact_contract=ArtifactContract(expected_outputs=["deployment_url"]),
        )
        reason = _build_spawn_reason(task)
        assert "Deploy Demo to Vercel" in reason
        assert "deploy" in reason.lower()
        assert "hosting" in reason
        assert "deployment_url" in reason
        assert "task_deploy_01" not in reason  # Should NOT just be a task_id

    def test_minimal_task(self) -> None:
        task = TaskNode(
            task_id="t1", project_id="p",
            name="Simple Task", task_type=TaskType.BUILD,
        )
        reason = _build_spawn_reason(task)
        assert "Simple Task" in reason
        assert "build" in reason.lower()


@pytest.mark.asyncio
async def test_spawn_installs_skills(tmp_path: Path) -> None:
    """Full integration: scheduler spawns agent with skills installed."""
    engine = TaskGraphEngine()
    engine.add_node(TaskNode(
        task_id="research_task",
        project_id="p",
        name="Research hosting platforms",
        task_type=TaskType.RESEARCH,
        description="Research and compare hosting platforms for web demo deployment",
        executor_requirement=ExecutorRequirement(
            agent_type="research_agent",
            capability_tags=["research", "hosting"],
        ),
        spawn_policy=SpawnPolicy(spawn_if_missing=True, reuse_existing_if_match=True),
    ))

    lifecycle = AgentLifecycleManager(tmp_path / "agents")
    skill_manager = SkillManager(SKILLS_DIR)
    scheduler = Scheduler(engine, lifecycle, skill_manager=skill_manager)

    dispatched = await scheduler.tick()
    assert len(dispatched) == 1

    # Check the spawned agent
    active = lifecycle.list_active(project_id="p")
    assert len(active) == 1
    agent = active[0]

    # Basic skills are always installed
    assert "find-skills" in agent.spec.installed_skills
    assert "browser-use" in agent.spec.installed_skills
    assert "skill-creator" in agent.spec.installed_skills

    # Spawn reason is descriptive, not just a task_id
    assert "Research hosting platforms" in agent.spec.spawn_reason
    assert "research" in agent.spec.spawn_reason.lower()
    assert "task_id" not in agent.spec.spawn_reason


@pytest.mark.asyncio
async def test_spawn_without_skill_manager(tmp_path: Path) -> None:
    """Scheduler still works without a SkillManager (backward compat)."""
    engine = TaskGraphEngine()
    engine.add_node(TaskNode(
        task_id="t1", project_id="p", name="Build it",
        task_type=TaskType.BUILD,
        executor_requirement=ExecutorRequirement(
            agent_type="build_agent", capability_tags=["build"],
        ),
        spawn_policy=SpawnPolicy(),
    ))

    lifecycle = AgentLifecycleManager(tmp_path / "agents")
    scheduler = Scheduler(engine, lifecycle)  # no skill_manager

    dispatched = await scheduler.tick()
    assert len(dispatched) == 1

    agent = lifecycle.list_active(project_id="p")[0]
    assert agent.spec.installed_skills == []
    # spawn_reason is still descriptive even without skills
    assert "Build it" in agent.spec.spawn_reason
