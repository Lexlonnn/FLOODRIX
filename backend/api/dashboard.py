"""Dashboard endpoint re-export."""
from api.v1.dashboard import DashboardSummaryResponse, get_dashboard_summary, router

__all__ = ["router", "get_dashboard_summary", "DashboardSummaryResponse"]
