# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Today's Schedule for Jordan
==============================================================
Time   Pet      Task                Min  Priority 
--------------------------------------------------------------
07:30  Biscuit  Morning walk        30   high     
08:00  Mochi    Breakfast           10   high     
12:00  Mochi    Medication          5    high     
18:00  Mochi    Play time           20   medium   
--------------------------------------------------------------
Plan uses 65 of 90 available minutes.
Tasks were chosen highest priority first, then shown in time order.
Skipped 'Grooming' (Biscuit): needs 40 min but only 25 min were left.
```

```
# e.g.:
# Daily plan for Biscuit (Golden Retriever):
#   08:00 — Morning walk (30 min) [priority: high]
#   09:00 — Feeding (10 min) [priority: high]
#   ...
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
python -m pytest

# Run with coverage:
pytest --cov
```

Sample test output:
collected 11 items                                                                                                                                   

tests/test_pawpal.py ...........                                                                                                               [100%]

================================================================= 11 passed in 0.03s ==
```

```

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

Set your name and how many minutes you have available today
Add pets (name, species, age)
Add tasks to a pet (description, time, duration, frequency, priority)
See all tasks sorted by time, and filter them by pet and by status
See a warning whenever two pending tasks share a start time
Mark tasks complete (daily and weekly tasks reappear for the next day or week)
Generate today's schedule, with a summary, skipped tasks, and an explanation

## Testing PawPal+

Run the full suite from the project folder:

```bash
python -m pytest
```

The 35 tests cover:

- **Sorting:** chronological order, unpadded times like `7:30`, midnight and 23:59, due-date ordering, and empty lists
- **Filtering:** by pet, by status, by both, unknown pets, and pets with no tasks
- **Recurrence:** daily (+1 day) and weekly (+7 days), month and year rollover, copied task details, one-off tasks, completing twice, and unattached tasks
- **Conflicts:** same time across pets and within one pet, three-way conflicts, different days, and completed tasks
- **Planning:** priority-first selection, time-ordered output, exact-fit tasks, zero available minutes, ties, overdue tasks, and skipped-task reporting
- **Validation:** bad priorities, frequencies, and times are rejected

Sample test output:

```
platform darwin -- Python 3.14.3, pytest-9.1.1, pluggy-1.7.0
rootdir: /Users/eashukumar/Downloads/ai110-module2show-pawpal-starter-main
plugins: anyio-4.15.1
collected 35 items                                                                                                                                   

tests/test_pawpal.py ...................................                                                                                       [100%]

================================================================= 35 passed in 0.04s =
```

**Confidence Level:(4/5)**

The scheduling logic is well covered, including edge cases that exposed two real bugs, and all tests pass. I stopped at four stars because the Streamlit UI has no automated tests, conflict detection only compares exact start times and not overlapping durations, and the greedy planner doesn't search for the best combination of tasks.

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
