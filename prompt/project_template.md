# Creating Project Template with UV
```sh
mkdir task-manager
uv init --package task-manager-app
cd task-manager-app

# Run and Test Application
uv run task-manager-app
# Add Application Dependencies
uv add typer pydantic rich
ls s        
# Add Development Dependencies
uv add mypy ruff pytest typing-extensions --dev
```

# Runnig and Testing App
```sh
# 1. Create a Parent Task
uv run task-manager-ap create "Develop Login API" --desc "Backend authentication logic"

# 2. Create a Child Task (Replace <ID> with the ID from above)
uv run task-manager-app create "Write JWT Logic" --parent <ID>

# 3. Create another Child
uv run task-manager-app create "Setup Redis Cache" --parent <ID>

# 4. viewing all created task
uv run task-manager-app list

# 5. viewing parent-child relationship for all task created
uv run task-manager-app tree

6. Real Time updating a child doesn't break the parent's UI state
# Update a child status
uv run task-traveler update <CHILD_ID> --status in_progress

# View the tree again
uv run task-manager-app tree

# Testing Undo/Redo Functionality
uv run task-manager-app create "Marketing Campaign"
uv run task-manager-app create "Design Banner" --parent <PARENT_ID>
uv run task-manager-app tree
uv run task-manager-app undo
uv run task-manager-app redo

# Strategic Detachment: Verify that if an "Update" or "Creation" is undone in a specific order, the state remains consistent.
uv run task-manager-app create "Database Migration"
uv run task-manager-app update <ID> --status in_progress
uv run task-manager-app history
uv run task-manager-app undo
uv run task-manager-app tree
```

