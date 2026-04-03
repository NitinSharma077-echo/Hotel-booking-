import requests
from app.config import OLLAMA_URL, OLLAMA_MODEL
from app.utils.logger import get_logger

logger = get_logger("ollama_service")

def generate_response(prompt: str, model: str = None) -> str:
    """Call local Ollama LLM and return the text response."""
    model = model or OLLAMA_MODEL
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=60
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except requests.exceptions.ConnectionError:
        logger.warning("Ollama not running. Falling back to rule-based logic.")
        return ""
    except Exception as e:
        logger.error(f"Ollama error: {e}")
        return ""
