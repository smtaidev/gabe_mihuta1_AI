import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenAI API configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-1106-preview")

# Tavily API configuration
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "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")

# API settings
API_PORT = 8031

# Program settings
PROGRAM_DURATION_DAYS = 30
OPENAI_CALLS_PER_DAY = 6
TOTAL_ITERATIONS = 5