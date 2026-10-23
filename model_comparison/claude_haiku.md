# Response: Claude Haiku (verbatim)

Here is the Scheduler.mark_task_complete implementation for the PawPal Task/Pet/Owner model.

```python
from dataclasses import replace
from datetime import timedelta
from typing import Optional

RECURRENCE = {
    "daily": timedelta(days=1),
    "weekly": timedelta(days=7),
}

class Scheduler:
    def __init__(self, owner: "Owner"):
        self.owner = owner

    def mark_task_complete(self, pet_name: str, description: str) -> Optional[Task]:
        """Complete the first open task matching description.

        Returns the newly created next occurrence for daily/weekly tasks,
        or None for one-off tasks.
        Raises ValueError if the pet or an open matching task is missing.
        """
        pet = self.owner.get_pet(pet_name)
        if pet is None:
            raise ValueError(f"No pet named {pet_name!r}")

        task = next(
            (t for t in pet.tasks if t.description == description and not t.completed),
            None,
        )
        if task is None:
            raise ValueError(f"No open task {description!r} for {pet_name!r}")

        task.completed = True

        step = RECURRENCE.get(task.frequency)
        if step is None:
            return None

        next_task = replace(task, due_date=task.due_date + step, completed=False)
        pet.add_task(next_task)
        return next_task
```

Design choices:
- Matching only open tasks means a repeat call never re-completes an old instance, and it picks up the newly created occurrence on the next run.
- dataclasses.replace copies every field (including pet_name, time, priority, frequency), so only due_date and completed change. New fields added to Task later carry over automatically.
- The next occurrence advances from due_date, not from today, as the spec requires. A late completion stays on the original schedule.
- A lookup table for recurrence means adding a frequency such as "monthly" is one dict entry. Unknown frequencies return None and are treated as one-off.
- Missing pets or tasks raise ValueError. This keeps a caller error distinct from a valid one-off task, which returns None. If you prefer silent handling, return a result object that reports success or failure instead.

Assumptions: Owner.get_pet returns None when the pet is missing (not raise), and Pet.name exists. I did not run this code; no tools were used, per your instruction.
