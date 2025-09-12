import json
import asyncio
import calendar
import logging
from datetime import datetime, timedelta
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from openai import AsyncOpenAI
from app.core.config import OPENAI_API_KEY, OPENAI_MODEL
from app.services.Phase2.Phase2_Schema import WorkoutPlanRequest, WorkoutPlanResponse, WorkoutExercise
from app.services.video_search import video_search_service

# Set up logging
logger = logging.getLogger(__name__)

class Phase2Service:
    # Define more challenging workout focus for each day of the week
    DAY_FOCUS_MAP = {
        "Monday": "Upper body compound movements",
        "Tuesday": "Lower body power and strength", 
        "Wednesday": "Core and rotational stability",
        "Thursday": "High-intensity interval training",
        "Friday": "Full-body functional circuits",
        "Saturday": "Compound movement patterns",
        "Sunday": "Active recovery and mobility"
    }
    
    # Define intensity multipliers for Phase 2 (higher than Phase 1)
    INTENSITY_MULTIPLIERS = {
        "sets": 1.2,  # 20% more sets
        "reps": 1.15, # 15% more reps
        "rest": 0.85  # 15% less rest
    }
    
    # Batch size for parallel API calls
    BATCH_SIZE = 6
    
    # Collection of motivational quotes for Phase 2 (intermediate level)
    MOTIVATIONAL_QUOTES = [
        "When you feel like stopping, think about why you started.",
        "Your body is the reflection of your lifestyle.",
        "Push harder today if you want a different tomorrow.",
        "You don't get what you wish for. You get what you work for.",
        "Discipline is doing what needs to be done even when you don't want to do it.",
        "No pain, no gain. Shut up and train.",
        "The best project you'll ever work on is you.",
        "It's not about having time, it's about making time.",
        "Strength is earned, not given.",
        "The harder the battle, the sweeter the victory.",
        "Be stronger than your excuses.",
        "Nothing worth having comes easy.",
        "You're only one workout away from a good mood.",
        "The pain of discipline weighs ounces, the pain of regret weighs tons.",
        "Don't wish for it, work for it.",
        "The only way to define your limits is by going beyond them.",
        "The body achieves what the mind believes.",
        "Train like you've never won. Perform like you've never lost.",
        "When your legs get tired, run with your heart.",
        "If it doesn't challenge you, it won't change you.",
        "Focus on your goals, not your fears.",
        "Ability is what you're capable of doing. Motivation determines what you do. Attitude determines how well you do it.",
        "Champions keep playing until they get it right.",
        "Challenges are what make life interesting. Overcoming them is what makes life meaningful.",
        "It's going to be hard, but hard is not impossible.",
        "Go the extra mile. It's never crowded.",
        "Be better than you were yesterday.",
        "Good is not good when better is expected.",
        "The difference between the impossible and the possible lies in a person's determination.",
        "Excellence is not a singular act but a habit. You are what you do repeatedly."
    ]
    
    # Collection of rest day quotes for Phase 2
    REST_DAY_QUOTES = [
        "Rest is not a luxury, it's a performance enhancer.",
        "Strategic recovery makes champions. Your body is rebuilding stronger as you rest.",
        "Today you rest, tomorrow you conquer.",
        "Recovery is not optional for high performance. It's mandatory.",
        "Rest is training. Treat it with the same discipline as your hardest workout.",
        "Performance is what you do during training. Progress happens during rest.",
        "Recovery is when adaptation happens. It's when you actually get stronger.",
        "A rested athlete is a dangerous athlete.",
        "Recovery is your secret weapon. Without it, training is just breaking down.",
        "Smart training includes strategic recovery. Today is part of your plan for success.",
        "Rest with purpose. Your body is busy building the athlete you will become.",
        "Your muscles grow during recovery, not during training. Honor this process.",
        "The quality of your recovery determines the quality of your performance.",
        "Champions recognize that rest is as important as work.",
        "Today's rest creates tomorrow's personal record."
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
        seed = f"phase2-{today}-day{day_number}-{'rest' if is_rest_day else 'workout'}"
        hash_value = int(hashlib.md5(seed.encode()).hexdigest(), 16)
        
        # Select quote based on the hash value
        if is_rest_day:
            return Phase2Service.REST_DAY_QUOTES[hash_value % len(Phase2Service.REST_DAY_QUOTES)]
        else:
            return Phase2Service.MOTIVATIONAL_QUOTES[hash_value % len(Phase2Service.MOTIVATIONAL_QUOTES)]
    
    @staticmethod
    def calculate_calories_burned(time_commitment, gear, mission, day_number: int) -> int:
        """
        Calculate estimated calories burned for a Phase 2 workout based on parameters.
        
        This calculation uses higher intensity multipliers compared to Phase 1 due to:
        - More advanced exercise selection
        - Higher training volumes
        - More challenging movement patterns
        - Increased training density
        
        Args:
            time_commitment: TimeCommitment enum value
            gear: GearType enum value 
            mission: MissionType enum value
            day_number: Day number in the 30-day plan (1-30)
            
        Returns:
            Estimated calories burned as integer
        """
        # Base calories per minute for Phase 2 (higher than Phase 1)
        base_calories_per_minute = {
            "10 min": 10,     # Higher intensity, advanced movements
            "20-30 min": 12,  # Moderate to high intensity
            "45+ min": 14     # High intensity with advanced techniques
        }
        
        # Time duration mapping
        time_minutes = {
            "10 min": 10,
            "20-30 min": 25,  # Average of 20-30
            "45+ min": 45     # Minimum of 45+
        }
        
        # Equipment intensity multipliers (higher than Phase 1)
        gear_multipliers = {
            "Bodyweight": 1.1,     # Advanced bodyweight movements
            "Sandbag": 1.3,        # Complex functional training
            "Dumbbells": 1.25,     # Advanced resistance patterns
            "Full Gym": 1.4        # Maximum equipment with advanced techniques
        }
        
        # Mission type intensity multipliers (higher than Phase 1)
        mission_multipliers = {
            "Lose Fat": 1.3,           # Higher intensity cardio and circuits
            "Build Strength": 1.15,    # Heavy compound movements
            "Move Pain-Free": 0.9,     # Moderate intensity, movement focused
            "Tactical Readiness": 1.35 # Very high intensity, functional training
        }
        
        # Progressive intensity based on day (weeks 1-5) - more aggressive progression
        week_number = (day_number - 1) // 7 + 1
        progression_multipliers = {
            1: 0.9,   # Week 1: Building up from Phase 1
            2: 1.0,   # Week 2: Standard Phase 2 intensity
            3: 1.1,   # Week 3: Increased intensity
            4: 1.2,   # Week 4: High intensity
            5: 1.25   # Week 5: Peak Phase 2 intensity
        }
        
        # Get base values
        time_str = time_commitment.value
        base_cal_per_min = base_calories_per_minute.get(time_str, 12)
        duration = time_minutes.get(time_str, 25)
        
        # Calculate base calories
        base_calories = base_cal_per_min * duration
        
        # Apply multipliers
        gear_factor = gear_multipliers.get(gear.value, 1.0)
        mission_factor = mission_multipliers.get(mission.value, 1.0)
        progression_factor = progression_multipliers.get(week_number, 1.0)
        
        # Final calculation with Phase 2 intensity boost
        total_calories = base_calories * gear_factor * mission_factor * progression_factor * 1.15
        
        # Round to nearest 5 calories for cleaner numbers
        return round(total_calories / 5) * 5
    
    @staticmethod
    async def generate_workout_plan(request: WorkoutPlanRequest) -> WorkoutPlanResponse:
        """
        Generate a more challenging 30-day workout plan using OpenAI.
        
        Features:
        - Makes 6 parallel API calls for each batch of days (30 days total)
        - Only generates full workout details on specified workout days
        - Provides motivational quotes for rest days
        - Ensures variety in exercises across different days
        - Features more challenging exercises than Phase 1
        - Handles errors gracefully with fallback options
        
        Args:
            request: WorkoutPlanRequest containing user preferences
            
        Returns:
            WorkoutPlanResponse with 30 days of workout data
        """
        # Initialize OpenAI client
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        
        # Create system message for context - enhanced for more advanced workout instructions
        system_message = """
        You are an elite strength and conditioning coach with expertise in creating advanced fitness programs for intermediate to advanced trainees.
        
        TASK:
        - For WORKOUT DAYS: Create professional, challenging exercise entries with these fields: Day, Name, Sets, Reps, Description, Rest, Motivational_Quote
        - For REST DAYS: Provide only a meaningful motivational quote focused on recovery, patience, and long-term progress
        
        EXERCISE SELECTION GUIDELINES - PHASE 2 (MORE CHALLENGING):
        - Design challenging exercises with increased intensity, volume, or complexity compared to beginner workouts
        - Include compound movements, more advanced variations, and exercise progressions
        - Focus on efficient, challenging workouts that push the client to new levels
        - Include supersets, drop sets, or other advanced techniques where appropriate
        - Ensure exercises match the user's equipment availability while providing progressive overload
        - Exercise names should be specific and technical (e.g., "Bulgarian Split Squat with Tempo Control" not just "Split Squat")
        - Exercise descriptions must include precise form cues, technique guidance, and performance standards
        
        RESPONSE FORMAT:
        - Provide JSON format with only the required fields
        - Be precise with recommended sets, reps, and rest periods based on the day's focus
        - Set challenging but achievable parameters for the exercises
        - Ensure motivational quotes are relevant to pushing through difficult training periods
        
        This plan should be professional quality, appropriate for a motivated client who has mastered the basics and is ready for the next level.
        """
        
        # Helper function to get day of week from day number
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
            
        # Helper function to check if a day is a workout day
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
            
        # Helper function to get week number and progress percentage
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
            Generate a single day's workout or rest day exercise with higher intensity for Phase 2
            
            This function determines if the given day is a workout day based on user preferences,
            then generates an appropriate, more challenging exercise or motivational quote.
            
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
                focus = Phase2Service.DAY_FOCUS_MAP.get(day_of_week, "General fitness")
                
            # Determine intensity based on progress through the program - higher baseline for Phase 2
            intensity_level = "intermediate"
            if progress_percentage > 70:
                intensity_level = "advanced"
            elif progress_percentage > 40:
                intensity_level = "intermediate-advanced"
                
            # Create user message based on whether it's a workout day or rest day
            if workout_day:
                user_message = f"""
                Create a challenging, advanced exercise for Day {day_number} ({day_of_week}) of a 30-day Phase 2 workout plan:
                
                CLIENT DETAILS:
                - Fitness Goal: {request.mission}
                - Available Time: {request.time_commitment}
                - Equipment Access: {request.gear}
                {f"- Training Style: {request.squad}" if request.squad else ""}
                
                WORKOUT SPECIFICS:
                - Day: {day_number}/30 ({progress_percentage:.1f}% through program)
                - Week: {week_number} of 5
                - Today's Focus: {focus} (PHASE 2 - MORE CHALLENGING)
                - Intensity Level: {intensity_level} (This is a Phase 2 program - more demanding than beginner level)
                
                REQUIREMENTS:
                - Create a {intensity_level}-level exercise suitable for today's focus area
                - Exercise must be MORE CHALLENGING than a Phase 1 beginner workout
                - Include advanced techniques like tempo control, supersets, or increased time under tension
                - Exercise should be achievable with the client's available equipment but push their limits
                - Exercise should fit within the client's time commitment while maximizing intensity
                - This exercise should contribute to the client's primary goal: {request.mission}
                
                IMPORTANT:
                - The exercise "name" MUST include the client's mission ({request.mission}) and available gear ({request.gear})
                - The "description" MUST be specific to the client's mission and available gear
                - Make this exercise DIFFERENT from exercises on other days
                
                FORMAT:
                {{
                    "day": {day_number},
                    "name": "Specific, technical exercise name with advanced elements",
                    "sets": Number of sets appropriate for this advanced exercise (3-6 range),
                    "reps": "Precise rep count or duration with proper progression for week {week_number} (challenging)",
                    "description": "Detailed, professional description with advanced form cues and technique guidance",
                    "rest": "Optimal rest time between sets for this challenging exercise (typically shorter for increased intensity)",
                    "motivational_quote": "An inspiring, specific quote relevant to pushing through challenges and reaching new levels",
                    "is_workout_day": true
                }}
                
                Remember: This is a PHASE 2 program - exercises should be noticeably more challenging than beginner workouts.
                """
            else:
                user_message = f"""
                Create an impactful motivational message for Day {day_number} ({day_of_week}), which is a scheduled REST DAY in a more challenging Phase 2 30-day workout program.
                
                CLIENT CONTEXT:
                - Currently {progress_percentage:.1f}% through their 30-day program (Day {day_number})
                - Primary Goal: {request.mission}
                - Rest day following or preceding more challenging Phase 2 workouts focused on: {Phase2Service.DAY_FOCUS_MAP.get(get_day_of_week(day_number-1))}
                
                REQUIREMENTS:
                - Motivational quote should emphasize the importance of recovery after intense training sessions
                - Message should acknowledge the increased demands of the Phase 2 training program
                - Content should be relevant to the client's specific fitness journey ({request.mission})
                - Quote should inspire continued dedication to the more challenging program
                
                FORMAT:
                {{
                    "day": {day_number},
                    "motivational_quote": "An inspiring quote about balancing intensity with recovery in more advanced training",
                    "is_workout_day": false
                }}
                
                Create something truly meaningful that will keep the client engaged in their more challenging Phase 2 program even on their rest day.
                """
            
            try:
                logger.info(f"Generating Phase 2 exercise for day {day_number} ({day_of_week}) - Workout day: {workout_day}")
                
                # Make OpenAI API call with enhanced parameters for more challenging workouts
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
                                exercise_data[field] = f"Day {day_number} Advanced Workout"
                            elif field == "sets":
                                exercise_data[field] = 3
                            elif field == "reps":
                                exercise_data[field] = "8-12"
                            elif field == "description":
                                exercise_data[field] = "Perform this advanced exercise with proper form."
                            elif field == "rest":
                                exercise_data[field] = "60 seconds"
                            elif field == "motivational_quote":
                                exercise_data[field] = "Push your limits and exceed your expectations."
                    
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
                            exercise_data["video_url"] = f"https://www.youtube.com/results?search_query={request.mission.value.replace(' ', '+')}+{request.gear.value.replace(' ', '+')}+workout"
                    except Exception as video_error:
                        logger.warning(f"Failed to find video for day {day_number}: {video_error}")
                        # Provide a fallback YouTube search URL
                        exercise_name = exercise_data.get("name", request.mission.value)
                        exercise_data["video_url"] = f"https://www.youtube.com/results?search_query={exercise_name.replace(' ', '+')}+{request.mission.value.replace(' ', '+')}+{request.gear.value.replace(' ', '+')}"
                    
                    # Calculate and add calories burned for workout days
                    exercise_data["calories_burned"] = Phase2Service.calculate_calories_burned(
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
                        exercise_data["motivational_quote"] = Phase2Service.get_daily_quote(day_number, is_rest_day=is_rest)
                    
                    # Ensure workout-specific fields are None for rest days
                    exercise_data["name"] = None
                    exercise_data["sets"] = None
                    exercise_data["reps"] = None
                    exercise_data["description"] = None
                    exercise_data["rest"] = None
                    exercise_data["video_url"] = None  # No video for rest days
                    exercise_data["calories_burned"] = None  # No calories burned on rest days
                
                logger.info(f"Successfully generated Phase 2 exercise for day {day_number}")
                return exercise_data
                
            except Exception as e:
                # Enhanced error handling
                error_message = f"Error generating Phase 2 workout for day {day_number}: {str(e)}"
                logger.error(error_message)
                
                # Determine if it should be a workout day
                day_of_week = get_day_of_week(day_number)
                is_workout = is_workout_day(day_of_week)
                
                # Create more relevant placeholder exercises based on day focus - PHASE 2 MORE CHALLENGING
                if is_workout:
                    focus = Phase2Service.DAY_FOCUS_MAP.get(day_of_week, "General fitness")
                    week_number, progress = get_week_and_progress_info(day_number)
                    
                    # Different fallbacks based on focus - more advanced than Phase 1 and dynamic based on mission and gear
                    if "strength" in focus.lower() or "compound" in focus.lower():
                        fallback_exercise = {
                            "day": day_number,
                            "name": f"Advanced {request.mission.value} {focus} Circuit with {request.gear.value}",
                            "sets": 4,  # More sets than Phase 1
                            "reps": "6-8 per exercise",  # Lower rep range for more intensity
                            "description": f"Complete a challenging circuit of {focus.lower()} exercises designed for {request.mission.value.lower()} using {request.gear.value.lower()}. Include compound movements and focus on progressive overload.",
                            "rest": "45 seconds between sets",  # Less rest than Phase 1
                            "motivational_quote": Phase2Service.get_daily_quote(day_number, is_rest_day=False),
                            "is_workout_day": True,
                            "video_url": f"https://www.youtube.com/results?search_query=advanced+{focus.replace(' ', '+')}+{request.gear.value}+{request.mission.value}+workout",
                            "calories_burned": Phase2Service.calculate_calories_burned(
                                time_commitment=request.time_commitment,
                                gear=request.gear,
                                mission=request.mission,
                                day_number=day_number
                            )
                        }
                    elif "interval" in focus.lower() or "intensity" in focus.lower():
                        fallback_exercise = {
                            "day": day_number,
                            "name": f"Advanced {request.mission.value} Interval Training with {request.gear.value}",
                            "sets": 5,  # More sets than Phase 1
                            "reps": "40 seconds work, 20 seconds rest",  # More work, less rest
                            "description": f"Perform high-intensity intervals with minimal rest using {request.gear.value.lower()}. Choose challenging variations optimized for {request.mission.value.lower()} to increase heart rate and metabolic demand.",
                            "rest": "45 seconds between rounds",  # Less rest than Phase 1
                            "motivational_quote": Phase2Service.get_daily_quote(day_number, is_rest_day=False),
                            "is_workout_day": True,
                            "video_url": f"https://www.youtube.com/results?search_query=advanced+interval+training+{request.gear.value}+{request.mission.value}",
                            "calories_burned": Phase2Service.calculate_calories_burned(
                                time_commitment=request.time_commitment,
                                gear=request.gear,
                                mission=request.mission,
                                day_number=day_number
                            )
                        }
                    else:
                        fallback_exercise = {
                            "day": day_number,
                            "name": f"Advanced {request.mission.value} Circuit Training with {request.gear.value}",
                            "sets": 3,
                            "reps": "15-20 per exercise with minimal transition time",
                            "description": f"Choose 5-6 advanced exercises using {request.gear.value.lower()} that support your {request.mission.value.lower()} goal. Perform them in circuit style with complex movements and challenging progressions.",
                            "rest": "30 seconds between exercises",
                            "motivational_quote": Phase2Service.get_daily_quote(day_number, is_rest_day=False),
                            "is_workout_day": True,
                            "video_url": f"https://www.youtube.com/results?search_query=advanced+circuit+training+{request.gear.value}+{request.mission.value}",
                            "calories_burned": Phase2Service.calculate_calories_burned(
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
                    daily_rest_quote = Phase2Service.get_daily_quote(day_number, is_rest_day=True)
                    
                    return {
                        "day": day_number,
                        "motivational_quote": daily_rest_quote,
                        "is_workout_day": False,
                        "calories_burned": None
                    }
        
        # Process days in parallel batches to optimize API usage
        all_exercises = []
        
        try:
            # Log the workout days for debugging
            logger.info(f"Generating Phase 2 30-day plan with default workout days: Monday, Tuesday, Thursday, Friday")
            
            # Process in batches of BATCH_SIZE (6 by default)
            for batch_start in range(1, 31, Phase2Service.BATCH_SIZE):
                # Calculate the days in this batch
                batch_end = min(batch_start + Phase2Service.BATCH_SIZE, 31)
                batch_days = range(batch_start, batch_end)
                batch_size = len(batch_days)
                
                logger.info(f"Processing Phase 2 batch from day {batch_start} to {batch_end-1} ({batch_size} days)")
                
                # Create tasks for parallel processing of each day in the batch
                tasks = [generate_single_day_exercise(day) for day in batch_days]
                
                # Run tasks in parallel with timeout handling
                try:
                    batch_results = await asyncio.gather(*tasks)
                    logger.info(f"Successfully processed Phase 2 batch of {batch_size} days")
                except asyncio.TimeoutError:
                    logger.error(f"Timeout occurred while processing Phase 2 batch starting at day {batch_start}")
                    # Process days sequentially as fallback
                    batch_results = []
                    for day in batch_days:
                        result = await generate_single_day_exercise(day)
                        batch_results.append(result)
                
                # Add the batch results to the overall list
                all_exercises.extend(batch_results)
            
            # Process the results
            logger.info(f"Processing {len(all_exercises)} days of Phase 2 exercises")
            
            # Check for any missing days and fill them in
            day_numbers = [ex.get("day") for ex in all_exercises]
            for day in range(1, 31):
                if day not in day_numbers:
                    logger.warning(f"Day {day} missing from Phase 2 results, generating placeholder")
                    day_of_week = get_day_of_week(day)
                    is_workout = is_workout_day(day_of_week)
                    
                    if is_workout:
                        placeholder = {
                            "day": day,
                            "name": "Advanced Full-Body Circuit",
                            "sets": 4,  # More sets for Phase 2
                            "reps": "12 reps with 2-second pause at peak contraction",  # More challenging rep scheme
                            "description": "Select challenging exercises that target multiple muscle groups. Focus on controlled movement and time under tension.",
                            "rest": "45 seconds",  # Less rest for Phase 2
                            "motivational_quote": Phase2Service.get_daily_quote(day, is_rest_day=False),
                            "is_workout_day": True
                        }
                    else:
                        placeholder = {
                            "day": day,
                            "motivational_quote": Phase2Service.get_daily_quote(day, is_rest_day=True),
                            "is_workout_day": False
                        }
                    all_exercises.append(placeholder)
            
            # Convert the dictionaries to WorkoutExercise objects
            workout_exercises = [WorkoutExercise(**exercise) for exercise in all_exercises]
            
            # Sort exercises by day number to ensure proper order
            workout_exercises.sort(key=lambda x: x.day)
            
            # Add program statistics
            workout_count = sum(1 for ex in workout_exercises if getattr(ex, 'is_workout_day', False))
            rest_count = len(workout_exercises) - workout_count
            
            logger.info(f"Generated complete Phase 2 30-day plan with {workout_count} workout days and {rest_count} rest days")
            
            # Create and return the enhanced response
            return WorkoutPlanResponse(workout_plan=workout_exercises)
            
        except Exception as e:
            # Enhanced error handling
            error_message = f"Error generating complete Phase 2 workout plan: {str(e)}"
            logger.error(error_message)
            
            # Provide a more helpful error message with context
            detailed_error = (
                f"Failed to generate Phase 2 workout plan with mission '{request.mission}', "
                f"time commitment '{request.time_commitment}', and gear '{request.gear}'. "
                f"Error details: {str(e)}"
            )
            raise Exception(detailed_error)
