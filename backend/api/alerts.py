"""Alerts endpoint re-export."""
from api.v1.alerts import get_active_alerts, router

__all__ = ["router", "get_active_alerts"]
