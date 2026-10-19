"""Temporary demo script: sorting, filtering, conflicts, recurring tasks, and today's schedule."""

from pawpal_system import Owner, Pet, Task, Scheduler


def show(title: str, tasks) -> None:
    """Print a titled list of tasks, one per line."""
    print(f"\n{title}")
    print("-" * len(title))
    for t in tasks:
        print(f"  {t.time}  {t.pet_name:<8}{t.description:<16}{t.frequency:<7}{'done' if t.completed else 'pending'}")
    if not tasks:
        print("  (none)")


def print_schedule(scheduler: Scheduler) -> None:
    """Print today's schedule as a table, followed by the scheduler's explanation."""
    plan = scheduler.generate_daily_plan()
    print(f"\nToday's Schedule for {scheduler.owner.name}")
    print("=" * 62)
    print(f"{'Time':<7}{'Pet':<9}{'Task':<20}{'Min':<5}{'Priority':<9}")
    print("-" * 62)
    for t in plan:
        print(f"{t.time:<7}{t.pet_name:<9}{t.description:<20}{t.duration_minutes:<5}{t.priority:<9}")
    print("-" * 62)
    print(scheduler.explain_plan())


def main() -> None:
    """Build sample data (added out of order on purpose) and exercise each algorithm."""
    owner = Owner("Jordan", available_minutes=90)
    biscuit, mochi = Pet("Biscuit", "dog", age=4), Pet("Mochi", "cat", age=2)
    owner.add_pet(biscuit)
    owner.add_pet(mochi)

    # Deliberately out of time order; Vet check-in and Breakfast share 08:00.
    biscuit.add_task(Task("Grooming", "19:00", 40, "weekly", "low"))
    biscuit.add_task(Task("Vet check-in", "08:00", 15, "once", "high"))
    biscuit.add_task(Task("Morning walk", "7:30", 30, "daily", "high"))   # "7:30" is normalized to "07:30"
    mochi.add_task(Task("Play time", "18:00", 20, "daily", "medium"))
    mochi.add_task(Task("Breakfast", "08:00", 10, "daily", "high"))
    mochi.add_task(Task("Medication", "12:00", 5, "daily", "high"))

    scheduler = Scheduler(owner)

    show("All tasks, as added", scheduler.get_all_tasks())
    show("Sorted by time", scheduler.sort_by_time())
    show("Filtered: Mochi only", scheduler.filter_tasks(pet_name="Mochi"))

    print("\nConflict check")
    print("--------------")
    for warning in scheduler.detect_conflicts() or ["No conflicts."]:
        print(f"  {warning}")

    print_schedule(scheduler)

    walk = next(t for t in biscuit.tasks if t.description == "Morning walk")
    print("\nRecurring task demo")
    print("-------------------")
    print(f"  Completing: {walk}")
    follow_up = scheduler.mark_task_complete(walk)
    print(f"  New task created: {follow_up}")
    show("Filtered: completed tasks", scheduler.filter_tasks(completed=True))
    show("Filtered: Biscuit, pending", scheduler.filter_tasks(pet_name="Biscuit", completed=False))


if __name__ == "__main__":
    main()