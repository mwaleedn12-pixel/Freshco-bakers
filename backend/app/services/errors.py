"""
Business-rule errors raised by services. main.py converts them into clean JSON
responses ({"detail": "..."}) with the right HTTP status code, so endpoints
don't need try/except blocks.
"""


class ServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
