from typing import Optional

class HTTPException(Exception):
    def __init__(self, status_code: int, message: Optional[str] = None):
        self.status_code = status_code
        self.message = message or f"HTTP {status_code}"
        super().__init__(self.message)

class InvalidTemplateException(Exception):
    def __init__(self, message: str):
        super().__init__(message)