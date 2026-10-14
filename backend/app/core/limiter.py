from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

# In-memory rate limiter keyed by client remote IP (disabled during tests)
limiter = Limiter(
    key_func=get_remote_address,
    enabled=settings.ENVIRONMENT != "test",
)
