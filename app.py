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

# ---------------------------------------------------------------------------
# Application "memory": Streamlit reruns this whole script on every click, so
# the Owner is stored in st.session_state and only created if it isn't there yet.
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_minutes=90)

owner: Owner = st.session_state.owner
scheduler = Scheduler(owner)  # cheap to build; always reads the owner's current data


def load_sample_data() -> None:
    """Fill an empty owner with two pets and a few tasks (two share 08:00 to show a conflict)."""
    biscuit, mochi = Pet("Biscuit", "dog", age=4), Pet("Mochi", "cat", age=2)
    owner.add_pet(biscuit)
    owner.add_pet(mochi)
    biscuit.add_task(Task("Grooming", "19:00", 40, "weekly", "low"))
    biscuit.add_task(Task("Vet check-in", "08:00", 15, "once", "high"))
    biscuit.add_task(Task("Morning walk", "07:30", 30, "daily", "high"))
    mochi.add_task(Task("Play time", "18:00", 20, "daily", "medium"))
    mochi.add_task(Task("Breakfast", "08:00", 10, "daily", "high"))
    mochi.add_task(Task("Medication", "12:00", 5, "daily", "high"))


with st.sidebar:
    st.header("Try it quickly")
    if st.button("Load sample data"):
        if owner.pets:
            st.warning("Sample data only loads into an empty owner. Remove your pets by refreshing the page.")
        else:
            load_sample_data()
            st.session_state.flash = "Loaded two pets and six tasks."
            st.rerun()

# A message saved before a rerun, so it survives the page refresh.
if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))

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
# Your tasks: sorted by time (Scheduler.sort_by_time) and filtered
# (Scheduler.filter_tasks), with conflict warnings (Scheduler.detect_conflicts)
# ---------------------------------------------------------------------------
st.subheader("Your tasks")
if not scheduler.get_all_tasks():
    st.info("No tasks yet. Add a pet and a task above, or load the sample data from the sidebar.")
else:
    # Conflicts first, so the owner sees problems before reading the table.
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        for message in conflicts:
            st.warning(f"{message}\n\nYou can't do both at once, so consider moving one of them to a different time.")
    else:
        st.success("No scheduling conflicts.")

    f1, f2 = st.columns(2)
    pet_choice = f1.selectbox("Show pet", ["All pets"] + [p.name for p in owner.pets])
    status_choice = f2.radio("Show status", ["Pending", "Completed", "All"], horizontal=True)
    shown = scheduler.filter_tasks(
        pet_name=None if pet_choice == "All pets" else pet_choice,
        completed={"Pending": False, "Completed": True, "All": None}[status_choice],
    )
    shown = scheduler.sort_by_time(shown)
    if shown:
        st.table([
            {"Date": str(t.due_date), "Time": t.time, "Pet": t.pet_name, "Task": t.description,
             "Min": t.duration_minutes, "Priority": t.priority, "Repeats": t.frequency,
             "Status": "✅ done" if t.completed else "⏳ pending"}
            for t in shown
        ])
    else:
        st.info("No tasks match that filter.")

    # -----------------------------------------------------------------------
    # Complete a task -> Scheduler.mark_task_complete() (daily/weekly tasks repeat)
    # -----------------------------------------------------------------------
    pending = scheduler.get_pending_tasks()
    if pending:
        st.markdown("**Mark a task complete**")
        with st.form("complete_task_form"):
            labels = [f"{t.due_date}  {t.time}  {t.description} ({t.pet_name})" for t in pending]
            choice = st.selectbox("Which task is done?", labels)
            if st.form_submit_button("Mark complete"):
                done = pending[labels.index(choice)]
                follow_up = scheduler.mark_task_complete(done)
                if follow_up:
                    st.session_state.flash = (
                        f"Done! Next '{done.description}' for {done.pet_name} is scheduled for {follow_up.due_date}.")
                else:
                    st.session_state.flash = f"Done! '{done.description}' is complete."
                st.rerun()  # redraw so the table above shows the new status

# ---------------------------------------------------------------------------
# Today's schedule -> Scheduler.generate_daily_plan() / explain_plan()
# ---------------------------------------------------------------------------
st.subheader("Today's schedule")
if st.button("Generate schedule"):
    plan = scheduler.generate_daily_plan()
    if not plan:
        st.warning("Nothing to schedule today. Add some tasks, or check your available minutes.")
    else:
        used = sum(t.duration_minutes for t in plan)
        st.success(f"Planned {len(plan)} task(s): {used} of {owner.available_minutes} available minutes.")
        st.table([
            {"Time": t.time, "Pet": t.pet_name, "Task": t.description,
             "Min": t.duration_minutes, "Priority": t.priority}
            for t in plan
        ])
        for task, reason in scheduler.skipped_tasks:
            st.info(f"Skipped '{task.description}' ({task.pet_name}): {reason}.")
        with st.expander("Why this plan?"):
            st.text(scheduler.explain_plan())