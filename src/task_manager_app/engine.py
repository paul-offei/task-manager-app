from typing import Dict, List, Optional
from uuid import UUID
import json
from .models import Task, TaskStatus


# src/task_traveler/engine.py

class ReconstructionEngine:
    @staticmethod
    def project_state(events: list[dict], slider_pos: int = 999999) -> dict[UUID, Task]:
        """
        Replays active events up to slider_pos to reconstruct the task forest.
        """
        tasks: dict[UUID, Task] = {}

        # 1. Filter: Replay only events that are NOT undone AND within the slider range
        active_timeline = [
            e for e in events 
            if not e.get("is_undone") and e.get("sequence", 0) <= slider_pos
        ]
        
        for event in active_timeline:
            task_id = UUID(event["task_id"])
            # Ensure we handle the payload whether it's a dict or a JSON string
            payload = event["payload"]
            if isinstance(payload, str):
                payload = json.loads(payload)
            
            event_type = event["event_type"]

            if event_type == "task_created":
                tasks[task_id] = Task.model_validate(payload)
            
            elif event_type == "task_updated":
                if task_id in tasks:
                    # Merge current state with new updates
                    current_data = tasks[task_id].model_dump()
                    current_data.update(payload)
                    tasks[task_id] = Task.model_validate(current_data)

            elif event_type == "task_deleted":
                tasks.pop(task_id, None)

        # 2. Strategy: DETACH Children
        # If a child's parent doesn't exist in this point in time, orphan it.
        for task in tasks.values():
            if task.parent_id and task.parent_id not in tasks:
                task.parent_id = None
        
        return tasks

# class ReconstructionEngine:
#     @staticmethod
#     def project_state(events: List[dict]) -> Dict[UUID, Task]:
#         tasks: Dict[UUID, Task] = {}

#         # 1. Replay only active events
#         active_events = [e for e in events if not e.get("is_undone")]
        
#         for event in active_events:
#             task_id = UUID(event["task_id"])
#             payload = json.loads(event["payload"])
            
#             if event["event_type"] == "task_created":
#                 tasks[task_id] = Task.model_validate(payload)
#             elif event["event_type"] == "task_updated":
#                 if task_id in tasks:
#                     tasks[task_id] = Task.model_validate({**tasks[task_id].model_dump(), **payload})

#         # 2. Strategy: DETACH Children
#         for task in tasks.values():
#             if task.parent_id and task.parent_id not in tasks:
#                 task.parent_id = None  # Detach orphan from non-existent parent
        
#         return tasks

# class ReconstructionEngine:
#     @staticmethod
#     def project_state(events: List[dict], slider_pos: int) -> Dict[UUID, Task]:
#         """
#         Replays events up to slider_pos to reconstruct the task forest.
#         """
#         tasks: Dict[UUID, Task] = {}

#         # 1. Replay events in sequence
#         for event in events:
#             if event["sequence"] > slider_pos:
#                 break

#             task_id = UUID(event["task_id"])
#             payload = json.loads(event["payload"])
#             event_type = event["event_type"]

#             if event_type == "task_created":
#                 tasks[task_id] = Task.model_validate(payload)
            
#             elif event_type == "task_updated":
#                 if task_id in tasks:
#                     # Update existing task with new payload values
#                     current_data = tasks[task_id].model_dump()
#                     current_data.update(payload)
#                     tasks[task_id] = Task.model_validate(current_data)

#             elif event_type == "task_deleted":
#                 tasks.pop(task_id, None)

#         # 2. Parent-Child Reconciliation Logic
#         # If a child's parent doesn't exist at this point in time, 
#         # we orphan the child (parent_id = None) to keep the state valid.
#         for task in tasks.values():
#             if task.parent_id and task.parent_id not in tasks:
#                 task.parent_id = None
        
#         return tasks