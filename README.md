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

All phases now return the same consistent response format:

**For workout days:**
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
  "video_url": "https://youtube.com/watch?v=example",
  "calories_burned": 85
}
```

**For rest days:**
```json
{
  "day": 2,
  "name": null,
  "sets": null,
  "reps": null,
  "description": null,
  "rest": null,
  "motivational_quote": "Recovery focused quote",
  "is_workout_day": false,
  "video_url": null,
  "calories_burned": null
}
```

**Complete Response Structure:**
```json
{
  "workout_plan": [
    {
      "day": 1,
      "name": "Push-Up Variations",
      "sets": 3,
      "reps": "12-15",
      "description": "Standard push-ups focusing on proper form and control",
      "rest": "60 seconds",
      "motivational_quote": "When you feel like stopping, think about why you started.",
      "is_workout_day": true,
      "video_url": "https://youtube.com/watch?v=example",
      "calories_burned": 85
    }
  ]
}
```

## Project Structure

```
app/
├── __init__.py
├── core/
│   ├── __init__.py
│   └── config.py              # Configuration settings
├── services/
│   ├── video_search.py        # YouTube video search integration
│   ├── Phase1/
│   │   ├── Phase1.py          # Beginner workout logic
│   │   ├── Phase1_Route.py    # API routes for Phase 1
│   │   └── Phase1_Schema.py   # Pydantic models for Phase 1
│   ├── Phase2/
│   │   ├── Phase2.py          # Intermediate workout logic
│   │   ├── Phase2_Route.py    # API routes for Phase 2
│   │   └── Phase2_Schema.py   # Pydantic models for Phase 2
│   ├── Phase3/
│   │   ├── Phase3.py          # Elite workout logic
│   │   ├── Phase3_Route.py    # API routes for Phase 3
│   │   └── Phase3_Schema.py   # Pydantic models for Phase 3
│   └── TextToSpeech/
│       ├── Text_To_Speech.py
│       ├── Text_To_Speech_Route.py
│       └── Text_To_Speech_Schema.py
main.py                        # FastAPI application entry point
requirements.txt               # Python dependencies
Dockerfile                     # Docker configuration
docker-compose.yml            # Docker Compose configuration
```

## API Endpoints

### Core Endpoints

- **Root**: `GET /` - Welcome message and API overview
- **Health Check**: `GET /health` - Service health status
- **API Documentation**: `GET /docs` - Swagger UI
- **API Documentation (Alternative)**: `GET /redoc` - ReDoc UI

### Phase 1 Endpoints (Beginner Level)
- **POST** `/api/phase1/Phase_1` - Generate workout plan with JSON body
- **GET** `/api/phase1/Phase_1` - Generate workout plan with query parameters

### Phase 2 Endpoints (Intermediate Level)
- **POST** `/api/phase2/Phase_2` - Generate advanced workout plan with JSON body
- **GET** `/api/phase2/Phase_2` - Generate advanced workout plan with query parameters

### Phase 3 Endpoints (Elite Level)
- **POST** `/api/phase3/Phase_3` - Generate elite workout plan with JSON body
- **GET** `/api/phase3/Phase_3` - Generate elite workout plan with query parameters

## Configuration

The application uses environment variables for configuration. Create a `.env` file:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-1106-preview

# Tavily API for YouTube video search
TAVILY_API_KEY=your_tavily_api_key_here

# Server Configuration
API_PORT=8031
```

## Deployment

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd gabe_mihuta1_AI-main
   ```

2. **Set up environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   # Copy and edit the environment file
   cp .env.example .env  # Edit with your API keys
   ```

4. **Run the application**
   ```bash
   python main.py
   # Or use uvicorn directly
   uvicorn main:app --host 0.0.0.0 --port 8031 --reload
   ```

### Docker Deployment

1. **Using Docker Compose (Recommended)**
   ```bash
   # Build and start the container
   docker-compose up -d --build
   
   # View logs
   docker-compose logs -f
   
   # Stop the service
   docker-compose down
   ```

2. **Using Docker directly**
   ```bash
   # Build the image
   docker build -t workout-api .
   
   # Run the container
   docker run -d -p 8031:8031 --env-file .env workout-api
   ```

### Production Deployment

For production deployment, consider:

- Using a production WSGI server like Gunicorn
- Setting up SSL/TLS certificates
- Implementing proper logging and monitoring
- Using environment-specific configuration files
- Setting up a reverse proxy (nginx)

## Features in Detail

### Workout Plan Generation
- **Personalized Plans**: Based on mission, time commitment, gear, and squad preferences
- **Progressive Difficulty**: Three phases from beginner to elite level
- **Smart Scheduling**: Optimized workout and rest day distribution
- **Motivation**: Daily motivational quotes tailored to difficulty level

### Video Integration
- **Exercise Demonstrations**: YouTube videos for each exercise
- **Tavily API Integration**: Intelligent video search and selection
- **Quality Assurance**: Videos are selected based on exercise relevance

### API Design
- **RESTful Architecture**: Clean and intuitive endpoint structure
- **Input Validation**: Pydantic models ensure data integrity
- **Error Handling**: Comprehensive error responses
- **Documentation**: Auto-generated API documentation

## Dependencies

- **FastAPI**: Modern, fast web framework for building APIs
- **Uvicorn**: ASGI server for FastAPI
- **Pydantic**: Data validation using Python type annotations
- **OpenAI**: GPT model integration for workout generation
- **Python-dotenv**: Environment variable management
- **Python-multipart**: File upload support
- **Tavily-python**: YouTube video search integration

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository or contact the development team.

## Changelog

### Version 1.0.0
- Initial release with Phase 1, 2, and 3 workout generation
- YouTube video integration
- Comprehensive API documentation
- Docker support
- Consistent response format across all phases

