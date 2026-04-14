# Input
Let focus on examples for user to test the interface with  Undo/redo functionality

# output
Now that we've fixed the engine's signature and the UUID resolution, let's put the **Undo/Redo** functionality through its paces. As a Product Owner, I want the user to feel that "time" is a tangible slider they can manipulate without fear of breaking the data.

Here is a structured testing suite to verify the **Temporal Masking** and **Parent-Child Integrity**.

---

### 🧪 Test Scenario 1: The "Ghost Parent" Recovery
**Goal:** Verify that undoing a parent task orphans the child, and redoing the parent restores the hierarchy.

1.  **Create the Parent:**
    ```bash
    uv run task-traveler create "Marketing Campaign"
    ```
    *(Note the 8-character ID, e.g., `a1b2c3d4`)*

2.  **Create the Child:**
    ```bash
    uv run task-traveler create "Design Banner" --parent <PARENT_ID>
    ```

3.  **Verify the Tree:**
    ```bash
    uv run task-traveler tree
    ```
    *Should show "Design Banner" nested under "Marketing Campaign".*

4.  **Perform the Undo:**
    ```bash
    uv run task-traveler undo
    ```
    *This undid the child creation. Tree should now only show the Parent.*

5.  **Perform another Undo:**
    ```bash
    uv run task-traveler undo
    ```
    *This undid the parent. `uv run task-traveler tree` should now be empty.*

6.  **The Redo (Recovery):**
    ```bash
    uv run task-traveler redo
    ```
    *The Parent reappears! Run `tree` to confirm.*

---

### 🧪 Test Scenario 2: Strategic Detachment
**Goal:** Verify that if an "Update" or "Creation" is undone in a specific order, the state remains consistent.

1.  **Setup:** Create a Task.
    ```bash
    uv run task-traveler create "Database Migration"
    ```
2.  **Update it:**
    ```bash
    uv run task-traveler update <ID> --status in_progress
    ```
3.  **Check History:**
    ```bash
    uv run task-traveler history
    ```
    *You should see two events: `task_created` and `task_updated`.*

4.  **Undo the Status:**
    ```bash
    uv run task-traveler undo
    uv run task-traveler tree
    ```
    *The task should still exist, but its status should have reverted to `todo`.*

---

### 📊 Expected UI Behavior Table

| Action | `history` status | `tree` visualization | Logic Applied |
| :--- | :--- | :--- | :--- |
| **Initial** | 2 active events | Parent ➔ Child | Hierarchy logic |
| **Undo Child** | Last event `is_undone=1` | Parent (Root) | Filtered sequence |
| **Undo Parent** | Both events `is_undone=1` | (Empty) | Empty projection |
| **Redo Parent** | First event `is_undone=0` | Parent (Root) | Partial reconstruction |
| **Redo Child** | All events `is_undone=0` | Parent ➔ Child | Link restoration |

---

### 🛠️ Troubleshooting the UI
When testing these, keep an eye on the **Sequence Numbers** in the `history` command. 

* **Redo** will always pick the *lowest* sequence number where `is_undone=1`.
* **Undo** will always pick the *highest* sequence number where `is_undone=0`.

This "LIFO" (Last-In-First-Out) stack approach ensures that your time-travel feels linear and intuitive.

**How do these tests perform on your machine? Are you seeing the parent-child links snapping back into place during the `redo`?**