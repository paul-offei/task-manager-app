# Input
I'm getting error applying undo operation. Help me fix the error. Here is the error:
   180 @app.command()                                                                                                                                                │
│   181 def undo():                                                                                                                                                   │
│   182 │   """Step back in time without losing data."""                                                                                                              │
│ ❱ 183 │   repo.undo()                                                                                                                                               │
│   184 │   console.print("[yellow]⏪ Undid last action. Use 'redo' to restore.[/yellow]")                                                                            │
│   185                                                                                                                                                               │
│   186 @app.command()                                                                                                                                                │
│                                                                                                                                                                     │
│ /home/ntow/cntxt/task-manager/task-manager-app/src/task_manager_app/database.py:112 in undo                                                                         │
│                                                                                                                                                                     │
│   109 │   │   │                                                                                                                                                     │
│   110 │   │   │   if res:                                                                                                                                           │
│   111 │   │   │   │   conn.execute("UPDATE events SET is_undone = 1 WHERE sequence = ?", (res[                                                                      │
│ ❱ 112 │   │   │   │   self.rebuild_materialized_view()                                                                                                              │
│   113 │                                                                                                                                                             │
│   114 │   def redo(self):                                                                                                                                           │
│   115 │   │   """Mark the earliest undone event as active again."""                                                                                                 │
│                                                                                                                                                                     │
│ /home/ntow/cntxt/task-manager/task-manager-app/src/task_manager_app/database.py:129 in rebuild_materialized_view                                                    │
│                                                                                                                                                                     │
│   126 │   def rebuild_materialized_view(self):                                                                                                                      │
│   127 │   │   """Wipes and regenerates the tasks_view from the event log."""                                                                                        │
│   128 │   │   with self._get_connection() as conn:                                                                                                                  │
│ ❱ 129 │   │   │   conn.execute("DELETE FROM tasks_view")                                                                                                            │
│   130 │   │   │   # Fetch all events in order                                                                                                                       │
│   131 │   │   │   conn.row_factory = sqlite3.Row                                                                                                                    │
│   132 │   │   │   events = conn.execute("SELECT * FROM events ORDER BY sequence ASC").fetchall                                                                      │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
OperationalError: database is locked

# Output
The `OperationalError: database is locked` occurs because we are attempting to start a **new** write transaction (`DELETE FROM tasks_view`) while we still have an **active** open connection or cursor from the previous step (`UPDATE events`). 

In SQLite, only one connection can write to the database at a time. When `repo.undo()` calls `self.rebuild_materialized_view()`, it's tripping over its own open transaction.

### 🛠️ The Fix: Connection Management

We need to ensure the connection used to mark the event as undone is **committed and closed** before we call the rebuild method.

Update your `undo` and `redo` methods in `src/task_manager_app/database.py` to use a separate context for the update:

```python
# src/task_manager_app/database.py

def undo(self):
    """Mark the latest active event as undone."""
    with self._get_connection() as conn:
        res = conn.execute(
            "SELECT sequence FROM events WHERE is_undone = 0 ORDER BY sequence DESC LIMIT 1"
        ).fetchone()
        
        if res:
            conn.execute("UPDATE events SET is_undone = 1 WHERE sequence = ?", (res[0],))
            # Transaction commits here when exiting the 'with' block
    
    # Now that the lock is released, we can rebuild safely
    if res:
        self.rebuild_materialized_view()

def redo(self):
    """Mark the earliest undone event as active again."""
    with self._get_connection() as conn:
        res = conn.execute(
            "SELECT sequence FROM events WHERE is_undone = 1 ORDER BY sequence ASC LIMIT 1"
        ).fetchone()
        
        if res:
            conn.execute("UPDATE events SET is_undone = 0 WHERE sequence = ?", (res[0],))
            # Transaction commits here
            
    if res:
        self.rebuild_materialized_view()
```

### 🧠 Why this solves it:
SQLite's `with connection` block automatically commits the transaction when it finishes. By moving `self.rebuild_materialized_view()` **outside** of that block, we ensure that the "Undo" update is finished and the file lock is released before the "Rebuild" starts its own transaction.

### 🧪 Retry the Test
1. Create a task.
2. Run `uv run task-traveler undo`.
3. It should now successfully update the event log and refresh the view without the locking error.

**Does the undo operation complete successfully now?**