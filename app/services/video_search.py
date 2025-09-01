import logging
from typing import Optional
from tavily import TavilyClient
from app.core.config import TAVILY_API_KEY

# Set up logging
logger = logging.getLogger(__name__)

class VideoSearchService:
    """Service for finding YouTube workout videos using Tavily API"""
    
    def __init__(self):
        """Initialize the Tavily client"""
        try:
            self.client = TavilyClient(api_key=TAVILY_API_KEY)
            logger.info("Tavily client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Tavily client: {e}")
            self.client = None
    
    async def find_workout_video(self, exercise_name: str, gear: str, mission: str) -> Optional[str]:
        """
        Find a relevant YouTube workout video for the given exercise
        
        Args:
            exercise_name: Name of the exercise/workout
            gear: Available equipment (Bodyweight, Dumbbells, etc.)
            mission: Fitness goal (Lose Fat, Build Strength, etc.)
            
        Returns:
            YouTube video URL or None if not found
        """
        if not self.client:
            logger.warning("Tavily client not available, cannot search for videos")
            return None
            
        try:
            # Create a comprehensive search query that emphasizes mission and gear
            search_query = f"{exercise_name} {gear} {mission} workout YouTube"
            logger.info(f"Searching for video with query: {search_query}")
            
            # Search for videos using Tavily
            response = self.client.search(
                query=search_query,
                search_depth="basic",
                include_domains=["youtube.com", "youtu.be"],
                max_results=5
            )
            
            # Extract YouTube URLs from results
            if response and "results" in response:
                for result in response["results"]:
                    url = result.get("url", "")
                    if "youtube.com" in url or "youtu.be" in url:
                        logger.info(f"Found YouTube video: {url}")
                        return url
            
            logger.warning(f"No YouTube videos found for: {exercise_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error searching for workout video: {e}")
            return None
    
    async def find_generic_workout_video(self, mission: str, gear: str, time_commitment: str) -> Optional[str]:
        """
        Find a generic workout video when specific exercise video is not found
        
        Args:
            mission: Fitness goal
            gear: Available equipment
            time_commitment: Time available for workout
            
        Returns:
            YouTube video URL or None if not found
        """
        if not self.client:
            return None
            
        try:
            # Create a generic search query that prioritizes mission and gear
            search_query = f"{mission} with {gear} {time_commitment} workout routine YouTube"
            logger.info(f"Searching for generic video with query: {search_query}")
            
            response = self.client.search(
                query=search_query,
                search_depth="basic",
                include_domains=["youtube.com", "youtu.be"],
                max_results=3
            )
            
            if response and "results" in response:
                for result in response["results"]:
                    url = result.get("url", "")
                    if "youtube.com" in url or "youtu.be" in url:
                        logger.info(f"Found generic YouTube video: {url}")
                        return url
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching for generic workout video: {e}")
            return None

# Global instance
video_search_service = VideoSearchService()
