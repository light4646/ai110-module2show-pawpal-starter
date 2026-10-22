"""PawPal+ logic layer: Owner, Pet, Task and Scheduler classes."""

import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
RECURRENCE_STEP = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}
PRIORITY_BADGE = {"high": "🔴 high", "medium": "🟡 medium", "low": "🟢 low"}
TASK_EMOJI = {
    "walk": "🦮", "feed": "🍽️", "breakfast": "🍽️", "dinner": "🍽️", "lunch": "🍽️",
    "med": "💊", "pill": "💊", "vet": "🩺", "appointment": "🩺", "groom": "✂️",
    "bath": "🛁", "play": "🎾", "train": "🎓", "litter": "🧹",
}


def to_minutes(hhmm: str) -> int:
    """Convert an "HH:MM" string to minutes after midnight."""
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)


def to_hhmm(minutes: int) -> str:
    """Convert minutes after midnight back to an "HH:MM" string."""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def task_emoji(description: str) -> str:
    """Pick an emoji for a task based on keywords in its description."""
    lowered = description.lower()
    for keyword, emoji in TASK_EMOJI.items():
        if keyword in lowered:
            return emoji
    return "🐾"


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

    def __post_init__(self) -> None:
        """Validate fields so bad input fails early instead of breaking sorting later."""
        try:
            hours, minutes = map(int, self.time.split(":"))
        except ValueError:
            raise ValueError(f"time must be HH:MM, got {self.time!r}") from None
        if not (0 <= hours < 24 and 0 <= minutes < 60):
            raise ValueError(f"time must be HH:MM, got {self.time!r}")
        self.time = f"{hours:02d}:{minutes:02d}"
        if self.priority not in PRIORITY_RANK:
            raise ValueError(f"priority must be one of {list(PRIORITY_RANK)}")
        if self.frequency not in ("once", *RECURRENCE_STEP):
            raise ValueError("frequency must be once, daily or weekly")
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def start_minutes(self) -> int:
        """Return the start time as minutes after midnight."""
        return to_minutes(self.time)

    def end_minutes(self) -> int:
        """Return the end time as minutes after midnight."""
        return self.start_minutes() + self.duration_minutes

    def next_occurrence(self) -> "Task | None":
        """Return a fresh copy due on the next daily/weekly date, or None for one-off tasks."""
        step = RECURRENCE_STEP.get(self.frequency)
        if step is None:
            return None
        return Task(
            self.description, self.time, self.duration_minutes, self.priority,
            self.frequency, self.due_date + step, False, self.pet_name,
        )

    def to_dict(self) -> dict:
        """Serialize to a JSON-friendly dict."""
        return {
            "description": self.description, "time": self.time,
            "duration_minutes": self.duration_minutes, "priority": self.priority,
            "frequency": self.frequency, "due_date": self.due_date.isoformat(),
            "completed": self.completed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Build a Task from a dict made by to_dict."""
        return cls(**{**data, "due_date": date.fromisoformat(data["due_date"])})


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

    def to_dict(self) -> dict:
        """Serialize the pet and its tasks to a JSON-friendly dict."""
        return {
            "name": self.name, "species": self.species, "age": self.age,
            "tasks": [t.to_dict() for t in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Pet":
        """Build a Pet (and its tasks) from a dict made by to_dict."""
        pet = cls(data["name"], data["species"], data.get("age", 0))
        for task_data in data.get("tasks", []):
            pet.add_task(Task.from_dict(task_data))
        return pet


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

    def save_to_json(self, path: str | Path) -> None:
        """Write the owner, pets and tasks to a JSON file."""
        data = {"name": self.name, "pets": [p.to_dict() for p in self.pets]}
        Path(path).write_text(json.dumps(data, indent=2))

    @classmethod
    def load_from_json(cls, path: str | Path) -> "Owner":
        """Rebuild an Owner from a JSON file written by save_to_json."""
        data = json.loads(Path(path).read_text())
        owner = cls(data["name"])
        for pet_data in data.get("pets", []):
            owner.add_pet(Pet.from_dict(pet_data))
        return owner


@dataclass
class PlanEntry:
    """One line of a daily plan: a task, when it will happen, and why."""

    task: Task
    start: str | None  # None means it could not fit in the day
    reason: str


class Scheduler:
    """The 'brain' that reads tasks from an Owner's pets and organizes them."""

    def __init__(self, owner: Owner, day_start: str = "07:00", day_end: str = "21:00"):
        self.owner = owner
        self.day_start = day_start
        self.day_end = day_end

    def get_all_tasks(self) -> list[Task]:
        """Collect tasks from every pet the owner has."""
        return self.owner.get_all_tasks()

    def todays_schedule(self, day: date | None = None) -> list[Task]:
        """Return the tasks due on the given day (default today), sorted by time."""
        day = day or date.today()
        return self.sort_by_time([t for t in self.get_all_tasks() if t.due_date == day])

    def sort_by_time(self, tasks: list[Task] | None = None) -> list[Task]:
        """Sort tasks chronologically by due date, then "HH:MM" time."""
        tasks = self.get_all_tasks() if tasks is None else tasks
        return sorted(tasks, key=lambda t: (t.due_date, t.start_minutes()))

    def sort_by_priority(self, tasks: list[Task] | None = None) -> list[Task]:
        """Sort tasks by priority (high first), breaking ties by time."""
        tasks = self.get_all_tasks() if tasks is None else tasks
        return sorted(tasks, key=lambda t: (PRIORITY_RANK.get(t.priority, 1), t.due_date, t.start_minutes()))

    def filter_tasks(self, pet_name: str | None = None, completed: bool | None = None,
                     day: date | None = None) -> list[Task]:
        """Filter tasks across all pets by pet name, completion status and/or day."""
        result = self.get_all_tasks()
        if pet_name is not None:
            result = [t for t in result if t.pet_name.lower() == pet_name.lower()]
        if completed is not None:
            result = [t for t in result if t.completed == completed]
        if day is not None:
            result = [t for t in result if t.due_date == day]
        return result

    def mark_task_complete(self, pet_name: str, description: str,
                           day: date | None = None) -> Task | None:
        """Complete a pet's pending task; if it recurs, schedule and return the next occurrence."""
        pet = self.owner.get_pet(pet_name)
        if pet is None:
            raise ValueError(f"No pet named {pet_name}")
        candidates = [t for t in pet.pending_tasks() if t.description == description
                      and (day is None or t.due_date == day)]
        if not candidates:
            raise ValueError(f"{pet_name} has no pending task '{description}'")
        task = min(candidates, key=lambda t: (t.due_date, t.start_minutes()))
        task.mark_complete()
        follow_up = task.next_occurrence()
        if follow_up is not None:
            pet.add_task(follow_up)
        return follow_up

    def detect_conflicts(self, day: date | None = None) -> list[str]:
        """Return warnings for pending tasks on a day whose time windows overlap."""
        tasks = [t for t in self.todays_schedule(day) if not t.completed]
        warnings = []
        for i, first in enumerate(tasks):
            for second in tasks[i + 1:]:
                if second.start_minutes() >= first.end_minutes():
                    break  # sorted by start, so nothing later can overlap `first`
                who = "same pet" if first.pet_name == second.pet_name else "different pets"
                warnings.append(
                    f"{first.time} {first.pet_name}: {first.description} overlaps "
                    f"{second.time} {second.pet_name}: {second.description} ({who})"
                )
        return warnings

    def next_available_slot(self, duration_minutes: int, day: date | None = None,
                            not_before: str | None = None) -> str | None:
        """Find the earliest free "HH:MM" start for a task of this length, or None if the day is full."""
        busy = sorted(
            (t.start_minutes(), t.end_minutes())
            for t in self.todays_schedule(day) if not t.completed
        )
        return self._first_gap(busy, duration_minutes, not_before)

    def build_daily_plan(self, day: date | None = None) -> list[PlanEntry]:
        """Time-block the day: place high-priority tasks first and move clashing lower-priority ones."""
        pending = [t for t in self.todays_schedule(day) if not t.completed]
        placed: list[tuple[int, int, Task]] = []
        plan = []
        for task in self.sort_by_priority(pending):
            start = task.start_minutes()
            clash = next((other for s, e, other in placed
                          if start < e and s < start + task.duration_minutes), None)
            if clash is None:
                slot, reason = task.time, f"{task.priority} priority, at requested time"
            else:
                busy = sorted((s, e) for s, e, _ in placed)
                slot = self._first_gap(busy, task.duration_minutes, task.time)
                reason = (f"moved from {task.time}: clashed with {clash.pet_name}'s "
                          f"'{clash.description}' ({clash.priority} priority)")
                if slot is None:
                    reason += "; no free slot left today"
            if slot is not None:
                placed.append((to_minutes(slot), to_minutes(slot) + task.duration_minutes, task))
            plan.append(PlanEntry(task, slot, reason))
        return sorted(plan, key=lambda p: to_minutes(p.start) if p.start else 24 * 60)

    def _first_gap(self, busy: list[tuple[int, int]], duration: int,
                   not_before: str | None = None) -> str | None:
        """Scan sorted busy intervals for the first gap of `duration` minutes inside the day."""
        cursor = to_minutes(self.day_start)
        if not_before is not None:
            cursor = max(cursor, to_minutes(not_before))
        for start, end in busy:
            if start - cursor >= duration:
                break
            cursor = max(cursor, end)
        if cursor + duration > to_minutes(self.day_end):
            return None
        return to_hhmm(cursor)
