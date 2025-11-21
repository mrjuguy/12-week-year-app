from typing import List
from src.models import Tactic

def calculate_weekly_execution_score(tactics: List[Tactic]) -> float:
    if not tactics:
        return 0.0
    
    completed_count = sum(1 for t in tactics if t.is_completed or t.status == "Complete")
    return round((completed_count / len(tactics)) * 100.0, 1)

def check_score_threshold(score: float) -> bool:
    return score < 85.0
