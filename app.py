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
        ui.tags.style("""
            :root {
                --primary: #002633;
                --secondary: #FF6B35;
                --neutral-light: #F5F5F5;
                --neutral-dark: #333333;
                --white: #FFFFFF;
            }
            
            body {
                font-family: 'Inter', Arial, sans-serif;
                background-color: var(--neutral-light);
                color: var(--neutral-dark);
                margin: 0;
                padding: 0;
            }
            
            .app-container {
                max-width: 1400px;
                margin: 0 auto;
                padding: 0;
            }
            
            /* Navigation Bar */
            .navbar {
                background: linear-gradient(135deg, var(--primary) 0%, #2A4A7A 100%);
                color: var(--white);
                padding: 16px 32px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            }
            
            .navbar-content {
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 16px;
            }
            
            .navbar-brand {
                display: flex;
                flex-direction: column;
            }
            
            .navbar-title {
                font-size: 24px;
                font-weight: 700;
                margin: 0;
                color: var(--white);
            }
            
            .navbar-subtitle {
                font-size: 12px;
                opacity: 0.9;
                margin: 4px 0 0 0;
                color: var(--white);  /* Fix: Ensure subtitle is white */
            }
            
            .navbar-nav {
                display: flex;
                gap: 8px;
            }
            
            .nav-link,
            .navbar-nav .btn.nav-link,
            .navbar-nav button.nav-link {
                background: transparent !important;
                border: 1px solid rgba(255,255,255,0.3) !important;
                color: rgba(255,255,255,0.7) !important;  /* Non-selected: light gray */
                padding: 8px 16px !important;
                border-radius: 6px !important;
                font-size: 13px !important;
                cursor: pointer;
                transition: all 0.2s;
            }
            
            .nav-link:hover,
            .navbar-nav .btn.nav-link:hover,
            .navbar-nav button.nav-link:hover {
                background: rgba(255,255,255,0.1) !important;
                color: #FFFFFF !important;
            }
            
            .nav-link.active,
            .navbar-nav .btn.nav-link.active,
            .navbar-nav button.nav-link.active {
                background: rgba(255,255,255,0.25) !important;
                border-color: #FFFFFF !important;
                color: #FFFFFF !important;  /* Active: white text */
                font-weight: 600 !important;
            }
            
            /* Filter Panel */
            .filter-panel {
                background: var(--white);
                padding: 16px 32px;
                border-bottom: 1px solid #E0E0E0;
                position: sticky;
                top: 0;
                z-index: 100;
            }
            
            .filter-row {
                display: flex;
                flex-wrap: wrap;
                align-items: flex-end;
                gap: 16px;
            }
            
            .filter-group {
                display: flex;
                flex-direction: column;
            }
            
            .filter-label {
                font-size: 11px;
                font-weight: 600;
                color: var(--primary);
                margin-bottom: 4px;
                text-transform: uppercase;
                letter-spacing: 0.3px;
            }
            
            .btn-reset {
                background: var(--neutral-light);
                border: 1px solid #DDD;
                color: var(--neutral-dark);
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
                cursor: pointer;
                transition: all 0.2s;
                height: 38px;  /* Match height of select inputs */
                display: inline-flex;
                align-items: center;
                justify-content: center;
            }
            
            .btn-reset:hover {
                background: var(--primary);
                color: var(--white);
                border-color: var(--primary);
            }
            
            /* Main Content */
            .main-wrapper {
                padding: 24px 32px;
            }
            
            .page-content {
                max-width: 100%;
            }
            
            /* Section Headers */
            .section-header {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 24px;
            }
            
            .section-title {
                font-size: 20px;
                font-weight: 600;
                color: var(--primary);
                margin: 0 0 4px 0;
            }
            
            .section-subtitle {
                font-size: 13px;
                color: #666;
                margin: 0;
            }
            
            /* KPI Grid */
            .kpi-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                gap: 16px;
                margin-bottom: 24px;
            }
            
            .kpi-card {
                background: var(--white);
                border-radius: 8px;
                padding: 20px;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.08);
                border-top: 4px solid var(--primary);
                transition: transform 0.2s, box-shadow 0.2s;
            }
            
            .kpi-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.12);
            }
            
            .kpi-card.applicants { border-top-color: var(--primary); }
            .kpi-card.admitted { border-top-color: #4A90E2; }
            .kpi-card.enrolled { border-top-color: #50C878; }
            .kpi-card.yield { border-top-color: var(--secondary); }
            .kpi-card.admit { border-top-color: #9B59B6; }
            
            .kpi-label {
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                color: #666;
                margin-bottom: 8px;
                font-weight: 600;
            }
            
            .kpi-value {
                font-size: 28px;
                font-weight: 700;
                color: var(--primary);
                line-height: 1.2;
            }
            
            .kpi-subtext {
                font-size: 11px;
                color: #888;
                margin-top: 4px;
            }
            
            .kpi-delta {
                font-size: 12px;
                font-weight: 600;
                margin-top: 4px;
            }
            
            .kpi-delta.positive { color: #10B981; }
            .kpi-delta.negative { color: #EF4444; }
            .kpi-delta.neutral { color: #64748B; }
            
            /* Cards and Chart Sections */
            .card {
                background: var(--white);
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.08);
                margin-bottom: 24px;
                overflow: hidden;
            }
            
            .card-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 16px 20px;
                border-bottom: 1px solid #E0E0E0;
                flex-wrap: nowrap;
                gap: 16px;
            }
            
            /* Ensure chart controls align horizontally with title on same line */
            .card-header .chart-controls {
                display: inline-flex;
                align-items: center;
                gap: 4px;
                flex-shrink: 0;
            }
            
            .card-header .chart-controls .shiny-input-radiogroup {
                display: inline-flex !important;
                align-items: center;
                margin: 0 !important;
            }
            
            .card-header .chart-controls .shiny-options-group {
                display: inline-flex !important;
                flex-direction: row !important;
                align-items: center;
                gap: 12px;
                flex-wrap: nowrap;
            }
            
            .card-header .chart-controls .shiny-options-group label {
                margin: 0 !important;
                white-space: nowrap;
            }
            
            .card-title {
                font-size: 14px;
                font-weight: 600;
                color: var(--primary);
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin: 0;
            }
            
            .card-body {
                padding: 20px;
            }
            
            .chart-section {
                background: var(--white);
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.08);
                margin-bottom: 24px;
            }
            
            .chart-row {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
                gap: 24px;
                margin-bottom: 24px;
            }
            
            .chart-controls {
                display: flex;
                gap: 8px;
            }
            
            .chart-controls .shiny-input-radiogroup label {
                font-size: 12px;
            }
            
            /* Rankings Grid */
            .rankings-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 16px;
            }
            
            .ranking-card {
                background: var(--neutral-light);
                border-radius: 6px;
                padding: 12px;
                text-align: center;
            }
            
            .ranking-metric {
                font-size: 11px;
                text-transform: uppercase;
                color: #666;
                margin-bottom: 4px;
            }
            
            .ranking-value {
                font-size: 24px;
                font-weight: 700;
                color: var(--primary);
            }
            
            .ranking-percentile {
                font-size: 11px;
                color: #888;
            }
            
            /* Data Table */
            .data-table-container {
                overflow-x: auto;
            }
            
            .data-table {
                width: 100%;
                border-collapse: collapse;
                font-size: 13px;
            }
            
            .data-table th {
                background: var(--neutral-light);
                padding: 12px 16px;
                text-align: left;
                font-weight: 600;
                color: var(--primary);
                border-bottom: 2px solid #E0E0E0;
            }
            
            .data-table td {
                padding: 10px 16px;
                border-bottom: 1px solid #E0E0E0;
            }
            
            .data-table tr:hover {
                background: #F8F9FA;
            }
            
            .data-table tr.highlighted {
                background: #FFF3E0;
            }
            
            /* Buttons */
            .btn {
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s;
                border: none;
            }
            
            .btn-primary {
                background: var(--primary);
                color: var(--white);
            }
            
            .btn-secondary {
                background: var(--neutral-light);
                color: var(--neutral-dark);
                border: 1px solid #DDD;
            }
            
            .btn-sm {
                padding: 6px 12px;
                font-size: 12px;
            }
            
            /* Badges */
            .badge {
                display: inline-block;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
            }
            
            .badge-success { background: #D1FAE5; color: #065F46; }
            .badge-warning { background: #FEF3C7; color: #92400E; }
            .badge-danger { background: #FEE2E2; color: #991B1B; }
            .badge-info { background: #DBEAFE; color: #1E40AF; }
            
            /* Footer */
            .footer {
                text-align: center;
                padding: 24px;
                color: #666;
                font-size: 12px;
                border-top: 1px solid #E0E0E0;
                margin-top: 24px;
                background: var(--white);
            }
            
            .footer-link {
                color: var(--primary);
                text-decoration: none;
            }
            
            .footer-text {
                margin: 0;
            }
            
            /* Insights Panel */
            .insights-panel {
                background: #FFF7ED;
                border: 1px solid #FDBA74;
                border-radius: 8px;
                padding: 12px 16px;
            }
            
            .insight-item {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 4px 0;
                font-size: 13px;
            }
            
            /* Hero Section (for Institution Profile) */
            .hero-section {
                background: linear-gradient(135deg, var(--primary) 0%, #2A4A7A 100%);
                color: var(--white);
                padding: 32px;
                border-radius: 8px;
                margin-bottom: 24px;
            }
            
            .hero-title {
                font-size: 28px;
                font-weight: 700;
                margin: 0 0 8px 0;
            }
            
            .hero-subtitle {
                font-size: 14px;
                opacity: 0.9;
                margin: 0 0 16px 0;
            }
            
            .hero-actions {
                display: flex;
                gap: 12px;
            }
            
            .hero-btn {
                background: rgba(255,255,255,0.2);
                border: 1px solid rgba(255,255,255,0.4);
                color: var(--white);
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
                cursor: pointer;
            }
            
            /* Tabs */
            .tabs-container {
                margin-bottom: 24px;
            }
            
            .tabs-nav {
                background: var(--white);
                padding: 12px 20px;
                border-radius: 8px 8px 0 0;
                border-bottom: 1px solid #E0E0E0;
            }
            
            /* Slider Groups (for Simulator) */
            .slider-group {
                margin-bottom: 20px;
            }
            
            .slider-label {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;
            }
            
            .slider-name {
                font-size: 13px;
                font-weight: 500;
            }
            
            /* Responsive */
            @media (max-width: 768px) {
                .navbar-content {
                    flex-direction: column;
                    align-items: flex-start;
                }
                
                .chart-row {
                    grid-template-columns: 1fr;
                }
                
                .kpi-grid {
                    grid-template-columns: repeat(2, 1fr);
                }
            }
            
            /* Shiny overrides */
            .shiny-input-checkboxgroup label.checkbox-inline {
                margin-right: 12px;
            }
            
            /* Filter row alignment fix */
            .filter-row {
                display: flex;
                flex-wrap: wrap;
                align-items: flex-end;
                gap: 16px;
            }
            
            .filter-group.filter-years {
                flex-shrink: 0;
            }
            
            .filter-group.filter-institution {
                min-width: 200px;
                max-width: 220px;
            }
            
            /* Reduce dropdown widths and align Reset button */
            .filter-group .selectize-control {
                min-width: 140px;
            }
            
            .filter-row .filter-group {
                display: flex;
                flex-direction: column;
                justify-content: flex-end;
            }
            
            .filter-row .filter-group:last-child {
                align-self: flex-end;
                padding-bottom: 0;
            }
            
            /* KPI card title height fix for Simulator */
            .kpi-card .kpi-label {
                min-height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .selectize-input {
                border-radius: 4px !important;
            }
            
            /* Force Plotly to fill container */
            .card-body .shiny-html-output,
            .card-body .html-widget,
            .card-body .plotly,
            .card-body .js-plotly-plot {
                width: 100% !important;
            }
            
            /* Export PDF Button */
            .btn-export-pdf {
                background: transparent;
                border: 1px solid var(--primary);
                color: var(--primary);
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 12px;
                cursor: pointer;
                transition: all 0.2s;
                display: inline-flex;
                align-items: center;
                gap: 6px;
            }
            
            .btn-export-pdf:hover {
                background: var(--primary);
                color: var(--white);
            }
            
            /* Print styles for PDF export */
            @media print {
                .navbar, .filter-panel, .btn-export-pdf, .btn-reset,
                .hero-actions, .tabs-nav, .download-button {
                    display: none !important;
                }
                
                .main-wrapper {
                    padding: 0 !important;
                }
                
                .card {
                    box-shadow: none !important;
                    border: 1px solid #ddd !important;
                    page-break-inside: avoid;
                }
                
                .page-content {
                    max-width: 100% !important;
                }
                
                body {
                    -webkit-print-color-adjust: exact !important;
                    print-color-adjust: exact !important;
                }
            }
        """),
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
            
            // Update navbar active state when clicking navigation buttons
            function updateNavActive(activeId) {
                document.querySelectorAll('.nav-link').forEach(function(btn) {
                    btn.classList.remove('active');
                });
                var activeBtn = document.getElementById(activeId);
                if (activeBtn) {
                    activeBtn.classList.add('active');
                }
            }
            
            document.addEventListener('DOMContentLoaded', function() {
                ['nav_overview', 'nav_benchmarking', 'nav_profile', 'nav_simulator'].forEach(function(id) {
                    var btn = document.getElementById(id);
                    if (btn) {
                        btn.addEventListener('click', function() {
                            updateNavActive(id);
                        });
                    }
                });
            });
            
            // Export current page as PDF using browser print
            function exportPageAsPDF() {
                // Add a temporary title for the PDF
                var pageTitle = document.querySelector('.section-title, .hero-title');
                var originalTitle = document.title;
                if (pageTitle) {
                    document.title = 'Enrollment Analytics - ' + pageTitle.textContent.trim();
                }
                
                // Trigger print dialog (user can save as PDF)
                window.print();
                
                // Restore original title
                document.title = originalTitle;
            }
            
            // Prevent client-side errors during page transitions
            // Wrap Shiny's setInputValue to handle undefined targets gracefully
            (function() {
                var originalSetInputValue = Shiny.setInputValue;
                if (originalSetInputValue) {
                    Shiny.setInputValue = function(name, value, opts) {
                        try {
                            return originalSetInputValue.call(Shiny, name, value, opts);
                        } catch (e) {
                            console.warn('Shiny setInputValue error caught:', e.message);
                        }
                    };
                }
            })();
            
            // Handle Plotly resize errors gracefully during page transitions
            window.addEventListener('error', function(e) {
                if (e.message && e.message.includes('Cannot set properties of undefined')) {
                    e.preventDefault();
                    console.warn('Plotly transition error suppressed');
                    return true;
                }
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
