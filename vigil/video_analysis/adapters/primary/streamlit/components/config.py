import os

API_BASE_URL: str = os.getenv("VIGIL_API_URL", "http://localhost:8000")
REQUEST_TIMEOUT: float = float(os.getenv("VIGIL_REQUEST_TIMEOUT", "10"))
