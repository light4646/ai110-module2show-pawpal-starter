"""Run both models' mark_task_complete against PawPal's real classes on the same scenarios."""

import sys
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pawpal_system import Owner, Pet, Scheduler, Task

STEPS = {"daily": timedelta(days=1), "weekly": timedelta(days=7)}


def model_version(scheduler, pet_name, description):
    """Both answers share this logic: first open match in list order, then dataclasses.replace."""
    pet = scheduler.owner.get_pet(pet_name)
    if pet is None:
        raise ValueError(f"No pet named {pet_name!r}")
    task = next((t for t in pet.tasks if t.description == description and not t.completed), None)
    if task is None:
        raise ValueError(f"No open task {description!r} for {pet_name!r}")
    task.completed = True
    step = STEPS.get(task.frequency)
    if step is None:
        return None
    next_task = replace(task, due_date=task.due_date + step, completed=False)
    pet.add_task(next_task)
    return next_task


def scenario():
    """A pet whose Monday and Tuesday copies of a daily task were added out of order."""
    owner = Owner("Jordan")
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    monday = date(2026, 10, 19)
    pet.add_task(Task("Morning walk", "07:30", frequency="daily", due_date=monday + timedelta(days=1)))
    pet.add_task(Task("Morning walk", "07:30", frequency="daily", due_date=monday))
    return owner


for name, complete in [("Both models", model_version),
                       ("PawPal final", lambda s, p, d: s.mark_task_complete(p, d))]:
    scheduler = Scheduler(scenario())
    new = complete(scheduler, "Mochi", "Morning walk")
    done = [t.due_date.isoformat() for t in scheduler.get_all_tasks() if t.completed]
    print(f"{name:13} completed {done}, created {new.due_date.isoformat()}")

for name, complete in [("Both models", model_version),
                       ("PawPal final", lambda s, p, d: s.mark_task_complete(p, d))]:
    scheduler = Scheduler(scenario())
    try:
        complete(scheduler, "Ghost", "Morning walk")
    except ValueError as err:
        print(f"{name:13} missing pet -> ValueError: {err}")
