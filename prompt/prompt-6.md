# User  Input:
yes proceed with the next step

# AI Response:
The next logical step is the **Reconstruction Engine**. This is the "brain" that makes the time-travel slider possible. 

The goal here is to solve the parent-child reconciliation challenge: if we move the slider back to a point where a parent task didn't exist yet, the engine must decide what to do with any child tasks that *did* exist.

---

### ⚙️ The Time-Travel Engine (`src/task_traveler/engine.py`)

This module is responsible for taking a raw list of events and "projecting" them into a coherent task tree.

```python
from typing import Dict, List, Optional
from uuid import UUID
import json
from .models import Task, TaskStatus

class ReconstructionEngine:
    @staticmethod
    def project_state(events: List[dict], slider_pos: int) -> Dict[UUID, Task]:
        """
        Replays events up to slider_pos to reconstruct the task forest.
        """
        tasks: Dict[UUID, Task] = {}

        # 1. Replay events in sequence
        for event in events:
            if event["sequence"] > slider_pos:
                break

            task_id = UUID(event["task_id"])
            payload = json.loads(event["payload"])
            event_type = event["event_type"]

            if event_type == "task_created":
                tasks[task_id] = Task.model_validate(payload)
            
            elif event_type == "task_updated":
                if task_id in tasks:
                    # Update existing task with new payload values
                    current_data = tasks[task_id].model_dump()
                    current_data.update(payload)
                    tasks[task_id] = Task.model_validate(current_data)

            elif event_type == "task_deleted":
                tasks.pop(task_id, None)

        # 2. Parent-Child Reconciliation Logic
        # If a child's parent doesn't exist at this point in time, 
        # we orphan the child (parent_id = None) to keep the state valid.
        for task in tasks.values():
            if task.parent_id and task.parent_id not in tasks:
                task.parent_id = None
        
        return tasks
```

---

### 🎛️ Implementing the Slider (`src/task_traveler/cli.py`)

Now we add the `history` and `travel` commands to the CLI. The `travel` command won't just show you the past; it will allow you to "reset" the current state to that point (effectively a Git-style hard reset).

```python
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
```

---

### 🛡️ Handling the Key Challenge
By using the **`project_state`** method, we solve the dependency issue:
* **The Problem:** Parent A is created (Seq 1), Child B is created (Seq 2). If we travel to Seq 0, both disappear. If we travel to Seq 1, only A appears.
* **The Solution:** The reconciliation loop at the end of `project_state` ensures that if a user somehow "travels" to a state where an event log is inconsistent (e.g., a child exists but its parent creation event was deleted), the UI won't crash because we dynamically orphan the task.

### 🚀 Next Steps
We have a working Create/List and a "Read-only" Time Travel. To finish the MVP:
1.  **Undo/Redo:** Implement a command that actually moves the `HEAD` of the database back by deleting/archiving newer events.
2.  **Branching:** (Optional but powerful) Allow a user to "travel" to Seq 5 and then "Commit" a new change, creating a new fork in the timeline.

**Would you like to focus on the active Undo/Redo logic next, or should we refine the Tree View to show nested tasks more clearly?**