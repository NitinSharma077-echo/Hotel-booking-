from typing import List, Dict
from app.utils.logger import get_logger

logger = get_logger("filter_agent")

class FilterAgent:
    def run(self, hotels: List[Dict], criteria: Dict) -> List[Dict]:
        budget = criteria.get("budget", float("inf"))
        min_rating = criteria.get("min_rating", 0.0)
        required_amenities = [a.lower() for a in criteria.get("amenities", [])]

        filtered = []
        for h in hotels:
            if h["price"] > budget:
                continue
            if h["rating"] < min_rating:
                continue
            if required_amenities:
                hotel_amenities = [a.lower() for a in h.get("amenities", [])]
                if not all(a in hotel_amenities for a in required_amenities):
                    continue
            filtered.append(h)

        logger.info(
            f"FilterAgent: {len(filtered)}/{len(hotels)} hotels pass "
            f"(budget<={budget}, rating>={min_rating}, amenities={required_amenities})"
        )
        return filtered
