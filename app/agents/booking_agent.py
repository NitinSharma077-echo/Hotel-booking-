from typing import Dict
from app.utils.logger import get_logger

logger = get_logger("booking_agent")

class BookingAgent:
    def prepare(self, hotel: Dict, request_data: Dict) -> Dict:
        payload = {
            "hotel": hotel.get("hotel_name"),
            "hotel_link": hotel.get("link", ""),
            "location": request_data.get("location"),
            "checkin": request_data.get("checkin"),
            "checkout": request_data.get("checkout"),
            "guests": request_data.get("guests", 2),
            "price_per_night": hotel.get("price"),
            "rating": hotel.get("rating"),
            "user": {
                "session_id": request_data.get("session_id", ""),
            }
        }
        logger.info(f"BookingAgent: prepared payload for '{hotel.get('hotel_name')}'")
        return payload
