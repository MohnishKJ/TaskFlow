import streamlit as st
from datetime import datetime, timedelta
import json
import os
import pandas as pd
import plotly.express as px

# Initialize session state for persistent storage
if "tasks" not in st.session_state:
    st.session_state.tasks = {}
if "todo_list" not in st.session_state:
    st.session_state.todo_list = []

# Function to save data to a local JSON file
def save_data():
    with open("task_logger_data.json", "w") as f:
        json.dump({"tasks": st.session_state.tasks, "todo_list": st.session_state.todo_list}, f)

# Function to load data from a local JSON file
def load_data():
    if os.path.exists("task_logger_data.json"):
        try:
            with open("task_logger_data.json", "r") as f:
                data = json.load(f)
                # Ensure backward compatibility for tasks and to-do list
                st.session_state.tasks = data.get("tasks", {})
                todo_list = data.get("todo_list", [])
                # Add 'deadline' key to old to-do items if missing
                for todo in todo_list:
                    if "deadline" not in todo:
                        todo["deadline"] = str(datetime.now().date())  # Default deadline: today
                st.session_state.todo_list = todo_list
        except (json.JSONDecodeError, FileNotFoundError):
            # If the file is empty or invalid, reset to default values
            st.session_state.tasks = {}
            st.session_state.todo_list = []
            save_data()

# Load data on app start
load_data()

# Custom CSS for professional UI
st.markdown("""
    <style>
    .main {
        padding: 20px;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
    }
    .stProgress>div>div>div {
        background-color: #4CAF50;
    }
    .calendar-tile {
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        color: white;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .calendar-tile:hover {
        transform: scale(1.1);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .completed {
        background-color: #4CAF50;
    }
    .incomplete {
        background-color: #e0e0e0;
        color: black;
    }
    </style>
""", unsafe_allow_html=True)

# App Title
st.title("TaskFlow: Your Daily Productivity Companion")

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Track Progress", "Log Tasks", "Reset Data"])

# Track Page
if page == "Track Progress":
    st.header("Track Your Progress")

    # Tile-Based Calendar View
    st.subheader("Progress Tracker (Current Month)")
    current_date = datetime.now().date()
    current_month = current_date.month
    current_year = current_date.year
    first_day_of_month = datetime(current_year, current_month, 1).date()
    last_day_of_month = (datetime(current_year, current_month + 1, 1) - timedelta(days=1)).date()

    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    columns = [col1, col2, col3, col4, col5, col6, col7]

    for day in range((last_day_of_month - first_day_of_month).days + 1):
        current_day = first_day_of_month + timedelta(days=day)
        with columns[current_day.weekday()]:
            if str(current_day) in st.session_state.tasks:
                # Highlight days with tasks
                st.markdown(f"<div class='calendar-tile completed'>{current_day.day}</div>", unsafe_allow_html=True)
            else:
                # Empty tiles for days without tasks
                st.markdown(f"<div class='calendar-tile incomplete'>{current_day.day}</div>", unsafe_allow_html=True)

    # Streak Tracking
    st.subheader("Streak Tracker")
    sorted_dates = sorted([datetime.strptime(date, "%Y-%m-%d").date() for date in st.session_state.tasks.keys()])
    current_streak = 0
    if sorted_dates:
        last_date = sorted_dates[-1]
        while last_date in sorted_dates:
            current_streak += 1
            last_date -= timedelta(days=1)

    st.progress(current_streak / 30 if sorted_dates else 0)
    st.write(f"Current Streak: {current_streak} days")

    # Statistics and Insights
    st.subheader("Statistics")
    if st.session_state.tasks:
        all_tasks = [task for tasks in st.session_state.tasks.values() for task in tasks]
        task_counts = pd.DataFrame(all_tasks).groupby("type").size().reset_index(name="count")
        fig_pie = px.pie(task_counts, values="count", names="type", title="Task Distribution")
        st.plotly_chart(fig_pie)

        daily_counts = pd.DataFrame(
            [(date, len(tasks)) for date, tasks in st.session_state.tasks.items()],
            columns=["Date", "Tasks"]
        )
        fig_bar = px.bar(daily_counts, x="Date", y="Tasks", title="Tasks Per Day")
        st.plotly_chart(fig_bar)
    else:
        st.write("No tasks logged yet.")

# Log Tasks Page
elif page == "Log Tasks":
    st.header("Log Your Tasks")

    # Task Logging Form
    st.subheader("Log a Task")
    with st.form("task_form"):
        task_type = st.selectbox("Task Type", ["Coding", "Exercise", "Reading", "Other"])
        task_description = st.text_area("Task Description")
        priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        submit_task = st.form_submit_button("Log Task")
        if submit_task:
            today = str(datetime.now().date())
            if today not in st.session_state.tasks:
                st.session_state.tasks[today] = []
            st.session_state.tasks[today].append({
                "type": task_type,
                "description": task_description,
                "priority": priority
            })
            save_data()
            st.success(f"Logged {task_type} for today ({today})")

    # To-Do List
    st.subheader("To-Do List")
    new_todo = st.text_input("Add a new task:")
    priority = st.selectbox("Priority", ["High", "Medium", "Low"], key="todo_priority")
    deadline = st.date_input("Deadline Date")
    if st.button("Add Task"):
        st.session_state.todo_list.append({
            "task": new_todo,
            "completed": False,
            "priority": priority,
            "deadline": str(deadline)
        })
        save_data()

    # Display To-Do List
    if st.session_state.todo_list:
        st.subheader("Your To-Do List")
        for idx, todo in enumerate(st.session_state.todo_list):
            col1, col2, col3, col4 = st.columns([0.1, 0.4, 0.3, 0.2])
            with col1:
                completed = st.checkbox("", key=f"todo_{idx}", value=todo["completed"])
                st.session_state.todo_list[idx]["completed"] = completed
            with col2:
                st.write(todo["task"] if not completed else f"~~{todo['task']}~~")
            with col3:
                st.write(f"Due: {todo['deadline']}")
            with col4:
                if st.button("Delete", key=f"delete_{idx}"):
                    st.session_state.todo_list.pop(idx)
                    save_data()
    else:
        st.write("No tasks in your to-do list.")

# Reset Page
elif page == "Reset Data":
    st.header("Reset Data")
    st.warning("Are you sure you want to reset all data? This action cannot be undone.")
    if st.button("Confirm Reset"):
        st.session_state.tasks = {}
        st.session_state.todo_list = []
        save_data()
        st.success("All data has been reset!")

# Save data before app ends
save_data()