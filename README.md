# Personalized Monthly Workout Plan Generator

A FastAPI application that generates personalized monthly workout plans using OpenAI GPT models. The application creates customized 30-day workout programs based on user preferences.

## Features

- Generate personalized monthly workout plans based on user selections:
  - **Mission**: "Lose Fat", "Build Strength", "Move Pain-Free", "Tactical Readiness"
  - **Time Commitment**: "10 min", "20-30 min", "45+ min"
  - **Gear**: "Bodyweight", "Sandbag", "Dumbbells", "Full Gym"
  - **Squad Selection** (optional): "Lone Wolf", "Guardian", "Warrior", "Rebuilder"
  - **Workout Days**: Customizable days of the week for workouts
- Three workout difficulty levels:
  - **Phase 1**: Beginner-friendly workout plans
  - **Phase 2**: More challenging workout routines with advanced techniques
  - **Phase 3**: Elite-level performance training for peak athletes and competitors
- Comprehensive 30-day program with workout and rest days
- Personalized motivational quotes for each day
- **YouTube video links** for each workout exercise using Tavily API
- Detailed exercise information with sets, reps, descriptions, and rest periods
- Efficient workout generation using parallel API calls

## Requirements

- Python 3.8+
- OpenAI API key
- Tavily API key (for YouTube video search)
- FastAPI
- Docker (optional)

## Setup

### Environment Variables

Create a `.env` file in the root directory with the following:

```
OPENAI_API_KEY="your_openai_api_key"
OPENAI_MODEL="gpt-4-1106-preview"
TAVILY_API_KEY="your_tavily_api_key"
```

### Installation

1. Clone the repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

### Running the Application

#### With Python

```bash
uvicorn main:app --host 0.0.0.0 --port 8031 --reload
```

#### With Docker

```bash
docker-compose up -d
docker-compose up --build
```

## API Usage

### Phase 1 (Beginner Level)

**Generate a Monthly Workout Plan (POST)**:

**Endpoint**: `POST /api/phase1/Phase_1`

**Request Body**:
```json
{
  "mission": "Lose Fat",
  "time_commitment": "10 min",
  "gear": "Bodyweight",
  "squad": "Lone Wolf"
}
```

**Get a Monthly Workout Plan with Query Parameters (GET)**:

**Endpoint**: `GET /api/phase1/Phase_1?mission=Lose%20Fat&time_commitment=10%20min&gear=Bodyweight&squad=Lone%20Wolf`

### Phase 2 (Advanced Level)

**Generate an Advanced Monthly Workout Plan (POST)**:

**Endpoint**: `POST /api/phase2/Phase_2`

**Request Body**:
```json
{
  "mission": "Build Strength",
  "time_commitment": "20-30 min",
  "gear": "Dumbbells",
  "squad": "Warrior"
}
```

**Get an Advanced Monthly Workout Plan with Query Parameters (GET)**:

**Endpoint**: `GET /api/phase2/Phase_2?mission=Build%20Strength&time_commitment=20-30%20min&gear=Dumbbells&squad=Warrior`

### Phase 3 (Elite Level)

**Generate an Elite Monthly Workout Plan (POST)**:

**Endpoint**: `POST /api/phase3/Phase_3`

**Request Body**:
```json
{
  "mission": "Tactical Readiness",
  "time_commitment": "45+ min",
  "gear": "Full Gym",
  "squad": "Warrior"
}
```

**Get an Elite Monthly Workout Plan with Query Parameters (GET)**:

**Endpoint**: `GET /api/phase3/Phase_3?mission=Tactical%20Readiness&time_commitment=45%2B%20min&gear=Full%20Gym&squad=Warrior`

### Response Format

For workout days:
```json
{
  "day": 1,
  "name": "Exercise Name",
  "sets": 3,
  "reps": "10-12",
  "description": "Detailed exercise description with form cues",
  "rest": "60 seconds",
  "motivational_quote": "An inspiring quote",
  "is_workout_day": true,
  "video_url": "https://youtube.com/watch?v=example"
}
```

For rest days:
```json
{
  "day": 2,
  "motivational_quote": "Recovery focused quote",
  "is_workout_day": false,
  "video_url": null
}
```

## Documentation

- API documentation available at `/docs` or `/redoc` when the server is running

## Current Implementation

- Phase 1: Beginner level workout plan generation with OpenAI integration
- Phase 2: Advanced level workout plan generation with increased difficulty
- Phase 3: Elite level workout plan generation for peak performance and competition preparation

