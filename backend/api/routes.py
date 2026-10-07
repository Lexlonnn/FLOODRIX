"""Routes endpoint re-export."""
from api.v1.routes import plan_route, router

__all__ = ["router", "plan_route"]
