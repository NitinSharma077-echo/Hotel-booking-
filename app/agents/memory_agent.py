import json
from typing import Dict, Optional
from app.db.redis_client import r
from app.db.database import bookings_collection
from app.utils.logger import get_logger

logger = get_logger("memory_agent")

_local_store: Dict = {}  # fallback if Redis unavailable

class MemoryAgent:
    def store_session(self, session_id: str, data: Dict):
        serialized = json.dumps(data)
        if r:
            r.setex(session_id, 86400, serialized)  # TTL 24h
        _local_store[session_id] = data
        logger.info(f"MemoryAgent: stored session {session_id}")

    def get_session(self, session_id: str) -> Optional[Dict]:
        if r:
            raw = r.get(session_id)
            if raw:
                return json.loads(raw)
        return _local_store.get(session_id)

    def store_booking(self, session_id: str, hotel: Dict, booking_payload: Dict):
        record = {
            "session_id": session_id,
            "hotel": hotel,
            "booking": booking_payload,
        }
        if bookings_collection is not None:
            bookings_collection.insert_one(record)
            logger.info(f"MemoryAgent: booking saved to MongoDB for session {session_id}")
        else:
            logger.warning("MemoryAgent: MongoDB unavailable, booking not persisted")
