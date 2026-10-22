"""CLI demo for PawPal+: builds an owner with pets and exercises the Scheduler."""

from datetime import date
from pathlib import Path

from tabulate import tabulate

from pawpal_system import PRIORITY_BADGE, Owner, Pet, Scheduler, Task, task_emoji

BOLD, YELLOW, GREEN, RESET = "\033[1m", "\033[33m", "\033[32m", "\033[0m"


def heading(text: str) -> None:
    """Print a bold section heading."""
    print(f"\n{BOLD}{text}{RESET}")


def task_table(tasks: list[Task]) -> str:
    """Format tasks as a grid table with emojis and priority badges."""
    rows = [
        [t.time, t.pet_name, f"{task_emoji(t.description)} {t.description}",
         f"{t.duration_minutes} min", PRIORITY_BADGE[t.priority], t.frequency,
         "✅ done" if t.completed else "⏳ pending"]
        for t in tasks
    ]
    return tabulate(rows, headers=["Time", "Pet", "Task", "Length", "Priority", "Repeats", "Status"],
                    tablefmt="rounded_outline")


def build_demo_owner() -> Owner:
    """Create the sample owner, pets and tasks (added out of time order on purpose)."""
    owner = Owner("Jordan")
    mochi = Pet("Mochi", "dog", age=3)
    luna = Pet("Luna", "cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    mochi.add_task(Task("Evening walk", "18:30", 30, "medium", "daily"))
    mochi.add_task(Task("Morning walk", "07:30", 30, "high", "daily"))
    luna.add_task(Task("Play session", "18:00", 20, "low", "daily"))
    mochi.add_task(Task("Breakfast", "08:00", 10, "high", "daily"))
    luna.add_task(Task("Breakfast", "08:00", 10, "high", "daily"))
    luna.add_task(Task("Flea medication", "09:00", 5, "high", "weekly"))
    mochi.add_task(Task("Vet appointment", "15:00", 60, "medium", "once"))
    return owner


def main() -> None:
    today = date.today()
    owner = build_demo_owner()
    scheduler = Scheduler(owner)

    heading(f"🐾 Today's Schedule for {owner.name} ({today:%a %b %d}) — sorted by time")
    print(task_table(scheduler.todays_schedule()))

    heading("🔎 Filter: only Luna's tasks")
    print(task_table(scheduler.sort_by_time(scheduler.filter_tasks(pet_name="Luna"))))

    heading("⚠️  Conflict check")
    for warning in scheduler.detect_conflicts():
        print(f"{YELLOW}WARNING:{RESET} {warning}")

    heading("🔁 Completing Mochi's daily Morning walk")
    follow_up = scheduler.mark_task_complete("Mochi", "Morning walk")
    print(f"{GREEN}Done.{RESET} Next occurrence created for {follow_up.due_date:%a %b %d} at {follow_up.time}")
    print("Pending today:", len(scheduler.filter_tasks(completed=False, day=today)),
          "| Completed today:", len(scheduler.filter_tasks(completed=True, day=today)))

    heading("⭐ Priority order (high first, then by time)")
    print(task_table(scheduler.sort_by_priority(scheduler.filter_tasks(completed=False, day=today))))

    heading("🧩 Time-blocked daily plan (clashes moved to the next free slot)")
    plan_rows = [[entry.start or "—", entry.task.pet_name,
                  f"{task_emoji(entry.task.description)} {entry.task.description}", entry.reason]
                 for entry in scheduler.build_daily_plan()]
    print(tabulate(plan_rows, headers=["Start", "Pet", "Task", "Why"], tablefmt="rounded_outline"))

    heading("🕒 Next available 45-minute slot")
    print(f"Earliest free slot after 07:30: {scheduler.next_available_slot(45, not_before='07:30')}")
    print(f"Earliest free slot after 15:00: {scheduler.next_available_slot(45, not_before='15:00')}")

    heading("💾 Persistence")
    path = Path("data.json")
    owner.save_to_json(path)
    reloaded = Owner.load_from_json(path)
    print(f"Saved to {path} and reloaded: {len(reloaded.pets)} pets, "
          f"{len(reloaded.get_all_tasks())} tasks")


if __name__ == "__main__":
    main()
