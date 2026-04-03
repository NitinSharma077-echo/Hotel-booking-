from typing import List, Dict
from app.services.hotel_api_service import get_hotels
from app.utils.logger import get_logger

logger = get_logger("search_agent")

class SearchAgent:
    def run(self, data: Dict) -> List[Dict]:
        location = data.get("location", "")
        logger.info(f"SearchAgent: fetching hotels in '{location}'")
        hotels = get_hotels(
            location=location,
            checkin=data.get("checkin", ""),
            checkout=data.get("checkout", ""),
            guests=int(data.get("guests", 2)),
        )
        logger.info(f"SearchAgent: found {len(hotels)} hotels")
        return hotels
