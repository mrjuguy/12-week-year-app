import json
from datetime import date
from typing import List
from src.models import Cycle, Goal, Tactic, Metric, BlockType, MetricType

# Mock Data for MVP
def init_mock_data() -> Cycle:
    tactic1 = Tactic(id="t1", title="Call 50 leads", due_week=1, block_type=BlockType.STRATEGIC)
    tactic2 = Tactic(id="t2", title="Write 2 blog posts", due_week=1, block_type=BlockType.STRATEGIC)
    tactic3 = Tactic(id="t3", title="Update CRM", due_week=1, block_type=BlockType.BUFFER)
    
    goal1 = Goal(id="g1", title="Hit $10k MRR", tactics=[tactic1, tactic2, tactic3])
    
    return Cycle(id="c1", start_date=date.today(), goals=[goal1])

class Storage:
    def __init__(self):
        self.cycle = init_mock_data()

    def get_cycle(self) -> Cycle:
        return self.cycle
    
    def save_cycle(self, cycle: Cycle):
        self.cycle = cycle
        # ---------------------------------------------------------
        # WARNING: EPHEMERAL STORAGE
        # ---------------------------------------------------------
        # This MVP stores data in memory (session_state).
        # On Streamlit Cloud, this data WILL BE LOST on reboot.
        #
        # TODO: Connect to a persistent DB (Supabase, Firestore, Google Sheets)
        # for production use.
        # ---------------------------------------------------------


# Singleton instance for session state
# In Streamlit, we'll use session_state, but this class helps structure it.
