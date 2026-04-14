# Input
I'm getting error when creating a Child Task. Here is the error:
  19 @app.command()                                                                                                                                                │
│    20 def create(title: str, desc: str = "", parent: Optional[str] = None):                                                                                         │
│    21 │   """Create a new task (optionally as a child)."""                                                                                                          │
│ ❱  22 │   parent_uuid = UUID(parent) if parent else None                                                                                                            │
│    23 │   task = Task(title=title, description=desc, parent_id=parent_uuid)                                                                                         │
│    24 │                                                                                                                                                             │
│    25 │   repo.save_task(task, EventType.CREATED)                                                                                                                   │
│                                                                                                                                                                     │
│ /usr/lib/python3.12/uuid.py:178 in __init__                                                                                                                         │
│                                                                                                                                                                     │
│   175 │   │   │   hex = hex.replace('urn:', '').replace('uuid:', '')                                                                                                │
│   176 │   │   │   hex = hex.strip('{}').replace('-', '')                                                                                                            │
│   177 │   │   │   if len(hex) != 32:                                                                                                                                │
│ ❱ 178 │   │   │   │   raise ValueError('badly formed hexadecimal UUID string')                                                                                      │
│   179 │   │   │   int = int_(hex, 16)                                                                                                                               │
│   180 │   │   if bytes_le is not None:                                                                                                                              │
│   181 │   │   │   if len(bytes_le) != 16:                                                                                                                           │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
ValueError: badly formed hexadecimal UUID string

# Output
The error `ValueError: badly formed hexadecimal UUID string` is happening because we are passing a "short ID" (like `a1b2c3d`) to the `UUID()` constructor, which strictly expects a full 36-character string.

As your Senior Engineer, I should have anticipated that users would want to use those convenient short IDs I provided in the UI! Let's fix the `create` command in `cli.py` to resolve the full UUID from the database before trying to create the child task.

### 🛠️ The Fix: Resolve Short IDs (`src/task_traveler/cli.py`)

We need to add a helper to look up the real UUID based on the prefix the user types in.

```python
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
```

---

### 🧪 Why this fixes it
1.  **User Convenience:** You can now type `uv run task-traveler create "Subtask" --parent a1b2`.
2.  **Validation:** The `resolve_id` function checks the database first. If you type a typo, it gives a clean error instead of a Python crash.
3.  **Type Safety:** It returns a proper `UUID` object that our `Task` model expects.

### 🚀 Try it again!
1. Run `uv run task-traveler list` to see your existing IDs.
2. Run your create command again using just the first 4 or 8 characters of the parent ID.

**Does the tree view correctly show the nesting now?**