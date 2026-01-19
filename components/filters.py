"""Filter panel component for the enrollment dashboard."""

from shiny import ui


def create_filters(years: list, institutions: list, regions: list, 
                   states_by_region: dict, sizes: list):
    """Create the filter panel with year, institution, region/state, and size filters."""
    
    # Build hierarchical region/state choices
    # Format: {"Region: South": "South", "  AL (South)": "state:AL", ...}
    region_state_choices = {}
    for region in sorted(regions):
        # Add region as a choice
        region_state_choices[region] = f"🌎 {region}"
        # Add states under each region
        if region in states_by_region:
            for state in states_by_region[region]:
                region_state_choices[f"state:{region}:{state}"] = f"    └ {state}"
    
    return ui.div(
        ui.div(
            # Row 1: Year filter
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
            class_="filter-row"
        ),
        ui.div(
            # Row 2: Region/State, Size, and Institution filters
            ui.div(
                ui.input_selectize(
                    "region_state_filter",
                    "Region / State",
                    choices=region_state_choices,
                    selected=[],
                    multiple=True,
                    options={"placeholder": "All regions and states..."}
                ),
                class_="filter-item",
                style="min-width: 200px;"
            ),
            ui.div(
                ui.input_selectize(
                    "size_filter",
                    "Institution Size",
                    choices={"Small": "Small", "Medium": "Medium", "Large": "Large"},
                    selected=[],
                    multiple=True,
                    options={"placeholder": "All sizes..."}
                ),
                class_="filter-item",
                style="min-width: 150px;"
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
