import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "hotel_agent")

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")

BOOKING_USERNAME = os.getenv("BOOKING_USERNAME", "")
BOOKING_PASSWORD = os.getenv("BOOKING_PASSWORD", "")

HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"

SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots")
