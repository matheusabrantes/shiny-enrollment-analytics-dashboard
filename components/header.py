"""Header component for the enrollment dashboard."""

from shiny import ui
from utils.styling import CARNEGIE_COLORS


def create_header():
    """Create the dashboard header with title and subtitle."""
    return ui.div(
        ui.div(
            ui.h1(
                "Higher Education Enrollment Funnel Analytics",
                class_="dashboard-title"
            ),
            ui.p(
                "371 U.S. Institutions | 2022-2024 | IPEDS Data",
                class_="dashboard-subtitle"
            ),
            class_="header-content"
        ),
        class_="dashboard-header"
    )
