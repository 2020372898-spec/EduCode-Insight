"""Object-oriented Streamlit application controller."""
import streamlit as st
from .auth import AuthenticationPage
from .navigation import Navigation
from .home import HomePage
from .analyse import AnalysePage
from .dashboard import DashboardPage
from .reports import ReportsPage


class EduCodeInsightApp:
    """Compose and route GUI pages.

    Streamlit rendering remains view-oriented, while this controller owns navigation
    and page composition. Page objects can be replaced independently in tests.
    """
    def __init__(self, auth_page=None, navigation=None, pages=None):
        self.auth_page = auth_page or AuthenticationPage()
        self.navigation = navigation or Navigation()
        self.pages = pages or {
            "Home": HomePage(),
            "Analyse": AnalysePage(),
            "Dashboard": DashboardPage(),
            "Reports": ReportsPage(),
        }

    def run(self):
        if not st.session_state.get("authenticated", False):
            return self.auth_page.render()
        self.navigation.render()
        page_name = st.session_state.get("page", "Home")
        page = self.pages.get(page_name)
        if page is None:
            st.session_state["page"] = "Home"
            page = self.pages["Home"]
        return page.render()


def main():
    return EduCodeInsightApp().run()


if __name__ == "__main__":
    main()
