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

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
