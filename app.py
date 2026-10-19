"""PawPal+ Streamlit UI: connects the browser to the logic layer in pawpal_system.py."""

import streamlit as st

from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("A pet care planner that fits your pets' tasks into the time you have.")

with st.expander("Scenario", expanded=False):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.
Add your pets and their tasks below, then generate a daily schedule that fits
the time you have and explains what it chose.
"""
    )

st.divider()

# ---------------------------------------------------------------------------
# Application "memory": Streamlit reruns this whole script on every click, so
# the Owner is stored in st.session_state and only created if it isn't there yet.
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_minutes=90)

owner: Owner = st.session_state.owner

# ---------------------------------------------------------------------------
# Owner info
# ---------------------------------------------------------------------------
st.subheader("Owner")
col1, col2 = st.columns(2)
owner.name = col1.text_input("Your name", value=owner.name)
owner.available_minutes = col2.number_input(
    "Minutes available today", min_value=0, max_value=1440, step=5, value=owner.available_minutes
)

# ---------------------------------------------------------------------------
# Add a pet -> Owner.add_pet(Pet(...))
# ---------------------------------------------------------------------------
st.subheader("Add a pet")
with st.form("add_pet_form", clear_on_submit=True):
    c1, c2, c3 = st.columns(3)
    pet_name = c1.text_input("Pet name")
    species = c2.selectbox("Species", ["dog", "cat", "bird", "rabbit", "other"])
    age = c3.number_input("Age", min_value=0, max_value=40, step=1)
    if st.form_submit_button("Add pet"):
        name = pet_name.strip()
        if not name:
            st.error("Please enter a pet name.")
        elif name in [p.name for p in owner.pets]:
            st.error(f"You already have a pet named {name}.")
        else:
            owner.add_pet(Pet(name=name, species=species, age=int(age)))
            st.success(f"Added {name} the {species}!")

# ---------------------------------------------------------------------------
# Add a task -> Pet.add_task(Task(...))
# ---------------------------------------------------------------------------
st.subheader("Add a task")
if not owner.pets:
    st.info("Add a pet first, then you can give it tasks.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        target = st.selectbox("For which pet?", [p.name for p in owner.pets])
        description = st.text_input("Task", placeholder="e.g. Morning walk")
        c1, c2, c3, c4 = st.columns(4)
        start = c1.time_input("Time")
        duration = c2.number_input("Minutes", min_value=1, max_value=480, value=15, step=5)
        frequency = c3.selectbox("Frequency", ["once", "daily", "weekly"])
        priority = c4.selectbox("Priority", ["high", "medium", "low"], index=1)
        if st.form_submit_button("Add task"):
            if not description.strip():
                st.error("Please describe the task.")
            else:
                pet = next(p for p in owner.pets if p.name == target)
                try:
                    pet.add_task(Task(
                        description=description.strip(),
                        time=start.strftime("%H:%M"),
                        duration_minutes=int(duration),
                        frequency=frequency,
                        priority=priority,
                    ))
                    st.success(f"Added '{description.strip()}' for {target}.")
                except ValueError as err:
                    st.error(str(err))

# ---------------------------------------------------------------------------
# Show what's currently stored in memory
# ---------------------------------------------------------------------------
st.subheader("Your pets and tasks")
if not owner.pets:
    st.write("No pets yet.")
for pet in owner.pets:
    st.markdown(f"**{pet.name}** ({pet.species}, age {pet.age}) - {len(pet.tasks)} task(s)")
    if pet.tasks:
        st.table([
            {"Time": t.time, "Task": t.description, "Min": t.duration_minutes,
             "Frequency": t.frequency, "Priority": t.priority,
             "Done": "yes" if t.completed else "no"}
            for t in sorted(pet.tasks, key=lambda t: t.time)
        ])

# ---------------------------------------------------------------------------
# Conflict warnings -> Scheduler.detect_conflicts()
# ---------------------------------------------------------------------------
for warning in Scheduler(owner).detect_conflicts():
    st.warning(warning)

# ---------------------------------------------------------------------------
# Complete a task -> Scheduler.mark_task_complete() (daily/weekly tasks repeat)
# ---------------------------------------------------------------------------
pending = Scheduler(owner).get_pending_tasks()
if pending:
    st.subheader("Complete a task")
    with st.form("complete_task_form"):
        labels = [f"{t.time}  {t.description} ({t.pet_name}) - due {t.due_date}" for t in pending]
        choice = st.selectbox("Which task is done?", labels)
        if st.form_submit_button("Mark complete"):
            done = pending[labels.index(choice)]
            follow_up = Scheduler(owner).mark_task_complete(done)
            if follow_up:
                st.success(f"Done! Next '{done.description}' is scheduled for {follow_up.due_date}.")
            else:
                st.success(f"Done! '{done.description}' is complete.")

# ---------------------------------------------------------------------------
# Generate the plan -> Scheduler(owner).generate_daily_plan()
# ---------------------------------------------------------------------------
st.subheader("Today's schedule")
if st.button("Generate schedule"):
    scheduler = Scheduler(owner)
    plan = scheduler.generate_daily_plan()
    if not plan:
        st.warning("No tasks to schedule yet.")
    else:
        st.table([
            {"Time": t.time, "Pet": t.pet_name, "Task": t.description,
             "Min": t.duration_minutes, "Priority": t.priority}
            for t in plan
        ])
        st.text(scheduler.explain_plan())