from typing import List, Dict, Optional
from app.services.ollama_service import generate_response
from app.utils.logger import get_logger

logger = get_logger("decision_agent")

class DecisionAgent:
    def run(self, hotels: List[Dict], auto_mode: bool = True) -> Dict:
        if not hotels:
            return {}

        if auto_mode:
            # Rule-based: just take top scored
            chosen = hotels[0]
            logger.info(f"DecisionAgent (auto): selected '{chosen['hotel_name']}'")

            # Optionally enhance with LLM explanation
            prompt = (
                f"You selected this hotel for a user: {chosen}. "
                "In one sentence, explain why it's a great choice in a friendly tone."
            )
            explanation = generate_response(prompt)
            if explanation:
                chosen["llm_reason"] = explanation
            return chosen
        else:
            # Return top 3 for user to choose
            return hotels[:3]
