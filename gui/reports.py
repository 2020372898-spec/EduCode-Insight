"""ReportsPage: Streamlit page/controller."""
from ._legacy_app_impl import render_reports


class ReportsPage:
    def render(self):
        """Render this part of the Streamlit application."""
        return render_reports()


__all__ = ["ReportsPage"]
