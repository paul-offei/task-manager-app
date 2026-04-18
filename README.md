# How to get APP Started 
- [Intall Python 3.10 >= for your OS](https://www.python.org/downloads/)
- [Install uv for your OS](https://docs.astral.sh/uv/getting-started/installation/)
- [Install SQLite3 for your OS](https://sqlite.org/index.html)
- Run `uv syn` in the project directory on your terminal to install the necessary packages
```sh
cd task-manager-app
uv syn 
```

# Runnig and Testing App on CLI
```sh
# 0. See Command Line Help
uv run task-manager-app --help

# 1. Create a Parent Task
uv run task-manager-app create "Develop Login API" --desc "Backend authentication logic"

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
uv run task-manager-app update <CHILD_ID> --status in_progress

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

# User AI Interaction and Video Demo Link
- Decision to use Google Gemina was because of I having Pro Account for unlimited interaction
- [Refine my starting prompt with ChatGPT](https://chatgpt.com/share/69de3671-37f8-8325-9d82-8e3660b41eaf)
- [Used the Refine Prompt to start develoment iteration](https://gemini.google.com/share/a55572e352b1)
- [Demo Video](https://drive.google.com/file/d/1DVx0pMYLPvPuEDKkQel3F11Fn11xvrQf/view?usp=sharing)



# Video DemoExamples of Task
## Home Organization
1. Create a Parent Task
   
uv run task-manager-app create "Clean the Kitchen" --desc "Deep clean all kitchen surfaces and appliances for the week."

1. Create a Child Task

uv run task-manager-app create "Empty the dishwasher" --parent

uv run task-manager-app create "Scrub the sink" --parent

uv run task-manager-app create "Wipe down countertops" --parent 

## Professional Projects
1. Create a Parent Task
   
uv run task-manager-app create "Prepare Monthly Report" --desc "Compile and analyze departmental 
performance metrics for stakeholders."

1. Create a Child Task
   
uv run task-manager-app create "Gather data from sales" --parent

uv run task-manager-app create "Create visual charts" --parent

uv run task-manager-app create "Write the executive summary" --parent 

## Personal Wellness

1. Create a Parent Task
   
uv run task-manager-app create "Start a Fitness Routine" --desc "Establish a consistent physical activity schedule to improve health."

1. Create a Child Task
   
uv run task-manager-app create "Buy new running shoes" --parent

uv run task-manager-app create "Join a local gym" --parent

uv run task-manager-app create "Schedule three workouts weekly" --parent 

## Software Development
1. Create a Parent Task
   
uv run task-manager-app create "Develop Login API" --desc "Backend authentication logic"

1. Create another Child
   
uv run task-manager-app create "Setup Redis Cache" --parent 

uv run task-manager-app create "Write JWT Logic" --parent 

uv run task-manager-app create "Write UI Interface" --parent 


