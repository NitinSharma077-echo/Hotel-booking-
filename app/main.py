from fastapi import FastAPI
from app.routes.booking_routes import router
import os

app = FastAPI(
    title="Multi-Agent Hotel Booking System",
    description="AI-powered hotel search, ranking, and booking automation",
    version="1.0.0"
)

app.include_router(router)
os.makedirs(os.path.join(os.path.dirname(__file__), "screenshots"), exist_ok=True)
