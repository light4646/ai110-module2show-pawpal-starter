# Response: Claude Sonnet (verbatim)

```python
from dataclasses import replace
from datetime import timedelta
from typing import Optional

class Scheduler:
    def __init__(self, owner):
        self.owner = owner

    def mark_task_complete(self, pet_name: str, description: str) -> Optional[Task]:
        """Complete a task. Returns the newly created recurrence, or None."""
        pet = self.owner.get_pet(pet_name)
        if pet is None:
            raise ValueError(f"No pet named '{pet_name}'")

        task = next(
            (t for t in pet.tasks
             if t.description == description and not t.completed),
            None,
        )
        if task is None:
            raise ValueError(
                f"No pending task '{description}' for {pet_name}"
            )

        task.completed = True

        delta = {"daily": timedelta(days=1),
                 "weekly": timedelta(days=7)}.get(task.frequency)
        if delta is None:          # "once" (or unknown): nothing to schedule
            return None

        next_task = replace(task,
                            due_date=task.due_date + delta,
                            completed=False)
        pet.add_task(next_task)
        return next_task
```

**Design choices**

- **`dataclasses.replace`** copies every field (time, duration, priority, frequency, pet_name) into a fresh instance. Only `due_date` and `completed` are overridden, so adding a field to Task later doesn't break this code. The original is kept as completed history rather than mutated.
- **Next date is based on the task's `due_date`, not `date.today()`.** If a daily task is completed late, the schedule stays anchored to its original cadence. If you'd rather the next one start from the completion day, swap in `date.today()`.
- **Only pending tasks match.** Without the `not t.completed` check, completing "Feed Rex" on day 2 would match day 1's already-completed copy and silently spawn a duplicate chain.
- **Errors raise `ValueError`.** This assumes `get_pet` returns `None` for a missing pet (adjust if it raises). Raising makes failures visible to the caller. A UI like Streamlit can catch it and show a message. Returning `False` would let typos pass silently.
- **Return value:** the new Task (or `None` for one-offs). This makes the behavior easy to unit test and lets the UI say "Next feeding scheduled for 2026-10-23".
- **Unknown frequencies** are treated like "once". For stricter validation, check frequency in `Task.__post_init__`.

Tests worth writing: daily moves +1 day, weekly +7, once returns None and adds nothing, missing pet and missing task raise, and completing the same task twice raises.
