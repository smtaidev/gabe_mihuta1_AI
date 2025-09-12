from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Union

class MissionType(str, Enum):
    LOSE_FAT = "Lose Fat"
    BUILD_STRENGTH = "Build Strength"
    MOVE_PAIN_FREE = "Move Pain-Free"
    TACTICAL_READINESS = "Tactical Readiness"

class TimeCommitment(str, Enum):
    TEN_MIN = "10 min"
    TWENTY_TO_THIRTY_MIN = "20-30 min"
    FORTY_FIVE_PLUS_MIN = "45+ min"

class GearType(str, Enum):
    BODYWEIGHT = "Bodyweight"
    SANDBAG = "Sandbag"
    DUMBBELLS = "Dumbbells"
    FULL_GYM = "Full Gym"

class SquadSelection(str, Enum):
    LONE_WOLF = "Lone Wolf"
    GUARDIAN = "Guardian"
    WARRIOR = "Warrior"
    REBUILDER = "Rebuilder"

class WorkoutPlanRequest(BaseModel):
    mission: MissionType
    time_commitment: TimeCommitment
    gear: GearType
    squad: Optional[SquadSelection] = None
    

class WorkoutExercise(BaseModel):
    day: int
    name: Optional[str] = None
    sets: Optional[int] = None
    reps: Optional[str] = None
    description: Optional[str] = None
    rest: Optional[str] = None
    motivational_quote: str
    is_workout_day: bool
    video_url: Optional[str] = None
    calories_burned: Optional[int] = Field(None, description="Estimated calories burned during the exercise")

class WorkoutPlanResponse(BaseModel):
    workout_plan: List[WorkoutExercise] = []