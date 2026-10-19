"""Tests for the PawPal+ logic layer (pawpal_system.py).

Organized as: basics, sorting, filtering, recurrence, conflicts, planning, validation.
Dates are passed explicitly wherever possible so results don't depend on the day you run them.
"""

import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pawpal_system import Owner, Pet, Task, Scheduler

DAY = date(2026, 3, 10)  # fixed "today" for deterministic plan tests


def make_owner(minutes=120):
    """Build an owner with a dog (Biscuit) and a cat (Mochi), and return all three."""
    owner = Owner("Jordan", available_minutes=minutes)
    dog, cat = Pet("Biscuit", "dog"), Pet("Mochi", "cat")
    owner.add_pet(dog)
    owner.add_pet(cat)
    return owner, dog, cat


def names(tasks):
    """Return just the descriptions of a list of tasks, for easy assertions."""
    return [t.description for t in tasks]


# ----------------------------------------------------------------------- basics
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


def test_add_task_records_pet_name():
    """Pet.add_task should stamp the pet's name on the task so combined plans can name the pet."""
    pet = Pet("Biscuit", "dog")
    task = Task("Feeding", "08:00")
    pet.add_task(task)
    assert task.pet_name == "Biscuit"


def test_scheduler_reads_tasks_from_all_pets():
    """The Scheduler should see tasks from every pet through the Owner."""
    owner, dog, cat = make_owner()
    dog.add_task(Task("Walk", "07:30"))
    cat.add_task(Task("Breakfast", "08:00"))
    assert len(Scheduler(owner).get_all_tasks()) == 2


# ---------------------------------------------------------------------- sorting
def test_sort_by_time_orders_tasks_chronologically():
    """Tasks added out of order should come back earliest first, even with an unpadded time like '7:30'."""
    owner, dog, cat = make_owner()
    dog.add_task(Task("Evening", "19:00"))
    dog.add_task(Task("Early", "7:30"))
    cat.add_task(Task("Noon", "12:00"))
    assert names(Scheduler(owner).sort_by_time()) == ["Early", "Noon", "Evening"]


def test_sort_handles_midnight_and_end_of_day():
    """00:00 should sort first and 23:59 last."""
    owner, dog, _ = make_owner()
    dog.add_task(Task("Late", "23:59"))
    dog.add_task(Task("Midday", "12:00"))
    dog.add_task(Task("Midnight", "00:00"))
    assert names(Scheduler(owner).sort_by_time()) == ["Midnight", "Midday", "Late"]


def test_sort_with_no_tasks_returns_empty_list():
    """Sorting an owner with pets but no tasks (or no pets at all) should return an empty list, not crash."""
    owner, _, _ = make_owner()
    assert Scheduler(owner).sort_by_time() == []
    assert Scheduler(Owner("Nobody")).sort_by_time() == []


def test_sort_puts_earlier_due_date_first():
    """A task due earlier should come before a later-dated task, even if its clock time is later."""
    owner, dog, _ = make_owner()
    dog.add_task(Task("Tomorrow early", "06:00", due_date=DAY + timedelta(days=1)))
    dog.add_task(Task("Today late", "22:00", due_date=DAY))
    assert names(Scheduler(owner).sort_by_time()) == ["Today late", "Tomorrow early"]


# -------------------------------------------------------------------- filtering
def test_filter_by_pet_and_status():
    """filter_tasks should narrow by pet name, by completion, or by both."""
    owner, dog, cat = make_owner()
    walk, feed = Task("Walk", "07:30"), Task("Feed", "08:00")
    dog.add_task(walk)
    cat.add_task(feed)
    walk.mark_complete()
    s = Scheduler(owner)
    assert names(s.filter_tasks(pet_name="Mochi")) == ["Feed"]
    assert names(s.filter_tasks(completed=True)) == ["Walk"]
    assert s.filter_tasks(pet_name="Mochi", completed=True) == []


def test_filter_unknown_pet_returns_empty_and_no_filter_returns_all():
    """An unknown pet name matches nothing; no filters at all returns every task."""
    owner, dog, cat = make_owner()
    dog.add_task(Task("Walk", "07:30"))
    cat.add_task(Task("Feed", "08:00"))
    s = Scheduler(owner)
    assert s.filter_tasks(pet_name="Rex") == []
    assert len(s.filter_tasks()) == 2


def test_pet_with_no_tasks_is_handled():
    """A pet with no tasks should simply contribute nothing to the combined list."""
    owner, dog, cat = make_owner()
    dog.add_task(Task("Walk", "07:30"))
    assert names(Scheduler(owner).get_all_tasks()) == ["Walk"]
    assert cat.get_pending_tasks() == []


# ------------------------------------------------------------------- recurrence
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
    weekly = Task("Grooming", "19:00", frequency="weekly", due_date=DAY)
    once = Task("Vet", "09:00", frequency="once", due_date=DAY)
    dog.add_task(weekly)
    dog.add_task(once)
    s = Scheduler(owner)
    assert s.mark_task_complete(weekly).due_date == DAY + timedelta(days=7)
    assert s.mark_task_complete(once) is None
    assert len(dog.tasks) == 3


def test_recurrence_crosses_month_and_year_boundaries():
    """Dec 31 + 1 day should land on Jan 1 of the next year (timedelta handles calendar math)."""
    task = Task("Walk", "07:30", frequency="daily", due_date=date(2026, 12, 31))
    assert task.next_occurrence().due_date == date(2027, 1, 1)


def test_recurrence_copies_task_details():
    """The follow-up should keep the same description, time, duration, priority, and frequency."""
    task = Task("Meds", "12:00", duration_minutes=5, frequency="daily", priority="high", due_date=DAY)
    new = task.next_occurrence()
    assert (new.description, new.time, new.duration_minutes, new.frequency, new.priority) == \
           ("Meds", "12:00", 5, "daily", "high")
    assert new is not task


def test_completing_a_task_twice_does_not_duplicate_follow_up():
    """A second completion of the same recurring task must not create another follow-up."""
    owner, dog, _ = make_owner()
    task = Task("Walk", "07:30", frequency="daily", due_date=DAY)
    dog.add_task(task)
    s = Scheduler(owner)
    assert s.mark_task_complete(task) is not None
    assert s.mark_task_complete(task) is None
    assert len(dog.tasks) == 2


def test_recurring_task_not_attached_to_a_pet_raises_clear_error():
    """A recurring task with no pet can't be rescheduled; it should raise ValueError and stay incomplete."""
    owner, _, _ = make_owner()
    orphan = Task("Walk", "07:30", frequency="daily")
    with pytest.raises(ValueError):
        Scheduler(owner).mark_task_complete(orphan)
    assert orphan.completed is False


def test_next_days_task_is_not_in_todays_plan():
    """The follow-up for a completed daily task is due tomorrow, so today's plan must not include it."""
    owner, dog, _ = make_owner()
    task = Task("Walk", "07:30", frequency="daily", due_date=DAY)
    dog.add_task(task)
    s = Scheduler(owner)
    s.mark_task_complete(task)
    assert s.generate_daily_plan(on_date=DAY) == []
    assert names(s.generate_daily_plan(on_date=DAY + timedelta(days=1))) == ["Walk"]


# -------------------------------------------------------------------- conflicts
def test_conflict_detected_across_pets_at_same_time():
    """Two pending tasks at the same time (even for different pets) should produce one warning."""
    owner, dog, cat = make_owner()
    dog.add_task(Task("Vet", "08:00", due_date=DAY))
    cat.add_task(Task("Breakfast", "08:00", due_date=DAY))
    warnings = Scheduler(owner).detect_conflicts()
    assert len(warnings) == 1
    assert "Vet (Biscuit)" in warnings[0] and "Breakfast (Mochi)" in warnings[0]


def test_conflict_detected_for_same_pet():
    """Two tasks for one pet at the same time are also a conflict."""
    owner, dog, _ = make_owner()
    dog.add_task(Task("Walk", "08:00", due_date=DAY))
    dog.add_task(Task("Feed", "08:00", due_date=DAY))
    assert len(Scheduler(owner).detect_conflicts()) == 1


def test_three_tasks_in_one_slot_give_one_warning_naming_all():
    """Three tasks sharing a slot should produce a single warning that lists all three."""
    owner, dog, cat = make_owner()
    for pet, name in ((dog, "A"), (dog, "B"), (cat, "C")):
        pet.add_task(Task(name, "08:00", due_date=DAY))
    warnings = Scheduler(owner).detect_conflicts()
    assert len(warnings) == 1 and all(n in warnings[0] for n in ("A (", "B (", "C ("))


def test_no_conflict_for_different_times_or_completed_tasks():
    """Different times, or a completed task at the same time, should not raise a warning."""
    owner, dog, cat = make_owner()
    done = Task("Vet", "08:00", due_date=DAY)
    dog.add_task(done)
    cat.add_task(Task("Breakfast", "08:00", due_date=DAY))
    cat.add_task(Task("Play", "09:00", due_date=DAY))
    done.mark_complete()
    assert Scheduler(owner).detect_conflicts() == []


def test_same_time_on_different_days_is_not_a_conflict():
    """Today's 08:00 and tomorrow's 08:00 are different slots."""
    owner, dog, _ = make_owner()
    dog.add_task(Task("Walk", "08:00", due_date=DAY))
    dog.add_task(Task("Walk", "08:00", due_date=DAY + timedelta(days=1)))
    assert Scheduler(owner).detect_conflicts() == []


def test_conflict_check_with_nothing_scheduled():
    """No tasks (or no pets) means no warnings and no crash."""
    assert Scheduler(Owner("Nobody")).detect_conflicts() == []


# --------------------------------------------------------------------- planning
def test_plan_picks_high_priority_first_and_reports_skipped():
    """When time is short, high priority tasks win and the skipped task is recorded with a reason."""
    owner, dog, _ = make_owner(minutes=40)
    dog.add_task(Task("Grooming", "07:00", 30, priority="low", due_date=DAY))
    dog.add_task(Task("Meds", "12:00", 30, priority="high", due_date=DAY))
    s = Scheduler(owner)
    assert names(s.generate_daily_plan(on_date=DAY)) == ["Meds"]
    assert [t.description for t, _ in s.skipped_tasks] == ["Grooming"]
    assert "Grooming" in s.explain_plan()


def test_plan_is_ordered_by_time_not_priority():
    """Chosen tasks are shown in clock order even though they were picked by priority."""
    owner, dog, _ = make_owner()
    dog.add_task(Task("Evening", "19:00", 10, priority="high", due_date=DAY))
    dog.add_task(Task("Morning", "07:00", 10, priority="low", due_date=DAY))
    assert names(Scheduler(owner).generate_daily_plan(on_date=DAY)) == ["Morning", "Evening"]


def test_task_that_exactly_fits_remaining_time_is_included():
    """A task whose duration equals the minutes left should still fit (<=, not <)."""
    owner, dog, _ = make_owner(minutes=30)
    dog.add_task(Task("Walk", "07:00", 30, due_date=DAY))
    assert names(Scheduler(owner).generate_daily_plan(on_date=DAY)) == ["Walk"]


def test_zero_available_minutes_schedules_nothing():
    """With no time available every task is skipped and nothing crashes."""
    owner, dog, _ = make_owner(minutes=0)
    dog.add_task(Task("Walk", "07:00", 10, due_date=DAY))
    s = Scheduler(owner)
    assert s.generate_daily_plan(on_date=DAY) == []
    assert len(s.skipped_tasks) == 1


def test_equal_priority_tasks_are_taken_earliest_first():
    """When priorities tie, the earlier task gets the time first."""
    owner, dog, _ = make_owner(minutes=10)
    dog.add_task(Task("Later", "15:00", 10, priority="medium", due_date=DAY))
    dog.add_task(Task("Sooner", "09:00", 10, priority="medium", due_date=DAY))
    assert names(Scheduler(owner).generate_daily_plan(on_date=DAY)) == ["Sooner"]


def test_completed_tasks_are_not_planned():
    """Finished tasks should never show up in the plan."""
    owner, dog, _ = make_owner()
    done = Task("Walk", "07:00", due_date=DAY)
    dog.add_task(done)
    done.mark_complete()
    assert Scheduler(owner).generate_daily_plan(on_date=DAY) == []


def test_overdue_task_is_still_planned():
    """A pending task due yesterday should still appear in today's plan."""
    owner, dog, _ = make_owner()
    dog.add_task(Task("Missed meds", "08:00", due_date=DAY - timedelta(days=1)))
    assert names(Scheduler(owner).generate_daily_plan(on_date=DAY)) == ["Missed meds"]


def test_skipped_list_resets_between_plans():
    """Generating the plan twice should not double up the skipped list."""
    owner, dog, _ = make_owner(minutes=5)
    dog.add_task(Task("Walk", "07:00", 30, due_date=DAY))
    s = Scheduler(owner)
    s.generate_daily_plan(on_date=DAY)
    s.generate_daily_plan(on_date=DAY)
    assert len(s.skipped_tasks) == 1


def test_plan_with_no_tasks_still_explains():
    """An empty plan should produce an explanation instead of an error."""
    owner, _, _ = make_owner()
    assert "0 of" in Scheduler(owner).explain_plan()


# ------------------------------------------------------------------- validation
def test_invalid_priority_and_frequency_are_rejected():
    """Unknown priority or frequency values should raise ValueError at creation."""
    with pytest.raises(ValueError):
        Task("X", "08:00", priority="urgent")
    with pytest.raises(ValueError):
        Task("X", "08:00", frequency="monthly")


def test_invalid_times_are_rejected_and_loose_times_are_normalized():
    """Out-of-range or malformed times are rejected; '7:30' is accepted and becomes '07:30'."""
    for bad in ("25:00", "12:60", "", "noon", "07:30:00"):
        with pytest.raises(ValueError):
            Task("X", bad)
    assert Task("X", "7:30").time == "07:30"