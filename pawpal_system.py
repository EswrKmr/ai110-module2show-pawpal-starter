"""PawPal+ logic layer: class skeletons (no scheduling logic yet)."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Task:
    """A single pet care task (walk, feeding, meds, grooming, ...)."""
    title: str
    duration_minutes: int
    priority: str = "medium"  # "low" | "medium" | "high"
    category: str = "general"
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as done."""
        pass

    def priority_rank(self) -> int:
        """Return a number for the priority so tasks can be sorted (e.g. high=3)."""
        pass


@dataclass
class Pet:
    """A pet and the care tasks that belong to it."""
    name: str
    species: str
    age: int = 0
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a care task to this pet."""
        pass

    def remove_task(self, title: str) -> None:
        """Remove a task by title."""
        pass

    def get_pending_tasks(self) -> List[Task]:
        """Return tasks that are not yet completed."""
        pass


@dataclass
class Owner:
    """The pet owner: holds pets and the daily time/preferences constraints."""
    name: str
    available_minutes: int = 120
    preferences: List[str] = field(default_factory=list)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        pass

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet from this owner."""
        pass

    def get_all_tasks(self) -> List[Task]:
        """Collect pending tasks across all of the owner's pets."""
        pass


class Scheduler:
    """Builds a daily plan from an owner's tasks and constraints."""

    def __init__(self, owner: Owner):
        self.owner = owner

    def generate_daily_plan(self) -> List[Task]:
        """Choose and order tasks to fit the owner's available time by priority."""
        pass

    def explain_plan(self) -> str:
        """Return a human-readable explanation of why the plan looks the way it does."""
        pass