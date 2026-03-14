"""CLI entry point for UnifiedCLI."""

from __future__ import annotations

import asyncio
from pathlib import Path

import click

from unifiedcli.adapters.vault import VaultManager
from unifiedcli.agents.main_agent import MainAgent
from unifiedcli.agents.skills import SkillManager
from unifiedcli.council.council import Council
from unifiedcli.council.providers import ClaudeProvider, GeminiProvider, OpenAIProvider
from unifiedcli.decisions.gate import DecisionGateEngine
from unifiedcli.workspace.project import ProjectManager
from unifiedcli.workspace.workspace import WorkspaceManager


def _prompt_api_keys(vault: VaultManager) -> None:
    """Prompt the user for all 3 council model API keys and store in vault."""
    click.echo("\nThe AI Council requires API keys for 3 models:")
    click.echo("  - Claude (Planner)")
    click.echo("  - Gemini (Critic)")
    click.echo("  - OpenAI (Balancer)\n")

    claude_key = click.prompt("Claude API key", hide_input=True)
    vault.store("claude", "api_key", claude_key)
    click.echo("  Stored as vault://claude/api_key")

    gemini_key = click.prompt("Gemini API key", hide_input=True)
    vault.store("gemini", "api_key", gemini_key)
    click.echo("  Stored as vault://gemini/api_key")

    openai_key = click.prompt("OpenAI API key", hide_input=True)
    vault.store("openai", "api_key", openai_key)
    click.echo("  Stored as vault://openai/api_key")

    click.echo("\nAll API keys stored securely in vault.")


def _check_api_keys(vault: VaultManager) -> bool:
    """Check if all 3 API keys are configured."""
    return (
        vault.has_secret("vault://claude/api_key")
        and vault.has_secret("vault://gemini/api_key")
        and vault.has_secret("vault://openai/api_key")
    )


def _build_council(vault: VaultManager) -> Council:
    """Build the 3-model council from vault-stored API keys."""
    planner = ClaudeProvider(api_key=vault.resolve("vault://claude/api_key"))
    critic = GeminiProvider(api_key=vault.resolve("vault://gemini/api_key"))
    balancer = OpenAIProvider(api_key=vault.resolve("vault://openai/api_key"))
    return Council(planner, critic, balancer)


def _build_main_agent(
    project: ProjectManager,
    vault: VaultManager,
    skills_dir: Path | None = None,
) -> MainAgent:
    """Build a fully wired MainAgent with council, scheduler, and skills."""
    council = _build_council(vault)
    agent = MainAgent(project, council)
    if skills_dir and skills_dir.exists():
        skill_manager = SkillManager(skills_dir)
        agent.scheduler.skill_manager = skill_manager
    return agent


@click.group()
@click.option(
    "--workspace", "-w",
    default=".",
    type=click.Path(),
    help="Workspace directory (default: current directory)",
)
@click.pass_context
def cli(ctx: click.Context, workspace: str) -> None:
    """UnifiedCLI — Multi-agent AI execution system."""
    ctx.ensure_object(dict)
    ctx.obj["workspace_path"] = Path(workspace).resolve()


@cli.command()
@click.pass_context
def init(ctx: click.Context) -> None:
    """Initialize a new workspace and configure API keys."""
    ws_path = ctx.obj["workspace_path"]
    wm = WorkspaceManager(ws_path)
    config = wm.initialize()
    click.echo(f"Workspace initialized at {ws_path}")
    click.echo(f"Workspace ID: {config.workspace_id}")

    _prompt_api_keys(wm.vault)


@cli.command()
@click.argument("goal")
@click.option("--name", "-n", default="", help="Project name")
@click.pass_context
def new(ctx: click.Context, goal: str, name: str) -> None:
    """Create a new project from a natural language goal and start execution."""
    ws_path = ctx.obj["workspace_path"]
    wm = WorkspaceManager(ws_path)

    try:
        wm.load()
    except FileNotFoundError:
        click.echo("No workspace found. Initializing...")
        wm.initialize()
        _prompt_api_keys(wm.vault)

    # Check API keys
    if not _check_api_keys(wm.vault):
        click.echo("\nAPI keys not configured. Please provide them now.")
        _prompt_api_keys(wm.vault)

    import uuid
    project_id = name or f"project_{uuid.uuid4().hex[:8]}"
    project_path = wm.project_path(project_id)
    pm = ProjectManager(project_path)
    config = pm.create(project_id=project_id, goal=goal, name=project_id)

    click.echo(f"\nProject created: {config.project_id}")
    click.echo(f"Goal: {goal}")
    click.echo(f"Path: {project_path}")

    # Build and run the main agent
    skills_dir = Path(__file__).parent / ".agents" / "skills"
    agent = _build_main_agent(pm, wm.vault, skills_dir)

    click.echo("\nStarting AI Council deliberation...")
    click.echo("  Planner (Claude) -> Critic (Gemini) -> Balancer (OpenAI)\n")

    asyncio.run(_run_project(agent, goal))


@cli.command()
@click.argument("project_id", required=False)
@click.pass_context
def status(ctx: click.Context, project_id: str | None) -> None:
    """Show workspace or project status."""
    ws_path = ctx.obj["workspace_path"]
    wm = WorkspaceManager(ws_path)

    try:
        wm.load()
    except FileNotFoundError:
        click.echo("No workspace found. Run 'unifiedcli init' first.")
        return

    if project_id:
        project_path = wm.project_path(project_id)
        pm = ProjectManager(project_path)
        try:
            config = pm.load()
            click.echo(f"Project: {config.project_id}")
            click.echo(f"Status: {config.status.value}")
            click.echo(f"Goal: {config.goal}")
            graph = pm.graph
            nodes = graph.nodes
            click.echo(f"Tasks: {len(nodes)}")
            for node in nodes.values():
                click.echo(f"  [{node.status.value}] {node.task_id}: {node.name}")
        except FileNotFoundError:
            click.echo(f"Project '{project_id}' not found.")
    else:
        projects = wm.list_projects()
        click.echo(f"Workspace: {ws_path}")
        click.echo(f"Projects: {len(projects)}")
        for pid in projects:
            click.echo(f"  - {pid}")

        # Show API key status
        keys_ok = _check_api_keys(wm.vault)
        click.echo(f"API Keys: {'configured' if keys_ok else 'not configured'}")


@cli.command()
@click.argument("project_id")
@click.pass_context
def resume(ctx: click.Context, project_id: str) -> None:
    """Resume execution of an existing project."""
    ws_path = ctx.obj["workspace_path"]
    wm = WorkspaceManager(ws_path)

    try:
        wm.load()
    except FileNotFoundError:
        click.echo("No workspace found.")
        return

    if not _check_api_keys(wm.vault):
        click.echo("API keys not configured. Please provide them now.")
        _prompt_api_keys(wm.vault)

    project_path = wm.project_path(project_id)
    pm = ProjectManager(project_path)
    try:
        config = pm.load()
    except FileNotFoundError:
        click.echo(f"Project '{project_id}' not found.")
        return

    click.echo(f"Resuming project: {project_id}")
    click.echo(f"Goal: {config.goal}")

    skills_dir = Path(__file__).parent / ".agents" / "skills"
    agent = _build_main_agent(pm, wm.vault, skills_dir)

    click.echo("\nResuming AI Council execution...")
    click.echo("  Planner (Claude) -> Critic (Gemini) -> Balancer (OpenAI)\n")

    asyncio.run(_resume_project(agent))


@cli.command(name="list")
@click.pass_context
def list_projects(ctx: click.Context) -> None:
    """List all projects in the workspace."""
    ws_path = ctx.obj["workspace_path"]
    wm = WorkspaceManager(ws_path)

    try:
        wm.load()
    except FileNotFoundError:
        click.echo("No workspace found. Run 'unifiedcli init' first.")
        return

    projects = wm.list_projects()
    if not projects:
        click.echo("No projects found.")
    else:
        for pid in projects:
            click.echo(pid)


@cli.command()
@click.pass_context
def configure(ctx: click.Context) -> None:
    """Update API keys for the AI Council."""
    ws_path = ctx.obj["workspace_path"]
    wm = WorkspaceManager(ws_path)

    try:
        wm.load()
    except FileNotFoundError:
        click.echo("No workspace found. Run 'unifiedcli init' first.")
        return

    _prompt_api_keys(wm.vault)


async def _run_project(agent: MainAgent, goal: str) -> None:
    """Run the full project lifecycle: intake -> plan -> execute -> verify."""
    # Intake
    click.echo("[INTAKE] Parsing goal and initializing memory...")
    await agent.intake(goal)
    click.echo(f"  State: {agent.state.value}")

    # Planning via council deliberation
    click.echo("[PLANNING] Council deliberating on task graph...")
    try:
        await agent.plan()
        click.echo(f"  State: {agent.state.value}")
        click.echo(f"  Tasks in graph: {len(agent.graph.nodes)}")
    except Exception as e:
        click.echo(f"  Council deliberation error: {e}")
        click.echo("  (The council requires valid API keys for all 3 providers)")
        return

    # Execute
    if agent.graph.nodes:
        click.echo("[EXECUTING] Running scheduler loop...")
        await agent.execute_loop()
        click.echo(f"  State: {agent.state.value}")

    # Verify
    click.echo("[VERIFYING] Checking results...")
    success = await agent.verify_and_finish()
    click.echo(f"  State: {agent.state.value}")
    click.echo(f"  Result: {'SUCCESS' if success else 'INCOMPLETE'}")


async def _resume_project(agent: MainAgent) -> None:
    """Resume execution from current graph state."""
    pending = [n for n in agent.graph.nodes.values() if n.status.value in ("pending", "ready")]
    click.echo(f"  Pending tasks: {len(pending)}")

    if not pending and not agent.graph.nodes:
        click.echo("  No tasks to execute. Run planning first.")
        return

    click.echo("[EXECUTING] Resuming scheduler loop...")
    await agent.execute_loop()
    click.echo(f"  State: {agent.state.value}")

    click.echo("[VERIFYING] Checking results...")
    success = await agent.verify_and_finish()
    click.echo(f"  State: {agent.state.value}")
    click.echo(f"  Result: {'SUCCESS' if success else 'INCOMPLETE'}")


if __name__ == "__main__":
    cli()
