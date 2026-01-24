"""
Institution Profile page module.
Provides detailed view of a single institution with trends, drivers, and comparisons.
"""

from shiny import ui, reactive, render, module
from shinywidgets import output_widget, render_widget
import pandas as pd
import numpy as np

from .components_kpis import create_kpi_card, create_insights_panel
from .components_charts import (
    create_trends_chart,
    create_demographics_chart,
    create_waterfall_chart,
    create_distribution_chart,
    create_small_multiples_trends,
)
from .components_tables import create_comparison_table
from utils.metrics import (
    get_yoy_metrics,
    decompose_enrolled_variation,
    calculate_institution_diversity,
    generate_insights,
    wilson_interval_simple,
    find_similar_institutions_simple,
)


def profile_ui():
    """Create the Institution Profile page UI."""
    return ui.div(
        # Hero Section
        ui.output_ui("profile_hero"),
        
        # Snapshot KPI Cards
        ui.output_ui("profile_kpi_cards"),
        
        # Dynamic Insights
        ui.output_ui("profile_insights"),
        
        # Tabs for different views
        ui.div(
            ui.div(
                ui.input_radio_buttons(
                    "profile_tab",
                    None,
                    choices={
                        "trends": "📈 Trends",
                        "drivers": "🔍 Drivers",
                        "demographics": "👥 Demographics",
                        "benchmark": "📊 Benchmark Context",
                    },
                    selected="trends",
                    inline=True
                ),
                class_="tabs-nav"
            ),
            
            # Tab content
            ui.output_ui("profile_tab_content"),
            
            class_="tabs-container"
        ),
        
        # Compare Basket (if institutions selected)
        ui.output_ui("profile_compare_section"),
        
        class_="page-content"
    )


def profile_server(input, output, session, filtered_data, full_data,
                   selected_years, selected_institution, latest_year, institutions_list):
    """Server logic for the Institution Profile page."""
    
    # Reactive: Get institution data across all years
    @reactive.calc
    def institution_data():
        inst = selected_institution()
        if not inst:
            return pd.DataFrame()
        
        df = full_data()
        return df[df['institution_name'] == inst].sort_values('year')
    
    # Reactive: Get latest year data for institution
    @reactive.calc
    def institution_latest():
        inst_df = institution_data()
        if inst_df.empty:
            return None
        
        year = latest_year()
        if year:
            year_data = inst_df[inst_df['year'] == year]
            if not year_data.empty:
                return year_data.iloc[0].to_dict()
        
        return inst_df.iloc[-1].to_dict()
    
    # Hero Section
    @render.ui
    def profile_hero():
        inst = selected_institution()
        latest = institution_latest()
        
        if not inst or not latest:
            return ui.div(
                ui.div(
                    ui.h2("Institution Profile", class_="hero-title"),
                    ui.p("Select an institution from the filter bar to view its profile",
                         class_="hero-subtitle"),
                    class_="hero-section"
                )
            )
        
        state = latest.get('state', '')
        region = latest.get('region', '')
        size = latest.get('institution_size', '')
        
        return ui.div(
            ui.h1(inst, class_="hero-title"),
            ui.p(f"{state} • {region} Region • {size} Institution", class_="hero-subtitle"),
            ui.div(
                ui.input_action_button(
                    "profile_add_compare",
                    "➕ Add to Compare",
                    class_="hero-btn"
                ),
                ui.input_action_button(
                    "profile_share",
                    "🔗 Share Link",
                    class_="hero-btn"
                ),
                class_="hero-actions"
            ),
            class_="hero-section"
        )
    
    # KPI Cards
    @render.ui
    def profile_kpi_cards():
        latest = institution_latest()
        inst_df = institution_data()
        
        if not latest or inst_df.empty:
            return ui.div(class_="kpi-grid")
        
        # Get YoY metrics
        year = latest.get('year')
        yoy = get_yoy_metrics(inst_df, year) if year else {}
        
        # Calculate confidence intervals for rates
        applicants = latest.get('applicants', 0)
        admitted = latest.get('admissions', 0)
        enrolled = latest.get('enrolled_total', 0)
        
        admit_ci = wilson_interval_simple(admitted, applicants) if applicants > 0 else (0, 0)
        yield_ci = wilson_interval_simple(enrolled, admitted) if admitted > 0 else (0, 0)
        
        cards = []
        
        # Applicants
        cards.append(create_kpi_card(
            label="Applicants",
            value=applicants,
            delta=yoy.get('delta_applicants'),
            delta_type="percent",
            subtext=f"Year {year}",
            card_type="applicants"
        ))
        
        # Admitted
        cards.append(create_kpi_card(
            label="Admitted",
            value=admitted,
            delta=yoy.get('delta_admitted'),
            delta_type="percent",
            subtext=f"{latest.get('admit_rate', 0):.1f}% admit rate",
            card_type="admitted"
        ))
        
        # Enrolled
        cards.append(create_kpi_card(
            label="Enrolled",
            value=enrolled,
            delta=yoy.get('delta_enrolled'),
            delta_type="percent",
            subtext=f"{latest.get('yield_rate', 0):.1f}% yield rate",
            card_type="enrolled"
        ))
        
        # Admit Rate with CI
        cards.append(create_kpi_card(
            label="Admit Rate",
            value=latest.get('admit_rate', 0),
            delta=yoy.get('delta_admit_rate'),
            delta_type="pp",
            subtext=f"95% CI: [{admit_ci[0]:.1f}%, {admit_ci[1]:.1f}%]",
            card_type="admit"
        ))
        
        # Yield Rate with CI
        cards.append(create_kpi_card(
            label="Yield Rate",
            value=latest.get('yield_rate', 0),
            delta=yoy.get('delta_yield_rate'),
            delta_type="pp",
            subtext=f"95% CI: [{yield_ci[0]:.1f}%, {yield_ci[1]:.1f}%]",
            card_type="yield"
        ))
        
        return ui.div(*cards, class_="kpi-grid")
    
    # Insights Panel
    @render.ui
    def profile_insights():
        inst = selected_institution()
        latest = institution_latest()
        inst_df = institution_data()
        
        if not inst or not latest:
            return ui.div()
        
        # Get peer data for percentiles
        df = full_data()
        year = latest.get('year')
        if not year:
            return ui.div()
        
        year_data = df[df['year'] == year]
        
        # Calculate peer percentiles
        peer_percentiles = {}
        for metric in ['yield_rate', 'admit_rate']:
            if metric in year_data.columns:
                values = year_data[metric].dropna()
                peer_percentiles[metric] = {
                    'p25': values.quantile(0.25),
                    'p50': values.quantile(0.50),
                    'p75': values.quantile(0.75),
                }
        
        # Add diversity if available
        if 'pct_hispanic' in latest:
            diversity = calculate_institution_diversity(pd.Series(latest))
            latest['diversity_index'] = diversity
            
            div_values = year_data.apply(
                lambda row: calculate_institution_diversity(row), axis=1
            )
            peer_percentiles['diversity_index'] = {
                'p25': div_values.quantile(0.25),
                'p50': div_values.quantile(0.50),
                'p75': div_values.quantile(0.75),
            }
        
        # Get YoY metrics
        yoy = get_yoy_metrics(inst_df, year)
        
        # Add decomposition info if we have decline
        if yoy.get('delta_enrolled') and yoy['delta_enrolled'] < -5:
            # Get previous year data
            prev_year = year - 1
            prev_data = inst_df[inst_df['year'] == prev_year]
            curr_data = inst_df[inst_df['year'] == year]
            
            if not prev_data.empty and not curr_data.empty:
                prev = prev_data.iloc[0]
                curr = curr_data.iloc[0]
                
                decomp = decompose_enrolled_variation(
                    prev['applicants'], prev['admit_rate'], prev['yield_rate'],
                    curr['applicants'], curr['admit_rate'], curr['yield_rate']
                )
                yoy['primary_driver'] = decomp.get('primary_driver', 'unknown')
        
        insights = generate_insights(latest, peer_percentiles, yoy)
        
        return create_insights_panel(insights, inst)
    
    # Tab Content
    @render.ui
    def profile_tab_content():
        tab = input.profile_tab()
        
        if tab == "trends":
            return ui.div(
                ui.div(
                    ui.h3("Enrollment Trends", class_="card-title"),
                    class_="card-header"
                ),
                ui.div(
                    output_widget("profile_trends_chart"),
                    class_="card-body"
                ),
                ui.div(
                    ui.h3("Rate Trends", class_="card-title"),
                    class_="card-header"
                ),
                ui.div(
                    output_widget("profile_rates_chart"),
                    class_="card-body"
                ),
                class_="card chart-section"
            )
        
        elif tab == "drivers":
            return ui.div(
                ui.div(
                    ui.h3("Enrollment Change Decomposition", class_="card-title"),
                    ui.p("Breaking down the change in enrolled students by driver", class_="section-subtitle"),
                    class_="card-header"
                ),
                ui.div(
                    output_widget("profile_waterfall_chart"),
                    class_="card-body"
                ),
                ui.output_ui("profile_driver_summary"),
                class_="card chart-section"
            )
        
        elif tab == "demographics":
            return ui.div(
                ui.div(
                    ui.h3("Demographic Composition Over Time", class_="card-title"),
                    class_="card-header"
                ),
                ui.div(
                    output_widget("profile_demographics_chart"),
                    class_="card-body"
                ),
                ui.output_ui("profile_demographic_changes"),
                class_="card chart-section"
            )
        
        elif tab == "benchmark":
            return ui.div(
                ui.div(
                    ui.h3("Position Within Peer Group", class_="card-title"),
                    class_="card-header"
                ),
                ui.div(
                    output_widget("profile_benchmark_dist"),
                    class_="card-body"
                ),
                ui.div(
                    ui.h3("Similar Institutions", class_="card-title"),
                    class_="card-header"
                ),
                ui.div(
                    ui.output_ui("profile_similar_table"),
                    class_="card-body"
                ),
                class_="card chart-section"
            )
        
        return ui.div()
    
    # Trends Chart (counts)
    @render_widget
    def profile_trends_chart():
        inst_df = institution_data()
        
        if inst_df.empty:
            return create_trends_chart(pd.DataFrame())
        
        # Prepare data
        trends_df = inst_df[['year', 'applicants', 'admissions', 'enrolled_total']].copy()
        trends_df = trends_df.rename(columns={
            'admissions': 'admitted',
            'enrolled_total': 'enrolled'
        })
        
        # Create line chart for counts
        import plotly.graph_objects as go
        
        fig = go.Figure()
        
        colors = {'applicants': '#0F172A', 'admitted': '#2563EB', 'enrolled': '#10B981'}
        
        for col in ['applicants', 'admitted', 'enrolled']:
            if col in trends_df.columns:
                fig.add_trace(go.Scatter(
                    x=trends_df['year'],
                    y=trends_df[col],
                    mode='lines+markers',
                    name=col.capitalize(),
                    line=dict(color=colors.get(col, '#64748B'), width=2),
                    marker=dict(size=8),
                ))
        
        fig.update_layout(
            font={'family': 'Inter, sans-serif', 'size': 12},
            paper_bgcolor='#FFFFFF',
            plot_bgcolor='#FFFFFF',
            margin={'l': 50, 'r': 30, 't': 20, 'b': 50},
            xaxis=dict(title=None, tickmode='linear', dtick=1, gridcolor='#E2E8F0'),
            yaxis=dict(title='Count', gridcolor='#E2E8F0'),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
            height=280,
            hovermode='x unified',
        )
        
        return fig
    
    # Rates Chart
    @render_widget
    def profile_rates_chart():
        inst_df = institution_data()
        
        if inst_df.empty:
            return create_trends_chart(pd.DataFrame())
        
        trends_df = inst_df[['year', 'admit_rate', 'yield_rate']].copy()
        
        # Calculate overall conversion
        if 'applicants' in inst_df.columns and 'enrolled_total' in inst_df.columns:
            trends_df['overall_rate'] = (inst_df['enrolled_total'] / inst_df['applicants'] * 100).round(1)
        
        return create_trends_chart(trends_df, metrics=['admit_rate', 'yield_rate', 'overall_rate'])
    
    # Waterfall Chart
    @render_widget
    def profile_waterfall_chart():
        inst_df = institution_data()
        
        if inst_df.empty or len(inst_df) < 2:
            return create_waterfall_chart(0, 0, 0, 0, 0)
        
        # Get last two years
        sorted_df = inst_df.sort_values('year')
        years = sorted_df['year'].unique()
        
        if len(years) < 2:
            return create_waterfall_chart(0, 0, 0, 0, 0)
        
        base_year = years[-2]
        compare_year = years[-1]
        
        base_data = sorted_df[sorted_df['year'] == base_year].iloc[0]
        compare_data = sorted_df[sorted_df['year'] == compare_year].iloc[0]
        
        decomp = decompose_enrolled_variation(
            base_data['applicants'], base_data['admit_rate'], base_data['yield_rate'],
            compare_data['applicants'], compare_data['admit_rate'], compare_data['yield_rate']
        )
        
        return create_waterfall_chart(
            decomp['enrolled_base'],
            decomp['effect_applicants'],
            decomp['effect_admit_rate'],
            decomp['effect_yield'],
            decomp['enrolled_compare']
        )
    
    # Driver Summary
    @render.ui
    def profile_driver_summary():
        inst_df = institution_data()
        
        if inst_df.empty or len(inst_df) < 2:
            return ui.p("Need at least 2 years of data for decomposition analysis",
                       style="color: var(--color-text-muted); text-align: center; padding: 16px;")
        
        sorted_df = inst_df.sort_values('year')
        years = sorted_df['year'].unique()
        
        if len(years) < 2:
            return ui.div()
        
        base_year = years[-2]
        compare_year = years[-1]
        
        base_data = sorted_df[sorted_df['year'] == base_year].iloc[0]
        compare_data = sorted_df[sorted_df['year'] == compare_year].iloc[0]
        
        decomp = decompose_enrolled_variation(
            base_data['applicants'], base_data['admit_rate'], base_data['yield_rate'],
            compare_data['applicants'], compare_data['admit_rate'], compare_data['yield_rate']
        )
        
        driver = decomp.get('primary_driver', 'unknown')
        driver_text = driver.replace('_', ' ').title()
        
        delta = decomp['delta_enrolled']
        direction = "increased" if delta > 0 else "decreased"
        
        return ui.div(
            ui.p(
                f"Enrollment {direction} by {abs(delta):,.0f} students from {base_year} to {compare_year}. ",
                ui.strong(f"Primary driver: {driver_text}"),
                style="padding: 16px; background: var(--color-bg); border-radius: 8px; margin-top: 16px;"
            )
        )
    
    # Demographics Chart
    @render_widget
    def profile_demographics_chart():
        inst_df = institution_data()
        
        if inst_df.empty:
            return create_demographics_chart(pd.DataFrame())
        
        demo_cols = ['year', 'pct_hispanic', 'pct_white', 'pct_black', 'pct_asian', 'pct_other']
        demo_cols = [c for c in demo_cols if c in inst_df.columns]
        
        demo_df = inst_df[demo_cols].copy()
        
        return create_demographics_chart(demo_df)
    
    # Demographic Changes
    @render.ui
    def profile_demographic_changes():
        inst_df = institution_data()
        
        if inst_df.empty or len(inst_df) < 2:
            return ui.div()
        
        sorted_df = inst_df.sort_values('year')
        first = sorted_df.iloc[0]
        last = sorted_df.iloc[-1]
        
        demo_cols = ['pct_hispanic', 'pct_white', 'pct_black', 'pct_asian', 'pct_other']
        
        changes = []
        for col in demo_cols:
            if col in first.index and col in last.index:
                change = last[col] - first[col]
                if abs(change) > 1:  # Only show significant changes
                    group = col.replace('pct_', '').replace('_', ' ').title()
                    direction = "↑" if change > 0 else "↓"
                    badge_class = "badge-success" if change > 0 else "badge-danger"
                    changes.append(ui.span(
                        f"{direction} {group}: {change:+.1f}pp",
                        class_=f"badge {badge_class}",
                        style="margin-right: 8px;"
                    ))
        
        if not changes:
            return ui.div()
        
        return ui.div(
            ui.p("Changes from first to last year:", style="font-weight: 500; margin-bottom: 8px;"),
            *changes,
            style="padding: 16px; background: var(--color-bg); border-radius: 8px; margin-top: 16px;"
        )
    
    # Benchmark Distribution
    @render_widget
    def profile_benchmark_dist():
        inst = selected_institution()
        latest = institution_latest()
        
        if not inst or not latest:
            return create_distribution_chart(pd.Series([]))
        
        df = full_data()
        year = latest.get('year')
        
        if not year:
            return create_distribution_chart(pd.Series([]))
        
        year_data = df[df['year'] == year]
        values = year_data['yield_rate'].dropna()
        target_value = latest.get('yield_rate')
        
        return create_distribution_chart(
            values,
            target_value=target_value,
            target_name=inst[:30],
            metric_name='Yield Rate (%)',
            chart_type='violin'
        )
    
    # Similar Institutions Table
    @render.ui
    def profile_similar_table():
        inst = selected_institution()
        latest = institution_latest()
        
        if not inst or not latest:
            return ui.p("Select an institution to see similar peers",
                       style="color: var(--color-text-muted); text-align: center; padding: 24px;")
        
        df = full_data()
        year = latest.get('year')
        
        if not year:
            return ui.div()
        
        similar = find_similar_institutions_simple(df, inst, year, k=10)
        
        if similar.empty:
            return ui.p("No similar institutions found",
                       style="color: var(--color-text-muted); text-align: center; padding: 24px;")
        
        from .components_tables import create_data_table
        
        return create_data_table(
            similar,
            columns=['institution_name', 'applicants', 'admit_rate', 'yield_rate', 'enrolled_total', 'diversity_index'],
            column_labels={
                'enrolled_total': 'Enrolled',
                'diversity_index': 'Diversity',
            }
        )
    
    # Compare Section
    @render.ui
    def profile_compare_section():
        # Placeholder for compare basket functionality
        return ui.div()
