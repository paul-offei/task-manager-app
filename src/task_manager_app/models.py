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