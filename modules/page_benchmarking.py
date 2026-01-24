"""
Institutional Benchmarking page module.
Provides peer group comparison, distribution analysis, and context mapping.
"""

from shiny import ui, reactive, render, module
from shinywidgets import output_widget, render_widget
import pandas as pd
import numpy as np

from .components_kpis import create_kpi_card
from .components_charts import (
    create_distribution_chart,
    create_scatter_chart,
    create_comparison_bar_chart,
)
from .components_tables import create_peer_table
from utils.metrics import (
    calculate_percentiles,
    calculate_rank_and_percentile,
    find_similar_institutions_simple,
)
from utils.data_model import get_peer_group, calculate_peer_statistics


def benchmarking_ui():
    """Create the Benchmarking page UI."""
    return ui.div(
        ui.div(
            # Left sidebar with controls
            ui.div(
                ui.div(
                    ui.h3("Benchmarking Controls", class_="card-title"),
                    class_="card-header"
                ),
                ui.div(
                    # Target Institution
                    ui.div(
                        ui.div("Target Institution", class_="filter-label"),
                        ui.output_ui("bench_target_selector"),
                        class_="filter-group",
                        style="margin-bottom: 16px;"
                    ),
                    
                    # Peer Group Definition
                    ui.div(
                        ui.div("Peer Group", class_="filter-label"),
                        ui.input_select(
                            "bench_peer_type",
                            None,
                            choices={
                                "national": "🌎 National (All)",
                                "same_region": "📍 Same Region",
                                "same_state": "🏛️ Same State",
                                "same_size": "📊 Same Size Band",
                                "top_n_applicants": "🏆 Top N by Applicants",
                                "similar": "🔗 Similar Institutions (kNN)",
                            },
                            selected="national"
                        ),
                        class_="filter-group",
                        style="margin-bottom: 16px;"
                    ),
                    
                    # N slider (for top_n and similar)
                    ui.output_ui("bench_n_slider"),
                    
                    # Metric Focus
                    ui.div(
                        ui.div("Metric Focus", class_="filter-label"),
                        ui.input_select(
                            "bench_metric",
                            None,
                            choices={
                                "yield_rate": "Yield Rate",
                                "admit_rate": "Admit Rate",
                                "enrolled_total": "Total Enrolled",
                                "applicants": "Applicants",
                            },
                            selected="yield_rate"
                        ),
                        class_="filter-group",
                        style="margin-bottom: 16px;"
                    ),
                    
                    # Year Focus
                    ui.div(
                        ui.div("Year", class_="filter-label"),
                        ui.output_ui("bench_year_selector"),
                        class_="filter-group"
                    ),
                    
                    class_="card-body"
                ),
                class_="card",
                style="position: sticky; top: 140px;"
            ),
            style="width: 280px; flex-shrink: 0;"
        ),
        
        # Main content area
        ui.div(
            # Page header with Export PDF button
            ui.div(
                ui.h2("Institutional Benchmarking", class_="section-title", style="margin: 0;"),
                ui.tags.button(
                    "📄 Export PDF",
                    onclick="exportPageAsPDF()",
                    class_="btn-export-pdf"
                ),
                style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;"
            ),
            
            # Benchmark KPI Cards
            ui.output_ui("bench_kpi_cards"),
            
            # Distribution Chart
            ui.div(
                ui.div(
                    ui.h3("Peer Group Distribution", class_="card-title"),
                    ui.output_ui("bench_distribution_info"),
                    class_="card-header"
                ),
                ui.div(
                    output_widget("bench_distribution_chart"),
                    class_="card-body"
                ),
                class_="card chart-section"
            ),
            
            # Scatter Plot Context Map
            ui.div(
                ui.div(
                    ui.h3("Context Map", class_="card-title"),
                    ui.p("Click on any point to add to comparison", class_="section-subtitle", style="margin: 0;"),
                    class_="card-header"
                ),
                ui.div(
                    output_widget("bench_scatter_chart"),
                    class_="card-body"
                ),
                class_="card chart-section"
            ),
            
            # Peer Table
            ui.div(
                ui.div(
                    ui.h3("Peer Institutions", class_="card-title"),
                    ui.download_button("download_peer_data", "📥 Download", class_="btn btn-secondary btn-sm"),
                    class_="card-header"
                ),
                ui.div(
                    ui.output_ui("bench_peer_table"),
                    class_="card-body"
                ),
                class_="card chart-section"
            ),
            
            style="flex: 1; min-width: 0;"
        ),
        
        class_="page-content",
        style="display: flex; gap: 24px; align-items: flex-start;"
    )


def benchmarking_server(input, output, session, filtered_data, full_data, 
                        selected_years, selected_institution, latest_year, institutions_list,
                        current_page=None):
    """Server logic for the Benchmarking page."""
    
    def is_active():
        """Check if this page is currently active."""
        if current_page is None:
            return True
        return current_page.get() == "benchmarking"
    
    # Target institution selector
    @render.ui
    def bench_target_selector():
        inst = selected_institution()
        return ui.input_selectize(
            "bench_target",
            None,
            choices=[""] + institutions_list,
            selected=inst if inst else "",
            options={"placeholder": "Select institution..."}
        )
    
    # Year selector
    @render.ui
    def bench_year_selector():
        years = selected_years()
        if not years:
            years = [2024, 2023, 2022]
        
        year = latest_year() or max(years)
        
        return ui.input_select(
            "bench_year",
            None,
            choices={str(y): str(y) for y in sorted(years, reverse=True)},
            selected=str(year)
        )
    
    # N slider for top_n and similar
    @render.ui
    def bench_n_slider():
        peer_type = input.bench_peer_type()
        if peer_type in ['top_n_applicants', 'similar']:
            return ui.div(
                ui.div("Number of Peers", class_="filter-label"),
                ui.input_slider(
                    "bench_n",
                    None,
                    min=5,
                    max=50,
                    value=15 if peer_type == 'similar' else 25,
                    step=5
                ),
                class_="filter-group",
                style="margin-bottom: 16px;"
            )
        return ui.div()
    
    # Reactive: Get target institution data
    @reactive.calc
    def target_data():
        target = input.bench_target()
        if not target:
            return None
        
        df = full_data()
        year = int(input.bench_year()) if input.bench_year() else latest_year()
        
        if year is None:
            return None
        
        target_df = df[(df['institution_name'] == target) & (df['year'] == year)]
        if target_df.empty:
            return None
        
        return target_df.iloc[0].to_dict()
    
    # Reactive: Get peer group
    @reactive.calc
    def peer_group():
        df = full_data()
        target = input.bench_target()
        year = int(input.bench_year()) if input.bench_year() else latest_year()
        peer_type = input.bench_peer_type()
        
        if df.empty or year is None:
            return pd.DataFrame()
        
        # Get N for applicable peer types
        n = input.bench_n() if peer_type in ['top_n_applicants', 'similar'] else 25
        
        # For similar institutions, calculate them first
        similar_df = None
        if peer_type == 'similar' and target:
            similar_df = find_similar_institutions_simple(df, target, year, k=n)
        
        # Create a facts-like dataframe
        year_data = df[df['year'] == year].copy()
        year_data = year_data.rename(columns={
            'admissions': 'admitted',
            'enrolled_total': 'enrolled'
        })
        
        # Apply peer group filter
        if peer_type == 'national':
            peers = year_data
        elif peer_type == 'same_region' and target:
            target_row = year_data[year_data['institution_name'] == target]
            if not target_row.empty:
                region = target_row.iloc[0]['region']
                peers = year_data[year_data['region'] == region]
            else:
                peers = year_data
        elif peer_type == 'same_state' and target:
            target_row = year_data[year_data['institution_name'] == target]
            if not target_row.empty:
                state = target_row.iloc[0]['state']
                peers = year_data[year_data['state'] == state]
            else:
                peers = year_data
        elif peer_type == 'same_size' and target:
            target_row = year_data[year_data['institution_name'] == target]
            if not target_row.empty:
                size = target_row.iloc[0]['institution_size']
                peers = year_data[year_data['institution_size'] == size]
            else:
                peers = year_data
        elif peer_type == 'top_n_applicants':
            peers = year_data.nlargest(n, 'applicants')
            # Ensure target institution is included for ranking purposes
            if target and target not in peers['institution_name'].values:
                target_row = year_data[year_data['institution_name'] == target]
                if not target_row.empty:
                    peers = pd.concat([peers, target_row], ignore_index=True)
        elif peer_type == 'similar' and similar_df is not None and not similar_df.empty:
            similar_names = similar_df['institution_name'].tolist()
            if target:
                similar_names.append(target)
            peers = year_data[year_data['institution_name'].isin(similar_names)]
        else:
            peers = year_data
        
        # Always ensure target institution is included in peers for proper ranking display
        if target and target not in peers['institution_name'].values:
            target_row = year_data[year_data['institution_name'] == target]
            if not target_row.empty:
                peers = pd.concat([peers, target_row], ignore_index=True)
        
        return peers
    
    # Reactive: Peer statistics
    @reactive.calc
    def peer_stats():
        peers = peer_group()
        metric = input.bench_metric()
        
        if peers.empty:
            return {}
        
        # Map metric names
        metric_col = metric
        if metric == 'enrolled_total':
            metric_col = 'enrolled' if 'enrolled' in peers.columns else 'enrolled_total'
        
        if metric_col not in peers.columns:
            return {}
        
        values = peers[metric_col].dropna()
        
        return {
            'mean': round(values.mean(), 2),
            'median': round(values.median(), 2),
            'p25': round(values.quantile(0.25), 2),
            'p75': round(values.quantile(0.75), 2),
            'p10': round(values.quantile(0.10), 2),
            'p90': round(values.quantile(0.90), 2),
            'min': round(values.min(), 2),
            'max': round(values.max(), 2),
            'count': len(values),
        }
    
    # KPI Cards
    @render.ui
    def bench_kpi_cards():
        target = target_data()
        stats = peer_stats()
        metric = input.bench_metric()
        
        if not stats:
            return ui.div(
                ui.p("Select a target institution and peer group to see benchmarks",
                     style="color: var(--color-text-muted); text-align: center; padding: 24px;"),
                class_="kpi-grid"
            )
        
        # Get target value
        metric_col = metric
        if metric == 'enrolled_total':
            metric_col = 'enrolled_total'
        
        target_value = target.get(metric_col, 0) if target else None
        
        # Calculate delta vs median
        delta_vs_median = None
        if target_value is not None and stats.get('median'):
            if 'rate' in metric:
                delta_vs_median = target_value - stats['median']
            else:
                delta_vs_median = ((target_value - stats['median']) / stats['median']) * 100 if stats['median'] > 0 else 0
        
        # Calculate percentile
        percentile = None
        if target_value is not None:
            peers = peer_group()
            if not peers.empty and metric_col in peers.columns:
                values = peers[metric_col].dropna()
                percentile = (values < target_value).sum() / len(values) * 100
        
        cards = []
        
        # Target Value
        if target_value is not None:
            is_rate = 'rate' in metric
            cards.append(create_kpi_card(
                label="Target Value",
                value=f"{target_value:.1f}%" if is_rate else target_value,
                delta=None,
                subtext=input.bench_target()[:30] if input.bench_target() else "",
                card_type="yield" if 'yield' in metric else "admit" if 'admit' in metric else "enrolled"
            ))
        
        # Peer Median
        cards.append(create_kpi_card(
            label="Peer Median (p50)",
            value=f"{stats['median']:.1f}%" if 'rate' in metric else int(stats['median']),
            delta=None,
            subtext=f"n={stats['count']} institutions",
            card_type="default"
        ))
        
        # Peer p75
        cards.append(create_kpi_card(
            label="Peer 75th Percentile",
            value=f"{stats['p75']:.1f}%" if 'rate' in metric else int(stats['p75']),
            delta=None,
            subtext="Top quartile threshold",
            card_type="default"
        ))
        
        # Delta vs Median
        if delta_vs_median is not None:
            delta_label = "pp" if 'rate' in metric else "%"
            cards.append(create_kpi_card(
                label="Delta vs Median",
                value=f"{delta_vs_median:+.1f}{delta_label}",
                delta=delta_vs_median,
                delta_type="pp" if 'rate' in metric else "percent",
                subtext="vs peer median",
                card_type="default"
            ))
        
        # Percentile
        if percentile is not None:
            cards.append(create_kpi_card(
                label="Percentile Rank",
                value=f"{percentile:.0f}th",
                delta=None,
                subtext="within peer group",
                card_type="default"
            ))
        
        return ui.div(*cards, class_="kpi-grid")
    
    # Distribution info
    @render.ui
    def bench_distribution_info():
        stats = peer_stats()
        if not stats:
            return ui.span()
        
        return ui.span(
            f"{stats['count']} institutions in peer group",
            class_="badge badge-info"
        )
    
    # Distribution Chart
    @render_widget
    def bench_distribution_chart():
        if not is_active():
            return create_distribution_chart(pd.Series([]))
        peers = peer_group()
        target = target_data()
        metric = input.bench_metric()
        
        if peers.empty:
            return create_distribution_chart(pd.Series([]))
        
        # Map metric names
        metric_col = metric
        if metric == 'enrolled_total':
            metric_col = 'enrolled' if 'enrolled' in peers.columns else 'enrolled_total'
        
        if metric_col not in peers.columns:
            return create_distribution_chart(pd.Series([]))
        
        values = peers[metric_col].dropna()
        
        target_value = None
        target_name = None
        if target:
            target_value = target.get(metric_col)
            target_name = input.bench_target()
        
        metric_labels = {
            'yield_rate': 'Yield Rate (%)',
            'admit_rate': 'Admit Rate (%)',
            'enrolled_total': 'Total Enrolled',
            'enrolled': 'Total Enrolled',
            'applicants': 'Applicants',
        }
        
        return create_distribution_chart(
            values,
            target_value=target_value,
            target_name=target_name,
            metric_name=metric_labels.get(metric, metric),
            chart_type='box'
        )
    
    # Scatter Chart
    @render_widget
    def bench_scatter_chart():
        if not is_active():
            return create_scatter_chart(pd.DataFrame(), 'applicants', 'yield_rate')
        peers = peer_group()
        target = input.bench_target()
        
        if peers.empty:
            return create_scatter_chart(pd.DataFrame(), 'applicants', 'yield_rate')
        
        # Ensure we have the right columns
        if 'enrolled' not in peers.columns and 'enrolled_total' in peers.columns:
            peers = peers.copy()
            peers['enrolled'] = peers['enrolled_total']
        
        return create_scatter_chart(
            peers,
            x_col='applicants',
            y_col='yield_rate',
            color_col='region',
            size_col='enrolled',
            target_institution=target,
            x_label='Applicants',
            y_label='Yield Rate (%)'
        )
    
    # Peer Table
    @render.ui
    def bench_peer_table():
        peers = peer_group()
        target = input.bench_target()
        metric = input.bench_metric()
        
        if peers.empty:
            return ui.p("No peer data available", 
                       style="color: var(--color-text-muted); text-align: center; padding: 24px;")
        
        # Map metric names
        metric_col = metric
        if metric == 'enrolled_total':
            metric_col = 'enrolled' if 'enrolled' in peers.columns else 'enrolled_total'
        
        return create_peer_table(
            peers,
            target_institution=target,
            metric=metric_col
        )
    
    # Download handler
    @render.download(filename="peer_comparison.csv")
    def download_peer_data():
        peers = peer_group()
        yield peers.to_csv(index=False)
