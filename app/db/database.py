from pymongo import MongoClient
from app.config import MONGO_URI, MONGO_DB
from app.utils.logger import get_logger

logger = get_logger("database")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    client.server_info()
    db = client[MONGO_DB]
    bookings_collection = db["bookings"]
    logger.info("MongoDB connected successfully")
except Exception as e:
    logger.warning(f"MongoDB not available: {e}. Persistence disabled.")
    client = None
    db = None
    bookings_collection = None
