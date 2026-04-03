from typing import Dict, List
from app.services.ollama_service import generate_response
from app.utils.logger import get_logger

logger = get_logger("retry_agent")

BUDGET_INCREMENT = 2000
RATING_DECREMENT = 0.5
MIN_RATING_FLOOR = 2.0

class RetryAgent:
    def handle(self, data: Dict, hotels_fn, filter_fn) -> Dict:
        """
        Adaptive retry:
        1. Increase budget by BUDGET_INCREMENT
        2. If still empty, reduce min_rating
        3. If still empty, ask user
        Returns dict with {status, message, data (updated criteria)}
        """
        original_budget = data.get("budget", 0)
        original_rating = data.get("min_rating", 3.5)

        # Attempt 1: increase budget
        data_try1 = {**data, "budget": original_budget + BUDGET_INCREMENT}
        hotels = hotels_fn(data_try1)
        filtered = filter_fn(hotels, data_try1)
        if filtered:
            msg = self._message(data, data_try1, "budget")
            logger.info(f"RetryAgent: found hotels after budget increase to {data_try1['budget']}")
            return {"status": "retry_success", "message": msg, "updated_criteria": data_try1, "hotels": filtered}

        # Attempt 2: reduce rating
        new_rating = max(MIN_RATING_FLOOR, original_rating - RATING_DECREMENT)
        data_try2 = {**data_try1, "min_rating": new_rating}
        hotels = hotels_fn(data_try2)
        filtered = filter_fn(hotels, data_try2)
        if filtered:
            msg = self._message(data, data_try2, "both")
            logger.info(f"RetryAgent: found hotels after relaxing rating to {new_rating}")
            return {"status": "retry_success", "message": msg, "updated_criteria": data_try2, "hotels": filtered}

        # Attempt 3: ask user
        prompt = (
            f"A user searched hotels in {data.get('location')} "
            f"with budget ₹{original_budget} and rating ≥ {original_rating}. "
            "No hotels found even after relaxing constraints. "
            "Suggest alternatives in a friendly, helpful tone."
        )
        suggestion = generate_response(prompt) or (
            f"No hotels found in {data.get('location')} even with relaxed budget and rating. "
            "Please try a different location or very flexible criteria."
        )
        logger.info("RetryAgent: all retries exhausted, asking user")
        return {"status": "no_results", "message": suggestion}

    def _message(self, original: Dict, updated: Dict, changed: str) -> str:
        if changed == "budget":
            return (
                f"No hotels found under ₹{original['budget']} with ⭐{original['min_rating']}. "
                f"I found options under ₹{updated['budget']}. Want to proceed?"
            )
        return (
            f"No hotels under ₹{original['budget']} with ⭐{original['min_rating']}. "
            f"Found options under ₹{updated['budget']} with ⭐{updated['min_rating']}. Proceed?"
        )
