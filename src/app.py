import streamlit as st
import streamlit_shadcn_ui as ui
import plotly.graph_objects as go
import sys
import os
from datetime import date

# Add the project root to sys.path so we can import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models import Cycle, Goal, Tactic
from src.logic import calculate_weekly_execution_score
from src.storage import init_mock_data

# Page Config
st.set_page_config(page_title="12-Week Year OS", layout="wide")

# State Management
if "cycle" not in st.session_state:
    st.session_state.cycle = init_mock_data()

cycle = st.session_state.cycle

# --- Sidebar ---
with st.sidebar:
    st.title("12-Week Year")
    page = ui.tabs(options=["Dashboard", "Execute", "Plan", "Review"], default_value="Dashboard", key="nav_tabs")

# --- Helper Functions ---
def get_current_week_num(start_date: date) -> int:
    # Simple logic: days since start / 7 + 1
    days_diff = (date.today() - start_date).days
    return max(1, min(13, (days_diff // 7) + 1))

current_week = get_current_week_num(cycle.start_date)

# --- Pages ---

if page == "Dashboard":
    st.title("Dashboard")
    
    # Metrics
    all_tactics = [t for g in cycle.goals for t in g.tactics if t.due_week == current_week]
    score = calculate_weekly_execution_score(all_tactics)
    
    cols = st.columns(3)
    with cols[0]:
        ui.metric_card(title="Current Week", content=f"Week {current_week}/12", description="Execution Phase")
    with cols[1]:
        ui.metric_card(title="Weekly Score", content=f"{score}%", description="Target: 85%+")
    with cols[2]:
        status = "On Track" if score >= 85 else "At Risk"
        ui.metric_card(title="Goal Status", content=status, description="Based on execution")

    st.markdown("---")
    st.subheader("Active Goals")
    for goal in cycle.goals:
        with st.container(border=True):
            st.markdown(f"**{goal.title}**")
            progress = len([t for t in goal.tactics if t.is_completed]) / len(goal.tactics) if goal.tactics else 0
            st.progress(progress)

elif page == "Execute":
    st.title("Execute: Week " + str(current_week))
    st.caption("Focus on today's tactics.")
    
    tactics = [t for g in cycle.goals for t in g.tactics if t.due_week == current_week]
    
    if not tactics:
        st.info("No tactics scheduled for this week.")
    
    for tactic in tactics:
        # Card-like container
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"### {tactic.title}")
                st.caption(f"Type: {tactic.block_type.value}")
            with c2:
                # Toggle button
                btn_text = "Completed" if tactic.is_completed else "Mark Done"
                btn_variant = "primary" if tactic.is_completed else "outline"
                
                if ui.button(text=btn_text, variant=btn_variant, key=f"btn_{tactic.id}"):
                    tactic.is_completed = not tactic.is_completed
                    st.rerun()

elif page == "Plan":
    st.title("Strategic Plan")
    
    with st.container(border=True):
        st.subheader("Add New Goal")
        new_goal_title = st.text_input("Goal Title")
        if st.button("Add Goal"):
            if new_goal_title:
                cycle.goals.append(Goal(id=f"g{len(cycle.goals)+1}", title=new_goal_title))
                st.rerun()

    st.subheader("Current Goals & Tactics")
    for goal in cycle.goals:
        with st.expander(goal.title, expanded=True):
            # List tactics
            for t in goal.tactics:
                st.text(f"- [Week {t.due_week}] {t.title} ({t.status})")
            
            # Add Tactic Form
            with st.form(key=f"add_tactic_{goal.id}"):
                c1, c2 = st.columns([3, 1])
                with c1:
                    t_title = st.text_input("New Tactic")
                with c2:
                    t_week = st.number_input("Week", min_value=1, max_value=13, value=current_week)
                
                if st.form_submit_button("Add Tactic"):
                    new_tactic = Tactic(
                        id=f"t{len(goal.tactics)+100}", 
                        title=t_title, 
                        due_week=t_week
                    )
                    goal.tactics.append(new_tactic)
                    st.rerun()

elif page == "Review":
    st.title("Weekly Review")
    
    # Mock History Data
    weeks = list(range(1, current_week + 1))
    scores = [80, 90, 85, 60][:len(weeks)] # Mock data
    
    fig = go.Figure(data=[go.Bar(x=weeks, y=scores, marker_color='#0f172a')])
    fig.update_layout(title="Execution Score History", xaxis_title="Week", yaxis_title="Score (%)", yaxis_range=[0, 100])
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Reflection")
    c1, c2 = st.columns(2)
    with c1:
        st.text_area("Weekly Wins", height=150, placeholder="What went well?")
    with c2:
        st.text_area("Lessons Learned", height=150, placeholder="What can be improved?")
    
    ui.button("Submit Review", variant="primary")
