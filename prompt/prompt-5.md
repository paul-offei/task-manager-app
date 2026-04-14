# User Input:
yes continue with the next steps

# AI Response:
Excellent. Moving into the **Persistence Layer**, we need a repository that ensures every "write" is double-edged: it must append to the **Event Log** (the history) and update the **State View** (the current reality).

I'll implement a `TaskRepository` using a context manager to ensure atomic transactions. If the event fails to log, the task doesn't update—keeping our "time-travel" integrity 100% accurate.

---

### 🗄️ The Persistence Layer (`src/task_traveler/database.py`)

```python
import sqlite3
import json
from typing import List, Optional
from uuid import UUID
from .models import Task, TaskEvent, EventType, TaskStatus

class TaskRepository:
    def __init__(self, db_path: str = "tasks.db"):
        self.db_path = db_path
        self._bootstrap()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _bootstrap(self):
        """Initialize tables if they don't exist."""
        with self._get_connection() as conn:
            # Source of Truth: The Event Log
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Optimized View: The Current State
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks_view (
                    id TEXT PRIMARY KEY,
                    parent_id TEXT,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def save_task(self, task: Task, event_type: EventType):
        """
        Atomically saves a task and logs the event. 
        This is the heart of our collaborative history.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Log the Event
            payload = task.model_dump_json()
            cursor.execute(
                "INSERT INTO events (event_id, task_id, event_type, payload) VALUES (?, ?, ?, ?)",
                (str(task.id), str(task.id), event_type.value, payload)
            )
            
            # 2. Update the Materialized View
            cursor.execute("""
                INSERT OR REPLACE INTO tasks_view (id, parent_id, title, description, status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                str(task.id), 
                str(task.parent_id) if task.parent_id else None,
                task.title,
                task.description,
                task.status.value,
                task.updated_at.isoformat()
            ))

    def list_tasks(self) -> List[Task]:
        """Fetch all active tasks from the current state view."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM tasks_view")
            # In a real app, we'd map columns to the Task model properly
            rows = cursor.fetchall()
            # For brevity, returning titles for now; 
            # we'll build the full Pydantic mapper in the engine.
            return rows
```

---

### 🚦 The First "Real" CLI Loop (`src/task_traveler/cli.py`)

Now we tie the model and database together into the **Create, List, Update** commands.

```python
import typer
from rich.console import Console
from rich.table import Table
from .models import Task, TaskStatus, EventType
from .database import TaskRepository

app = typer.Typer()
repo = TaskRepository()
console = Console()

@app.command()
def create(title: str, desc: str = "", parent: Optional[str] = None):
    """Create a new task (optionally as a child)."""
    parent_uuid = UUID(parent) if parent else None
    task = Task(title=title, description=desc, parent_id=parent_uuid)
    
    repo.save_task(task, EventType.CREATED)
    console.print(f"[bold green]✔[/bold green] Task created: {task.title} (ID: {str(task.id)[:8]})")

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
def update(task_id: str, status: TaskStatus):
    """Update a task's status (Records a new history event)."""
    # Logic: Fetch current -> modify -> save
    # This will be refined in Iteration 3
    pass

if __name__ == "__main__":
    app()
```

---

### 🛡️ Why this works for the "Team Lead" requirements:
1.  **Collaborative-Ready:** Because we use an `events` table with an auto-incrementing `sequence`, if two users sync their databases, we can simply re-play the events in order to resolve conflicts.
2.  **Time-Travel Infrastructure:** The `sequence` in the `events` table *is* the slider. To "undo" to step 5, we just run `SELECT * FROM events WHERE sequence <= 5` and rebuild the view.
3.  **Parent-Child Safety:** The `tasks_view` explicitly tracks `parent_id`.

### 🚀 Next Step: The "Engine"
I'll implement the **Reconciliation Logic** in `engine.py`. This will handle the "key challenge" mentioned: when we slide time back, it will check if a child's parent still exists at that point in history.

**Should I proceed to the Engine implementation or add the `update` and `delete` command logic first?**