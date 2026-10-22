"""PawPal+ logic layer: Owner, Pet, Task and Scheduler classes."""

from dataclasses import dataclass, field
from datetime import date


def to_minutes(hhmm: str) -> int:
    """Convert an "HH:MM" string to minutes after midnight."""
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)


@dataclass
class Task:
    """A single pet care activity scheduled for a time on a given day."""

    description: str
    time: str  # "HH:MM", 24-hour clock
    duration_minutes: int = 15
    priority: str = "medium"  # low / medium / high
    frequency: str = "once"  # once / daily / weekly
    due_date: date = field(default_factory=date.today)
    completed: bool = False
    pet_name: str = ""  # filled in by Pet.add_task

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def start_minutes(self) -> int:
        """Return the start time as minutes after midnight."""
        return to_minutes(self.time)

    def end_minutes(self) -> int:
        """Return the end time as minutes after midnight."""
        return self.start_minutes() + self.duration_minutes


@dataclass
class Pet:
    """A pet and the care tasks that belong to it."""

    name: str
    species: str
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, description: str) -> bool:
        """Remove the first task with this description; return True if one was removed."""
        for task in self.tasks:
            if task.description == description:
                self.tasks.remove(task)
                return True
        return False

    def list_tasks(self) -> list[Task]:
        """Return a copy of this pet's tasks."""
        return list(self.tasks)

    def pending_tasks(self) -> list[Task]:
        """Return the tasks that are not yet complete."""
        return [t for t in self.tasks if not t.completed]


class Owner:
    """A pet owner who manages one or more pets."""

    def __init__(self, name: str):
        self.name = name
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet; pet names must be unique for this owner."""
        if self.get_pet(pet.name) is not None:
            raise ValueError(f"{self.name} already has a pet named {pet.name}")
        self.pets.append(pet)

    def get_pet(self, name: str) -> Pet | None:
        """Find a pet by name (case-insensitive)."""
        for pet in self.pets:
            if pet.name.lower() == name.lower():
                return pet
        return None

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all pets."""
        return [task for pet in self.pets for task in pet.tasks]


class Scheduler:
    """The 'brain' that reads tasks from an Owner's pets and organizes them."""

    def __init__(self, owner: Owner):
        self.owner = owner

    def get_all_tasks(self) -> list[Task]:
        """Collect tasks from every pet the owner has."""
        return self.owner.get_all_tasks()

    def todays_schedule(self, day: date | None = None) -> list[Task]:
        """Return the tasks due on the given day (default today)."""
        day = day or date.today()
        return [t for t in self.get_all_tasks() if t.due_date == day]
