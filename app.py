"""
Higher Education Enrollment Funnel Analytics Dashboard
State-of-the-art data product for enrollment analytics.

A production-grade interactive data visualization dashboard using Shiny for Python.
Features: Multi-page navigation, benchmarking, institution profiles, scenario simulation.

Author: Matheus Abrantes
Date: January 2026
"""

from shiny import App, reactive, render, ui
from shinywidgets import output_widget, render_widget
import pandas as pd
from pathlib import Path

from utils.data_loader import (
    load_ipeds_data, 
    get_unique_years, 
    get_unique_institutions,
    get_unique_regions,
    get_unique_sizes,
    get_states_by_region
)
from modules.filters import create_global_filters, filters_server
from modules.page_overview import overview_ui, overview_server
from modules.page_benchmarking import benchmarking_ui, benchmarking_server
from modules.page_institution_profile import profile_ui, profile_server
from modules.page_simulator import simulator_ui, simulator_server


# Load data at startup
print("Loading IPEDS enrollment data...")
DATA = load_ipeds_data()
YEARS = get_unique_years(DATA)
INSTITUTIONS = get_unique_institutions(DATA)
REGIONS = get_unique_regions(DATA)
SIZES = get_unique_sizes(DATA)
STATES_BY_REGION = get_states_by_region(DATA)
print(f"Loaded {len(DATA)} records for {len(INSTITUTIONS)} institutions across {len(YEARS)} years")


# Define UI with navbar and page routing
app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.link(rel="stylesheet", href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"),
        ui.tags.link(rel="stylesheet", href="www/styles.css"),
        ui.tags.script("""
            // Force Plotly charts to resize after page load
            document.addEventListener('DOMContentLoaded', function() {
                setTimeout(function() { resizePlotlyCharts(); }, 1000);
                window.addEventListener('resize', resizePlotlyCharts);
            });
            
            function resizePlotlyCharts() {
                var plots = document.querySelectorAll('.js-plotly-plot');
                plots.forEach(function(plot) {
                    if (plot && typeof Plotly !== 'undefined') {
                        Plotly.Plots.resize(plot);
                    }
                });
            }
            
            var observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.addedNodes.length) {
                        setTimeout(resizePlotlyCharts, 500);
                    }
                });
            });
            
            document.addEventListener('DOMContentLoaded', function() {
                observer.observe(document.body, { childList: true, subtree: true });
            });
        """),
    ),
    
    # App Container
    ui.div(
        # Navigation Bar
        ui.div(
            ui.div(
                # Brand
                ui.div(
                    ui.h1("Enrollment Analytics", class_="navbar-title"),
                    ui.p("IPEDS Data • 371 Institutions • 2022-2024", class_="navbar-subtitle"),
                    class_="navbar-brand"
                ),
                
                # Navigation Links
                ui.div(
                    ui.input_action_button("nav_overview", "Overview", class_="nav-link active"),
                    ui.input_action_button("nav_benchmarking", "Benchmarking", class_="nav-link"),
                    ui.input_action_button("nav_profile", "Institution Profile", class_="nav-link"),
                    ui.input_action_button("nav_simulator", "Simulator", class_="nav-link"),
                    class_="navbar-nav"
                ),
                
                class_="navbar-content"
            ),
            class_="navbar"
        ),
        
        # Global Filters
        create_global_filters(YEARS, INSTITUTIONS, REGIONS, STATES_BY_REGION, SIZES),
        
        # Main Content Area
        ui.div(
            ui.output_ui("page_content"),
            class_="main-wrapper"
        ),
        
        # Footer
        ui.div(
            ui.div(
                ui.p(
                    ui.strong("Higher Education Enrollment Funnel Analytics"),
                    " • Data Source: IPEDS (U.S. Department of Education) • ",
                    "Built by ",
                    ui.a("Matheus Abrantes", href="https://github.com/matheusabrantes", target="_blank", class_="footer-link"),
                    " • January 2026",
                    class_="footer-text"
                ),
                class_="footer-content"
            ),
            class_="footer"
        ),
        
        class_="app-container"
    ),
)


def server(input, output, session):
    """Server logic for the enrollment dashboard."""
    
    # =========================================================================
    # Navigation State
    # =========================================================================
    current_page = reactive.value("overview")
    
    @reactive.effect
    @reactive.event(input.nav_overview)
    def nav_to_overview():
        current_page.set("overview")
    
    @reactive.effect
    @reactive.event(input.nav_benchmarking)
    def nav_to_benchmarking():
        current_page.set("benchmarking")
    
    @reactive.effect
    @reactive.event(input.nav_profile)
    def nav_to_profile():
        current_page.set("profile")
    
    @reactive.effect
    @reactive.event(input.nav_simulator)
    def nav_to_simulator():
        current_page.set("simulator")
    
    # =========================================================================
    # Global Filter State
    # =========================================================================
    @reactive.calc
    def filtered_data() -> pd.DataFrame:
        """Reactive calculation for filtered dataset."""
        df = DATA.copy()
        
        # Apply year filter
        selected_years = input.year_filter()
        if selected_years:
            years = [int(y) for y in selected_years]
            df = df[df['year'].isin(years)]
        
        # Apply region/state filter
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
        
        # Apply size filter
        selected_sizes = input.size_filter()
        if selected_sizes:
            df = df[df['institution_size'].isin(selected_sizes)]
        
        # Apply institution filter
        selected_institution = input.institution_filter()
        if selected_institution and selected_institution != "":
            df = df[df['institution_name'] == selected_institution]
        
        return df
    
    @reactive.calc
    def full_data() -> pd.DataFrame:
        """Return full dataset for peer comparisons."""
        return DATA.copy()
    
    @reactive.calc
    def selected_years_list():
        """Get list of selected years as integers."""
        years_str = input.year_filter()
        if years_str:
            return [int(y) for y in years_str]
        return list(YEARS)
    
    @reactive.calc
    def selected_institution():
        """Get selected institution name or None."""
        inst = input.institution_filter()
        return inst if inst and inst != "" else None
    
    @reactive.calc
    def latest_year():
        """Get the latest selected year."""
        years = selected_years_list()
        return max(years) if years else None
    
    @reactive.effect
    @reactive.event(input.reset_filters)
    def reset_filters():
        """Reset all filters to default values."""
        ui.update_checkbox_group("year_filter", selected=[str(y) for y in YEARS])
        ui.update_selectize("region_state_filter", selected=[])
        ui.update_selectize("size_filter", selected=[])
        ui.update_selectize("institution_filter", selected="")
    
    # =========================================================================
    # Page Content Routing
    # =========================================================================
    @render.ui
    def page_content():
        """Render the current page based on navigation state."""
        page = current_page.get()
        
        if page == "overview":
            return overview_ui()
        elif page == "benchmarking":
            return benchmarking_ui()
        elif page == "profile":
            return profile_ui()
        elif page == "simulator":
            return simulator_ui()
        else:
            return overview_ui()
    
    # =========================================================================
    # Page-specific Server Logic
    # =========================================================================
    
    # Call page servers with shared reactive values
    overview_server(
        input, output, session,
        filtered_data=filtered_data,
        full_data=full_data,
        selected_years=selected_years_list,
        selected_institution=selected_institution,
        latest_year=latest_year
    )
    
    benchmarking_server(
        input, output, session,
        filtered_data=filtered_data,
        full_data=full_data,
        selected_years=selected_years_list,
        selected_institution=selected_institution,
        latest_year=latest_year,
        institutions_list=INSTITUTIONS
    )
    
    profile_server(
        input, output, session,
        filtered_data=filtered_data,
        full_data=full_data,
        selected_years=selected_years_list,
        selected_institution=selected_institution,
        latest_year=latest_year,
        institutions_list=INSTITUTIONS
    )
    
    simulator_server(
        input, output, session,
        filtered_data=filtered_data,
        full_data=full_data,
        selected_years=selected_years_list,
        selected_institution=selected_institution,
        latest_year=latest_year,
        institutions_list=INSTITUTIONS
    )


# Create app with static assets directory
app_dir = Path(__file__).parent
app = App(app_ui, server, static_assets=app_dir / "www")
