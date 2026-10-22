"""Tests for the PawPal+ logic layer."""

from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task

TODAY = date(2026, 10, 22)


@pytest.fixture
def owner():
    """An owner with two pets and tasks added out of time order."""
    owner = Owner("Jordan")
    mochi, luna = Pet("Mochi", "dog"), Pet("Luna", "cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)
    mochi.add_task(Task("Evening walk", "18:30", 30, "medium", "daily", TODAY))
    mochi.add_task(Task("Morning walk", "07:30", 30, "high", "daily", TODAY))
    luna.add_task(Task("Play session", "18:00", 20, "low", "once", TODAY))
    luna.add_task(Task("Flea medication", "09:00", 5, "high", "weekly", TODAY))
    return owner


# --- Core classes ---------------------------------------------------------

def test_mark_complete_changes_status():
    task = Task("Morning walk", "07:30")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    pet = Pet("Mochi", "dog")
    assert len(pet.list_tasks()) == 0
    pet.add_task(Task("Breakfast", "08:00"))
    assert len(pet.list_tasks()) == 1
    assert pet.list_tasks()[0].pet_name == "Mochi"


@pytest.mark.parametrize("kwargs", [
    {"time": "25:00"}, {"time": "noon"}, {"time": "08:00", "priority": "urgent"},
    {"time": "08:00", "frequency": "monthly"}, {"time": "08:00", "duration_minutes": 0},
])
def test_task_rejects_invalid_input(kwargs):
    with pytest.raises(ValueError):
        Task("Walk", **kwargs)


def test_task_normalizes_time():
    assert Task("Walk", "9:05").time == "09:05"


def test_remove_task():
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Breakfast", "08:00"))
    assert pet.remove_task("Breakfast") is True
    assert pet.remove_task("Breakfast") is False
    assert pet.list_tasks() == []


def test_owner_rejects_duplicate_pet_names(owner):
    with pytest.raises(ValueError):
        owner.add_pet(Pet("mochi", "dog"))


def test_owner_collects_tasks_from_all_pets(owner):
    assert len(owner.get_all_tasks()) == 4
    assert {t.pet_name for t in owner.get_all_tasks()} == {"Mochi", "Luna"}


def test_pet_with_no_tasks_gives_empty_schedule():
    owner = Owner("Sam")
    owner.add_pet(Pet("Rex", "dog"))
    scheduler = Scheduler(owner)
    assert scheduler.todays_schedule(TODAY) == []
    assert scheduler.detect_conflicts(TODAY) == []


# --- Sorting and filtering -------------------------------------------------

def test_sort_by_time_is_chronological_across_pets(owner):
    times = [t.time for t in Scheduler(owner).sort_by_time()]
    assert times == ["07:30", "09:00", "18:00", "18:30"]


def test_sort_by_time_compares_as_times_not_strings():
    pet = Pet("Rex", "dog")
    pet.add_task(Task("Late", "10:00", due_date=TODAY))
    pet.add_task(Task("Early", "9:30", due_date=TODAY))  # no leading zero
    owner = Owner("Sam")
    owner.add_pet(pet)
    assert [t.description for t in Scheduler(owner).sort_by_time()] == ["Early", "Late"]


def test_sort_by_priority_then_time(owner):
    ordered = Scheduler(owner).sort_by_priority()
    assert [(t.priority, t.time) for t in ordered] == [
        ("high", "07:30"), ("high", "09:00"), ("medium", "18:30"), ("low", "18:00"),
    ]


def test_filter_by_pet_and_status(owner):
    scheduler = Scheduler(owner)
    assert {t.description for t in scheduler.filter_tasks(pet_name="luna")} == {
        "Play session", "Flea medication"}
    owner.get_pet("Luna").tasks[0].mark_complete()
    assert [t.description for t in scheduler.filter_tasks(completed=True)] == ["Play session"]
    assert len(scheduler.filter_tasks(completed=False)) == 3


# --- Recurrence ------------------------------------------------------------

def test_completing_daily_task_creates_next_day_task(owner):
    scheduler = Scheduler(owner)
    follow_up = scheduler.mark_task_complete("Mochi", "Morning walk")
    assert follow_up.due_date == TODAY + timedelta(days=1)
    assert follow_up.time == "07:30" and follow_up.completed is False
    assert follow_up in owner.get_pet("Mochi").tasks


def test_completing_weekly_task_creates_task_a_week_later(owner):
    follow_up = Scheduler(owner).mark_task_complete("Luna", "Flea medication")
    assert follow_up.due_date == TODAY + timedelta(weeks=1)


def test_completing_one_off_task_creates_nothing(owner):
    scheduler = Scheduler(owner)
    assert scheduler.mark_task_complete("Luna", "Play session") is None
    assert len(owner.get_all_tasks()) == 4


def test_completing_unknown_task_raises(owner):
    with pytest.raises(ValueError):
        Scheduler(owner).mark_task_complete("Luna", "Bath")


# --- Conflict detection ----------------------------------------------------

def test_detects_exact_same_time_across_pets(owner):
    owner.get_pet("Luna").add_task(Task("Breakfast", "07:30", 10, due_date=TODAY))
    warnings = Scheduler(owner).detect_conflicts(TODAY)
    assert len(warnings) == 1
    assert "Morning walk" in warnings[0] and "Breakfast" in warnings[0]
    assert "different pets" in warnings[0]


def test_detects_overlapping_durations_for_same_pet(owner):
    owner.get_pet("Mochi").add_task(Task("Brushing", "07:45", 10, due_date=TODAY))
    warnings = Scheduler(owner).detect_conflicts(TODAY)
    assert len(warnings) == 1 and "same pet" in warnings[0]


def test_back_to_back_tasks_do_not_conflict(owner):
    owner.get_pet("Mochi").add_task(Task("Breakfast", "08:00", 10, due_date=TODAY))
    assert Scheduler(owner).detect_conflicts(TODAY) == []


def test_completed_tasks_are_not_conflicts(owner):
    owner.get_pet("Luna").add_task(Task("Breakfast", "07:30", 10, due_date=TODAY))
    scheduler = Scheduler(owner)
    scheduler.mark_task_complete("Mochi", "Morning walk")
    assert scheduler.detect_conflicts(TODAY) == []


# --- Next available slot and time-blocked plan ------------------------------

def test_next_available_slot_skips_busy_windows(owner):
    scheduler = Scheduler(owner)
    assert scheduler.next_available_slot(30, TODAY) == "07:00"
    assert scheduler.next_available_slot(45, TODAY) == "08:00"
    # 18:00-18:20 and 18:30-19:00 are busy, and the 10-minute gap between them is too short
    assert scheduler.next_available_slot(30, TODAY, not_before="17:45") == "19:00"


def test_next_available_slot_returns_none_when_day_is_full():
    pet = Pet("Rex", "dog")
    pet.add_task(Task("Long hike", "07:00", 14 * 60, due_date=TODAY))
    owner = Owner("Sam")
    owner.add_pet(pet)
    assert Scheduler(owner).next_available_slot(15, TODAY) is None


def test_daily_plan_moves_lower_priority_clash(owner):
    owner.get_pet("Luna").add_task(Task("Grooming", "07:30", 15, "low", due_date=TODAY))
    plan = {e.task.description: e for e in Scheduler(owner).build_daily_plan(TODAY)}
    assert plan["Morning walk"].start == "07:30"
    assert plan["Grooming"].start == "08:00"
    assert "Morning walk" in plan["Grooming"].reason


# --- Persistence -------------------------------------------------------------

def test_json_round_trip(owner, tmp_path):
    Scheduler(owner).mark_task_complete("Mochi", "Morning walk")
    path = tmp_path / "data.json"
    owner.save_to_json(path)
    loaded = Owner.load_from_json(path)
    assert loaded.name == "Jordan"
    assert [p.name for p in loaded.pets] == ["Mochi", "Luna"]
    original = sorted((t.pet_name, t.description, t.due_date, t.completed) for t in owner.get_all_tasks())
    restored = sorted((t.pet_name, t.description, t.due_date, t.completed) for t in loaded.get_all_tasks())
    assert original == restored
