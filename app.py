"""PawPal+ Streamlit UI, backed by the classes in pawpal_system.py."""

from datetime import date
from pathlib import Path

import streamlit as st

from pawpal_system import PRIORITY_BADGE, Owner, Pet, Scheduler, Task, task_emoji

DATA_FILE = Path("data.json")

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")


def load_owner() -> Owner:
    """Load the saved owner from data.json, or start a fresh one."""
    if DATA_FILE.exists():
        try:
            return Owner.load_from_json(DATA_FILE)
        except (ValueError, KeyError):
            st.warning("data.json could not be read, so PawPal+ started with an empty profile.")
    return Owner("Jordan")


def save() -> None:
    """Persist the current owner so data survives app restarts."""
    st.session_state.owner.save_to_json(DATA_FILE)


def save_and_rerun(*messages: tuple[str, str]) -> None:
    """Save, queue (kind, text) messages for the next run, and rerun so every section is fresh."""
    save()
    st.session_state.flash = list(messages)
    st.rerun()


def task_rows(tasks: list[Task]) -> list[dict]:
    """Turn tasks into display rows with emojis and priority badges."""
    return [
        {
            "Time": t.time, "Pet": t.pet_name, "Task": f"{task_emoji(t.description)} {t.description}",
            "Length": f"{t.duration_minutes} min", "Priority": PRIORITY_BADGE[t.priority],
            "Repeats": t.frequency, "Status": "✅ done" if t.completed else "⏳ pending",
        }
        for t in tasks
    ]


# Streamlit reruns this script on every click, so the Owner lives in session_state.
if "owner" not in st.session_state:
    st.session_state.owner = load_owner()
owner: Owner = st.session_state.owner
scheduler = Scheduler(owner)

st.title("🐾 PawPal+")
st.caption("Plan pet care across all your pets: sorted schedules, conflict warnings and recurring tasks.")

for kind, text in st.session_state.pop("flash", []):
    getattr(st, kind)(text)

# --- Owner and pets ---------------------------------------------------------
st.subheader("👤 Owner & pets")
new_name = st.text_input("Owner name", value=owner.name)
if new_name.strip() and new_name != owner.name:
    owner.name = new_name.strip()
    save()

with st.form("add_pet", clear_on_submit=True):
    col1, col2, col3 = st.columns([2, 1, 1])
    pet_name = col1.text_input("Pet name")
    species = col2.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
    age = col3.number_input("Age", min_value=0, max_value=40, value=1)
    if st.form_submit_button("Add pet"):
        if not pet_name.strip():
            st.error("Give your pet a name first.")
        else:
            try:
                owner.add_pet(Pet(pet_name.strip(), species, int(age)))
            except ValueError as err:
                st.error(str(err))
            else:
                save_and_rerun(("success", f"Added {pet_name.strip()} the {species}."))

if owner.pets:
    st.write(" · ".join(f"**{p.name}** ({p.species}, {p.age}y, {len(p.tasks)} task{'' if len(p.tasks) == 1 else 's'})" for p in owner.pets))
else:
    st.info("No pets yet. Add one above to start scheduling.")

# --- Add a task --------------------------------------------------------------
st.subheader("📝 Schedule a task")
if owner.pets:
    with st.form("add_task", clear_on_submit=True):
        col1, col2 = st.columns(2)
        task_pet = col1.selectbox("Pet", [p.name for p in owner.pets])
        description = col2.text_input("Task", placeholder="Morning walk")
        col3, col4, col5 = st.columns(3)
        task_date = col3.date_input("Date", value=date.today())
        task_time = col4.text_input("Time (HH:MM)", placeholder="07:30")
        duration = col5.number_input("Duration (min)", min_value=1, max_value=600, value=20)
        col6, col7 = st.columns(2)
        priority = col6.selectbox("Priority", ["high", "medium", "low"], index=1)
        frequency = col7.selectbox("Repeats", ["once", "daily", "weekly"])
        if st.form_submit_button("Add task"):
            try:
                if not description.strip():
                    raise ValueError("A task needs a description.")
                task = Task(description.strip(), task_time.strip(), int(duration),
                            priority, frequency, task_date)
            except ValueError as err:
                st.error(str(err))
            else:
                owner.get_pet(task_pet).add_task(task)
                clashes = [w for w in scheduler.detect_conflicts(task_date) if task.description in w]
                save_and_rerun(("success", f"Scheduled {task.description} for {task_pet} at {task.time}."),
                               *(("warning", f"Heads up: {w}") for w in clashes))

    with st.expander("🕒 Find a free slot"):
        col1, col2 = st.columns(2)
        slot_len = col1.number_input("How long (min)?", min_value=5, max_value=600, value=30, step=5)
        slot_day = col2.date_input("On", value=date.today(), key="slot_day")
        slot = scheduler.next_available_slot(int(slot_len), slot_day)
        if slot:
            st.success(f"The earliest free {slot_len}-minute slot on {slot_day:%b %d} starts at **{slot}**.")
        else:
            st.warning(f"No {slot_len}-minute gap left between {scheduler.day_start} and {scheduler.day_end}.")

st.divider()

# --- Schedule view -------------------------------------------------------------
st.subheader("📅 Schedule")
col1, col2, col3, col4 = st.columns(4)
view_day = col1.date_input("Day", value=date.today(), key="view_day")
pet_filter = col2.selectbox("Pet", ["All pets"] + [p.name for p in owner.pets])
status_filter = col3.selectbox("Status", ["All", "Pending", "Done"])
sort_mode = col4.selectbox("Sort by", ["Time", "Priority"])

tasks = scheduler.filter_tasks(
    pet_name=None if pet_filter == "All pets" else pet_filter,
    completed={"All": None, "Pending": False, "Done": True}[status_filter],
    day=view_day,
)
tasks = scheduler.sort_by_time(tasks) if sort_mode == "Time" else scheduler.sort_by_priority(tasks)

conflicts = scheduler.detect_conflicts(view_day)
if conflicts:
    st.warning("**Schedule conflicts:** these tasks overlap, so you can't do both at once. "
               "Move one, or use the plan below.\n\n" + "\n".join(f"- {c}" for c in conflicts))
elif tasks:
    st.success("No conflicts on this day.")

if tasks:
    st.table(task_rows(tasks))
    pending = [t for t in tasks if not t.completed]
    if pending:
        with st.form("complete_task"):
            choice = st.selectbox("Mark a task done", pending,
                                  format_func=lambda t: f"{t.time} · {t.pet_name} · {t.description}")
            if st.form_submit_button("Mark complete ✅"):
                follow_up = scheduler.mark_task_complete(choice.pet_name, choice.description, view_day)
                msg = f"Marked {choice.description} done."
                if follow_up:
                    msg += f" Next {follow_up.frequency} occurrence added for {follow_up.due_date:%a %b %d}."
                save_and_rerun(("success", msg))
else:
    st.info("Nothing scheduled for this view.")

# --- Time-blocked plan -----------------------------------------------------------
st.subheader("🧩 Suggested plan")
st.caption("High-priority tasks keep their time; lower-priority clashes move to the next free slot.")
plan = scheduler.build_daily_plan(view_day)
if plan:
    st.table([
        {"Start": e.start or "—", "Pet": e.task.pet_name,
         "Task": f"{task_emoji(e.task.description)} {e.task.description}", "Why": e.reason}
        for e in plan
    ])
else:
    st.info("No pending tasks to plan for this day.")
