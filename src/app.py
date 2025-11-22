import streamlit as st
import streamlit_shadcn_ui as ui
import plotly.graph_objects as go
import sys
import os
from datetime import date, datetime, time

# Add the project root to sys.path so we can import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models import Cycle, Goal, Tactic, TacticStatus
from src.logic import calculate_weekly_execution_score
from src.storage import Storage

# Initialize Storage globally
storage = Storage()

# --- Helper Functions ---
def get_current_week_num(start_date: date) -> int:
    # Simple logic: days since start / 7 + 1
    days_diff = (date.today() - start_date).days
    return max(1, min(13, (days_diff // 7) + 1))

# Page Config
st.set_page_config(page_title="12-Week Year OS", layout="wide")

# State Management
# storage = Storage() # initialized at top

if "cycle" not in st.session_state or not hasattr(st.session_state.cycle, "vision_3_year"):
    # Load from Google Sheets (or default if empty)
    # Also reload if the schema has changed (missing new attributes)
    st.session_state.cycle = storage.get_cycle()

cycle = st.session_state.cycle

# --- Sidebar ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/target.png", width=60)
    st.title("12-Week Year")
    
    st.markdown("---")
    
    # Navigation
    page = st.radio(
        "Navigate",
        ["Dashboard", "Vision", "Plan", "Execute", "Review"],
        index=0,
        label_visibility="collapsed",
        format_func=lambda x: f" {x}" # Add spacing if needed, icons handled below if we mapped them
    )
    
    st.markdown("---")
    st.caption(f"Current Cycle: **{cycle.id}**")
    st.caption(f"Week: **{get_current_week_num(cycle.start_date)}**")
    
    if st.button("🔄 Reload Data"):
        del st.session_state.cycle
        st.rerun()

if page == "Vision":
    st.header("Establish Your Vision")
    st.markdown("""
    The 12-Week Year starts with a compelling vision of the future. 
    This vision creates the emotional connection that drives you through the discomfort of change.
    """)
    
    # Vision Board Image
    with st.expander("🖼️ Vision Board (Visual Anchor)", expanded=True):
        import base64
        
        # Load existing image
        current_img_b64 = storage.get_vision_image()
        if current_img_b64:
            st.image(base64.b64decode(current_img_b64), use_container_width=True)
        
        uploaded_file = st.file_uploader("Upload a new vision board image", type=['png', 'jpg', 'jpeg'])
        if uploaded_file is not None:
            bytes_data = uploaded_file.getvalue()
            b64_str = base64.b64encode(bytes_data).decode()
            
            if st.button("Save Image"):
                if storage.save_vision_image(b64_str):
                    st.success("Image saved!")
                    st.rerun()

    # The 'Why' Section (Moved to Top)
    with st.container(border=True):
        st.subheader("💭 The 'Why'")
        st.info("Why is this vision important to you? Connecting with your 'Why' helps you stay disciplined when motivation fades.")
        st.caption("Tip: You can include your 'Why' in the text areas below or keep it in mind as you write.")

    # Vision Columns
    col_info_1, col_info_2 = st.columns(2)
    
    with col_info_1:
        with st.container(border=True):
            st.subheader("🌟 3-Year Vision")
            st.info("Where do you want to be in 3 years? Dream big. Consider your physical, financial, spiritual, and professional life.")
            v3 = st.text_area("3-Year Vision", value=cycle.vision_3_year, height=300, key="v3_input", label_visibility="collapsed")
        
    with col_info_2:
        with st.container(border=True):
            st.subheader("🎯 12-Month Vision")
            st.info("What specific milestones must you hit in the next 12 months? Ensure these targets directly support your 3-year vision.")
            v1 = st.text_area("1-Year Vision", value=cycle.vision_1_year, height=300, key="v1_input", label_visibility="collapsed")
            
    if st.button("Save Vision", type="primary"):
        cycle.vision_3_year = v3
        cycle.vision_1_year = v1
        storage.save_cycle(cycle)
        st.balloons()




current_week = get_current_week_num(cycle.start_date)

# --- Pages ---

if page == "Dashboard":
    st.title("Dashboard")
    
    # Metrics
    # Metrics
    all_tactics = [t for g in cycle.goals for t in g.tactics if t.due_week == current_week]
    score = calculate_weekly_execution_score(all_tactics)
    
    # Cycle Progress
    total_cycle_tactics = sum(len(g.tactics) for g in cycle.goals)
    total_completed_tactics = sum(len([t for t in g.tactics if t.is_completed]) for g in cycle.goals)
    cycle_progress = total_completed_tactics / total_cycle_tactics if total_cycle_tactics > 0 else 0.0

    cols = st.columns(3)
    with cols[0]:
        ui.metric_card(title="Current Week", content=f"Week {current_week}/12", description="Execution Phase")
    with cols[1]:
        ui.metric_card(title="Weekly Score", content=f"{score}%", description="Target: 85%+")
    with cols[2]:
        ui.metric_card(title="Cycle Progress", content=f"{int(cycle_progress*100)}%", description=f"{total_completed_tactics}/{total_cycle_tactics} Tactics")

    # Lag Metrics Chart
    st.markdown("---")
    st.subheader("📈 Results (Lag Indicators)")
    
    metrics_data = []
    for goal in cycle.goals:
        for m in goal.metrics:
            metrics_data.append(m)
            
    if not metrics_data:
        st.info("No lag metrics tracked yet.")
    else:
        # Create a simple bar chart comparing Current vs Target for each metric
        # Normalize to % for a combined chart? Or just list them?
        # Let's do a row of small charts or a table for now, or a normalized bar chart.
        # User requested: "Graph the Lag Metric progress alongside the Execution Score"
        # Since units vary, a normalized % to target chart is best.
        
        metric_names = []
        metric_percentages = []
        metric_texts = []
        
        for m in metrics_data:
            metric_names.append(m.title)
            # Avoid division by zero
            range_val = m.target_value - m.starting_value
            if range_val == 0:
                pct = 100 if m.current_value >= m.target_value else 0
            else:
                pct = ((m.current_value - m.starting_value) / range_val) * 100
            
            metric_percentages.append(pct)
            metric_texts.append(f"{m.current_value} / {m.target_value} {m.unit}")
            
        fig_m = go.Figure(go.Bar(
            x=metric_names,
            y=metric_percentages,
            text=metric_texts,
            textposition='auto',
            marker_color='#3b82f6'
        ))
        fig_m.update_layout(
            title="Goal Progress (Lag Indicators)",
            yaxis_title="% to Target",
            yaxis_range=[0, 110],
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_m, use_container_width=True)

    st.markdown("---")
    st.subheader("Active Goals")
    
    if not cycle.goals:
        st.info("No goals set. Go to the Plan tab to get started.")
        
    for goal in cycle.goals:
        # Calculate Goal Progress
        g_total = len(goal.tactics)
        g_completed = len([t for t in goal.tactics if t.is_completed])
        g_progress = g_completed / g_total if g_total > 0 else 0.0
        
        with st.expander(f"{goal.title} ({int(g_progress*100)}%)"):
            st.progress(g_progress)
            if not goal.tactics:
                st.caption("No tactics.")
            for t in goal.tactics:
                icon = "✅" if t.is_completed else "⬜"
                st.markdown(f"{icon} **{t.title}** (Week {t.due_week}) - *{t.status.value}*")

elif page == "Execute":
    st.title("Execute: Week " + str(current_week))
    st.caption("Focus on today's tactics.")
    
    if not any(t for g in cycle.goals for t in g.tactics if t.due_week == current_week):
        st.info("No tactics scheduled for this week.")
    
    # Group by Goal
    for goal in cycle.goals:
        week_tactics = [t for t in goal.tactics if t.due_week == current_week]
        if week_tactics:
            st.subheader(goal.title)
            for tactic in week_tactics:
                with st.container(border=True):
                    # Columns: Status, Title, Save
                    c1, c2 = st.columns([1.5, 4])
                    
                    with c1:
                        # Status Dropdown
                        status_options = [s.value for s in TacticStatus]
                        current_index = 0
                        if tactic.status.value in status_options:
                            current_index = status_options.index(tactic.status.value)
                            
                        new_status = st.selectbox("Status", options=status_options, index=current_index, key=f"exec_status_{tactic.id}", label_visibility="collapsed")
                        if new_status != tactic.status.value:
                            tactic.status = TacticStatus(new_status)
                            # Sync is_completed
                            if new_status == TacticStatus.COMPLETED.value:
                                tactic.is_completed = True
                            else:
                                tactic.is_completed = False
                            storage.save_cycle(cycle)
                            st.rerun()
                            
                    with c2:
                        # Editable Title
                        new_title = st.text_input("Tactic", value=tactic.title, key=f"exec_title_{tactic.id}", label_visibility="collapsed")
                        if new_title != tactic.title:
                            tactic.title = new_title
                            storage.save_cycle(cycle)
                        
                        # Schedule UI
                        with st.popover("📅 Schedule"):
                            st.caption("Add to Google Calendar")
                            d = st.date_input("Date", value=date.today(), key=f"d_{tactic.id}")
                            t = st.time_input("Time", value=datetime.now().time(), key=f"t_{tactic.id}")
                            dur = st.number_input("Duration (min)", value=60, step=15, key=f"dur_{tactic.id}")
                            
                            if st.button("Add Event", key=f"cal_{tactic.id}", type="primary"):
                                # Check for Strategic Block alignment
                                if tactic.block_type == "Strategic":
                                    day_name = d.strftime("%A")
                                    # Check if this day has a strategic block
                                    blocks = [sb for sb in cycle.strategic_blocks if sb.day_of_week == day_name]
                                    if not blocks:
                                        st.warning(f"⚠️ You are scheduling a Strategic tactic on {day_name}, but you have no Strategic Blocks defined for this day.")
                                    else:
                                        # Simple check: is the start time within any block?
                                        is_aligned = False
                                        sched_start = t.strftime("%H:%M")
                                        for sb in blocks:
                                            if sb.start_time <= sched_start < sb.end_time:
                                                is_aligned = True
                                                break
                                        if not is_aligned:
                                            st.warning(f"⚠️ Strategic Tactic scheduled outside of your protected blocks ({', '.join([f'{b.start_time}-{b.end_time}' for b in blocks])}).")

                                start_dt = datetime.combine(d, t).isoformat()
                                success, link = storage.create_calendar_event(tactic.title, start_dt, dur)
                                if success:
                                    st.success(f"Added! [View Event]({link})")
                                else:
                                    st.error(f"Error: {link}")

elif page == "Plan":
    st.title("Strategic Plan")
    
    with st.container(border=True):
        st.subheader("Add New Goal")
        new_goal_title = st.text_input("Goal Title")
        if st.button("Add Goal"):
            if new_goal_title:
                cycle.goals.append(Goal(id=f"g{len(cycle.goals)+1}", title=new_goal_title))
                storage.save_cycle(cycle)
                st.rerun()

    st.subheader("Current Goals & Tactics")
    
    # Iterate over a copy to allow modification during iteration (for deletes)
    for i, goal in enumerate(cycle.goals):
        # Calculate Progress
        total_tactics = len(goal.tactics)
        completed_tactics = len([t for t in goal.tactics if t.is_completed])
        progress = completed_tactics / total_tactics if total_tactics > 0 else 0.0
        
        with st.expander(f"{goal.title} ({int(progress*100)}% Complete)", expanded=True):
            
            # Goal Progress Bar
            st.progress(progress)
            
            # Goal Actions
            c1, c2 = st.columns([4, 1])
            with c1:
                # Goal Rename
                new_title = st.text_input("Goal Name", value=goal.title, key=f"g_title_{goal.id}")
                if new_title != goal.title:
                    goal.title = new_title
                    storage.save_cycle(cycle)
                    st.rerun()
            with c2:
                if st.button("🗑️ Delete Goal", key=f"del_goal_{goal.id}", type="primary"):
                    cycle.goals.pop(i)
                    storage.save_cycle(cycle)
                    st.rerun()
            
            st.markdown("---")
            
            # --- Metrics Section ---
            st.caption("Lag Metrics (The Scoreboard)")
            
            if not goal.metrics:
                st.info("No metrics defined.")
            
            for m in goal.metrics:
                # Simple display of metric
                st.markdown(f"📊 **{m.title}**: {m.current_value} / {m.target_value} {m.unit}")

            # Add Metric Form
            with st.popover("➕ Add Metric"):
                m_title = st.text_input("Metric Name", key=f"m_title_{goal.id}")
                c_m1, c_m2 = st.columns(2)
                with c_m1:
                    m_start = st.number_input("Starting Value", value=0.0, key=f"m_start_{goal.id}")
                    m_target = st.number_input("Target Value", value=10.0, key=f"m_target_{goal.id}")
                with c_m2:
                    m_unit = st.text_input("Unit (e.g. kg, $)", key=f"m_unit_{goal.id}")
                
                if st.button("Add Metric", key=f"add_m_{goal.id}", type="primary"):
                    from src.models import Metric, MetricType
                    new_metric = Metric(
                        id=f"m{len(goal.metrics)+1}_{goal.id}",
                        title=m_title,
                        type=MetricType.LAG,
                        starting_value=m_start,
                        target_value=m_target,
                        current_value=m_start,
                        unit=m_unit
                    )
                    goal.metrics.append(new_metric)
                    storage.save_cycle(cycle)
                    st.rerun()

            st.markdown("---")
            st.caption("Tactics")
            
            # Tactics List (Editable)
            if not goal.tactics:
                st.info("No tactics yet.")
            
            for j, tactic in enumerate(goal.tactics):
                # Columns: Title, Status, Week, Delete
                tc1, tc2, tc3, tc4 = st.columns([3, 1.5, 1, 0.5])
                
                with tc1:
                    t_title = st.text_input("Tactic", value=tactic.title, key=f"t_title_{tactic.id}", label_visibility="collapsed")
                    if t_title != tactic.title:
                        tactic.title = t_title
                        storage.save_cycle(cycle)
                        
                with tc2:
                    # Status Dropdown
                    status_options = [s.value for s in TacticStatus]
                    # Handle case where current status might not be in options
                    current_index = 0
                    if tactic.status.value in status_options:
                        current_index = status_options.index(tactic.status.value)
                        
                    new_status = st.selectbox("Status", options=status_options, index=current_index, key=f"t_status_{tactic.id}", label_visibility="collapsed")
                    if new_status != tactic.status.value:
                        tactic.status = TacticStatus(new_status)
                        # Sync is_completed based on status
                        if new_status == TacticStatus.COMPLETED.value:
                            tactic.is_completed = True
                        else:
                            tactic.is_completed = False
                        storage.save_cycle(cycle)
                        st.rerun()

                with tc3:
                    t_week = st.number_input("Week", min_value=1, max_value=13, value=tactic.due_week, key=f"t_week_{tactic.id}", label_visibility="collapsed")
                    if t_week != tactic.due_week:
                        tactic.due_week = t_week
                        storage.save_cycle(cycle)
                        st.rerun()
                        
                with tc4:
                    if st.button("🗑️", key=f"del_tactic_{tactic.id}"):
                        goal.tactics.pop(j)
                        storage.save_cycle(cycle)
                        st.rerun()
            
            st.markdown("---")
            # Add Tactic Form
            with st.form(key=f"add_tactic_{goal.id}"):
                st.caption("Add New Tactic")
                c1, c2 = st.columns([3, 1])
                with c1:
                    t_title = st.text_input("New Tactic Title")
                with c2:
                    t_week = st.number_input("Week", min_value=1, max_value=13, value=current_week)
                
                if st.form_submit_button("Add Tactic"):
                    new_tactic = Tactic(
                        id=f"t{len(goal.tactics)+100}_{i}", # Ensure unique ID
                        title=t_title, 
                        due_week=t_week
                    )
                    goal.tactics.append(new_tactic)
                    storage.save_cycle(cycle)
                    st.rerun()

elif page == "Review":
    st.title("Weekly Review")
    
    # 1. Calculate Score for Current Week
    week_tactics = [t for g in cycle.goals for t in g.tactics if t.due_week == current_week]
    current_score = calculate_weekly_execution_score(week_tactics)
    
    # 2. Historical Chart
    # Create a map of week_num -> score from saved reviews
    history_map = {r.week_num: r.score for r in cycle.reviews}
    # Add current week's live score
    history_map[current_week] = current_score
    
    weeks = sorted(history_map.keys())
    scores = [history_map[w] for w in weeks]
    
    # Color code: Green if >= 85, else Red
    colors = ['#22c55e' if s >= 85 else '#ef4444' for s in scores]
    
    fig = go.Figure(data=[go.Bar(x=weeks, y=scores, marker_color=colors)])
    fig.update_layout(
        title="Execution Score History", 
        xaxis_title="Week", 
        yaxis_title="Score (%)", 
        yaxis_range=[0, 100],
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # 3. Review Form
    st.subheader(f"Review Week {current_week}")
    st.subheader(f"Review Week {current_week}")
    st.caption(f"Current Execution Score: **{current_score}%**")
    
    # Update Metrics
    st.markdown("### 📊 Update Metrics")
    active_metrics = [m for g in cycle.goals for m in g.metrics]
    if not active_metrics:
        st.info("No metrics to update.")
    
    # Use a form for metrics to avoid auto-rerun on every keystroke
    with st.form("metrics_update_form"):
        cols = st.columns(3)
        for idx, m in enumerate(active_metrics):
            col = cols[idx % 3]
            with col:
                new_val = st.number_input(
                    f"{m.title} ({m.unit})", 
                    value=float(m.current_value), 
                    key=f"rev_m_{m.id}"
                )
                if new_val != m.current_value:
                    m.current_value = new_val
                    m.last_updated = date.today()
        
        if st.form_submit_button("Save Metric Updates"):
            storage.save_cycle(cycle)
            st.toast("Metrics Updated!")
            st.rerun()
            
    st.markdown("---")
    
    # Reference: Completed Tactics
    completed_tactics = [t for t in week_tactics if t.is_completed]
    incomplete_tactics = [t for t in week_tactics if not t.is_completed]
    
    with st.expander("📝 View This Week's Completed Tactics", expanded=False):
        if not completed_tactics:
            st.info("No tactics completed this week.")
        for t in completed_tactics:
            st.markdown(f"- ✅ {t.title}")
            
    if incomplete_tactics:
        st.warning(f"You have {len(incomplete_tactics)} incomplete tactics. Go to the Plan tab to defer them or mark them as done.")
    
    # Check if already reviewed
    existing_review = next((r for r in cycle.reviews if r.week_num == current_week), None)
    
    with st.form("weekly_review_form"):
        c1, c2 = st.columns(2)
        with c1:
            wins = st.text_area("Weekly Wins", value=existing_review.wins if existing_review else "", height=150, placeholder="What went well?")
        with c2:
            lessons = st.text_area("Lessons Learned", value=existing_review.lessons if existing_review else "", height=150, placeholder="What can be improved?")
        
        if st.form_submit_button("Submit Review", type="primary"):
            from src.models import WeeklyReview # Import here
            
            # Create or Update Review
            if existing_review:
                existing_review.score = current_score
                existing_review.wins = wins
                existing_review.lessons = lessons
                existing_review.date_submitted = date.today()
                st.toast("Review Updated!")
            else:
                new_review = WeeklyReview(
                    week_num=current_week,
                    score=current_score,
                    wins=wins,
                    lessons=lessons
                )
                cycle.reviews.append(new_review)
                st.toast("Review Submitted!")
            
            storage.save_cycle(cycle)
            storage.save_cycle(cycle)
            st.balloons()

    # --- WAM Report Generator ---
    st.markdown("---")
    st.subheader("📢 WAM Report (Weekly Accountability Meeting)")
    
    if st.button("Generate WAM Report"):
        # Gather data
        wins_text = existing_review.wins if existing_review else "No wins recorded."
        struggles_text = existing_review.lessons if existing_review else "No struggles recorded."
        
        # Get next week's tactics
        next_week = current_week + 1
        next_tactics = [t for g in cycle.goals for t in g.tactics if t.due_week == next_week]
        commitment_text = "\n".join([f"- {t.title}" for t in next_tactics]) if next_tactics else "No tactics scheduled."
        
        wam_report = f"""
**12-Week Year WAM Report**
**Week {current_week}**

**Execution Score:** {current_score}%

**Top Wins:**
{wins_text}

**Key Struggles:**
{struggles_text}

**Commitments for Week {next_week}:**
{commitment_text}
"""
        st.code(wam_report, language="markdown")
        st.caption("Copy the text above and share it with your accountability partner.")

    # --- Cycle Archival ---
    if current_week >= 12:
        st.markdown("---")
        st.subheader("🏁 Close Cycle")
        st.warning("This will archive your current tactics, reviews, and metrics, and reset the board for the next 12 weeks. Vision and Settings will be preserved.")
        
        if st.button("Archive & Reset Cycle", type="primary"):
            if storage.archive_cycle(cycle):
                # Reset local state
                cycle.goals = []
                cycle.reviews = []
                # Keep vision and settings
                st.session_state.cycle = cycle
                st.rerun()
