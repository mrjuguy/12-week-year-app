from enum import Enum
from datetime import date, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field

class BlockType(str, Enum):
    STRATEGIC = "Strategic"
    BUFFER = "Buffer"
    BREAKOUT = "Breakout"
    NONE = "None"

class MetricType(str, Enum):
    LEAD = "Lead"
    LAG = "Lag"

class Metric(BaseModel):
    id: str
    title: str
    type: MetricType
    target_value: float
    current_value: float = 0.0

class Tactic(BaseModel):
    id: str
    title: str
    due_week: int = Field(..., ge=1, le=13)
    status: str = "Pending"  # Pending, Complete
    block_type: BlockType = BlockType.NONE
    is_completed: bool = False

class Goal(BaseModel):
    id: str
    title: str
    tactics: List[Tactic] = []
    metrics: List[Metric] = []

class Cycle(BaseModel):
    id: str
    start_date: date
    goals: List[Goal] = []
    
    @property
    def end_date(self) -> date:
        return self.start_date + timedelta(weeks=12)
    
    def get_week_type(self, week_num: int) -> str:
        if week_num == 13:
            return "Review_and_Celebrate"
        return "Execution"
