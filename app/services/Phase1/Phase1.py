import json
import asyncio
import calendar
import logging
from datetime import datetime, timedelta
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from openai import AsyncOpenAI
from app.core.config import OPENAI_API_KEY, OPENAI_MODEL
from app.services.Phase1.Phase1_Schema import WorkoutPlanRequest, WorkoutPlanResponse, WorkoutExercise
from app.services.video_search import video_search_service

# Set up logging
logger = logging.getLogger(__name__)

class Phase1Service:
    # Define workout focus for each day of the week for better organization
    DAY_FOCUS_MAP = {
        "Monday": "Upper body strength",
        "Tuesday": "Lower body strength", 
        "Wednesday": "Core and stability",
        "Thursday": "Cardio and endurance",
        "Friday": "Flexibility and mobility",
        "Saturday": "Functional movement",
        "Sunday": "Light active recovery"
    }
    
    # Batch size for parallel API calls
    BATCH_SIZE = 6
    
    # Collection of motivational quotes for Phase 1 (beginner-friendly)
    MOTIVATIONAL_QUOTES = [
        "The journey of a thousand miles begins with a single step.",
        "Small daily improvements lead to remarkable results.",
        "Your body can stand almost anything. It's your mind you have to convince.",
        "The only bad workout is the one that didn't happen.",
        "Make fitness a habit, not a chore.",
        "Success is the sum of small efforts repeated day in and day out.",
        "Strength does not come from physical capacity. It comes from an indomitable will.",
        "You don't have to be extreme, just consistent.",
        "Progress is progress, no matter how small.",
        "Every day is another chance to get stronger.",
        "The pain you feel today will be the strength you feel tomorrow.",
        "Strive for progress, not perfection.",
        "Your health is an investment, not an expense.",
        "The difference between try and triumph is just a little umph!",
        "Be stronger than your excuses.",
        "What seems impossible today will one day become your warm-up.",
        "Take care of your body. It's the only place you have to live.",
        "A year from now, you'll wish you had started today.",
        "Good things come to those who sweat.",
        "The hardest lift of all is lifting your butt off the couch.",
        "Motivation is what gets you started. Habit is what keeps you going.",
        "Your body hears everything your mind says.",
        "Don't stop when you're tired. Stop when you're done.",
        "Rome wasn't built in a day, and neither was your body.",
        "Fitness is not about being better than someone else. It's about being better than you used to be.",
        "The only workout you regret is the one you didn't do.",
        "If it doesn't challenge you, it doesn't change you.",
        "Discipline is choosing between what you want now and what you want most.",
        "The clock is ticking. Are you becoming the person you want to be?",
        "Fall in love with taking care of your body.",
        "Today I will do what others won't, so tomorrow I can accomplish what others can't."
    ]
    
    # Collection of rest day quotes for Phase 1
    REST_DAY_QUOTES = [
        "Rest days are an essential part of your fitness journey. They allow your body to recover and grow stronger.",
        "Recovery is where the magic happens. Give your body the respect it deserves.",
        "Today's rest is tomorrow's strength. Your body is rebuilding itself for the challenges ahead.",
        "Don't think of it as a day off. Think of it as letting your body catch up with your ambition.",
        "The space between workouts is where transformation happens.",
        "Rest is not a luxury, it's a necessity. Your muscles grow when you rest, not when you train.",
        "Honor your body's need for recovery. It's telling you what it needs to perform better tomorrow.",
        "Smart athletes know that rest is part of training, not separate from it.",
        "Recovery days are growth days. Trust the process.",
        "Rest is productive. Give yourself permission to recharge.",
        "Your body is speaking to you. Rest when it whispers, so you don't have to rest when it screams.",
        "Just as important as pushing hard is knowing when to pull back.",
        "Rest is not quitting. It's strategic preparation for your next victory.",
        "A well-rested body performs better than an overtrained one.",
        "Sometimes the most productive thing you can do is rest."
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
        seed = f"phase1-{today}-day{day_number}-{'rest' if is_rest_day else 'workout'}"
        hash_value = int(hashlib.md5(seed.encode()).hexdigest(), 16)
        
        # Select quote based on the hash value
        if is_rest_day:
            return Phase1Service.REST_DAY_QUOTES[hash_value % len(Phase1Service.REST_DAY_QUOTES)]
        else:
            return Phase1Service.MOTIVATIONAL_QUOTES[hash_value % len(Phase1Service.MOTIVATIONAL_QUOTES)]
    
    @staticmethod
    def calculate_calories_burned(time_commitment, gear, mission, day_number: int) -> int:
        """
        Calculate estimated calories burned for a workout based on parameters.
        
        This is a simplified estimation based on:
        - Time commitment
        - Equipment type (intensity factor)
        - Mission type (activity factor)
        - Day progression (intensity progression)
        
        Args:
            time_commitment: TimeCommitment enum value
            gear: GearType enum value 
            mission: MissionType enum value
            day_number: Day number in the 30-day plan (1-30)
            
        Returns:
            Estimated calories burned as integer
        """
        # Base calories per minute for different time commitments (conservative estimate)
        base_calories_per_minute = {
            "10 min": 8,      # Light to moderate intensity
            "20-30 min": 10,  # Moderate intensity
            "45+ min": 12     # Moderate to high intensity
        }
        
        # Time duration mapping
        time_minutes = {
            "10 min": 10,
            "20-30 min": 25,  # Average of 20-30
            "45+ min": 45     # Minimum of 45+
        }
        
        # Equipment intensity multipliers
        gear_multipliers = {
            "Bodyweight": 1.0,     # Base intensity
            "Sandbag": 1.2,        # Functional training increase
            "Dumbbells": 1.15,     # Moderate resistance increase
            "Full Gym": 1.3        # Maximum equipment variety
        }
        
        # Mission type intensity multipliers
        mission_multipliers = {
            "Lose Fat": 1.2,           # Higher cardio component
            "Build Strength": 1.0,     # Base strength training
            "Move Pain-Free": 0.8,     # Lower intensity, rehabilitation focus
            "Tactical Readiness": 1.25 # High intensity, functional training
        }
        
        # Progressive intensity based on day (weeks 1-5)
        week_number = (day_number - 1) // 7 + 1
        progression_multipliers = {
            1: 0.85,  # Week 1: Easier start
            2: 0.95,  # Week 2: Building up
            3: 1.0,   # Week 3: Standard intensity
            4: 1.1,   # Week 4: Increased intensity
            5: 1.15   # Week 5: Peak intensity
        }
        
        # Get base values
        time_str = time_commitment.value
        base_cal_per_min = base_calories_per_minute.get(time_str, 10)
        duration = time_minutes.get(time_str, 25)
        
        # Calculate base calories
        base_calories = base_cal_per_min * duration
        
        # Apply multipliers
        gear_factor = gear_multipliers.get(gear.value, 1.0)
        mission_factor = mission_multipliers.get(mission.value, 1.0)
        progression_factor = progression_multipliers.get(week_number, 1.0)
        
        # Final calculation
        total_calories = base_calories * gear_factor * mission_factor * progression_factor
        
        # Round to nearest 5 calories for cleaner numbers
        return round(total_calories / 5) * 5
    
    @staticmethod
    async def generate_workout_plan(request: WorkoutPlanRequest) -> WorkoutPlanResponse:
        """
        Generate a 30-day workout plan using OpenAI with a simplified format.
        
        Features:
        - Makes 6 parallel API calls for each batch of days (30 days total)
        - Only generates full workout details on specified workout days
        - Provides motivational quotes for rest days
        - Ensures variety in exercises across different days
        - Handles errors gracefully with fallback options
        
        Args:
            request: WorkoutPlanRequest containing user preferences
            
        Returns:
            WorkoutPlanResponse with 30 days of workout data
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
        
        # Create system message for context - enhanced for more specific instructions
        system_message = """
        You are an expert fitness trainer with specialized knowledge in exercise physiology, biomechanics, and progressive training methodologies.
        
        TASK:
        - For WORKOUT DAYS: Create professional, specific exercise entries with these fields: Day, Name, Sets, Reps, Description, Rest, Motivational_Quote
        - For REST DAYS: Provide only a meaningful motivational quote focused on recovery, patience, and long-term progress
        
        EXERCISE SELECTION GUIDELINES:
        - Ensure exercises match the user's equipment availability and fitness goal
        - Create progressive difficulty throughout the 30-day period
        - Vary muscle groups, movement patterns, and training modalities
        - Ensure exercise names are specific and descriptive (e.g., "Dumbbell Reverse Lunge with Twist" not just "Lunges")
        - Use commonly recognized exercise names that would have instructional videos available
        - Exercise descriptions should include clear form cues and proper technique guidance
        
        RESPONSE FORMAT:
        - Provide JSON format with only the required fields
        - Be precise with recommended sets, reps, and rest periods based on the day's focus
        - Ensure motivational quotes are relevant to the day's workout or recovery theme
        - Exercise names should be searchable and commonly used in fitness instruction
        
        This plan should be professional quality, as if created for a paying client at a high-end fitness facility.
        """
        
        @staticmethod
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
            Check if the given day is a workout day based on default schedule
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
            Calculate week number and progress percentage through the program
            
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
            Generate a single day's workout or rest day exercise
            
            This function determines if the given day is a workout day based on user preferences,
            then generates an appropriate exercise or motivational quote using the OpenAI API.
            
            Args:
                day_number: The day number in the 30-day plan (1-30)
                
            Returns:
                Dictionary containing the exercise data or motivational quote
            """
            # Determine the day of week and if it's a workout day
            day_of_week = get_day_of_week(day_number)
            workout_day = is_workout_day(day_of_week)
            
            # Get week number and progress through the program
            week_number, progress_percentage = get_week_and_progress_info(day_number)
            
            # Get the focus for today from our predefined map
            focus = "Rest and recovery"
            if workout_day:
                focus = Phase1Service.DAY_FOCUS_MAP.get(day_of_week, "General fitness")
                
            # Determine intensity based on progress through the program
            intensity_level = "beginner"
            if progress_percentage > 60:
                intensity_level = "advanced"
            elif progress_percentage > 30:
                intensity_level = "intermediate"
            # Create user message based on whether it's a workout day or rest day
            if workout_day:
                user_message = f"""
                Create a professional, detailed exercise for Day {day_number} ({day_of_week}) of a 30-day workout plan:
                
                CLIENT DETAILS:
                - Fitness Goal: {request.mission}
                - Available Time: {request.time_commitment}
                - Equipment Access: {request.gear}
                {f"- Training Style: {request.squad}" if request.squad else ""}
                
                WORKOUT SPECIFICS:
                - Day: {day_number}/30 ({progress_percentage:.1f}% through program)
                - Week: {week_number} of 5
                - Today's Focus: {focus}
                - Intensity Level: {intensity_level}
                
                REQUIREMENTS:
                - Create a {intensity_level}-level exercise suitable for today's focus area
                - Exercise should be achievable with the client's available equipment
                - Exercise should fit within the client's time commitment
                - This exercise should contribute to the client's primary goal: {request.mission}
                - Make this exercise DIFFERENT from exercises on other days
                
                IMPORTANT:
                - The exercise "name" MUST include the client's mission ({request.mission}) and available gear ({request.gear})
                - The "description" MUST be specific to the client's mission and available gear
                
                FORMAT:
                {{
                    "day": {day_number},
                    "name": "Specific and professional exercise name",
                    "sets": Number of sets appropriate for this exercise and intensity level,
                    "reps": "Precise rep count or duration with proper progression for week {week_number}",
                    "description": "Detailed, professional description with clear form cues and proper technique guidance",
                    "rest": "Optimal rest time between sets for this specific exercise and intensity",
                    "motivational_quote": "An inspiring, specific quote relevant to today's focus area and progress point",
                    "is_workout_day": true
                }}
                
                Remember: This should be professional quality, as if provided to a paying client.
                """
            else:
                user_message = f"""
                Create an impactful motivational message for Day {day_number} ({day_of_week}), which is a scheduled REST DAY in a 30-day workout program.
                
                CLIENT CONTEXT:
                - Currently {progress_percentage:.1f}% through their 30-day program (Day {day_number})
                - Primary Goal: {request.mission}
                - Rest day following or preceding workouts focused on: {Phase1Service.DAY_FOCUS_MAP.get(get_day_of_week(day_number-1))}
                
                REQUIREMENTS:
                - Motivational quote should emphasize the importance of recovery in achieving fitness goals
                - Message should be inspiring but also educational about why rest is vital
                - Content should be relevant to the client's specific fitness journey ({request.mission})
                - Quote should acknowledge their current progress point in the program
                
                FORMAT:
                {{
                    "day": {day_number},
                    "motivational_quote": "An inspiring and meaningful quote about the importance of recovery, patience, and consistency in fitness",
                    "is_workout_day": false
                }}
                
                Create something truly meaningful that will keep the client engaged even on their rest day.
                """
            
            try:
                logger.info(f"Generating exercise for day {day_number} ({day_of_week}) - Workout day: {workout_day}")
                
                # Make OpenAI API call with enhanced parameters
                response = await client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.7,  # Balanced creativity
                    max_tokens=600,   # Increased for more detailed responses
                    top_p=0.9,        # Slightly reduced for more focused responses
                    frequency_penalty=0.4,  # Increased to encourage unique wording
                    presence_penalty=0.2,   # Added to discourage repetition
                    response_format={"type": "json_object"}  # Request JSON format explicitly
                )
                
                # Extract and parse the response
                content = response.choices[0].message.content
                
                # Clean the content if needed (backup in case response_format doesn't work)
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                # Parse the JSON response
                exercise_data = json.loads(content)
                
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
                                exercise_data[field] = f"Day {day_number} Workout"
                            elif field == "sets":
                                exercise_data[field] = 3
                            elif field == "reps":
                                exercise_data[field] = "8-12"
                            elif field == "description":
                                exercise_data[field] = "Perform this exercise with proper form."
                            elif field == "rest":
                                exercise_data[field] = "60 seconds"
                            elif field == "motivational_quote":
                                exercise_data[field] = "Every workout brings you closer to your goals."
                    
                    # Search for YouTube video for this exercise
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
                            exercise_data["video_url"] = f"https://www.youtube.com/results?search_query={request.mission.value.replace(' ', '+')}+{request.gear.value}+workout"
                    except Exception as video_error:
                        logger.warning(f"Failed to find video for day {day_number}: {video_error}")
                        # Provide a fallback YouTube search URL
                        exercise_name = exercise_data.get("name", request.mission.value)
                        exercise_data["video_url"] = f"https://www.youtube.com/results?search_query={exercise_name.replace(' ', '+')}+{request.mission.value.replace(' ', '+')}+{request.gear.value.replace(' ', '+')}"
                    
                    # Calculate and add calories burned for workout days
                    exercise_data["calories_burned"] = Phase1Service.calculate_calories_burned(
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
                        exercise_data["motivational_quote"] = Phase1Service.get_daily_quote(day_number, is_rest_day=is_rest)
                    
                    # Ensure workout-specific fields are None for rest days
                    exercise_data["name"] = None
                    exercise_data["sets"] = None
                    exercise_data["reps"] = None
                    exercise_data["description"] = None
                    exercise_data["rest"] = None
                    exercise_data["video_url"] = None  # No video for rest days
                    exercise_data["calories_burned"] = None  # No calories burned on rest days
                
                logger.info(f"Successfully generated exercise for day {day_number}")
                return exercise_data
                
            except Exception as e:
                # Enhanced error handling
                error_message = f"Error generating workout for day {day_number}: {str(e)}"
                logger.error(error_message)
                
                # Determine if it should be a workout day
                day_of_week = get_day_of_week(day_number)
                is_workout = is_workout_day(day_of_week)
                
                # Create more relevant placeholder exercises based on day focus
                if is_workout:
                    focus = Phase1Service.DAY_FOCUS_MAP.get(day_of_week, "General fitness")
                    week_number, progress = get_week_and_progress_info(day_number)
                    
                    # Different fallbacks based on focus and user's mission and gear
                    if "strength" in focus.lower():
                        fallback_exercise = {
                            "day": day_number,
                            "name": f"{request.mission.value} {focus} Circuit with {request.gear.value}",
                            "sets": 3,
                            "reps": "8-10 per exercise",
                            "description": f"Complete a circuit of {request.mission.value.lower()}-focused {focus.lower()} exercises using {request.gear.value.lower()}. Adjust intensity to match your fitness level.",
                            "rest": "60 seconds between sets",
                            "motivational_quote": Phase1Service.get_daily_quote(day_number, is_rest_day=False),
                            "is_workout_day": True,
                            "video_url": None,
                            "calories_burned": Phase1Service.calculate_calories_burned(
                                time_commitment=request.time_commitment,
                                gear=request.gear,
                                mission=request.mission,
                                day_number=day_number
                            )
                        }
                    elif "cardio" in focus.lower():
                        fallback_exercise = {
                            "day": day_number,
                            "name": f"{request.mission.value} Interval Training with {request.gear.value}",
                            "sets": 4,
                            "reps": "30 seconds work, 30 seconds rest",
                            "description": f"Choose {request.gear.value.lower()}-based cardio exercises that support your {request.mission.value.lower()} goal. Alternate between high intensity work and rest periods.",
                            "rest": "1 minute between sets",
                            "motivational_quote": Phase1Service.get_daily_quote(day_number, is_rest_day=False),
                            "is_workout_day": True,
                            "video_url": None,
                            "calories_burned": Phase1Service.calculate_calories_burned(
                                time_commitment=request.time_commitment,
                                gear=request.gear,
                                mission=request.mission,
                                day_number=day_number
                            )
                        }
                    else:
                        fallback_exercise = {
                            "day": day_number,
                            "name": f"{request.mission.value} Workout Circuit with {request.gear.value}",
                            "sets": 2,
                            "reps": "12-15 per exercise",
                            "description": f"Choose 4-5 {request.gear.value.lower()} exercises that match today's focus and your {request.mission.value.lower()} goal. Perform each with proper form.",
                            "rest": "45 seconds between exercises",
                            "motivational_quote": Phase1Service.get_daily_quote(day_number, is_rest_day=False),
                            "is_workout_day": True,
                            "video_url": None,
                            "calories_burned": Phase1Service.calculate_calories_burned(
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
                        fallback_exercise["video_url"] = video_url if video_url else f"https://www.youtube.com/results?search_query={fallback_exercise['name'].replace(' ', '+')}+workout"
                    except Exception as video_error:
                        logger.warning(f"Failed to find video for fallback exercise day {day_number}: {video_error}")
                        # Provide a fallback YouTube search URL
                        fallback_exercise["video_url"] = f"https://www.youtube.com/results?search_query={fallback_exercise['name'].replace(' ', '+')}+workout"
                    
                    return fallback_exercise
                else:
                    # Get a unique daily motivational quote for rest days
                    daily_rest_quote = Phase1Service.get_daily_quote(day_number, is_rest_day=True)
                    
                    return {
                        "day": day_number,
                        "name": None,
                        "sets": None,
                        "reps": None,
                        "description": None,
                        "rest": None,
                        "motivational_quote": daily_rest_quote,
                        "is_workout_day": False,
                        "video_url": None,
                        "calories_burned": None
                    }
        
        # Process days in parallel batches to optimize API usage
        all_exercises = []
        
        try:
            # Log the workout days for debugging
            logger.info(f"Generating 30-day plan with default workout days: Monday, Tuesday, Thursday, Friday")
            
            # Process in batches of BATCH_SIZE (6 by default)
            for batch_start in range(1, 31, Phase1Service.BATCH_SIZE):
                # Calculate the days in this batch
                batch_end = min(batch_start + Phase1Service.BATCH_SIZE, 31)
                batch_days = range(batch_start, batch_end)
                batch_size = len(batch_days)
                
                logger.info(f"Processing batch from day {batch_start} to {batch_end-1} ({batch_size} days)")
                
                # Create tasks for parallel processing of each day in the batch
                tasks = [generate_single_day_exercise(day) for day in batch_days]
                
                # Run tasks in parallel with timeout handling
                try:
                    batch_results = await asyncio.gather(*tasks)
                    logger.info(f"Successfully processed batch of {batch_size} days")
                except asyncio.TimeoutError:
                    logger.error(f"Timeout occurred while processing batch starting at day {batch_start}")
                    # Process days sequentially as fallback
                    batch_results = []
                    for day in batch_days:
                        result = await generate_single_day_exercise(day)
                        batch_results.append(result)
                
                # Add the batch results to the overall list
                all_exercises.extend(batch_results)
            
            # Process the results
            logger.info(f"Processing {len(all_exercises)} days of exercises")
            
            # Check for any missing days and fill them in
            day_numbers = [ex.get("day") for ex in all_exercises]
            for day in range(1, 31):
                if day not in day_numbers:
                    logger.warning(f"Day {day} missing from results, generating placeholder")
                    day_of_week = get_day_of_week(day)
                    is_workout = is_workout_day(day_of_week)
                    
                    if is_workout:
                        placeholder = {
                            "day": day,
                            "name": "General Fitness Exercise",
                            "sets": 3,
                            "reps": "10-12",
                            "description": "Choose an exercise that matches your fitness level and available equipment.",
                            "rest": "60 seconds",
                            "motivational_quote": Phase1Service.get_daily_quote(day, is_rest_day=False),
                            "is_workout_day": True,
                            "video_url": f"https://www.youtube.com/results?search_query={request.mission.value.replace(' ', '+')}+{request.gear.value}+workout",
                            "calories_burned": Phase1Service.calculate_calories_burned(
                                time_commitment=request.time_commitment,
                                gear=request.gear,
                                mission=request.mission,
                                day_number=day
                            )
                        }
                    else:
                        placeholder = {
                            "day": day,
                            "name": None,
                            "sets": None,
                            "reps": None,
                            "description": None,
                            "rest": None,
                            "motivational_quote": Phase1Service.get_daily_quote(day, is_rest_day=True),
                            "is_workout_day": False,
                            "video_url": None,
                            "calories_burned": None
                        }
                    all_exercises.append(placeholder)
            
            # Convert the dictionaries to WorkoutExercise objects
            workout_exercises = [WorkoutExercise(**exercise) for exercise in all_exercises]
            
            # Sort exercises by day number to ensure proper order
            workout_exercises.sort(key=lambda x: x.day)
            
            # Add program statistics
            workout_count = sum(1 for ex in workout_exercises if getattr(ex, 'is_workout_day', False))
            rest_count = len(workout_exercises) - workout_count
            
            logger.info(f"Generated complete 30-day plan with {workout_count} workout days and {rest_count} rest days")
            
            # Create and return the enhanced response
            return WorkoutPlanResponse(workout_plan=workout_exercises)
            
        except Exception as e:
            # Enhanced error handling
            error_message = f"Error generating complete workout plan: {str(e)}"
            logger.error(error_message)
            
            # Provide a more helpful error message with context
            detailed_error = (
                f"Failed to generate workout plan with mission '{request.mission}', "
                f"time commitment '{request.time_commitment}', and gear '{request.gear}'. "
                f"Error details: {str(e)}"
            )
            raise Exception(detailed_error)