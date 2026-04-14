from datetime import datetime
import sqlite3

import typer
from typing import Optional, Any
from uuid import UUID
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

from task_manager_app.engine import ReconstructionEngine
from .models import Task, TaskStatus, EventType
from .database import TaskRepository

app = typer.Typer()
repo = TaskRepository()
console = Console()



def resolve_id(short_id: str) -> UUID:
    """Find a full UUID from a partial string prefix."""
    with repo._get_connection() as conn:
        # Search the view for any ID starting with the user's input
        res = conn.execute(
            "SELECT id FROM tasks_view WHERE id LIKE ?", 
            (f"{short_id}%",)
        ).fetchone()
    
    if not res:
        console.print(f"[bold red]Error:[/bold red] Parent ID '{short_id}' not found.")
        raise typer.Exit(1)
    
    return UUID(res[0])

@app.command()
def create(title: str, desc: str = "", parent: Optional[str] = None):
    """Create a new task (optionally as a child using a short or full ID)."""
    
    # NEW LOGIC: Resolve the ID if a parent is provided
    parent_uuid = resolve_id(parent) if parent else None
    
    task = Task(title=title, description=desc, parent_id=parent_uuid)
    repo.save_task(task, EventType.CREATED)
    
    console.print(f"[bold green]✔[/bold green] Task created: {task.title} (ID: {str(task.id)[:8]})")

# @app.command()
# def create(title: str, desc: str = "", parent: Optional[str] = None):
#     """Create a new task (optionally as a child)."""
#     parent_uuid = UUID(parent) if parent else None
#     task = Task(title=title, description=desc, parent_id=parent_uuid)
    
#     repo.save_task(task, EventType.CREATED)
#     console.print(f"[bold green]✔[/bold green] Task created: {task.title} (ID: {str(task.id)[:8]})")

@app.command()
def list():
    """List all tasks in their current state."""
    tasks = repo.list_tasks()
    table = Table(title="Current Tasks")
    table.add_column("ID", style="dim")
    table.add_column("Title")
    table.add_column("Status")
    table.add_column("Parent ID", style="blue")

    for row in tasks:
        table.add_row(row[0][:8], row[2], row[4], row[1][:8] if row[1] else "-")
    
    console.print(table)

@app.command()
def update(
    task_id: str, 
    status: TaskStatus = typer.Option(..., help="The new status: todo, in_progress, done"),
    title: Optional[str] = typer.Option(None, help="New title for the task"),
    desc: Optional[str] = typer.Option(None, "--desc", help="New description")
):
    """
    Update a task's status or details.
    This creates a new event in the history log.
    """
    # 1. Fetch current state to ensure the task exists
    with repo._get_connection() as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT data FROM tasks_view WHERE id LIKE ?", (f"{task_id}%",)).fetchone()
    
    if not row:
        console.print(f"[bold red]Error:[/bold red] Task with ID starting with '{task_id}' not found.")
        raise typer.Exit(1)

    # 2. Reconstruct the Pydantic model from the stored JSON
    current_task = Task.model_validate_json(row["data"])
    
    # 3. Apply updates
    current_task.status = status
    if title:
        current_task.title = title
    if desc:
        current_task.description = desc
    current_task.updated_at = datetime.now()

    # 4. Save via Repository (Triggers event log + view update)
    repo.save_task(current_task, EventType.UPDATED)
    
    console.print(f"[bold green]✔[/bold green] Task [bold]{str(current_task.id)[:8]}[/bold] updated to [blue]{status.value}[/blue].")


@app.command()
def history():
    """Show the event log and sequence numbers for time-travel."""
    with repo._get_connection() as conn:
        events = conn.execute("SELECT sequence, event_type, task_id, timestamp FROM events").fetchall()
    
    table = Table(title="Timeline Log")
    table.add_column("Seq", style="cyan")
    table.add_column("Event")
    table.add_column("Task ID")
    table.add_column("Time")

    for seq, etype, tid, ts in events:
        table.add_row(str(seq), etype, tid[:8], ts)
    
    console.print(table)

@app.command()
def travel(target_seq: int):
    """View the task list at a specific point in history."""
    with repo._get_connection() as conn:
        conn.row_factory = sqlite3.Row
        events = conn.execute("SELECT * FROM events ORDER BY sequence ASC").fetchall()
    
    # Use the engine to project the past
    past_state = ReconstructionEngine.project_state([dict(e) for e in events], target_seq)
    
    table = Table(title=f"State at Sequence {target_seq}")
    table.add_column("Title")
    table.add_column("Status")
    table.add_column("Parent")

    for task in past_state.values():
        parent_indicator = "↳ " if task.parent_id else ""
        table.add_row(f"{parent_indicator}{task.title}", task.status, str(task.parent_id)[:8] if task.parent_id else "-")
    
    console.print(table)



def display_task_tree(tasks: dict[UUID, Task], title: str):
    tree = Tree(f"[bold magenta]{title}[/bold magenta]")
    
    # Track nodes to avoid double-processing
    nodes = {tid: Tree(f"{t.title} [dim]({str(t.id)[:6]})[/dim] [{t.status}]") 
             for tid, t in tasks.items()}
    
    for tid, task in tasks.items():
        if task.parent_id and task.parent_id in nodes:
            nodes[task.parent_id].add(nodes[tid])
        else:
            # Root level task or orphaned child
            tree.add(nodes[tid])
            
    console.print(tree)   


@app.command()
def tree(seq: Optional[int] = typer.Option(None, "--seq", "-s")):
    """View the task hierarchy (optionally at a specific point in time)."""
    with repo._get_connection() as conn:
        conn.row_factory = sqlite3.Row
        events = conn.execute("SELECT * FROM events ORDER BY sequence ASC").fetchall()
    
    target = seq if seq is not None else repo.get_max_sequence()
    state = ReconstructionEngine.project_state([dict(e) for e in events], target)
    
    display_task_tree(state, f"Task Forest at Seq {target}")



@app.command()
def undo():
    """Step back in time without losing data."""
    repo.undo()
    console.print("[yellow]⏪ Undid last action. Use 'redo' to restore.[/yellow]")

@app.command()
def redo():
    """Step forward into the future."""
    repo.redo()
    console.print("[green]⏩ Redid the action.[/green]")