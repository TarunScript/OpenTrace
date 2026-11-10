"""
OpenTrace OSINT Engine Exceptions
"""

class OSINTException(Exception):
    """Base exception for all OSINT engine errors."""
    pass


class SSRFViolationError(OSINTException):
    """Raised when a request target resolves to a forbidden private or local IP."""
    pass


class RateLimitExceededError(OSINTException):
    """Raised when target service returns HTTP 429 or rate-limit indicator."""
    pass


class CaptchaDetectedError(OSINTException):
    """Raised when target service presents a bot challenge or captcha."""
    pass


class AdapterExecutionError(OSINTException):
    """Raised when an adapter encounters an unrecoverable runtime error."""
    pass

