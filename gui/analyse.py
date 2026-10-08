"""AnalysePage: Streamlit page/controller."""
from ._legacy_app_impl import render_analyse


class AnalysePage:
    def render(self):
        """Render this part of the Streamlit application."""
        return render_analyse()


__all__ = ["AnalysePage"]
