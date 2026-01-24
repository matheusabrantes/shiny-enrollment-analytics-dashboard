"""
Overview page module for the enrollment dashboard.
Enhanced with YoY deltas, rankings, cross-filtering, and data table.
"""

from shiny import ui, reactive, render, module
from shinywidgets import output_widget, render_widget
import pandas as pd

from .components_kpis import create_kpi_card, create_insights_panel
from .components_charts import (
    create_funnel_chart,
    create_trends_chart,
    create_demographics_chart,
    create_state_map,
    create_comparison_bar_chart,
)
from .components_tables import create_data_table, create_download_button
from utils.metrics import get_yoy_metrics, calculate_funnel_leakage, calculate_rank_and_percentile
from utils.data_model import get_aggregate_metrics


def overview_ui():
    """Create the Overview page UI."""
    return ui.div(
        # Page header with insights directly below title
        ui.div(
            ui.div(
                ui.h2("Executive Overview", class_="section-title", style="margin: 0;"),
                ui.tags.button(
                    "📄 Export PDF",
                    onclick="exportPageAsPDF()",
                    class_="btn-export-pdf"
                ),
                style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;"
            ),
            ui.p("Comprehensive view of enrollment funnel metrics across selected institutions", 
                 class_="section-subtitle"),
            # Insights panel directly under title for better visibility
            ui.output_ui("overview_insights_panel"),
            style="margin-bottom: 24px;"
        ),
        
        # KPI Cards Row
        ui.output_ui("overview_kpi_cards"),
        
        # Rankings Row (when institution selected)
        ui.output_ui("overview_rankings"),
        
        # Funnel Chart
        ui.div(
            ui.div(
                ui.h3("Enrollment Funnel", class_="card-title"),
                class_="card-header"
            ),
            ui.div(
                output_widget("overview_funnel_chart"),
                class_="card-body"
            ),
            class_="card chart-section"
        ),
        
        # Trends and Demographics Row
        ui.div(
            ui.div(
                ui.div(
                    ui.h3("Conversion Trends", class_="card-title"),
                    class_="card-header"
                ),
                ui.div(
                    output_widget("overview_trends_chart"),
                    class_="card-body"
                ),
                class_="card"
            ),
            ui.div(
                ui.div(
                    ui.div(
                        ui.h3("Enrollment Demographics", class_="card-title"),
                        ui.output_ui("demographic_focus_chip"),
                    ),
                    class_="card-header"
                ),
                ui.div(
                    output_widget("overview_demographics_chart"),
                    class_="card-body"
                ),
                class_="card"
            ),
            class_="chart-row"
        ),
        
        # Map and Benchmarking Row
        ui.div(
            ui.div(
                ui.div(
                    ui.h3("Geographic Distribution", class_="card-title"),
                    ui.div(
                        ui.input_radio_buttons(
                            "overview_map_metric",
                            None,
                            choices={
                                "yield_rate": "Yield Rate",
                                "enrolled_total": "Total Enrollment",
                                "admit_rate": "Admit Rate"
                            },
                            selected="yield_rate",
                            inline=True
                        ),
                        class_="chart-controls"
                    ),
                    class_="card-header"
                ),
                ui.div(
                    output_widget("overview_map"),
                    class_="card-body"
                ),
                class_="card"
            ),
            ui.div(
                ui.div(
                    ui.h3("Top Institutions", class_="card-title"),
                    ui.div(
                        ui.input_radio_buttons(
                            "overview_ranking_metric",
                            None,
                            choices={
                                "yield_rate": "By Yield",
                                "enrolled_total": "By Enrollment",
                                "admit_rate": "By Admit Rate"
                            },
                            selected="yield_rate",
                            inline=True
                        ),
                        class_="chart-controls"
                    ),
                    class_="card-header"
                ),
                ui.div(
                    output_widget("overview_ranking_chart"),
                    class_="card-body"
                ),
                class_="card"
            ),
            class_="chart-row"
        ),
        
        # Data Table Section
        ui.div(
            ui.div(
                ui.h3("Institution Data", class_="card-title"),
                ui.div(
                    ui.download_button("download_overview_data", "📥 Download CSV", class_="btn btn-secondary btn-sm"),
                ),
                class_="card-header"
            ),
            ui.div(
                ui.output_ui("overview_data_table"),
                class_="card-body"
            ),
            class_="card chart-section"
        ),
        
        class_="page-content"
    )


def overview_server(input, output, session, filtered_data, full_data, selected_years, 
                    selected_institution, latest_year):
    """Server logic for the Overview page."""
    
    # Reactive: Aggregate metrics with YoY
    @reactive.calc
    def overview_metrics():
        df = filtered_data()
        if df.empty:
            return {}
        
        year = latest_year()
        if year is None:
            year = df['year'].max()
        
        # Get YoY metrics
        yoy = get_yoy_metrics(df, year)
        
        # Calculate aggregate metrics directly from raw data
        # (raw data uses 'admissions' and 'enrolled_total' column names)
        year_df = df[df['year'] == year]
        
        if year_df.empty:
            return {}
        
        total_applicants = year_df['applicants'].sum()
        total_admitted = year_df['admissions'].sum()
        total_enrolled = year_df['enrolled_total'].sum()
        
        agg = {
            'year': year,
            'total_applicants': int(total_applicants),
            'total_admitted': int(total_admitted),
            'total_enrolled': int(total_enrolled),
            'admit_rate': round((total_admitted / total_applicants * 100), 1) if total_applicants > 0 else 0,
            'yield_rate': round((total_enrolled / total_admitted * 100), 1) if total_admitted > 0 else 0,
            'overall_conversion': round((total_enrolled / total_applicants * 100), 1) if total_applicants > 0 else 0,
            'institution_count': year_df['institution_name'].nunique(),
        }
        
        return {**agg, **yoy}
    
    # KPI Cards
    @render.ui
    def overview_kpi_cards():
        metrics = overview_metrics()
        if not metrics:
            return ui.div(class_="kpi-grid")
        
        cards = []
        
        # Applicants
        cards.append(create_kpi_card(
            label="Total Applicants",
            value=metrics.get('total_applicants', 0),
            delta=metrics.get('delta_applicants'),
            delta_type="percent",
            subtext=f"Year {metrics.get('year', '')}",
            card_type="applicants"
        ))
        
        # Admitted
        cards.append(create_kpi_card(
            label="Total Admitted",
            value=metrics.get('total_admitted', 0),
            delta=metrics.get('delta_admitted'),
            delta_type="percent",
            subtext="students admitted",
            card_type="admitted"
        ))
        
        # Enrolled
        cards.append(create_kpi_card(
            label="Total Enrolled",
            value=metrics.get('total_enrolled', 0),
            delta=metrics.get('delta_enrolled'),
            delta_type="percent",
            subtext="students enrolled",
            card_type="enrolled"
        ))
        
        # Yield Rate
        cards.append(create_kpi_card(
            label="Average Yield Rate",
            value=metrics.get('yield_rate', 0),
            delta=metrics.get('delta_yield_rate'),
            delta_type="pp",
            subtext="enrolled / admitted",
            card_type="yield"
        ))
        
        # Admit Rate
        cards.append(create_kpi_card(
            label="Average Admit Rate",
            value=metrics.get('admit_rate', 0),
            delta=metrics.get('delta_admit_rate'),
            delta_type="pp",
            subtext="admitted / applicants",
            card_type="admit"
        ))
        
        return ui.div(*cards, class_="kpi-grid")
    
    # Rankings (when institution selected)
    @render.ui
    def overview_rankings():
        inst = selected_institution()
        if not inst:
            return ui.div()
        
        df = full_data()
        year = latest_year()
        if year is None or df.empty:
            return ui.div()
        
        year_data = df[df['year'] == year]
        inst_data = year_data[year_data['institution_name'] == inst]
        
        if inst_data.empty:
            return ui.div()
        
        inst_row = inst_data.iloc[0]
        
        # Calculate rankings for each metric
        rankings = []
        metrics = [
            ('applicants', 'Applicants'),
            ('admissions', 'Admitted'),
            ('enrolled_total', 'Enrolled'),
            ('yield_rate', 'Yield Rate'),
        ]
        
        for col, label in metrics:
            if col not in year_data.columns:
                continue
            
            rank_info = calculate_rank_and_percentile(
                inst_row[col],
                year_data[col]
            )
            
            rankings.append(ui.div(
                ui.div(label, class_="ranking-metric"),
                ui.div(f"#{rank_info['rank']}", class_="ranking-value"),
                ui.div(f"of {rank_info['total']} ({rank_info['percentile']:.0f}th pctl)", class_="ranking-percentile"),
                class_="ranking-card"
            ))
        
        return ui.div(
            ui.div(
                ui.h3(f"Rankings: {inst[:40]}...", class_="card-title") if len(inst) > 40 else ui.h3(f"Rankings: {inst}", class_="card-title"),
                class_="card-header"
            ),
            ui.div(
                ui.div(*rankings, class_="rankings-grid"),
                class_="card-body"
            ),
            class_="card chart-section"
        )
    
    # Insights Panel
    @render.ui
    def overview_insights_panel():
        inst = selected_institution()
        if not inst:
            return ui.div()
        
        # Generate insights for selected institution
        from utils.metrics import generate_insights
        
        df = full_data()
        year = latest_year()
        if year is None or df.empty:
            return ui.div()
        
        year_data = df[df['year'] == year]
        inst_data = year_data[year_data['institution_name'] == inst]
        
        if inst_data.empty:
            # Institution not found in data for this year
            return create_insights_panel([], inst, no_data=True)
        
        inst_row = inst_data.iloc[0].to_dict()
        
        # Calculate peer percentiles
        peer_percentiles = {}
        for metric in ['yield_rate', 'admit_rate', 'diversity_index']:
            if metric in year_data.columns:
                values = year_data[metric].dropna()
                if not values.empty:
                    peer_percentiles[metric] = {
                        'p25': values.quantile(0.25),
                        'p50': values.quantile(0.50),
                        'p75': values.quantile(0.75),
                    }
        
        # Get YoY metrics for this specific institution
        inst_df = df[df['institution_name'] == inst]
        yoy = get_yoy_metrics(inst_df, year) if not inst_df.empty else {}
        
        insights = generate_insights(inst_row, peer_percentiles, yoy)
        
        # If no insights generated, provide a fallback message
        if not insights:
            return create_insights_panel([], inst, no_data=False)
        
        return create_insights_panel(insights, inst)
    
    # Funnel Chart
    @render_widget
    def overview_funnel_chart():
        df = filtered_data()
        if df.empty:
            return create_funnel_chart(0, 0, 0)
        
        applicants = df['applicants'].sum()
        admitted = df['admissions'].sum()
        enrolled = df['enrolled_total'].sum()
        
        return create_funnel_chart(applicants, admitted, enrolled)
    
    # Trends Chart
    @render_widget
    def overview_trends_chart():
        df = filtered_data()
        if df.empty:
            return create_trends_chart(pd.DataFrame({'year': [], 'admit_rate': [], 'yield_rate': []}))
        
        # Aggregate by year
        yearly = df.groupby('year').agg({
            'applicants': 'sum',
            'admissions': 'sum',
            'enrolled_total': 'sum',
        }).reset_index()
        
        yearly['admit_rate'] = (yearly['admissions'] / yearly['applicants'] * 100).round(1)
        yearly['yield_rate'] = (yearly['enrolled_total'] / yearly['admissions'] * 100).round(1)
        yearly['overall_rate'] = (yearly['enrolled_total'] / yearly['applicants'] * 100).round(1)
        
        return create_trends_chart(yearly)
    
    # Demographics Chart
    @render_widget
    def overview_demographics_chart():
        df = filtered_data()
        if df.empty:
            return create_demographics_chart(pd.DataFrame())
        
        # Aggregate demographics by year (weighted by enrollment)
        demo_cols = ['pct_hispanic', 'pct_white', 'pct_black', 'pct_asian', 'pct_other']
        
        results = []
        for year in sorted(df['year'].unique()):
            year_df = df[df['year'] == year]
            total_enrolled = year_df['enrolled_total'].sum()
            
            if total_enrolled > 0:
                row = {'year': year}
                for col in demo_cols:
                    if col in year_df.columns:
                        weighted_avg = (year_df[col] * year_df['enrolled_total']).sum() / total_enrolled
                        row[col] = round(weighted_avg, 1)
                results.append(row)
        
        demo_df = pd.DataFrame(results)
        return create_demographics_chart(demo_df)
    
    # Demographic focus chip
    @render.ui
    def demographic_focus_chip():
        # Placeholder for demographic focus feature
        return ui.span()
    
    # Geographic Map
    @render_widget
    def overview_map():
        df = filtered_data()
        metric = input.overview_map_metric()
        
        if df.empty:
            return create_state_map(pd.DataFrame(), metric)
        
        return create_state_map(df, metric)
    
    # Ranking Chart
    @render_widget
    def overview_ranking_chart():
        df = filtered_data()
        metric = input.overview_ranking_metric()
        
        if df.empty:
            return create_comparison_bar_chart(pd.DataFrame(), metric)
        
        # Aggregate by institution
        agg_df = df.groupby('institution_name').agg({
            'applicants': 'sum',
            'admissions': 'sum',
            'enrolled_total': 'sum',
        }).reset_index()
        
        agg_df['admit_rate'] = (agg_df['admissions'] / agg_df['applicants'] * 100).round(1)
        agg_df['yield_rate'] = (agg_df['enrolled_total'] / agg_df['admissions'] * 100).round(1)
        
        # Filter out very small institutions
        agg_df = agg_df[agg_df['enrolled_total'] >= 50]
        
        inst = selected_institution()
        
        return create_comparison_bar_chart(
            agg_df, 
            metric, 
            n=10,
            highlight_institution=inst
        )
    
    # Data Table
    @render.ui
    def overview_data_table():
        df = filtered_data()
        if df.empty:
            return create_data_table(pd.DataFrame())
        
        # Aggregate by institution for the latest year
        year = latest_year()
        if year:
            display_df = df[df['year'] == year].copy()
        else:
            display_df = df.copy()
        
        # Select and rename columns
        columns = ['institution_name', 'year', 'applicants', 'admissions', 'enrolled_total',
                   'admit_rate', 'yield_rate', 'state', 'region', 'institution_size']
        columns = [c for c in columns if c in display_df.columns]
        
        display_df = display_df[columns].sort_values('enrolled_total', ascending=False)
        
        return create_data_table(
            display_df,
            columns=columns,
            column_labels={
                'admissions': 'Admitted',
                'enrolled_total': 'Enrolled',
            }
        )
    
    # Download handler
    @render.download(filename="enrollment_data.csv")
    def download_overview_data():
        df = filtered_data()
        yield df.to_csv(index=False)
