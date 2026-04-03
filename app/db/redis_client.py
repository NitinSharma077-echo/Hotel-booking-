import redis
from app.config import REDIS_HOST, REDIS_PORT
from app.utils.logger import get_logger

logger = get_logger("redis_client")

try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    r.ping()
    logger.info("Redis connected successfully")
except Exception as e:
    logger.warning(f"Redis not available: {e}. Memory will be in-process only.")
    r = None
