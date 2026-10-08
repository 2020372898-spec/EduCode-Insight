"""HomePage: Streamlit page/controller."""
from ._legacy_app_impl import render_home


class HomePage:
    def render(self):
        """Render this part of the Streamlit application."""
        return render_home()


__all__ = ["HomePage"]
