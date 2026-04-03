import uuid
from datetime import datetime

def generate_session_id() -> str:
    return str(uuid.uuid4())

def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")
