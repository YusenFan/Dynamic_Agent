"""CLI entry point for UnifiedCLI."""

from __future__ import annotations

import asyncio
from pathlib import Path

import click

from unifiedcli.workspace.workspace import WorkspaceManager
from unifiedcli.workspace.project import ProjectManager


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
    """Initialize a new workspace."""
    ws_path = ctx.obj["workspace_path"]
    wm = WorkspaceManager(ws_path)
    config = wm.initialize()
    click.echo(f"Workspace initialized at {ws_path}")
    click.echo(f"Workspace ID: {config.workspace_id}")


@cli.command()
@click.argument("goal")
@click.option("--name", "-n", default="", help="Project name")
@click.pass_context
def new(ctx: click.Context, goal: str, name: str) -> None:
    """Create a new project from a natural language goal."""
    ws_path = ctx.obj["workspace_path"]
    wm = WorkspaceManager(ws_path)

    try:
        wm.load()
    except FileNotFoundError:
        click.echo("No workspace found. Initializing...")
        wm.initialize()

    import uuid
    project_id = name or f"project_{uuid.uuid4().hex[:8]}"
    project_path = wm.project_path(project_id)
    pm = ProjectManager(project_path)
    config = pm.create(project_id=project_id, goal=goal, name=project_id)

    click.echo(f"Project created: {config.project_id}")
    click.echo(f"Goal: {goal}")
    click.echo(f"Path: {project_path}")
    click.echo("\nShared memory initialized with 6 slots.")
    click.echo("Run 'unifiedcli status' to check project state.")


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

    project_path = wm.project_path(project_id)
    pm = ProjectManager(project_path)
    try:
        pm.load()
        click.echo(f"Resuming project: {project_id}")
        click.echo("(Council and scheduler would start here with real LLM providers)")
    except FileNotFoundError:
        click.echo(f"Project '{project_id}' not found.")


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


if __name__ == "__main__":
    cli()
