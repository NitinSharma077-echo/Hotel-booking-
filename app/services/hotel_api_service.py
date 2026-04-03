"""
Hotel API Service  —  RapidAPI Booking.com  (REAL DATA, NO MOCK)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GET YOUR FREE KEY (2 minutes)
──────────────────────────────
1. Go to  https://rapidapi.com/tipsters/api/booking-com
2. Sign up free → Subscribe to  Basic (500 req/month FREE)
3. Copy your  X-RapidAPI-Key  from the dashboard
4. Open  .env  and set:  RAPIDAPI_KEY=your_key_here
5. Restart the app

Verified working endpoints (booking-com.p.rapidapi.com):
  GET /v1/hotels/locations  ?name={city}&locale=en-gb   → dest_id + dest_type
  GET /v1/hotels/search     ?dest_id=...                → hotel list
"""

import os
import requests
from datetime import date, timedelta
from typing import List, Dict, Tuple
from dotenv import load_dotenv
from app.utils.logger import get_logger

load_dotenv()

logger       = get_logger("hotel_api_service")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
API_HOST     = "booking-com.p.rapidapi.com"
BASE_URL     = f"https://{API_HOST}"
TIMEOUT      = 20

HEADERS = {
    "X-RapidAPI-Key":  RAPIDAPI_KEY,
    "X-RapidAPI-Host": API_HOST,
}

_NO_KEY_MSG = (
    "RAPIDAPI_KEY is not set in .env\n\n"
    "Steps:\n"
    "  1. Visit https://rapidapi.com/tipsters/api/booking-com\n"
    "  2. Sign up free → Subscribe to Basic plan\n"
    "  3. Copy X-RapidAPI-Key from dashboard\n"
    "  4. Open .env → add:  RAPIDAPI_KEY=your_key_here\n"
    "  5. Restart the app"
)


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def get_hotels(location: str, checkin: str = "", checkout: str = "",
               guests: int = 2) -> List[Dict]:
    """
    Fetch real hotels from Booking.com via RapidAPI.
    Raises RuntimeError if key is missing or the API call fails.
    """
    if not RAPIDAPI_KEY:
        raise RuntimeError(_NO_KEY_MSG)

    dest_id, dest_type = _resolve_destination(location)
    if not dest_id:
        raise RuntimeError(
            f"Could not find '{location}' on Booking.com. "
            "Check the spelling or try a nearby major city."
        )

    raw = _search_hotels(dest_id, dest_type, checkin, checkout, guests)
    nights = _nights(checkin, checkout)
    hotels = [_normalise(h, location, nights) for h in raw]
    logger.info(f"Booking.com: {len(hotels)} hotels for '{location}'")
    return hotels


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — RESOLVE DESTINATION  →  dest_id + dest_type
# ══════════════════════════════════════════════════════════════════════════════

def _resolve_destination(city: str) -> Tuple[str, str]:
    """
    GET /v1/hotels/locations?name={city}&locale=en-gb
    Returns (dest_id, dest_type).
    """
    resp = requests.get(
        f"{BASE_URL}/v1/hotels/locations",
        headers=HEADERS,
        params={"name": city, "locale": "en-gb"},
        timeout=TIMEOUT,
    )
    _check_response(resp, "destination lookup")

    results = resp.json()
    if not results:
        return "", ""

    # prefer exact city / region name match
    city_lower = city.lower()
    for item in results:
        label = (item.get("name") or item.get("label") or "").lower()
        if city_lower in label:
            return str(item["dest_id"]), item.get("dest_type", "region")

    # fallback: use first result
    first = results[0]
    return str(first["dest_id"]), first.get("dest_type", "region")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — SEARCH HOTELS
# ══════════════════════════════════════════════════════════════════════════════

def _search_hotels(dest_id: str, dest_type: str,
                   checkin: str, checkout: str, guests: int) -> List[Dict]:
    """
    GET /v1/hotels/search  →  raw hotel list (up to 20 per call).
    """
    today    = date.today()
    checkin  = checkin  or (today + timedelta(days=7)).isoformat()
    checkout = checkout or (today + timedelta(days=10)).isoformat()

    params = {
        "dest_id":            dest_id,
        "dest_type":          dest_type,
        "checkin_date":       checkin,
        "checkout_date":      checkout,
        "adults_number":      str(guests),
        "room_number":        "1",
        "order_by":           "popularity",
        "filter_by_currency": "INR",
        "locale":             "en-gb",
        "units":              "metric",
        "include_adjacency":  "true",
    }

    resp = requests.get(
        f"{BASE_URL}/v1/hotels/search",
        headers=HEADERS, params=params, timeout=TIMEOUT,
    )
    _check_response(resp, "hotel search")

    data = resp.json()
    if isinstance(data, dict):
        return data.get("result", data.get("hotels", []))
    if isinstance(data, list):
        return data
    return []


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — NORMALISE TO INTERNAL SCHEMA
# ══════════════════════════════════════════════════════════════════════════════

def _normalise(raw: Dict, location: str, nights: int) -> Dict:
    """
    Booking.com record  →  internal schema used by all agents.
    price  = per-night INR
    rating = 0-5  (API gives 0-10)
    """
    nights    = max(nights, 1)
    total     = float(raw.get("min_total_price") or 0)
    per_night = round(total / nights, 2) if total else 0

    review    = float(raw.get("review_score") or 0)
    rating    = round(review / 2, 1)          # 0-10 → 0-5

    amenities = ["wifi"]
    if raw.get("has_swimming_pool"):      amenities.append("pool")
    if raw.get("breakfast_included"):     amenities.append("breakfast")
    if raw.get("is_free_cancellable"):    amenities.append("free_cancellation")
    if raw.get("is_no_prepayment_block"): amenities.append("no_prepayment")

    link = raw.get("url") or raw.get("hotel_url") or ""
    if link and not link.startswith("http"):
        link = "https://www.booking.com" + link

    return {
        "hotel_name":   raw.get("hotel_name") or "Unknown Hotel",
        "price":        per_night,
        "rating":       rating,
        "location":     raw.get("city") or raw.get("city_name_en") or location,
        "amenities":    amenities,
        "link":         link,
        # extra fields displayed in UI
        "hotel_id":     raw.get("hotel_id"),
        "photo":        raw.get("main_photo_url", ""),
        "stars":        int(raw.get("class") or 0),
        "review_word":  raw.get("review_score_word", ""),
        "total_price":  total,
        "review_count": int(raw.get("review_nr") or 0),
    }


# ══════════════════════════════════════════════════════════════════════════════
# UTILITY
# ══════════════════════════════════════════════════════════════════════════════

def _check_response(resp: requests.Response, context: str):
    if resp.status_code == 403:
        raise RuntimeError(
            f"RapidAPI key rejected during {context}. "
            "Check your key at https://rapidapi.com/developer/dashboard"
        )
    if resp.status_code == 429:
        raise RuntimeError(
            f"RapidAPI rate limit hit during {context}. "
            "Free plan allows 500 requests/month. Upgrade or wait."
        )
    resp.raise_for_status()


def _nights(checkin: str, checkout: str) -> int:
    try:
        return max(1, (date.fromisoformat(checkout)
                       - date.fromisoformat(checkin)).days)
    except Exception:
        return 3


def api_status() -> Dict:
    """
    Health check — tests the key against the live API.
    Run:  python -c "from app.services.hotel_api_service import api_status; print(api_status())"
    """
    if not RAPIDAPI_KEY:
        return {"ok": False, "message": _NO_KEY_MSG}
    try:
        resp = requests.get(
            f"{BASE_URL}/v1/hotels/locations",
            headers=HEADERS,
            params={"name": "Goa", "locale": "en-gb"},
            timeout=10,
        )
        if resp.status_code == 200 and resp.json():
            return {"ok": True, "message": "Booking.com API is working correctly"}
        return {"ok": False, "code": resp.status_code, "message": resp.text[:300]}
    except Exception as exc:
        return {"ok": False, "message": str(exc)}
