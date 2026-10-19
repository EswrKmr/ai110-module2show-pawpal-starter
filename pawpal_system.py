"""PawPal+ logic layer: Task, Pet, Owner, and Scheduler."""

from collections import defaultdict
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

PRIORITY_RANKS = {"low": 1, "medium": 2, "high": 3}
RECURRENCE_DAYS = {"daily": 1, "weekly": 7}
FREQUENCIES = ("once",) + tuple(RECURRENCE_DAYS)


@dataclass
class Task:
    """A single pet care activity (walk, feeding, meds, grooming, ...)."""
    description: str
    time: str                      # start time as "HH:MM" (24-hour)
    duration_minutes: int = 15
    frequency: str = "once"        # "once" | "daily" | "weekly"
    priority: str = "medium"       # "low" | "medium" | "high"
    completed: bool = False
    pet_name: str = ""             # filled in automatically by Pet.add_task
    due_date: date = field(default_factory=date.today)

    def __post_init__(self) -> None:
        """Validate fields and normalize the time to zero-padded 'HH:MM' so it sorts correctly."""
        if self.priority not in PRIORITY_RANKS:
            raise ValueError(f"priority must be one of {list(PRIORITY_RANKS)}, got '{self.priority}'")
        if self.frequency not in FREQUENCIES:
            raise ValueError(f"frequency must be one of {list(FREQUENCIES)}, got '{self.frequency}'")
        # strptime accepts "7:30"; re-formatting makes it "07:30" so string sorting is chronological
        self.time = datetime.strptime(self.time, "%H:%M").strftime("%H:%M")

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def priority_rank(self) -> int:
        """Return a sortable number for the priority (high=3, medium=2, low=1)."""
        return PRIORITY_RANKS[self.priority]

    def next_occurrence(self) -> Optional["Task"]:
        """Return a fresh copy due one period later (daily +1 day, weekly +7), or None for one-off tasks."""
        days = RECURRENCE_DAYS.get(self.frequency)
        if days is None:
            return None
        return replace(self, completed=False, due_date=self.due_date + timedelta(days=days))

    def __str__(self) -> str:
        """Return a one-line, human-readable summary of the task."""
        status = "done" if self.completed else "pending"
        who = f" ({self.pet_name})" if self.pet_name else ""
        return (f"{self.time}  {self.description}{who} - {self.duration_minutes} min, "
                f"{self.frequency}, {self.priority} priority, due {self.due_date} [{status}]")


@dataclass
class Pet:
    """A pet and the care tasks that belong to it."""
    name: str
    species: str
    age: int = 0
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet and record the pet's name on the task."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet."""
        self.tasks.remove(task)

    def get_pending_tasks(self) -> List[Task]:
        """Return the tasks that are not yet completed."""
        return [t for t in self.tasks if not t.completed]


@dataclass
class Owner:
    """The pet owner: manages pets and the time available for care each day."""
    name: str
    available_minutes: int = 120
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet from this owner."""
        self.pets.remove(pet)

    def get_all_tasks(self) -> List[Task]:
        """Return every task from every pet, combined into one list."""
        return [task for pet in self.pets for task in pet.tasks]


class Scheduler:
    """The 'brain': retrieves, organizes, and plans tasks across all of an owner's pets."""

    def __init__(self, owner: Owner):
        """Create a scheduler that reads its tasks from the given owner."""
        self.owner = owner
        self.skipped_tasks: List[Tuple[Task, str]] = []

    def get_all_tasks(self) -> List[Task]:
        """Fetch all tasks for all pets through Owner.get_all_tasks()."""
        return self.owner.get_all_tasks()

    # ------------------------------------------------------------------ sorting
    def sort_by_time(self, tasks: Optional[List[Task]] = None) -> List[Task]:
        """Return tasks (default: all) in clock order; 'HH:MM' strings sort chronologically as text."""
        if tasks is None:
            tasks = self.get_all_tasks()
        return sorted(tasks, key=lambda t: (t.due_date, t.time))

    # --------------------------------------------------------------- filtering
    def filter_tasks(self, pet_name: Optional[str] = None,
                     completed: Optional[bool] = None) -> List[Task]:
        """Return tasks matching a pet name and/or completion status; None means 'don't filter on this'."""
        return [
            t for t in self.get_all_tasks()
            if (pet_name is None or t.pet_name == pet_name)
            and (completed is None or t.completed == completed)
        ]

    def get_pending_tasks(self, pet_name: Optional[str] = None) -> List[Task]:
        """Return incomplete tasks in time order, optionally for one pet only."""
        return self.sort_by_time(self.filter_tasks(pet_name=pet_name, completed=False))

    # --------------------------------------------------------------- recurrence
    def mark_task_complete(self, task: Task) -> Optional[Task]:
        """Complete a task; if it is daily/weekly, add the next occurrence to the same pet and return it."""
        task.mark_complete()
        follow_up = task.next_occurrence()
        if follow_up is not None:
            pet = next(p for p in self.owner.pets if p.name == task.pet_name)
            pet.add_task(follow_up)
        return follow_up

    # ---------------------------------------------------------------- conflicts
    def detect_conflicts(self, tasks: Optional[List[Task]] = None) -> List[str]:
        """Return a warning message for each start time shared by two or more pending tasks.

        Lightweight by design: it only compares exact start times (same date and HH:MM),
        across one pet or several, and never raises.
        """
        if tasks is None:
            tasks = self.get_all_tasks()
        slots: Dict[Tuple[date, str], List[Task]] = defaultdict(list)
        for t in tasks:
            if not t.completed:
                slots[(t.due_date, t.time)].append(t)
        return [
            f"Warning: {when} on {day} has {len(group)} tasks: "
            + ", ".join(f"{t.description} ({t.pet_name})" for t in group)
            for (day, when), group in sorted(slots.items()) if len(group) > 1
        ]

    # ----------------------------------------------------------------- planning
    def generate_daily_plan(self, on_date: Optional[date] = None) -> List[Task]:
        """Pick tasks due on or before the date by priority until time runs out, then order by time."""
        on_date = on_date or date.today()
        self.skipped_tasks = []
        remaining = self.owner.available_minutes
        chosen: List[Task] = []
        due = [t for t in self.get_pending_tasks() if t.due_date <= on_date]
        by_importance = sorted(due, key=lambda t: (-t.priority_rank(), t.time))
        for task in by_importance:
            if task.duration_minutes <= remaining:
                chosen.append(task)
                remaining -= task.duration_minutes
            else:
                self.skipped_tasks.append(
                    (task, f"needs {task.duration_minutes} min but only {remaining} min were left"))
        return self.sort_by_time(chosen)

    def explain_plan(self) -> str:
        """Explain which tasks were scheduled, which were skipped, and why."""
        plan = self.generate_daily_plan()
        used = sum(t.duration_minutes for t in plan)
        lines = [
            f"Plan uses {used} of {self.owner.available_minutes} available minutes.",
            "Tasks were chosen highest priority first, then shown in time order.",
        ]
        for task, reason in self.skipped_tasks:
            lines.append(f"Skipped '{task.description}' ({task.pet_name}): {reason}.")
        return "\n".join(lines)