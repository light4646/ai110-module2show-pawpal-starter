# Prompt given to both models (identical, fresh session, no repo access)

> Do NOT use any tools, do not read or edit files. Just answer in text.
>
> I'm building a pet care scheduler in Python. My Task is a dataclass:
>
> ```python
> @dataclass
> class Task:
>     description: str
>     time: str            # "HH:MM"
>     duration_minutes: int = 15
>     priority: str = "medium"
>     frequency: str = "once"   # once / daily / weekly
>     due_date: date = field(default_factory=date.today)
>     completed: bool = False
>     pet_name: str = ""
> ```
>
> A Pet has `tasks: list[Task]` and `add_task(task)`. An Owner has `pets: list[Pet]` and `get_pet(name)`. A Scheduler holds the owner.
>
> Write `Scheduler.mark_task_complete(pet_name, description)` so that when a "daily" or "weekly" task is marked complete, a new instance is automatically created for the next occurrence (daily = due_date + 1 day, weekly = + 7 days). One-off tasks just get completed. Handle the case where the pet or task doesn't exist. Explain your design choices briefly and keep the whole answer under 350 words.
