"""Tests for the PawPal+ logic layer."""

from pawpal_system import Pet, Task


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
