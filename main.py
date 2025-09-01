import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.services.Phase1.Phase1_Route import router as phase1_router
from app.services.Phase2.Phase2_Route import router as phase2_router
from app.services.Phase3.Phase3_Route import router as phase3_router
from app.core.config import API_PORT

# Create FastAPI application
app = FastAPI(
    title="Personalized Workout Generator",
    description="API for generating personalized monthly workout plans based on user preferences",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(phase1_router)
app.include_router(phase2_router)
app.include_router(phase3_router)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to the Personalized Monthly Workout Plan Generator API",
        "phases": {
            "phase1": "Beginner-friendly workouts - /api/phase1/Phase_1",
            "phase2": "Intermediate to advanced workouts - /api/phase2/Phase_2", 
            "phase3": "Elite-level performance workouts - /api/phase3/Phase_3"
        },
        "documentation": "/docs",
        "redoc": "/redoc"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=API_PORT, reload=True)