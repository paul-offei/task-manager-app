# Input:
I'm getting error.
 22 │   parent_uuid = UUID(parent) if parent else None                                                                                                            │
│    23 │   task = Task(title=title, description=desc, parent_id=parent_uuid)                                                                                         │
│    24 │                                                                                                                                                             │
│ ❱  25 │   repo.save_task(task, EventType.CREATED)                                                                                                                   │
│    26 │   console.print(f"[bold green]✔[/bold green] Task created: {task.title} (ID: {str(task                                                                      │
│    27                                                                                                                                                               │
│    28 @app.command()    



54 │   │   │   )                                                                                                                                                 │
│    55 │   │   │                                                                                                                                                     │
│    56 │   │   │   # Update the materialized view for 'List' and 'Tree' commands                                                                                     │
│ ❱  57 │   │   │   cursor.execute("""                                                                                                                                │
│    58 │   │   │   │   INSERT OR REPLACE INTO tasks_view (id, parent_id, title, description, st                                                                      │
│    59 │   │   │   │   VALUES (?, ?, ?, ?, ?, ?, ?)                                                                                                                  │
│    60 │   │   │   """, (     



# Output
It looks like we've hit a classic **Schema Mismatch**. 

Based on the traceback, the `cursor.execute` call is failing during the `INSERT OR REPLACE` into `tasks_view`. This usually happens when the number of columns defined in the table doesn't match the number of values we are trying to inject, or a specific column (like `data`) is missing from the table definition.

### 🔍 The Root Cause
In my previous refactor, I added a `data` field to the `INSERT` statement to make fetching easier for updates, but if your local `tasks.db` was already created with the older schema, it’s missing that column.

### 🛠️ The Fix: Update your `_bootstrap` method
Update the `tasks_view` creation logic in `database.py` to ensure the `data` column exists:

```python
# src/task_traveler/database.py

def _bootstrap(self):
    """Initialize tables if they don't exist."""
    with self._get_connection() as conn:
        # Source of Truth
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL,
                task_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_undone INTEGER DEFAULT 0
            )
        """)
        # Materialized View - MAKE SURE 'data' IS HERE
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks_view (
                id TEXT PRIMARY KEY,
                parent_id TEXT,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                data TEXT  -- <--- THIS IS LIKELY THE MISSING COLUMN
            )
        """)
```

### ⚡ Quick Fix (Delete the DB)
Since we are in the testing phase and don't have critical data yet, the fastest way to resolve a schema mismatch is to **delete the existing database file** so the bootstrap can recreate it correctly:

```bash
rm tasks.db
```

### 🧪 Retry the UI Test
After deleting the file or updating the code:
1. Run `uv run task-traveler create "Test Task"` again.
2. It should now successfully execute line 57 and save the task.

**Did that clear the error, or is it still throwing a specific "table has X columns but Y values were supplied" message?**