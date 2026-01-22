"""
Higher Education Enrollment Funnel Analytics Dashboard

A production-grade interactive data visualization dashboard using Shiny for Python.

Author: Matheus Abrantes
Date: January 2026
"""

from shiny import App, reactive, render, ui
from shinywidgets import output_widget, render_widget
import pandas as pd

from utils.data_loader import (
    load_ipeds_data, 
    get_unique_years, 
    get_unique_institutions,
    get_unique_regions,
    get_unique_sizes,
    get_states_by_region
)
from utils.calculations import (
    calculate_metrics,
    calculate_funnel_data,
    calculate_trends_by_year,
    calculate_demographics_by_year,
    get_top_institutions
)
from utils.styling import CARNEGIE_COLORS
from components.header import create_header
from components.filters import create_filters
from components.funnel_chart import create_funnel_chart
from components.trends_chart import create_trends_chart
from components.demographics_chart import create_demographics_chart
from components.comparison_chart import create_comparison_chart
from components.geographic_map import create_state_map
from components.key_insights import create_key_insights_ui, render_key_insights, calculate_rankings


# Load data at startup
print("Loading IPEDS enrollment data...")
DATA = load_ipeds_data()
YEARS = get_unique_years(DATA)
INSTITUTIONS = get_unique_institutions(DATA)
REGIONS = get_unique_regions(DATA)
SIZES = get_unique_sizes(DATA)
STATES_BY_REGION = get_states_by_region(DATA)
print(f"Loaded {len(DATA)} records for {len(INSTITUTIONS)} institutions across {len(YEARS)} years")


# Define UI
app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.link(rel="stylesheet", href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"),
        ui.tags.script("""
            // Force Plotly charts to resize after page load
            document.addEventListener('DOMContentLoaded', function() {
                // Wait for Shiny and Plotly to fully initialize
                setTimeout(function() {
                    resizePlotlyCharts();
                }, 1000);
                
                // Also resize on window resize
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
            
            // Observer to catch dynamically added plots
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
            
            .dashboard-wrapper {
                max-width: 1400px;
                margin: 0 auto;
                padding: 16px 24px;
            }
            
            .dashboard-header {
                background: linear-gradient(135deg, var(--primary) 0%, #2A4A7A 100%);
                color: var(--white);
                padding: 24px 32px;
                margin-bottom: 0;
                box-shadow: 0 2px 8px rgba(0,0,0,0.15);
                border-radius: 12px 12px 0 0;
            }
            
            .header-content {
                max-width: 100%;
                margin: 0;
                padding: 0;
            }
            
            .dashboard-title {
                font-size: 28px;
                font-weight: 700;
                margin: 0 0 8px 0;
                letter-spacing: -0.5px;
            }
            
            .dashboard-subtitle {
                font-size: 14px;
                opacity: 0.9;
                margin: 0;
                font-weight: 400;
            }
            
            .filter-panel {
                background: var(--white);
                padding: 12px 32px;
                border-bottom: 1px solid #E0E0E0;
                position: sticky;
                top: 0;
                z-index: 100;
            }
            
            .filter-row {
                display: flex;
                flex-wrap: nowrap;
                align-items: flex-end;
                gap: 16px;
                max-width: 100%;
                margin: 0;
                padding: 0;
            }
            
            .filter-item {
                display: flex;
                flex-direction: column;
            }
            
            .filter-item label {
                font-size: 11px;
                font-weight: 600;
                color: var(--primary);
                margin-bottom: 4px;
                text-transform: uppercase;
                letter-spacing: 0.3px;
            }
            
            .filter-years {
                flex-shrink: 0;
            }
            
            .filter-years .shiny-input-checkboxgroup label.checkbox-inline {
                margin-right: 8px;
                font-size: 12px;
            }
            
            .filter-region {
                width: 160px;
                min-width: 160px;
            }
            
            .filter-size {
                width: 120px;
                min-width: 120px;
            }
            
            .filter-institution {
                flex: 1;
                min-width: 200px;
            }
            
            .filter-reset {
                flex-shrink: 0;
            }
            
            .btn-reset {
                background: var(--neutral-light);
                border: 1px solid #DDD;
                color: var(--neutral-dark);
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 12px;
                cursor: pointer;
                transition: all 0.2s;
            }
            
            .btn-reset:hover {
                background: var(--primary);
                color: var(--white);
                border-color: var(--primary);
            }
            
            .main-content {
                max-width: 100%;
                margin: 0;
                padding: 24px 0;
            }
            
            .kpi-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 16px;
                margin-bottom: 24px;
            }
            
            .kpi-card {
                background: var(--white);
                border-radius: 8px;
                padding: 20px;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.08);
                border-left: 4px solid var(--primary);
                transition: transform 0.2s, box-shadow 0.2s;
            }
            
            .kpi-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.12);
            }
            
            .kpi-card:nth-child(2) { border-left-color: #4A90E2; }
            .kpi-card:nth-child(3) { border-left-color: #50C878; }
            .kpi-card:nth-child(4) { border-left-color: var(--secondary); }
            
            .kpi-label {
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                color: #666;
                margin-bottom: 8px;
                font-weight: 600;
            }
            
            .kpi-value {
                font-size: 32px;
                font-weight: 700;
                color: var(--primary);
                line-height: 1.1;
            }
            
            .kpi-card:nth-child(4) .kpi-value { color: var(--secondary); }
            
            .kpi-subtext {
                font-size: 11px;
                color: #888;
                margin-top: 4px;
            }
            
            .chart-section {
                background: var(--white);
                border-radius: 8px;
                padding: 24px;
                margin-bottom: 24px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.08);
            }
            
            .chart-row {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
                gap: 24px;
                margin-bottom: 24px;
            }
            
            .section-title {
                font-size: 14px;
                font-weight: 600;
                color: var(--primary);
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 16px;
                padding-bottom: 8px;
                border-bottom: 2px solid var(--neutral-light);
            }
            
            .comparison-controls {
                display: flex;
                gap: 12px;
                margin-bottom: 16px;
            }
            
            .metric-btn {
                padding: 8px 16px;
                border: 1px solid #DDD;
                background: var(--white);
                border-radius: 4px;
                cursor: pointer;
                font-size: 13px;
                transition: all 0.2s;
            }
            
            .metric-btn:hover, .metric-btn.active {
                background: var(--primary);
                color: var(--white);
                border-color: var(--primary);
            }
            
            .footer {
                text-align: center;
                padding: 24px;
                color: #666;
                font-size: 12px;
                border-top: 1px solid #E0E0E0;
                margin-top: 24px;
            }
            
            .footer a {
                color: var(--primary);
                text-decoration: none;
            }
            
            /* Shiny specific overrides */
            .shiny-input-checkboxgroup label.checkbox-inline {
                margin-right: 16px;
            }
            
            .selectize-input {
                border-radius: 4px !important;
            }
            
            /* Force Plotly widgets to fill container width */
            .chart-section .shiny-html-output,
            .chart-section .html-widget,
            .chart-section .plotly,
            .chart-section .js-plotly-plot {
                width: 100% !important;
            }
            
            .chart-section .plotly .main-svg {
                width: 100% !important;
            }
            
            /* Key Insights Panel Styles */
            .key-insights-panel {
                min-height: 400px;
            }
            
            .insights-container {
                padding: 8px 0;
            }
            
            .insights-header {
                background: linear-gradient(135deg, var(--primary) 0%, #2A4A7A 100%);
                color: white;
                padding: 12px 16px;
                border-radius: 8px;
                margin-bottom: 16px;
                font-size: 13px;
                font-weight: 600;
                display: flex;
                align-items: center;
            }
            
            .institution-name-badge {
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            
            .insight-metric {
                background: #f8f9fa;
                border-radius: 8px;
                padding: 12px 16px;
                margin-bottom: 12px;
                border-left: 4px solid var(--primary);
            }
            
            .metric-header {
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 10px;
                font-weight: 600;
                color: var(--primary);
                font-size: 13px;
            }
            
            .metric-icon {
                font-size: 16px;
            }
            
            .rankings-row {
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
            }
            
            .rank-badge {
                display: flex;
                align-items: center;
                gap: 4px;
                padding: 6px 10px;
                border-radius: 6px;
                font-size: 12px;
                flex: 1;
                min-width: 80px;
            }
            
            .rank-badge.national {
                background: #e3f2fd;
                color: #1565c0;
            }
            
            .rank-badge.region {
                background: #fff3e0;
                color: #e65100;
            }
            
            .rank-badge.state {
                background: #e8f5e9;
                color: #2e7d32;
            }
            
            .rank-icon {
                font-size: 12px;
            }
            
            .rank-number {
                font-weight: 700;
                font-size: 14px;
            }
            
            .rank-total {
                font-size: 10px;
                opacity: 0.8;
            }
            
            .insights-placeholder {
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 300px;
                color: #666;
            }
            
            .funnel-insights-row {
                display: grid;
                grid-template-columns: 1.2fr 0.8fr;
                gap: 24px;
                margin-bottom: 24px;
            }
            
            @media (max-width: 1200px) {
                .funnel-insights-row {
                    grid-template-columns: 1fr;
                }
            }
        """)
    ),
    
    # Dashboard Wrapper
    ui.div(
        # Header
        create_header(),
        
        # Filters
        create_filters(YEARS, INSTITUTIONS, REGIONS, STATES_BY_REGION, SIZES),
        
        # Main Content
        ui.div(
            # KPI Cards
            ui.div(
                ui.div(
                    ui.div("Total Applicants", class_="kpi-label"),
                    ui.div(ui.output_text("kpi_applicants"), class_="kpi-value"),
                    ui.div("across selected filters", class_="kpi-subtext"),
                    class_="kpi-card"
                ),
                ui.div(
                    ui.div("Total Admissions", class_="kpi-label"),
                    ui.div(ui.output_text("kpi_admissions"), class_="kpi-value"),
                    ui.div("students admitted", class_="kpi-subtext"),
                    class_="kpi-card"
                ),
                ui.div(
                    ui.div("Total Enrolled", class_="kpi-label"),
                    ui.div(ui.output_text("kpi_enrolled"), class_="kpi-value"),
                    ui.div("students enrolled", class_="kpi-subtext"),
                    class_="kpi-card"
                ),
                ui.div(
                    ui.div("Average Yield Rate", class_="kpi-label"),
                    ui.div(ui.output_text("kpi_yield"), class_="kpi-value"),
                    ui.div("enrolled / admitted", class_="kpi-subtext"),
                    class_="kpi-card"
                ),
                class_="kpi-grid"
            ),
            
            # Funnel Chart and Key Insights Row
            ui.div(
                ui.div(
                    ui.div("Enrollment Funnel Overview", class_="section-title"),
                    output_widget("funnel_chart"),
                    class_="chart-section"
                ),
                create_key_insights_ui(),
                class_="funnel-insights-row"
            ),
            
            # Trends and Demographics Row
            ui.div(
                ui.div(
                    ui.div("Conversion Trends", class_="section-title"),
                    output_widget("trends_chart"),
                    class_="chart-section"
                ),
                ui.div(
                    ui.div("Enrollment Demographics", class_="section-title"),
                    output_widget("demographics_chart"),
                    class_="chart-section"
                ),
                class_="chart-row"
            ),
            
            # Geographic Distribution and Institution Benchmarking Row
            ui.div(
                ui.div(
                    ui.div("Geographic Distribution", class_="section-title"),
                    ui.div(
                        ui.input_radio_buttons(
                            "map_metric",
                            None,
                            choices={
                                "yield_rate": "Yield Rate",
                                "enrolled_total": "Total Enrollment",
                                "num_institutions": "Institutions"
                            },
                            selected="yield_rate",
                            inline=True
                        ),
                        class_="comparison-controls"
                    ),
                    output_widget("geographic_map"),
                    class_="chart-section"
                ),
                ui.div(
                    ui.div("Institution Benchmarking", class_="section-title"),
                    ui.div(
                        ui.input_radio_buttons(
                            "comparison_metric",
                            None,
                            choices={
                                "yield_rate": "By Yield Rate",
                                "enrolled_total": "By Total Enrollment",
                                "admit_rate": "By Admit Rate"
                            },
                            selected="yield_rate",
                            inline=True
                        ),
                        class_="comparison-controls"
                    ),
                    output_widget("comparison_chart"),
                    class_="chart-section"
                ),
                class_="chart-row"
            ),
            
            # Footer
            ui.div(
                ui.HTML("""
                    <p><strong>Higher Education Enrollment Analytics Dashboard</strong></p>
                    <p>Data Source: IPEDS (Integrated Postsecondary Education Data System) - U.S. Department of Education</p>
                    <p>Built by <a href="https://github.com/matheusabrantes" target="_blank">Matheus Abrantes</a> | January 2026</p>
                """),
                class_="footer"
            ),
            class_="main-content"
        ),
        class_="dashboard-wrapper"
    ),
)


def server(input, output, session):
    """Server logic for the enrollment dashboard."""
    
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
            # Parse selections: regions vs states
            selected_regions = []
            selected_states = []
            for item in selected_region_state:
                if item.startswith('state:'):
                    # Format: "state:Region:ST"
                    parts = item.split(':')
                    if len(parts) >= 3:
                        selected_states.append(parts[2])
                else:
                    # It's a region
                    selected_regions.append(item)
            
            # Filter by regions OR states
            if selected_regions or selected_states:
                mask = df['region'].isin(selected_regions) | df['state'].isin(selected_states)
                df = df[mask]
        
        # Apply size filter
        selected_sizes = input.size_filter()
        if selected_sizes:
            df = df[df['institution_size'].isin(selected_sizes)]
        
        # Apply institution filter
        selected_institutions = input.institution_filter()
        if selected_institutions and "All Institutions" not in selected_institutions:
            df = df[df['institution_name'].isin(selected_institutions)]
        
        return df
    
    @reactive.effect
    @reactive.event(input.reset_filters)
    def reset_filters():
        """Reset all filters to default values."""
        ui.update_checkbox_group("year_filter", selected=[str(y) for y in YEARS])
        ui.update_selectize("region_state_filter", selected=[])
        ui.update_selectize("size_filter", selected=[])
        ui.update_selectize("institution_filter", selected=["All Institutions"])
    
    # KPI Outputs
    @render.text
    def kpi_applicants():
        metrics = calculate_metrics(filtered_data())
        return f"{metrics['total_applicants']:,}"
    
    @render.text
    def kpi_admissions():
        metrics = calculate_metrics(filtered_data())
        return f"{metrics['total_admissions']:,}"
    
    @render.text
    def kpi_enrolled():
        metrics = calculate_metrics(filtered_data())
        return f"{metrics['total_enrolled']:,}"
    
    @render.text
    def kpi_yield():
        metrics = calculate_metrics(filtered_data())
        return f"{metrics['overall_yield_rate']:.1f}%"
    
    # Chart Outputs
    @render_widget
    def funnel_chart():
        funnel_data = calculate_funnel_data(filtered_data())
        return create_funnel_chart(funnel_data)
    
    @render_widget
    def trends_chart():
        trends_df = calculate_trends_by_year(filtered_data())
        return create_trends_chart(trends_df)
    
    @render_widget
    def demographics_chart():
        demo_df = calculate_demographics_by_year(filtered_data())
        return create_demographics_chart(demo_df)
    
    @render_widget
    def geographic_map():
        metric = input.map_metric()
        return create_state_map(filtered_data(), metric=metric)
    
    @render_widget
    def comparison_chart():
        metric = input.comparison_metric()
        top_df = get_top_institutions(filtered_data(), metric=metric, n=10)
        return create_comparison_chart(top_df, metric=metric)
    
    @render.ui
    def key_insights_content():
        """Render Key Insights panel with institution rankings."""
        selected_institutions = input.institution_filter()
        
        # Check if exactly one institution is selected
        if not selected_institutions or "All Institutions" in selected_institutions:
            return render_key_insights({}, None)
        
        if len(selected_institutions) != 1:
            return render_key_insights({}, None)
        
        institution_name = selected_institutions[0]
        
        # Get the latest year from selected years
        selected_years = input.year_filter()
        if selected_years:
            year = max(int(y) for y in selected_years)
        else:
            year = DATA['year'].max()
        
        # Calculate rankings using full dataset (not filtered)
        rankings = calculate_rankings(DATA, institution_name, year)
        
        return render_key_insights(rankings, institution_name)


# Create app
app = App(app_ui, server)
