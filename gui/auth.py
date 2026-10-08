"""AuthenticationPage: Streamlit page/controller."""
from ._legacy_app_impl import render_authentication


class AuthenticationPage:
    def render(self):
        """Render this part of the Streamlit application."""
        return render_authentication()


__all__ = ["AuthenticationPage"]
