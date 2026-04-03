from typing import List, Dict
from app.utils.logger import get_logger

logger = get_logger("ranking_agent")

class RankingAgent:
    RATING_WEIGHT = 0.6
    PRICE_WEIGHT = 0.4

    def run(self, hotels: List[Dict]) -> List[Dict]:
        if not hotels:
            return []

        max_price = max(h["price"] for h in hotels) or 1
        scored = []
        for h in hotels:
            normalized_price = 1 - (h["price"] / max_price)  # lower price → higher score
            score = (h["rating"] / 5) * self.RATING_WEIGHT + normalized_price * self.PRICE_WEIGHT
            h = {**h, "score": round(score, 4)}
            scored.append(h)

        ranked = sorted(scored, key=lambda x: x["score"], reverse=True)
        logger.info(f"RankingAgent: ranked {len(ranked)} hotels. Top: {ranked[0]['hotel_name']} (score={ranked[0]['score']})")
        return ranked
