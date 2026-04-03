from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

class BookingRequest(BaseModel):
    location: str
    checkin: str  # YYYY-MM-DD
    checkout: str  # YYYY-MM-DD
    guests: int = 2
    budget: float
    min_rating: float = 3.5
    amenities: Optional[List[str]] = []
    session_id: Optional[str] = None
    auto_mode: bool = True  # True=pick top 1, False=return top 3

class Hotel(BaseModel):
    hotel_name: str
    price: float
    rating: float
    location: str
    amenities: List[str] = []
    link: str = ""
    score: float = 0.0

class BookingResponse(BaseModel):
    status: str
    message: str
    hotel: Optional[Hotel] = None
    options: Optional[List[Hotel]] = None
    screenshots: Optional[List[str]] = []
    session_id: str = ""
