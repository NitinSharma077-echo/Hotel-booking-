from fastapi import APIRouter, Query
from app.models.schemas import BookingRequest
from app.orchestrator.orchestrator import Orchestrator
from app.utils.logger import get_logger

logger = get_logger("booking_routes")
router = APIRouter(prefix="/api", tags=["Booking"])

@router.post("/book")
def book_hotel(request: BookingRequest, automate: bool = Query(False, description="Run browser automation")):
    logger.info(f"POST /book — location={request.location}, budget={request.budget}")
    data = request.model_dump()
    result = Orchestrator().run(data, automate_browser=automate)
    return result

@router.get("/health")
def health():
    return {"status": "ok"}
