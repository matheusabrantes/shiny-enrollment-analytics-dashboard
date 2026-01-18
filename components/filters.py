"""Filter panel component for the enrollment dashboard."""

from shiny import ui


def create_filters(years: list, institutions: list):
    """Create the filter panel with year and institution filters."""
    return ui.div(
        ui.div(
            ui.div(
                ui.input_checkbox_group(
                    "year_filter",
                    "Select Years",
                    choices={str(y): f"Fall {y}" for y in years},
                    selected=[str(y) for y in years],
                    inline=True
                ),
                class_="filter-item"
            ),
            ui.div(
                ui.input_selectize(
                    "institution_filter",
                    "Filter Institutions",
                    choices=["All Institutions"] + institutions,
                    selected="All Institutions",
                    multiple=True,
                    options={"placeholder": "Select institutions..."}
                ),
                class_="filter-item filter-institution"
            ),
            ui.div(
                ui.input_action_button(
                    "reset_filters",
                    "Reset Filters",
                    class_="btn-reset"
                ),
                class_="filter-item"
            ),
            class_="filter-row"
        ),
        class_="filter-panel"
    )
