# Multi-Agent Hotel Booking System

AI-powered hotel search, filtering, ranking, and booking automation using FastAPI + Playwright + Ollama.

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Start Ollama (optional — for LLM reasoning)
```bash
ollama run llama3
```

### 3. Start Redis (optional — for session memory)
```bash
# Windows: use Redis for Windows or WSL
redis-server
```

### 4. Run the server
```bash
python app.py
```
API docs: http://localhost:8000/docs

## API Usage

### Search & Book (auto mode)
```bash
curl -X POST http://localhost:8000/api/book \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Goa",
    "checkin": "2026-04-10",
    "checkout": "2026-04-15",
    "guests": 2,
    "budget": 5000,
    "min_rating": 4.0,
    "amenities": ["wifi", "pool"],
    "auto_mode": true
  }'
```

### With browser automation
```bash
curl -X POST "http://localhost:8000/api/book?automate=true" \
  -H "Content-Type: application/json" \
  -d '{"location": "Goa", "checkin": "2026-04-10", "checkout": "2026-04-15", "guests": 2, "budget": 5000, "min_rating": 4.0}'
```

### Save browser session (manual login)
```python
from app.services.browser_service import save_session
save_session("auth.json")
```

## Architecture

```
User Request
    ↓ FastAPI (booking_routes.py)
    ↓ Orchestrator
    ├── SearchAgent   → fetch hotels by location
    ├── FilterAgent   → budget + rating + amenities
    ├── RetryAgent    → relax constraints if no results
    ├── RankingAgent  → score = rating×0.6 + (1/price)×0.4
    ├── DecisionAgent → pick top 1 (auto) or top 3 (interactive)
    ├── BookingAgent  → prepare booking payload
    ├── PaymentAgent  → Playwright browser automation
    └── MemoryAgent   → Redis (session) + MongoDB (bookings)
```

## Agents

| Agent | Responsibility |
|-------|---------------|
| SearchAgent | Fetch hotels from API/mock data |
| FilterAgent | Strict budget/rating/amenities filter |
| RankingAgent | Weighted score (rating + price) |
| DecisionAgent | LLM-enhanced selection |
| RetryAgent | Adaptive budget/rating relaxation |
| BookingAgent | Prepare booking payload |
| PaymentAgent | Browser automation via Playwright |
| MemoryAgent | Redis + MongoDB persistence |

## Notes
- Booking.com has bot detection — use `auth.json` session file for safer automation
- Replace `hotel_api_service.py` mock data with a real API for production
- Set `HEADLESS=true` in `.env` for background automation
