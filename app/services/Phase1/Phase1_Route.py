from fastapi import APIRouter, HTTPException, Query
from app.services.Phase1.Phase1_Schema import WorkoutPlanRequest, WorkoutPlanResponse
from app.services.Phase1.Phase1 import Phase1Service

# Create router for Phase 1
router = APIRouter(
    prefix="/api/phase1",
    tags=["Phase1"],
    responses={404: {"description": "Not found"}},
)

@router.post("/Phase_1", response_model=WorkoutPlanResponse)
async def generate_workout_plan(request: WorkoutPlanRequest):
    """
    Generate a 30-day workout plan with simplified exercise format.
    Uses default workout schedule: Monday, Tuesday, Thursday, Friday.
    
    - **mission**: Selected mission (Lose Fat, Build Strength, Move Pain-Free, Tactical Readiness)
    - **time_commitment**: Time available for workout (10 min, 20-30 min, 45+ min)
    - **gear**: Available equipment (Bodyweight, Sandbag, Dumbbells, Full Gym)
    - **squad** (optional): Squad selection (Lone Wolf, Guardian, Warrior, Rebuilder)
    """
    try:
        return await Phase1Service.generate_workout_plan(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/Phase_1", response_model=WorkoutPlanResponse)
async def get_workout_plan(
    mission: str = Query("Lose Fat", description="Selected mission"),
    time_commitment: str = Query("10 min", description="Time available for workout"),
    gear: str = Query("Bodyweight", description="Available equipment"),
    squad: str = Query(None, description="Squad selection (optional)")
):
    """
    Generate a 30-day workout plan with query parameters for preferences.
    Uses default workout schedule: Monday, Tuesday, Thursday, Friday.
    """
    try:
        # Create the request
        request = WorkoutPlanRequest(
            mission=mission,
            time_commitment=time_commitment,
            gear=gear,
            squad=squad
        )
        return await Phase1Service.generate_workout_plan(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))