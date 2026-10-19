# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?
I chose four classes. Task holds one care activity (title, duration, priority, category, completion status). Pet holds a pet’s details and its list of tasks. Owner holds the owner’s time budget and preferences, and manages their pets. Scheduler is the “brain”: it gathers the owner’s pending tasks and builds a priority-ordered daily plan that fits the available time, then explains its choices. I used dataclasses for Task, Pet, and Owner since they mostly store data, and kept Scheduler a regular class since it mainly holds behavior.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

After reviewing my skeleton, I made three changes. First, I added a pet_name field to Task because Owner.get_all_tasks() combines tasks from every pet, and without it the plan couldn’t say which pet a task was for. Second, I gave Scheduler a skipped_tasks list, since explain_plan() needs to say why tasks were left out and not only why others were chosen. Third, I added validation for priority so a misspelled value fails immediately instead of silently ranking wrong. I considered adding a separate ScheduledItem class to hold start times but decided to defer it to keep the design simple.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

The scheduler considers three things: the owner's available minutes, each task's priority, and each task's due date. I put priority first because missing a medication is a much worse outcome than skipping grooming. When priorities tie, the earlier task wins. Once tasks are chosen, they're displayed in clock order, because that's how a person actually follows a day. Tasks due today or earlier are included, so an overdue task isn't silently dropped, and tomorrow's recurring task stays out of today's plan. I left out owner preferences because nothing in the scheduler could act on them yet.

**b. Tradeoffs**

Conflict detection only compares exact start times. Two tasks at 08:00 are flagged, but a 30-minute walk at 07:45 and a feeding at 08:00 are not, even though they overlap. I chose this because exact matching is simple to explain and test, and it never crashes the program, since it only returns warnings. Checking real overlap would need start and end times for every pair of tasks, plus edge cases like back-to-back tasks and tasks that cross midnight. For a first version, an owner mostly needs to know about double-booked slots, and a missed partial overlap is a minor problem. The cost is that the plan can quietly schedule two tasks that collide.

A second tradeoff is that the planner is greedy: it takes tasks by priority until time runs out, so one long high-priority task can use up time that several shorter tasks could have shared. Finding the best combination is a harder optimization problem, and a predictable "most important first" rule is easier for an owner to trust.

---

## 3. AI Collaboration

**a. How you used AI**

 I used an AI assistant to draft the Mermaid UML diagram, generate the class skeleton, review that skeleton for missing relationships and bottlenecks, and then write the full implementation, demo script, and tests. Its design review flagged that tasks didn’t know their pet, that the plan had no way to explain skipped tasks, that string priorities were fragile, and that preferences was a list nothing could act on.

**b. Judgment and verification**

I accepted the pet_name field, skipped_tasks, and input validation, because each fixed a concrete problem I could see in the output. I also accepted the dataclass structure and the rule that the Scheduler must read tasks only through Owner.get_all_tasks(), which keeps it working across multiple pets. I deferred the ScheduledItem class and the preferences redesign. They would add complexity before I had working scheduling logic, and I can add them in a later phase if the plan output needs them. I ran python main.py and checked the schedule by hand: the owner has 90 minutes and 105 minutes of tasks, so exactly one low-priority task (grooming) should be skipped, and it was, with the correct reason. I also wrote tests for task completion, task addition, and the Scheduler seeing tasks from multiple pets, and ran them with python -m pytest. The AI’s first skeleton was clean but missed relationships I only noticed when I asked for a review. Next time I’ll ask for that review before writing any logic, and I’ll check each suggested change against the demo output, not only against whether the code runs.

---

## 4. Testing and Verification

**a. What you tested**

I wrote 35 pytest tests covering sorting, filtering, recurrence, conflict detection, planning, and input validation. They include edge cases like pets with no tasks, an owner with no pets, zero available minutes, a task that exactly fits the remaining time, midnight and 23:59, and recurrence across a year boundary. These mattered because the scheduler's value is in its decisions, and the decisions are easiest to get wrong at the edges. Two of the edge cases exposed real bugs in mark_task_complete(): completing a task twice created duplicate follow-ups, and an unattached recurring task crashed with a confusing StopIteration. Both are fixed and covered by tests.

**b. Confidence**

My confidence is 4 out of 5. The logic is well covered and all tests pass. I stopped short of 5 because the Streamlit UI has no automated tests, conflict detection ignores overlapping durations, and pets and tasks aren't saved between sessions. With more time I would test overlapping tasks (once I add real overlap detection), tasks that cross midnight, two pets with the same name, and the UI flows using Streamlit's testing tools.

---

## 5. Reflection

**a. What went well**

I'm most satisfied with the separation between the logic layer and the UI. Because pawpal_system.py knows nothing about Streamlit, I could test every behavior from the terminal and with pytest before building any screens, and the UI ended up being a thin layer of forms and tables over methods I already trusted.

**b. What you would improve**

I would add real overlap detection using each task's start time plus duration, save pets and tasks to a file so they survive a page refresh, and use the owner's preferences (like a preferred walk time) when choosing times. I would also add automated tests for the Streamlit UI.

**c. Key takeaway**

AI is very good at producing code and much less reliable at deciding what the system should be. The decisions that shaped PawPal+ were mine: four classes with clear responsibilities, the Scheduler reading only through Owner.get_all_tasks(), exact-time conflicts as an accepted limitation, and deferring extra classes until they were needed. Being the lead architect meant three habits: deciding the design before generating code, treating each AI suggestion as a proposal to evaluate against simplicity and readability, and verifying behavior by running things. Every real bug I found came from running code, not from reading it. The AI made me faster, but the judgment about what to keep, what to simplify, and what to leave out is what made the result a coherent system.
