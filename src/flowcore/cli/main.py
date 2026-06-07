# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

import typer
import json
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from .client import FlowcoreClient

app = typer.Typer(help="Flowcore CLI - Distributed Workflow Engine")
console = Console()

def get_status_color(status: str) -> str:
    colors = {
        "COMPLETED": "green",
        "FAILED": "red",
        "COMPENSATED": "yellow",
        "RUNNING": "blue",
        "PENDING": "cyan",
        "COMPENSATING": "magenta"
    }
    return colors.get(status.upper(), "white")

@app.command()
def run(
    workflow_name: str = typer.Argument(..., help="Name of the workflow to run"),
    version: Optional[str] = typer.Option(None, "--version", "-v", help="Specific version to run"),
    tenant: str = typer.Option("default", "--tenant", "-t", help="Tenant ID"),
    context: str = typer.Option("{}", "--context", "-c", help="JSON string for the workflow context"),
    host: str = typer.Option("http://localhost:8000", "--host", help="Flowcore API host")
):
    """Start a new workflow execution."""
    try:
        ctx_dict = json.loads(context)
    except json.JSONDecodeError:
        rprint("[red]Error: Context must be a valid JSON string.[/red]")
        raise typer.Exit(1)

    client = FlowcoreClient(host, tenant_id=tenant)
    result = client.run_workflow(workflow_name, ctx_dict, version=version)

    if result.get("error") and "execution_id" not in result:
        rprint(f"[red]Error: {result['error']}[/red]")
        raise typer.Exit(1)

    table = Table(title=f"Workflow Started: {workflow_name}")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="magenta")
    
    table.add_row("Execution ID", str(result.get("execution_id")))
    table.add_row("Status", result.get("status"))
    table.add_row("Tenant", tenant)
    if version:
        table.add_row("Version", version)
    
    console.print(table)

@app.command()
def status(
    execution_id: int = typer.Argument(..., help="ID of the execution to check"),
    tenant: str = typer.Option("default", "--tenant", "-t", help="Tenant ID"),
    host: str = typer.Option("http://localhost:8000", "--host", help="Flowcore API host")
):
    """Get the status of a specific workflow execution."""
    client = FlowcoreClient(host, tenant_id=tenant)
    result = client.get_status(execution_id)

    if result.get("error") and "id" not in result:
        rprint(f"[red]Error: {result['error']}[/red]")
        raise typer.Exit(1)

    table = Table(title=f"Execution Status: {execution_id}")
    table.add_column("Field", style="cyan")
    table.add_column("Value")
    
    table.add_row("Workflow", result.get("workflow_name"))
    
    status = result.get("status", "UNKNOWN")
    table.add_row("Status", f"[{get_status_color(status)}]{status}[/]")
    
    table.add_row("Started At", result.get("started_at"))
    table.add_row("Completed At", str(result.get("completed_at") or "-"))
    
    if result.get("error"):
        table.add_row("Error", f"[red]{result.get('error')}[/red]")

    console.print(table)

@app.command(name="list")
def list_executions(
    limit: int = typer.Option(20, "--limit", "-l", help="Number of executions to show"),
    tenant: str = typer.Option("default", "--tenant", "-t", help="Tenant ID"),
    host: str = typer.Option("http://localhost:8000", "--host", help="Flowcore API host")
):
    """List recent workflow executions."""
    client = FlowcoreClient(host, tenant_id=tenant)
    results = client.list_executions(limit)

    if isinstance(results, dict) and "error" in results:
        rprint(f"[red]Error: {results['error']}[/red]")
        raise typer.Exit(1)

    table = Table(title=f"Recent Executions (limit: {limit}, tenant: {tenant})")
    table.add_column("ID", style="cyan")
    table.add_column("Workflow", style="magenta")
    table.add_column("Status")
    table.add_column("Started At")

    for exec_data in results:
        status = exec_data.get("status", "UNKNOWN")
        table.add_row(
            str(exec_data.get("id")),
            exec_data.get("workflow_name"),
            f"[{get_status_color(status)}]{status}[/]",
            exec_data.get("started_at")
        )

    console.print(table)

@app.command()
def workflows(
    host: str = typer.Option("http://localhost:8000", "--host", help="Flowcore API host")
):
    """List all registered workflows."""
    client = FlowcoreClient(host)
    results = client.list_workflows()

    if isinstance(results, dict) and "error" in results:
        rprint(f"[red]Error: {results['error']}[/red]")
        raise typer.Exit(1)

    table = Table(title="Registered Workflows")
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="magenta")
    table.add_column("Description")

    for wf in results:
        table.add_row(
            wf.get("name"),
            wf.get("version"),
            wf.get("description") or "-"
        )

    console.print(table)

if __name__ == "__main__":
    app()
