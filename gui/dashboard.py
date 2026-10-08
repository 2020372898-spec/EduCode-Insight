"""Dashboard coordinator for assignment and overall analysis."""

from ._legacy_app_impl import (
    list_stored_assignments,
    render_overall_dashboard,
    st,
)
from .dashboard_assignment import (
    AssignmentDashboardPage,
    render_assignment_dashboard,
)
from .dashboard_overall import OverallDashboardPage


def render_dashboard():
    """Render dashboard navigation without the Question Analysis tab."""
    st.header("Dashboard")

    assignment_view, overall_view = st.tabs(
        [
            "Assignment Analysis",
            "Overall Analysis",
        ]
    )

    with assignment_view:
        assignments = list_stored_assignments()

        if not assignments:
            st.info("No processed assignments are available yet.")
        else:
            label_to_slug = {
                name: slug
                for name, slug in assignments
            }

            selected_assignment = st.selectbox(
                "Assignment",
                list(label_to_slug.keys()),
            )

            render_assignment_dashboard(
                selected_assignment,
                label_to_slug[selected_assignment],
            )

    with overall_view:
        render_overall_dashboard()


class DashboardPage:
    """Owns rendering for the dashboard page."""

    def render(self):
        return render_dashboard()


__all__ = [
    "DashboardPage",
    "AssignmentDashboardPage",
    "OverallDashboardPage",
    "render_dashboard",
]
