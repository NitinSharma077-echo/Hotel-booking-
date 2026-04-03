from typing import Dict
from app.services.browser_service import run_booking_flow
from app.utils.logger import get_logger

logger = get_logger("payment_agent")

class PaymentAgent:
    def run(self, booking_payload: Dict, session_id: str,
            payment: Dict = None, guest: Dict = None,
            auto_confirm: bool = False) -> Dict:
        logger.info(f"PaymentAgent: starting browser automation for session {session_id} "
                    f"(auto_confirm={auto_confirm})")
        result = run_booking_flow(
            booking_data=booking_payload,
            session_id=session_id,
            hotel_link=booking_payload.get("hotel_link", ""),
            payment=payment,
            guest=guest,
            auto_confirm=auto_confirm,
        )
        return result
