"""Road closures endpoint re-export."""
from api.v1.closures import get_active_closures, router

__all__ = ["router", "get_active_closures"]
