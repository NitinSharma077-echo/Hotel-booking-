from typing import Dict
from app.agents.search_agent import SearchAgent
from app.agents.filter_agent import FilterAgent
from app.agents.ranking_agent import RankingAgent
from app.agents.decision_agent import DecisionAgent
from app.agents.retry_agent import RetryAgent
from app.agents.booking_agent import BookingAgent
from app.agents.payment_agent import PaymentAgent
from app.agents.memory_agent import MemoryAgent
from app.utils.helpers import generate_session_id
from app.utils.logger import get_logger

logger = get_logger("orchestrator")

class Orchestrator:
    def __init__(self):
        self.search = SearchAgent()
        self.filter = FilterAgent()
        self.ranker = RankingAgent()
        self.decision = DecisionAgent()
        self.retry = RetryAgent()
        self.booking = BookingAgent()
        self.payment = PaymentAgent()
        self.memory = MemoryAgent()

    def run(self, data: Dict, automate_browser: bool = False) -> Dict:
        session_id = data.get("session_id") or generate_session_id()
        data["session_id"] = session_id
        logger.info(f"Orchestrator: starting session {session_id}")

        # ── 1. Search ─────────────────────────────────────────────────────
        hotels = self.search.run(data)

        # ── 2. Filter ─────────────────────────────────────────────────────
        filtered = self.filter.run(hotels, data)

        # ── 3. Retry if empty ─────────────────────────────────────────────
        retry_message = None
        if not filtered:
            logger.info("Orchestrator: no hotels after filter — triggering retry")
            retry_result = self.retry.handle(
                data,
                hotels_fn=self.search.run,
                filter_fn=self.filter.run
            )
            if retry_result["status"] == "no_results":
                return {
                    "status": "no_results",
                    "message": retry_result["message"],
                    "session_id": session_id,
                    "hotel": None,
                    "options": None,
                    "screenshots": []
                }
            # Use relaxed results
            filtered = retry_result["hotels"]
            data = retry_result["updated_criteria"]
            retry_message = retry_result.get("message")

        # ── 4. Rank ───────────────────────────────────────────────────────
        ranked = self.ranker.run(filtered)

        # ── 5. Decide ─────────────────────────────────────────────────────
        auto_mode = data.get("auto_mode", True)
        decision = self.decision.run(ranked, auto_mode=auto_mode)

        if not auto_mode:
            # Return top 3 for user to choose
            return {
                "status": "options",
                "message": "Here are the top 3 hotels for you.",
                "options": decision,
                "hotel": None,
                "session_id": session_id,
                "screenshots": []
            }

        chosen = decision

        # ── 6. Prepare booking ────────────────────────────────────────────
        booking_payload = self.booking.prepare(chosen, data)

        # ── 7. Save to memory ─────────────────────────────────────────────
        self.memory.store_session(session_id, data)
        self.memory.store_booking(session_id, chosen, booking_payload)

        # ── 8. Browser automation (optional) ─────────────────────────────
        screenshots = []
        if automate_browser:
            browser_result = self.payment.run(
                booking_payload, session_id,
                payment=data.get("payment"),
                guest=data.get("guest"),
                auto_confirm=data.get("auto_confirm", False),
            )
            screenshots = browser_result.get("screenshots", [])

        logger.info(f"Orchestrator: completed session {session_id}")
        final_message = retry_message or chosen.get("llm_reason", f"Best match: {chosen['hotel_name']}")
        return {
            "status": "success",
            "message": final_message,
            "hotel": chosen,
            "booking": booking_payload,
            "options": None,
            "screenshots": screenshots,
            "session_id": session_id
        }
