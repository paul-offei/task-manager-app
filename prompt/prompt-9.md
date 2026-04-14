# User Input:
Yes Let focus on the Undo/redo functionality.  know and consider this before refining it:
Undoing a parent must not corrupt state and You must define and implement a consistent strategy:
- delete children
- detach them
- mark invalid  

# AI Response:
To handle **Undo/Redo** in a collaborative environment without corrupting the state, we must move away from `DELETE` operations. If we delete a row, we lose the "Redo" data and the "Audit" trail.

### 🛡️ The Strategy: Temporal Masking (Detach & Invalidate)

When a parent is "undone" (i.e., we move the time-slider to a point before the parent was created), we will implement a **Temporal Masking** strategy:

1.  **Detach**: Children are preserved in the history but logically "orphaned" in the view if their parent is missing.
2.  **Invalidate**: Instead of deleting events, we add an `is_undone` column to the `events` table.
3.  **Redo Support**: To "Redo," we simply flip the `is_undone` flag back.

---

### 🗄️ 1. Database Schema Update (`database.py`)

We need to add a `status` or `is_undone` flag to our events.

```python
def _bootstrap(self):
    with self._get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL,
                task_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_undone INTEGER DEFAULT 0  -- 0 = Active, 1 = Undone
            )
        """)
        # ... tasks_view stays the same ...
```

---

### 🧠 2. The Reconciliation Engine Logic (`engine.py`)

The engine must now ignore events marked as undone. This naturally handles parent-child corruption: if a parent's creation event is "undone," the engine simply won't see it, and any child task referencing that `parent_id` will be **Detached** (rendered at the root level).

```python
class ReconstructionEngine:
    @staticmethod
    def project_state(events: List[dict]) -> Dict[UUID, Task]:
        tasks: Dict[UUID, Task] = {}

        # 1. Replay only active events
        active_events = [e for e in events if not e.get("is_undone")]
        
        for event in active_events:
            task_id = UUID(event["task_id"])
            payload = json.loads(event["payload"])
            
            if event["event_type"] == "task_created":
                tasks[task_id] = Task.model_validate(payload)
            elif event["event_type"] == "task_updated":
                if task_id in tasks:
                    tasks[task_id] = Task.model_validate({**tasks[task_id].model_dump(), **payload})

        # 2. Strategy: DETACH Children
        for task in tasks.values():
            if task.parent_id and task.parent_id not in tasks:
                task.parent_id = None  # Detach orphan from non-existent parent
        
        return tasks
```

---

### ⏪ 3. Implementation: Undo/Redo (`database.py`)

We manipulate the `is_undone` flag based on the current "HEAD" of the sequence.

```python
class TaskRepository:
    def undo(self):
        """Mark the latest active event as undone."""
        with self._get_connection() as conn:
            # Find the highest sequence that isn't undone
            res = conn.execute(
                "SELECT sequence FROM events WHERE is_undone = 0 ORDER BY sequence DESC LIMIT 1"
            ).fetchone()
            
            if res:
                conn.execute("UPDATE events SET is_undone = 1 WHERE sequence = ?", (res[0],))
                self.rebuild_materialized_view()

    def redo(self):
        """Mark the earliest undone event as active again."""
        with self._get_connection() as conn:
            # Find the lowest sequence that IS undone
            res = conn.execute(
                "SELECT sequence FROM events WHERE is_undone = 1 ORDER BY sequence ASC LIMIT 1"
            ).fetchone()
            
            if res:
                conn.execute("UPDATE events SET is_undone = 0 WHERE sequence = ?", (res[0],))
                self.rebuild_materialized_view()
```

---

### 🚀 4. CLI Integration (`cli.py`)

```python
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
```

---

### ⚖️ Why this is a "Senior" approach:

* **Non-Destructive**: We never `DELETE`. This is crucial for collaborative tools where another user might need to see the history of why a task disappeared.
* **State Integrity**: By detaching children in the `ReconstructionEngine` rather than deleting them from the DB, we ensure that if the user "Redoes" the parent creation, the child's `parent_id` link is instantly restored.
* **Consistency**: The "Source of Truth" (Event Log) remains an immutable sequence of human actions, while the "View" remains a clean projection of those actions.

**Risk:** If a user performs a *new* action while in an "undone" state (e.g., Undo, then Create New), we have a choice: do we overwrite the undone events (Git style) or allow multiple timelines?

**Should we stick to the "Git-style" (truncate undone events upon new action) or should we keep all history forever?**