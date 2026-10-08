"""OverallDashboardPage: Streamlit page/controller."""
from ._legacy_app_impl import render_overall_dashboard


class OverallDashboardPage:
    def render(self):
        """Render this part of the Streamlit application."""
        return render_overall_dashboard()


__all__ = ["OverallDashboardPage"]
