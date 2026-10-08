"""Navigation: Streamlit page/controller."""
from ._legacy_app_impl import render_navigation


class Navigation:
    def render(self):
        """Render this part of the Streamlit application."""
        return render_navigation()


__all__ = ["Navigation"]
