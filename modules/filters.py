"""
Global filters module for the enrollment dashboard.
Manages filter state and provides reactive filter values.
"""

from shiny import ui, reactive, module


def create_global_filters(years: list, institutions: list, regions: list, 
                          states_by_region: dict, sizes: list):
    """Create the global filter bar UI."""
    
    # Build hierarchical region/state choices
    region_state_choices = {}
    for region in sorted(regions):
        region_state_choices[region] = f"🌎 {region}"
        if region in states_by_region:
            for state in states_by_region[region]:
                region_state_choices[f"state:{region}:{state}"] = f"    └ {state}"
    
    return ui.div(
        ui.div(
            # Years filter
            ui.div(
                ui.div("Years", class_="filter-label"),
                ui.input_checkbox_group(
                    "year_filter",
                    None,
                    choices={str(y): str(y) for y in years},
                    selected=[str(y) for y in years],
                    inline=True
                ),
                class_="filter-group filter-years"
            ),
            
            # Region/State filter
            ui.div(
                ui.div("Region / State", class_="filter-label"),
                ui.input_selectize(
                    "region_state_filter",
                    None,
                    choices=region_state_choices,
                    selected=[],
                    multiple=True,
                    options={"placeholder": "All regions..."}
                ),
                class_="filter-group",
                style="min-width: 180px;"
            ),
            
            # Size filter
            ui.div(
                ui.div("Institution Size", class_="filter-label"),
                ui.input_selectize(
                    "size_filter",
                    None,
                    choices={"Small": "Small", "Medium": "Medium", "Large": "Large"},
                    selected=[],
                    multiple=True,
                    options={"placeholder": "All sizes..."}
                ),
                class_="filter-group",
                style="min-width: 140px;"
            ),
            
            # Institution filter
            ui.div(
                ui.div("Institution", class_="filter-label"),
                ui.input_selectize(
                    "institution_filter",
                    None,
                    choices=[""] + institutions,
                    selected="",
                    multiple=False,
                    options={"placeholder": "Search institution..."}
                ),
                class_="filter-group filter-institution"
            ),
            
            # Reset button
            ui.div(
                ui.input_action_button(
                    "reset_filters",
                    "↻ Reset",
                    class_="btn-reset"
                ),
                class_="filter-group",
                style="align-self: flex-end;"
            ),
            
            class_="filter-row"
        ),
        class_="filter-panel"
    )


def filters_server(input, output, session, data, years):
    """Server logic for global filters. Returns reactive filtered data."""
    
    @reactive.calc
    def filtered_data():
        """Apply all filters to the dataset."""
        df = data.copy()
        
        # Year filter
        selected_years = input.year_filter()
        if selected_years:
            year_list = [int(y) for y in selected_years]
            df = df[df['year'].isin(year_list)]
        
        # Region/State filter
        selected_region_state = input.region_state_filter()
        if selected_region_state:
            selected_regions = []
            selected_states = []
            for item in selected_region_state:
                if item.startswith('state:'):
                    parts = item.split(':')
                    if len(parts) >= 3:
                        selected_states.append(parts[2])
                else:
                    selected_regions.append(item)
            
            if selected_regions or selected_states:
                mask = df['region'].isin(selected_regions) | df['state'].isin(selected_states)
                df = df[mask]
        
        # Size filter
        selected_sizes = input.size_filter()
        if selected_sizes:
            df = df[df['institution_size'].isin(selected_sizes)]
        
        # Institution filter
        selected_institution = input.institution_filter()
        if selected_institution and selected_institution != "":
            df = df[df['institution_name'] == selected_institution]
        
        return df
    
    @reactive.effect
    @reactive.event(input.reset_filters)
    def reset_filters():
        """Reset all filters to default values."""
        ui.update_checkbox_group("year_filter", selected=[str(y) for y in years])
        ui.update_selectize("region_state_filter", selected=[])
        ui.update_selectize("size_filter", selected=[])
        ui.update_selectize("institution_filter", selected="")
    
    @reactive.calc
    def selected_years():
        """Get list of selected years as integers."""
        years_str = input.year_filter()
        if years_str:
            return [int(y) for y in years_str]
        return []
    
    @reactive.calc
    def selected_institution():
        """Get selected institution name or None."""
        inst = input.institution_filter()
        return inst if inst and inst != "" else None
    
    @reactive.calc
    def latest_year():
        """Get the latest selected year."""
        years = selected_years()
        return max(years) if years else None
    
    return {
        'filtered_data': filtered_data,
        'selected_years': selected_years,
        'selected_institution': selected_institution,
        'latest_year': latest_year,
    }
