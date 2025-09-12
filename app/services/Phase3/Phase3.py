import json
import asyncio
import calendar
import logging
from datetime import datetime, timedelta
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from openai import AsyncOpenAI
from app.core.config import OPENAI_API_KEY, OPENAI_MODEL
from app.services.Phase3.Phase3_Schema import WorkoutPlanRequest, WorkoutPlanResponse, WorkoutExercise
from app.services.video_search import video_search_service

# Set up logging
logger = logging.getLogger(__name__)

class Phase3Service:
    # Define elite-level workout focus for each day of the week
    DAY_FOCUS_MAP = {
        "Monday": "Elite strength and power",
        "Tuesday": "Advanced metabolic conditioning", 
        "Wednesday": "Olympic lifts and explosiveness",
        "Thursday": "Elite endurance and capacity",
        "Friday": "Peak performance and testing",
        "Saturday": "Competition preparation",
        "Sunday": "Active recovery and mobility"
    }
    
    # Batch size for parallel API calls
    BATCH_SIZE = 6
    
    # Collection of motivational quotes for Phase 3 (elite/advanced level)
    MOTIVATIONAL_QUOTES = [
        "Champions don't make excuses. They make adjustments.",
        "You are your only limit.",
        "Pain is temporary. Quitting lasts forever.",
        "When you want to succeed as bad as you want to breathe, then you'll be successful.",
        "The will to win is nothing without the will to prepare.",
        "It's not about perfect. It's about effort. When you bring that effort every day, that's where transformation happens.",
        "I don't count my sit-ups. I only start counting when it starts hurting because they're the only ones that count.",
        "The only place where success comes before work is in the dictionary.",
        "If something stands between you and your success, move it. Never be denied.",
        "The difference between the impossible and the possible lies in a person's determination.",
        "You didn't come this far to only come this far.",
        "What hurts today makes you stronger tomorrow.",
        "Great things come from hard work and perseverance. No excuses.",
        "Success isn't given. It's earned. On the track, on the field, in the gym. With blood, sweat, and the occasional tear.",
        "The real workout starts when you want to stop.",
        "I don't train until I feel good. I train until I know I couldn't have done more.",
        "Someone busier than you is working out right now.",
        "Your body can stand almost anything. It's your mind you have to convince.",
        "Mental toughness is to physical as four is to one.",
        "You can either suffer the pain of discipline or the pain of regret.",
        "Discipline is the bridge between goals and accomplishment.",
        "Your legacy is being written by yourself. Make the right decisions.",
        "Losers quit when they're tired. Winners quit when they've won.",
        "You don't get the ass you want by sitting on it.",
        "The harder you work for something, the greater you'll feel when you achieve it.",
        "The mind is the most powerful tool a person possesses.",
        "The past cannot be changed. The future is yet in your power.",
        "Champions keep playing until they get it right.",
        "If it doesn't challenge you, it won't change you.",
        "Champions aren't made in gyms. Champions are made from something they have deep inside them."
    ]
    
    # Collection of rest day quotes for Phase 3
    REST_DAY_QUOTES = [
        "Elite recovery is where champions are forged. Your body is optimizing for peak performance.",
        "Strategic recovery is part of your competitive advantage. Use it wisely.",
        "Rest is not a weakness; it's a tactical advantage. The best athletes master the art of recovery.",
        "Today's rest ensures tomorrow's peak performance. Make it count.",
        "Recovery is when your training adapts you into a champion. Honor this process.",
        "Elite performance requires elite recovery. This is where your competitive edge is built.",
        "The quality of your recovery determines the quality of your performance.",
        "Champions recover with the same intensity they train. Make today count.",
        "Your competitors are resting too. The difference is in how strategically you recover.",
        "Recovery is not passive for the elite. It's an active preparation for greatness.",
        "Strategic downtime is what separates champions from everyone else.",
        "Your muscles grow during recovery, not during training. This is where the magic happens.",
        "Tomorrow's personal record is being built in today's recovery.",
        "Recovery isn't the absence of training. It's a different type of training.",
        "The elite understand that sometimes the hardest thing to do is nothing at all."
    ]
    
    @staticmethod
    def get_daily_quote(day_number: int, is_rest_day: bool = False) -> str:
        """
        Generate a unique daily motivational quote based on the date and day number.
        
        Args:
            day_number: The day number in the workout plan (1-30)
            is_rest_day: Whether this is a rest day or workout day
            
        Returns:
            A motivational quote unique to this day
        """
        # Get current date to ensure quote changes daily
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Create a deterministic but seemingly random seed based on date and day number
        seed = f"phase3-{today}-day{day_number}-{'rest' if is_rest_day else 'workout'}"
        hash_value = int(hashlib.md5(seed.encode()).hexdigest(), 16)
        
        # Select quote based on the hash value
        if is_rest_day:
            return Phase3Service.REST_DAY_QUOTES[hash_value % len(Phase3Service.REST_DAY_QUOTES)]
        else:
            return Phase3Service.MOTIVATIONAL_QUOTES[hash_value % len(Phase3Service.MOTIVATIONAL_QUOTES)]
    
    @staticmethod
    def calculate_calories_burned(time_commitment, gear, mission, day_number: int) -> int:
        """
        Calculate estimated calories burned for a Phase 3 workout based on parameters.
        
        This calculation uses the highest intensity multipliers for elite-level training:
        - Maximum intensity exercise selection
        - Elite-level training volumes and density
        - Complex movement patterns and advanced techniques
        - Competition-level training demands
        
        Args:
            time_commitment: TimeCommitment enum value
            gear: GearType enum value 
            mission: MissionType enum value
            day_number: Day number in the 30-day plan (1-30)
            
        Returns:
            Estimated calories burned as integer
        """
        # Base calories per minute for Phase 3 (highest of all phases)
        base_calories_per_minute = {
            "10 min": 12,     # Elite intensity, maximum efficiency
            "20-30 min": 15,  # High to very high intensity
            "45+ min": 18     # Very high intensity with elite techniques
        }
        
        # Time duration mapping
        time_minutes = {
            "10 min": 10,
            "20-30 min": 25,  # Average of 20-30
            "45+ min": 45     # Minimum of 45+
        }
        
        # Equipment intensity multipliers (highest of all phases)
        gear_multipliers = {
            "Bodyweight": 1.2,     # Elite bodyweight movements and plyometrics
            "Sandbag": 1.4,        # Elite functional and explosive training
            "Dumbbells": 1.35,     # Elite resistance patterns and complexes
            "Full Gym": 1.5        # Maximum equipment with elite techniques
        }
        
        # Mission type intensity multipliers (highest of all phases)
        mission_multipliers = {
            "Lose Fat": 1.4,           # Very high intensity metabolic training
            "Build Strength": 1.3,     # Elite strength and power development
            "Move Pain-Free": 1.0,     # Controlled intensity, movement optimization
            "Tactical Readiness": 1.45 # Maximum intensity, combat/competition preparation
        }
        
        # Progressive intensity based on day (weeks 1-5) - elite progression
        week_number = (day_number - 1) // 7 + 1
        progression_multipliers = {
            1: 1.0,   # Week 1: Elite baseline intensity
            2: 1.1,   # Week 2: Increased elite intensity
            3: 1.2,   # Week 3: High elite intensity
            4: 1.25,  # Week 4: Peak elite intensity
            5: 1.3    # Week 5: Maximum elite intensity
        }
        
        # Get base values
        time_str = time_commitment.value
        base_cal_per_min = base_calories_per_minute.get(time_str, 15)
        duration = time_minutes.get(time_str, 25)
        
        # Calculate base calories
        base_calories = base_cal_per_min * duration
        
        # Apply multipliers
        gear_factor = gear_multipliers.get(gear.value, 1.0)
        mission_factor = mission_multipliers.get(mission.value, 1.0)
        progression_factor = progression_multipliers.get(week_number, 1.0)
        
        # Final calculation with Phase 3 elite intensity boost
        total_calories = base_calories * gear_factor * mission_factor * progression_factor * 1.25
        
        # Round to nearest 5 calories for cleaner numbers
        return round(total_calories / 5) * 5
    
    @staticmethod
    async def generate_workout_plan(request: WorkoutPlanRequest) -> WorkoutPlanResponse:
        """
        Generate a 30-day elite-level workout plan for peak performance using OpenAI.
        
        Features:
        - Elite-level training protocols for advanced athletes
        - Complex movement patterns and advanced techniques
        - Periodization and peak performance principles
        - Competition-level intensity and volume
        - Advanced recovery and optimization strategies
        
        Args:
            request: WorkoutPlanRequest containing user preferences
            
        Returns:
            WorkoutPlanResponse with 30 days of elite workout data
        """
        # Initialize OpenAI client with explicit configuration
        try:
            # Initialize with minimal parameters to avoid proxy-related issues
            client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        except TypeError as e:
            if "proxies" in str(e):
                # Fallback initialization without problematic parameters
                import os
                os.environ.pop('HTTP_PROXY', None)
                os.environ.pop('HTTPS_PROXY', None)
                client = AsyncOpenAI(api_key=OPENAI_API_KEY)
            else:
                raise e
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise Exception(f"OpenAI client initialization failed: {str(e)}")
        
        # Create system message for elite-level context
        system_message = """
        You are an elite performance coach with expertise in training Olympic athletes, professional competitors, and elite military operators.
        
        TASK:
        - For WORKOUT DAYS: Create elite-level, competition-ready exercise entries for peak performers
        - For REST DAYS: Provide elite recovery and mental preparation guidance
        
        EXERCISE SELECTION GUIDELINES - PHASE 3 (ELITE):
        - Design exercises for athletes already at advanced fitness levels
        - Include complex movement patterns, advanced techniques, and competition protocols
        - Focus on peak performance, power development, and competitive readiness
        - Incorporate periodization principles and performance testing
        - Use elite training methods: plyometrics, Olympic lifts, advanced metabolic conditioning
        - Exercise names should reflect elite-level complexity and specificity
        - Assume the athlete has excellent form and can handle high-intensity protocols
        - Include competition simulation and performance optimization techniques
        
        RESPONSE FORMAT:
        - Provide JSON format with precise elite-level programming
        - "sets" field must be a single integer (3, 4, 5, 6, etc.) - NO RANGES OR STRINGS
        - "reps" field should be a string with rep count or duration
        - "rest" field should be a string with time period
        - Motivational quotes should inspire peak performance and elite mindset
        - Exercise descriptions should include advanced technique cues and performance optimization
        
        CRITICAL: Always use exact integer values for "sets" field. Never use ranges like "3-5" or descriptions.
        
        This is PHASE 3 - Elite Performance Level. Train like a champion.
        """
        
        def get_day_of_week(day_number: int) -> str:
            """
            Map day number (1-30) to day of week (Monday, Tuesday, etc.)
            
            Args:
                day_number: The day number in the 30-day plan (1-30)
                
            Returns:
                The day of week as a string (e.g., "Monday")
            """
            today = datetime.now()
            target_date = today + timedelta(days=day_number - 1)
            return calendar.day_name[target_date.weekday()]
            
        def is_workout_day(day_of_week: str) -> bool:
            """
            Check if the given day is a workout day based on elite schedule
            Monday, Tuesday, Thursday, Friday are workout days
            
            Args:
                day_of_week: The day of week to check
                
            Returns:
                True if it's a workout day, False otherwise
            """
            workout_days = ["Monday", "Tuesday", "Thursday", "Friday"]
            return day_of_week in workout_days
            
        def get_week_and_progress_info(day_number: int) -> Tuple[int, float]:
            """
            Calculate week number and progress percentage through the elite program
            
            Args:
                day_number: The day number in the 30-day plan (1-30)
                
            Returns:
                Tuple of (week_number, progress_percentage)
            """
            week_number = (day_number - 1) // 7 + 1
            progress_percentage = (day_number / 30) * 100
            return week_number, progress_percentage
            
        async def generate_single_day_exercise(day_number: int) -> Dict[str, Any]:
            """
            Generate a single day's elite workout or recovery session
            
            This function creates elite-level training protocols for peak performers,
            incorporating advanced techniques and competition preparation.
            
            Args:
                day_number: The day number in the 30-day plan (1-30)
                
            Returns:
                Dictionary containing the elite exercise data or recovery protocol
            """
            # Determine the day of week and if it's a workout day
            day_of_week = get_day_of_week(day_number)
            workout_day = is_workout_day(day_of_week)
            
            # Get week number and progress through the program
            week_number, progress_percentage = get_week_and_progress_info(day_number)
            
            # Get the elite focus for today from our predefined map
            focus = "Elite recovery and optimization"
            if workout_day:
                focus = Phase3Service.DAY_FOCUS_MAP.get(day_of_week, "Elite performance training")
                
            # Determine elite intensity based on progress - peak performance focus
            intensity_level = "elite"
            if progress_percentage > 80:
                intensity_level = "competition-ready"
            elif progress_percentage > 60:
                intensity_level = "peak-performance"
            elif progress_percentage > 40:
                intensity_level = "advanced-elite"
                
            # Create user message based on whether it's a workout day or rest day
            if workout_day:
                user_message = f"""
                Create an elite-level, competition-ready workout for Day {day_number} ({day_of_week}) of a Phase 3 30-day program:
                
                ATHLETE PROFILE:
                - Performance Goal: {request.mission}
                - Training Window: {request.time_commitment}
                - Equipment Access: {request.gear}
                {f"- Elite Category: {request.squad}" if request.squad else ""}
                
                ELITE TRAINING SPECIFICS:
                - Day: {day_number}/30 ({progress_percentage:.1f}% through elite program)
                - Week: {week_number} of 5
                - Elite Focus: {focus} (PHASE 3 - ELITE PERFORMANCE)
                - Intensity Level: {intensity_level}
                
                REQUIREMENTS:
                - Create an ELITE-LEVEL workout for peak performers and competitors
                - Include advanced techniques, complex movements, and competition protocols
                - Assume excellent fitness base and technical competency
                - This should be significantly more demanding than Phase 1 or Phase 2
                - Include performance optimization and competitive edge training
                - Focus on power, speed, agility, and elite conditioning
                
                IMPORTANT:
                - The exercise "name" MUST include the athlete's mission ({request.mission}) and available gear ({request.gear})
                - The "description" MUST be specific to the athlete's mission and available gear
                
                FORMAT:
                {{
                    "day": {day_number},
                    "name": "Elite, technical exercise name with advanced protocols",
                    "sets": 5,
                    "reps": "Elite rep scheme with competition-level intensity and precision",
                    "description": "Elite-level technical description with advanced cues, competition prep notes, and performance optimization guidance",
                    "rest": "Precise rest intervals for elite performance and power development",
                    "motivational_quote": "Elite mindset quote focused on competition, excellence, and peak performance",
                    "is_workout_day": true
                }}
                
                IMPORTANT: The "sets" field must be a single integer (like 3, 4, 5, or 6). Do not use ranges or complex descriptions.
                """
            else:
                user_message = f"""
                Create an elite recovery and optimization protocol for Day {day_number} ({day_of_week}), which is a strategic REST DAY in a Phase 3 elite performance program.
                
                ATHLETE CONTEXT:
                - Currently {progress_percentage:.1f}% through their elite 30-day program (Day {day_number})
                - Performance Goal: {request.mission}
                - Elite recovery following high-intensity Phase 3 training focused on: {Phase3Service.DAY_FOCUS_MAP.get(get_day_of_week(day_number-1))}
                
                REQUIREMENTS:
                - Elite recovery protocol emphasizing performance optimization and competitive readiness
                - Message should reflect the demands of elite-level training and competition preparation
                - Content should be relevant to peak performers and competitive athletes
                - Quote should inspire continued excellence and elite mindset development
                
                FORMAT:
                {{
                    "day": {day_number},
                    "motivational_quote": "Elite mindset quote about strategic recovery, mental preparation, and competitive excellence",
                    "is_workout_day": false
                }}
                
                Elite athletes understand that recovery is not weakness - it's strategic optimization for peak performance.
                """
            
            try:
                logger.info(f"Generating Phase 3 elite exercise for day {day_number} ({day_of_week}) - Workout day: {workout_day}")
                
                # Make OpenAI API call with parameters optimized for elite content
                response = await client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.8,  # Higher creativity for elite variety
                    max_tokens=700,   # More tokens for detailed elite protocols
                    top_p=0.9,        
                    frequency_penalty=0.5,  # High variety in elite programming
                    presence_penalty=0.3,   # Encourage diverse elite techniques
                    response_format={"type": "json_object"}
                )
                
                # Extract and parse the response
                content = response.choices[0].message.content
                
                # Clean the content if needed
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                # Parse the JSON response
                exercise_data = json.loads(content)
                
                # Fix sets field if it's a string (convert to integer)
                if "sets" in exercise_data and isinstance(exercise_data["sets"], str):
                    try:
                        # Try to extract the first integer from the string
                        import re
                        sets_match = re.search(r'\d+', exercise_data["sets"])
                        if sets_match:
                            exercise_data["sets"] = int(sets_match.group())
                        else:
                            exercise_data["sets"] = 5  # Default elite sets
                        logger.warning(f"Converted sets from string to integer for day {day_number}: {exercise_data['sets']}")
                    except (ValueError, AttributeError):
                        exercise_data["sets"] = 5  # Default elite sets
                        logger.warning(f"Failed to parse sets, using default for day {day_number}")
                
                # Validate the response has all required fields
                if workout_day:
                    required_fields = ["day", "name", "sets", "reps", "description", "rest", "motivational_quote", "is_workout_day"]
                    for field in required_fields:
                        if field not in exercise_data:
                            logger.warning(f"Missing required field '{field}' in response for day {day_number}")
                            # Add default values based on field type
                            if field == "is_workout_day":
                                exercise_data[field] = True
                            elif field == "day":
                                exercise_data[field] = day_number
                            elif field == "name":
                                exercise_data[field] = f"Day {day_number} Elite Training"
                            elif field == "sets":
                                exercise_data[field] = 5  # Higher sets for elite
                            elif field == "reps":
                                exercise_data[field] = "3-5 at 95% intensity"  # Elite rep scheme
                            elif field == "description":
                                exercise_data[field] = "Perform this elite exercise with championship-level precision and intensity."
                            elif field == "rest":
                                exercise_data[field] = "90-120 seconds for power recovery"
                            elif field == "motivational_quote":
                                exercise_data[field] = "Champions are made when nobody is watching. Train with elite purpose."
                    
                    # Search for YouTube video for this elite exercise
                    try:
                        if exercise_data.get("name"):
                            video_url = await video_search_service.find_workout_video(
                                exercise_name=exercise_data["name"],
                                gear=request.gear.value,
                                mission=request.mission.value
                            )
                            
                            if not video_url:
                                # Try to find a generic video if specific exercise video not found
                                video_url = await video_search_service.find_generic_workout_video(
                                    mission=request.mission.value,
                                    gear=request.gear.value,
                                    time_commitment=request.time_commitment.value
                                )
                            
                            exercise_data["video_url"] = video_url if video_url else f"https://www.youtube.com/results?search_query={exercise_data['name'].replace(' ', '+')}+{request.mission.value.replace(' ', '+')}+{request.gear.value.replace(' ', '+')}"
                            logger.info(f"Added video URL for day {day_number}: {exercise_data['video_url']}")
                        else:
                            exercise_data["video_url"] = f"https://www.youtube.com/results?search_query=elite+{request.mission.value.replace(' ', '+')}+{request.gear.value.replace(' ', '+')}+workout"
                    except Exception as video_error:
                        logger.warning(f"Failed to find video for day {day_number}: {video_error}")
                        # Provide a fallback YouTube search URL
                        exercise_name = exercise_data.get("name", request.mission.value)
                        exercise_data["video_url"] = f"https://www.youtube.com/results?search_query={exercise_name.replace(' ', '+')}+{request.mission.value.replace(' ', '+')}+{request.gear.value.replace(' ', '+')}"
                    
                    # Calculate and add calories burned for workout days
                    exercise_data["calories_burned"] = Phase3Service.calculate_calories_burned(
                        time_commitment=request.time_commitment,
                        gear=request.gear,
                        mission=request.mission,
                        day_number=day_number
                    )
                        
                else:
                    # Validate rest day fields
                    if "is_workout_day" not in exercise_data:
                        exercise_data["is_workout_day"] = False
                    if "day" not in exercise_data:
                        exercise_data["day"] = day_number
                    if "motivational_quote" not in exercise_data:
                        is_rest = not exercise_data.get("is_workout_day", True)
                        exercise_data["motivational_quote"] = Phase3Service.get_daily_quote(day_number, is_rest_day=is_rest)
                    
                    # Ensure workout-specific fields are None for rest days
                    exercise_data["name"] = None
                    exercise_data["sets"] = None
                    exercise_data["reps"] = None
                    exercise_data["description"] = None
                    exercise_data["rest"] = None
                    exercise_data["video_url"] = None  # No video for rest days
                    exercise_data["calories_burned"] = None  # No calories burned on rest days
                
                logger.info(f"Successfully generated Phase 3 elite exercise for day {day_number}")
                return exercise_data
                
            except Exception as e:
                # Enhanced error handling for elite training
                error_message = f"Error generating Phase 3 elite workout for day {day_number}: {str(e)}"
                logger.error(error_message)
                
                # Determine if it should be a workout day
                day_of_week = get_day_of_week(day_number)
                is_workout = is_workout_day(day_of_week)
                
                # Create elite-level placeholder exercises based on day focus
                if is_workout:
                    focus = Phase3Service.DAY_FOCUS_MAP.get(day_of_week, "Elite performance training")
                    week_number, progress = get_week_and_progress_info(day_number)
                    
                    # Different elite fallbacks based on focus, mission, and gear
                    if "strength" in focus.lower() or "power" in focus.lower():
                        fallback_exercise = {
                            "day": day_number,
                            "name": f"Elite {request.mission.value} {focus} Complex with {request.gear.value}",
                            "sets": 5,  # Elite volume
                            "reps": "3-5 at competition intensity",  # Elite rep scheme
                            "description": f"Execute elite-level {focus.lower()} protocols with {request.gear.value.lower()} that specifically target your {request.mission.value.lower()} goals. Focus on power development and competitive readiness.",
                            "rest": "2-3 minutes for complete power recovery",  # Elite rest periods
                            "motivational_quote": Phase3Service.get_daily_quote(day_number, is_rest_day=False),
                            "is_workout_day": True,
                            "video_url": f"https://www.youtube.com/results?search_query=elite+{focus.replace(' ', '+')}+{request.gear.value}+{request.mission.value}+training",
                            "calories_burned": Phase3Service.calculate_calories_burned(
                                time_commitment=request.time_commitment,
                                gear=request.gear,
                                mission=request.mission,
                                day_number=day_number
                            )
                        }
                    elif "metabolic" in focus.lower() or "conditioning" in focus.lower():
                        fallback_exercise = {
                            "day": day_number,
                            "name": f"Elite {request.mission.value} Metabolic Power Circuit with {request.gear.value}",
                            "sets": 6,  # Elite volume
                            "reps": "30 seconds max effort, 15 seconds transition",  # Elite intensity
                            "description": f"Elite metabolic conditioning circuit using {request.gear.value.lower()} designed for {request.mission.value.lower()}. Focus on peak power output and competitive conditioning. Execute at championship intensity.",
                            "rest": "90 seconds between rounds for power maintenance",
                            "motivational_quote": Phase3Service.get_daily_quote(day_number, is_rest_day=False),
                            "is_workout_day": True,
                            "video_url": f"https://www.youtube.com/results?search_query=elite+metabolic+conditioning+{request.gear.value}+{request.mission.value}",
                            "calories_burned": Phase3Service.calculate_calories_burned(
                                time_commitment=request.time_commitment,
                                gear=request.gear,
                                mission=request.mission,
                                day_number=day_number
                            )
                        }
                    else:
                        fallback_exercise = {
                            "day": day_number,
                            "name": f"Elite {request.mission.value} Performance Training with {request.gear.value}",
                            "sets": 4,
                            "reps": "Competition-level intensity and precision",
                            "description": f"Elite training protocol using {request.gear.value.lower()} optimized for {request.mission.value.lower()}. Execute with championship-level focus and technical precision.",
                            "rest": "120 seconds for optimal power recovery",
                            "motivational_quote": Phase3Service.get_daily_quote(day_number, is_rest_day=False),
                            "is_workout_day": True,
                            "video_url": f"https://www.youtube.com/results?search_query=elite+performance+training+{request.gear.value}",
                            "calories_burned": Phase3Service.calculate_calories_burned(
                                time_commitment=request.time_commitment,
                                gear=request.gear,
                                mission=request.mission,
                                day_number=day_number
                            )
                        }
                    
                    # Try to find a video for the fallback exercise
                    try:
                        video_url = await video_search_service.find_generic_workout_video(
                            mission=request.mission.value,
                            gear=request.gear.value,
                            time_commitment=request.time_commitment.value
                        )
                        if video_url:
                            fallback_exercise["video_url"] = video_url
                    except Exception as video_error:
                        logger.warning(f"Failed to find video for fallback exercise day {day_number}: {video_error}")
                    
                    return fallback_exercise
                else:
                    # Get a unique daily motivational quote for rest days
                    daily_rest_quote = Phase3Service.get_daily_quote(day_number, is_rest_day=True)
                    
                    return {
                        "day": day_number,
                        "motivational_quote": daily_rest_quote,
                        "is_workout_day": False,
                        "calories_burned": None
                    }
        
        # Process days in parallel batches to optimize API usage
        all_exercises = []
        
        try:
            # Log the elite workout days for debugging
            logger.info(f"Generating Phase 3 elite 30-day plan with workout days: Monday, Tuesday, Thursday, Friday")
            
            # Process in batches of BATCH_SIZE (6 by default)
            for batch_start in range(1, 31, Phase3Service.BATCH_SIZE):
                # Calculate the days in this batch
                batch_end = min(batch_start + Phase3Service.BATCH_SIZE, 31)
                batch_days = range(batch_start, batch_end)
                batch_size = len(batch_days)
                
                logger.info(f"Processing Phase 3 elite batch from day {batch_start} to {batch_end-1} ({batch_size} days)")
                
                # Create tasks for parallel processing of each day in the batch
                tasks = [generate_single_day_exercise(day) for day in batch_days]
                
                # Run tasks in parallel with timeout handling
                try:
                    batch_results = await asyncio.gather(*tasks)
                    logger.info(f"Successfully processed Phase 3 elite batch of {batch_size} days")
                except asyncio.TimeoutError:
                    logger.error(f"Timeout occurred while processing Phase 3 elite batch starting at day {batch_start}")
                    # Process days sequentially as fallback
                    batch_results = []
                    for day in batch_days:
                        result = await generate_single_day_exercise(day)
                        batch_results.append(result)
                
                # Add the batch results to the overall list
                all_exercises.extend(batch_results)
            
            # Process the results
            logger.info(f"Processing {len(all_exercises)} days of Phase 3 elite exercises")
            
            # Check for any missing days and fill them in
            day_numbers = [ex.get("day") for ex in all_exercises]
            for day in range(1, 31):
                if day not in day_numbers:
                    logger.warning(f"Day {day} missing from Phase 3 elite results, generating placeholder")
                    day_of_week = get_day_of_week(day)
                    is_workout = is_workout_day(day_of_week)
                    
                    if is_workout:
                        placeholder = {
                            "day": day,
                            "name": "Elite Performance Training",
                            "sets": 5,  # Elite volume
                            "reps": "Competition-level intensity",  # Elite approach
                            "description": "Elite training protocol for peak performers. Execute with championship precision and competitive mindset.",
                            "rest": "2-3 minutes for power optimization",  # Elite rest
                            "motivational_quote": Phase3Service.get_daily_quote(day, is_rest_day=False),
                            "is_workout_day": True,
                            "calories_burned": Phase3Service.calculate_calories_burned(
                                time_commitment=request.time_commitment,
                                gear=request.gear,
                                mission=request.mission,
                                day_number=day
                            )
                        }
                    else:
                        placeholder = {
                            "day": day,
                            "motivational_quote": Phase3Service.get_daily_quote(day, is_rest_day=True),
                            "is_workout_day": False,
                            "calories_burned": None
                        }
                    all_exercises.append(placeholder)
            
            # Convert the dictionaries to WorkoutExercise objects
            workout_exercises = [WorkoutExercise(**exercise) for exercise in all_exercises]
            
            # Sort exercises by day number to ensure proper order
            workout_exercises.sort(key=lambda x: x.day)
            
            logger.info(f"Generated complete Phase 3 elite 30-day plan with {len(workout_exercises)} days")
            
            # Create and return the elite response
            return WorkoutPlanResponse(workout_plan=workout_exercises)
            
        except Exception as e:
            error_message = f"Failed to generate Phase 3 elite workout plan with mission '{request.mission}', time commitment '{request.time_commitment}', and gear '{request.gear}'. Error details: {str(e)}"
            logger.error(error_message)
            raise Exception(error_message)
