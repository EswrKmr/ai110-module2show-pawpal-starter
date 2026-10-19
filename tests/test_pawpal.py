"""Tests for the PawPal+ logic layer."""

import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pawpal_system import Owner, Pet, Task, Scheduler


def make_owner():
    """Build an owner with a dog and a cat for the tests below."""
    owner = Owner("Jordan")
    dog, cat = Pet("Biscuit", "dog"), Pet("Mochi", "cat")
    owner.add_pet(dog)
    owner.add_pet(cat)
    return owner, dog, cat


def test_mark_complete_changes_status():
    """Calling mark_complete() should flip a task's completed flag to True."""
    task = Task("Morning walk", "07:30")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    """Adding a task to a Pet should increase that pet's task count by one."""
    pet = Pet("Biscuit", "dog")
    assert len(pet.tasks) == 0
    pet.add_task(Task("Feeding", "08:00"))
    assert len(pet.tasks) == 1


def test_scheduler_reads_tasks_from_all_pets():
    """The Scheduler should see tasks from every pet through the Owner."""
    owner, dog, cat = make_owner()
    dog.add_task(Task("Walk", "07:30"))
    cat.add_task(Task("Breakfast", "08:00"))
    assert len(Scheduler(owner).get_all_tasks()) == 2


def test_sort_by_time_orders_tasks_chronologically():
    """Tasks added out of order should come back earliest first, even with an unpadded time like '7:30'."""
    owner, dog, cat = make_owner()
    dog.add_task(Task("Evening", "19:00"))
    dog.add_task(Task("Early", "7:30"))
    cat.add_task(Task("Noon", "12:00"))
    assert [t.description for t in Scheduler(owner).sort_by_time()] == ["Early", "Noon", "Evening"]


def test_filter_by_pet_and_status():
    """filter_tasks should narrow by pet name, by completion, or by both."""
    owner, dog, cat = make_owner()
    walk, feed = Task("Walk", "07:30"), Task("Feed", "08:00")
    dog.add_task(walk)
    cat.add_task(feed)
    walk.mark_complete()
    s = Scheduler(owner)
    assert [t.description for t in s.filter_tasks(pet_name="Mochi")] == ["Feed"]
    assert [t.description for t in s.filter_tasks(completed=True)] == ["Walk"]
    assert s.filter_tasks(pet_name="Mochi", completed=True) == []


def test_daily_task_creates_next_day_occurrence():
    """Completing a daily task should add a pending copy due one day later to the same pet."""
    owner, dog, _ = make_owner()
    task = Task("Walk", "07:30", frequency="daily")
    dog.add_task(task)
    new = Scheduler(owner).mark_task_complete(task)
    assert task.completed is True
    assert new.due_date == date.today() + timedelta(days=1)
    assert new.completed is False and new.pet_name == "Biscuit"
    assert len(dog.tasks) == 2


def test_weekly_task_recurs_in_seven_days_and_once_does_not_recur():
    """Weekly tasks recur after 7 days; one-off tasks create nothing new."""
    owner, dog, _ = make_owner()
    weekly, once = Task("Grooming", "19:00", frequency="weekly"), Task("Vet", "09:00", frequency="once")
    dog.add_task(weekly)
    dog.add_task(once)
    s = Scheduler(owner)
    assert s.mark_task_complete(weekly).due_date == date.today() + timedelta(days=7)
    assert s.mark_task_complete(once) is None
    assert len(dog.tasks) == 3


def test_next_days_task_is_not_in_todays_plan():
    """The follow-up for a completed daily task is due tomorrow, so today's plan must not include it."""
    owner, dog, _ = make_owner()
    task = Task("Walk", "07:30", frequency="daily")
    dog.add_task(task)
    s = Scheduler(owner)
    s.mark_task_complete(task)
    assert s.generate_daily_plan() == []


def test_conflict_detected_across_pets_at_same_time():
    """Two pending tasks at the same time (even for different pets) should produce one warning."""
    owner, dog, cat = make_owner()
    dog.add_task(Task("Vet", "08:00"))
    cat.add_task(Task("Breakfast", "08:00"))
    warnings = Scheduler(owner).detect_conflicts()
    assert len(warnings) == 1 and "Vet (Biscuit)" in warnings[0] and "Breakfast (Mochi)" in warnings[0]


def test_no_conflict_for_different_times_or_completed_tasks():
    """Different times, or a completed task at the same time, should not raise a warning."""
    owner, dog, cat = make_owner()
    done = Task("Vet", "08:00")
    dog.add_task(done)
    cat.add_task(Task("Breakfast", "08:00"))
    cat.add_task(Task("Play", "09:00"))
    done.mark_complete()
    assert Scheduler(owner).detect_conflicts() == []


def test_invalid_input_is_rejected():
    """Bad priority, frequency, or time strings should raise ValueError at creation."""
    for kwargs in ({"priority": "urgent"}, {"frequency": "monthly"}):
        try:
            Task("X", "08:00", **kwargs)
            assert False, "expected ValueError"
        except ValueError:
            pass
    try:
        Task("X", "25:99")
        assert False, "expected ValueError"
    except ValueError:
        pass