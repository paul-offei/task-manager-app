import sqlite3
import json
from typing import List, Optional
from uuid import UUID, uuid4
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
    
    def save_task(self, task: Task, event_type: EventType):
        """
        Atomically saves a task and logs the event.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Record the full state in the event log for easy reconstruction
            # In a more advanced version, we'd only store the 'diff'
            payload = task.model_dump_json()
            
            cursor.execute(
                "INSERT INTO events (event_id, task_id, event_type, payload) VALUES (?, ?, ?, ?)",
                (str(uuid4()), str(task.id), event_type.value, payload)
            )
            
            # Update the materialized view for 'List' and 'Tree' commands
            cursor.execute("""
                INSERT OR REPLACE INTO tasks_view (id, parent_id, title, description, status, updated_at, data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                str(task.id), 
                str(task.parent_id) if task.parent_id else None,
                task.title,
                task.description,
                task.status.value,
                task.updated_at.isoformat(),
                payload  # We store the full JSON here to make 'update' fetching easier
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
    

    def get_max_sequence(self) -> int:
        with self._get_connection() as conn:
            res = conn.execute("SELECT MAX(sequence) FROM events").fetchone()
            return res[0] if res[0] is not None else 0

    # def undo(self) -> int:
    #     """Moves the state back by one event."""
    #     current_max = self.get_max_sequence()
    #     if current_max <= 0:
    #         return 0
            
    #     with self._get_connection() as conn:
    #         # For a simple linear undo, we delete the latest event 
    #         # and rebuild the tasks_view.
    #         conn.execute("DELETE FROM events WHERE sequence = ?", (current_max,))
    #         self.rebuild_materialized_view()
    #     return current_max - 1
    
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

    def rebuild_materialized_view(self):
        """Wipes and regenerates the tasks_view from the event log."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM tasks_view")
            # Fetch all events in order
            conn.row_factory = sqlite3.Row
            events = conn.execute("SELECT * FROM events ORDER BY sequence ASC").fetchall()
            
            # Use engine to get state
            from .engine import ReconstructionEngine
            state = ReconstructionEngine.project_state([dict(e) for e in events], 999999)
            
            for task in state.values():
                conn.execute("""
                    INSERT INTO tasks_view (id, parent_id, title, description, status, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (str(task.id), str(task.parent_id) if task.parent_id else None, 
                      task.title, task.description, task.status.value, task.updated_at.isoformat()))