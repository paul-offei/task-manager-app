# User Input: 
Requirement Engineering feedback: Let focus on a working task manager  by building Task Management than can perform the following features  Create, list, and update tasks;

Here is our code base now:
Model.py:

# AI Response

Since we are working within a `uv` project structure, I will focus on making `models.py` the robust, type-safe heart of our application. 

To support the **Parent-Child** relationships and the **Time-Travel** requirements while keeping the "Create, List, Update" features working, I've designed the models to distinguish between the **Event** (the historical record) and the **State** (the task as it appears to the user).

### 🧰 The Model Design (src/task_traveler/models.py)

I'm using Pydantic's `ConfigDict` for performance and ensuring that every change results in a new `TaskEvent`.

```python
from datetime import datetime
from enum import Enum
from typing import Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict

# --- Enums ---

class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    ARCHIVED = "archived"

class EventType(str, Enum):
    CREATED = "task_created"
    UPDATED = "task_updated"
    DELETED = "task_deleted"
    RELOCATED = "task_moved"  # For parent-child changes

# --- Core Models ---

class Task(BaseModel):
    """
    The 'Materialized View' of a task at a specific point in time.
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    parent_id: Optional[UUID] = None
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.TODO
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class TaskEvent(BaseModel):
    """
    The immutable source of truth for the 'Time-Travel' slider.
    """
    event_id: UUID = Field(default_factory=uuid4)
    sequence: int  # The global incrementing counter (the slider index)
    task_id: UUID
    event_type: EventType
    
    # We store the 'delta' or the full state snapshot here
    # For the MVP, storing the dict of changed fields is more efficient
    payload: dict[str, Any] 
    
    timestamp: datetime = Field(default_factory=datetime.now)
    author: str = "local_user"  # Prepared for collaborative multi-user
```

---

### 🧠 Design Justification

1.  **The `sequence` Field**: This is the key for your "Time-Travel Slider." In the database, this will be an `AUTOINCREMENT` integer. To "undo," the system simply ignores all events where `sequence > slider_value`.
2.  **Parent-Child Logic**: By including `parent_id` in the `Task` model and the `payload` of a `TaskEvent`, our reconciliation engine (which we'll put in `engine.py`) can detect if a child's parent existed at that specific `sequence`.
3.  **Payload Flexibility**: Instead of a rigid schema for every tiny change, the `dict[str, Any]` payload allows us to update just the `status` or just the `title` without bloating the database with redundant data.



### 🛠️ Next Steps for the Sprint
Now that the models are defined, I suggest we move to the **Persistence Layer (`database.py`)**. We need to ensure that:
* Every `CREATE` or `UPDATE` operation is wrapped in a **transaction**.
* A single user action (e.g., updating a task) writes to both the `events` table (for history) and the `tasks` table (for quick listing).

**Shall I implement the SQLite repository pattern next to handle these atomic writes?**



