"""
Browser Automation — runs via subprocess
─────────────────────────────────────────
Problem:
  Playwright cannot launch inside Streamlit's event loop on Windows.
  Neither sync_playwright (ProactorEventLoop conflict) nor
  async_playwright + WindowsSelectorEventLoopPolicy (SelectorEventLoop
  has no subprocess transport on Windows) work from a thread.

Solution:
  Spawn browser_worker.py as a completely separate Python process.
  It runs its own interpreter + ProactorEventLoop with full subprocess
  support. Communication happens via temp JSON files.

Result:
  - Chrome opens visibly (headless=False, slow_mo=70ms)
  - User sees every action live in the browser window
  - Screenshots are saved and paths returned to Streamlit
"""
import os, sys, json, subprocess, tempfile
from typing import Dict
from app.config import HEADLESS, SCREENSHOTS_DIR
from app.utils.logger import get_logger

logger = get_logger("browser_service")

_WORKER   = os.path.join(os.path.dirname(__file__), "browser_worker.py")
AUTH_FILE = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "auth.json"))
PROFILE_FILE = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "user_profile.json"))
SLOW_MO_MS = 700   # ms per action — slows browser so user can watch live


def _load_profile() -> Dict:
    """Load full user profile (credentials + payment + guest info)."""
    try:
        if os.path.exists(PROFILE_FILE):
            with open(PROFILE_FILE, encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Could not read profile: {e}")
    return {}


def run_booking_flow(booking_data: Dict, session_id: str,
                     hotel_link: str = "",
                     payment: Dict = None,
                     guest: Dict = None,
                     auto_confirm: bool = False) -> Dict:
    """
    Launch browser_worker.py in a fresh Python process.
    Passes all data via a temp JSON file, reads results from another.
    Browser opens visibly and the user can watch every step live.
    """
    profile = _load_profile()
    creds = {
        "email":    profile.get("booking_email", profile.get("email", "")),
        "password": profile.get("booking_password", ""),
    }

    # Build guest dict from profile if not supplied by caller
    if guest is None:
        name_parts = profile.get("full_name", "").split(None, 1)
        guest = {
            "first_name": name_parts[0] if name_parts else "",
            "last_name":  name_parts[1] if len(name_parts) > 1 else "",
            "email":      profile.get("email", ""),
            "phone":      profile.get("phone", ""),
        }

    # Build payment dict from profile if not supplied by caller
    if payment is None:
        payment = {
            "card_number":    profile.get("card_number", ""),
            "expiry_month":   profile.get("expiry_month", ""),
            "expiry_year":    profile.get("expiry_year", ""),
            "cvv":            profile.get("cvv", ""),
            "name_on_card":   profile.get("name_on_card", ""),
        }

    # ── write input for the worker ────────────────────────────────────────
    worker_input = {
        "booking_data":    booking_data,
        "session_id":      session_id,
        "hotel_link":      hotel_link,
        "headless":        HEADLESS,
        "slow_mo":         SLOW_MO_MS,
        "auth_file":       AUTH_FILE,
        "screenshots_dir": SCREENSHOTS_DIR,
        "creds":           creds,
        "guest":           guest,
        "payment":         payment,
        "auto_confirm":    auto_confirm,
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json",
                                     delete=False, encoding="utf-8") as fin:
        json.dump(worker_input, fin)
        data_path = fin.name

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json",
                                      delete=False, encoding="utf-8") as fout:
        fout.write("{}")
        result_path = fout.name

    try:
        logger.info(f"Launching browser_worker.py as subprocess (PID will be logged)")

        proc = subprocess.run(
            [sys.executable, _WORKER, data_path, result_path],
            timeout=300,          # 5 min max
            capture_output=False, # let stdout/stderr show in Streamlit terminal
        )

        if proc.returncode != 0:
            logger.warning(f"browser_worker exited with code {proc.returncode}")

        with open(result_path, encoding="utf-8") as f:
            result = json.load(f)

        logger.info(
            f"Browser automation done — "
            f"status={result.get('status')}, "
            f"screenshots={len(result.get('screenshots', []))}"
        )
        return result

    except subprocess.TimeoutExpired:
        logger.error("browser_worker timed out after 5 minutes")
        return {"status": "error",
                "message": "Browser automation timed out.",
                "screenshots": []}
    except Exception as exc:
        logger.error(f"browser_worker launch failed: {exc}")
        return {"status": "error", "message": str(exc), "screenshots": []}
    finally:
        for p in (data_path, result_path):
            try: os.unlink(p)
            except Exception: pass
