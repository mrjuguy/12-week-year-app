from enum import Enum
from datetime import date, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field

class BlockType(str, Enum):
    STRATEGIC = "Strategic"
    BUFFER = "Buffer"
    BREAKOUT = "Breakout"
    NONE = "None"

class TacticStatus(str, Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    DEFERRED = "Deferred"
    CANCELLED = "Cancelled"

class MetricType(str, Enum):
    LEAD = "Lead"
    LAG = "Lag"

class Metric(BaseModel):
    id: str
    title: str
    type: MetricType
    starting_value: float = 0.0
    target_value: float
    current_value: float = 0.0
    unit: str = ""
    last_updated: date = Field(default_factory=date.today)

class Tactic(BaseModel):
    id: str
    title: str
    due_week: int = Field(..., ge=1, le=13)
    status: TacticStatus = TacticStatus.NOT_STARTED
    block_type: BlockType = BlockType.NONE
    is_completed: bool = False

class Goal(BaseModel):
    id: str
    title: str
    tactics: List[Tactic] = []
    metrics: List[Metric] = []

class WeeklyReview(BaseModel):
    week_num: int
    score: float
    wins: str = ""
    lessons: str = ""
    date_submitted: date = Field(default_factory=date.today)

class StrategicBlock(BaseModel):
    day_of_week: str # "Monday", "Tuesday", etc.
    start_time: str # "09:00"
    end_time: str # "12:00"

class Cycle(BaseModel):
    id: str
    start_date: date
    goals: List[Goal] = []
    reviews: List[WeeklyReview] = []
    strategic_blocks: List[StrategicBlock] = []
    vision_3_year: str = ""
    vision_1_year: str = ""
    
    @property
    def end_date(self) -> date:
        return self.start_date + timedelta(weeks=12)
    
    def get_week_type(self, week_num: int) -> str:
        if week_num == 13:
            return "Review_and_Celebrate"
        return "Execution"
