"""
AI Insights page module for the enrollment dashboard.
Provides LLM-powered natural language analytics using OpenAI gpt-5-mini.
"""

from shiny import ui, reactive, render
from shinywidgets import output_widget, render_widget
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from .components_charts import COLORS, CHART_PALETTE, LAYOUT_DEFAULTS
from utils.llm_client import (
    is_api_key_configured,
    get_data_schema_description,
    generate_ai_insight,
    AIInsightResponse
)

DERIVED_GROWTH_PCT = "enrollment_growth_pct"
DERIVED_GROWTH_ABS = "enrollment_growth_abs"


def ai_insights_ui():
    """Create the AI Insights page UI."""
    return ui.div(
        # Page header
        ui.div(
            ui.h2("AI Insights", class_="section-title", style="margin: 0;"),
            ui.p("Ask questions about enrollment data in natural language and get AI-generated insights with visualizations", 
                 class_="section-subtitle"),
            style="margin-bottom: 24px;"
        ),
        
        # Prompt input section with example buttons above
        ui.div(
            ui.div(
                ui.h3("Ask Your Data", class_="card-title"),
                class_="card-header"
            ),
            ui.div(
                # Example query buttons (above the input)
                ui.div(
                    _create_example_button("example_1", "Show me the large institutions that had the biggest enrollment growth in 2024, and highlight any important patterns across regions or segments."),
                    _create_example_button("example_2", "Which institutions in the South grew the most in enrollment between 2023 and 2024?"),
                    _create_example_button("example_3", "Explain the main drivers behind enrollment changes for large universities in 2024."),
                    _create_example_button("example_4", "Compare Stanford to its peer institutions and show how their yield rates differ."),
                    _create_example_button("example_5", "Which universities had unusually high admit rates in 2024? Show a ranked list."),
                    style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px;"
                ),
                # Text input
                ui.input_text_area(
                    "ai_prompt",
                    label=None,
                    placeholder="Type your question about enrollment data here...",
                    rows=3,
                    width="100%"
                ),
                ui.div(
                    ui.input_action_button(
                        "ai_generate",
                        "✨ Generate Insight",
                        class_="btn btn-primary",
                        style="background: linear-gradient(135deg, #0F172A 0%, #2563EB 100%); border: none; padding: 10px 24px; font-weight: 500;"
                    ),
                    ui.span(
                        ui.output_text("ai_loading_status"),
                        style="margin-left: 40px; color: #64748B; font-size: 13px;"
                    ),
                    style="margin-top: 12px; display: flex; align-items: center;"
                ),
                class_="card-body"
            ),
            class_="card chart-section"
        ),
        
        # Results section (hidden until results are available)
        ui.output_ui("ai_results_section"),
        
        class_="page-content"
    )


def _create_example_button(id: str, text: str) -> ui.Tag:
    """Create a clickable example query button."""
    return ui.input_action_button(
        id,
        text,
        class_="example-query-btn",
        style="""
            background: #F1F5F9;
            color: #475569;
            padding: 8px 14px;
            border-radius: 20px;
            font-size: 13px;
            cursor: pointer;
            display: inline-block;
            border: 1px solid #E2E8F0;
            transition: all 0.2s ease;
        """
    )


def ai_insights_server(
    input, output, session,
    filtered_data,
    full_data,
    years_list,
    regions_list,
    sizes_list,
    institutions_list,
    current_page=None
):
    """Server logic for the AI Insights page."""
    
    # Store the last AI response
    ai_response = reactive.value(None)
    is_loading = reactive.value(False)
    
    def is_active():
        """Check if this page is currently active."""
        if current_page is None:
            return True
        return current_page.get() == "ai_insights"
    
    # Example query button handlers
    EXAMPLE_QUERIES = {
        "example_1": "Show me the large institutions that had the biggest enrollment growth in 2024, and highlight any important patterns across regions or segments.",
        "example_2": "Which institutions in the South grew the most in enrollment between 2023 and 2024?",
        "example_3": "Explain the main drivers behind enrollment changes for large universities in 2024.",
        "example_4": "Compare Stanford to its peer institutions and show how their yield rates differ.",
        "example_5": "Which universities had unusually high admit rates in 2024? Show a ranked list.",
    }
    
    @reactive.effect
    @reactive.event(input.example_1)
    def _set_example_1():
        ui.update_text_area("ai_prompt", value=EXAMPLE_QUERIES["example_1"])
    
    @reactive.effect
    @reactive.event(input.example_2)
    def _set_example_2():
        ui.update_text_area("ai_prompt", value=EXAMPLE_QUERIES["example_2"])
    
    @reactive.effect
    @reactive.event(input.example_3)
    def _set_example_3():
        ui.update_text_area("ai_prompt", value=EXAMPLE_QUERIES["example_3"])
    
    @reactive.effect
    @reactive.event(input.example_4)
    def _set_example_4():
        ui.update_text_area("ai_prompt", value=EXAMPLE_QUERIES["example_4"])
    
    @reactive.effect
    @reactive.event(input.example_5)
    def _set_example_5():
        ui.update_text_area("ai_prompt", value=EXAMPLE_QUERIES["example_5"])
    
    # Loading status text
    @render.text
    def ai_loading_status():
        if is_loading.get():
            return "Analyzing your question..."
        return ""
    
    # Generate insight when button is clicked
    @reactive.effect
    @reactive.event(input.ai_generate)
    def handle_generate():
        prompt = input.ai_prompt()
        
        # Validate prompt
        if not prompt or len(prompt.strip()) < 3:
            ai_response.set(AIInsightResponse(
                summary_text="",
                filters={},
                chart={},
                error="Please enter a question about the enrollment data."
            ))
            return
        
        is_loading.set(True)
        
        try:
            # Build data schema description
            df = full_data()
            
            # Calculate aggregate statistics for key metrics
            stats = {}
            for col in ['yield_rate', 'admit_rate', 'applicants', 'enrolled_total']:
                if col in df.columns:
                    stats[col] = {
                        'min': df[col].min(),
                        'max': df[col].max(),
                        'avg': df[col].mean()
                    }
            
            # Get sample institutions
            sample_institutions = sorted(df['institution_name'].unique())[:15]
            
            # Build schema description
            data_schema = get_data_schema_description(
                columns=list(df.columns),
                years=years_list,
                regions=regions_list,
                sizes=sizes_list,
                sample_institutions=sample_institutions,
                stats=stats
            )
            
            # Generate AI insight
            response = generate_ai_insight(prompt.strip(), data_schema)
            ai_response.set(response)
            
        except Exception as e:
            ai_response.set(AIInsightResponse(
                summary_text="",
                filters={},
                chart={},
                error=f"An error occurred: {str(e)[:100]}"
            ))
        finally:
            is_loading.set(False)
    
    # Render results section
    @render.ui
    def ai_results_section():
        response = ai_response.get()
        
        if response is None:
            return ui.div()
        
        if response.error:
            return ui.div(
                ui.div(
                    ui.div(
                        ui.h3("Response", class_="card-title"),
                        class_="card-header"
                    ),
                    ui.div(
                        ui.div(
                            ui.tags.span("⚠️ ", style="font-size: 16px;"),
                            response.error,
                            style="background: #FEF2F2; color: #991B1B; padding: 16px; border-radius: 6px; font-size: 14px;"
                        ),
                        class_="card-body"
                    ),
                    class_="card chart-section"
                ),
                style="margin-top: 24px;"
            )
        
        return ui.div(
            # Summary text card
            ui.div(
                ui.div(
                    ui.h3("AI Analysis", class_="card-title"),
                    class_="card-header"
                ),
                ui.div(
                    ui.div(
                        ui.p(
                            response.summary_text,
                            style="font-size: 15px; line-height: 1.6; color: #1E293B; margin: 0;"
                        ),
                        style="background: linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 100%); padding: 20px; border-radius: 8px; border-left: 4px solid #2563EB;"
                    ),
                    # Show applied filters if any
                    ui.output_ui("ai_filters_summary"),
                    class_="card-body"
                ),
                class_="card chart-section"
            ),
            
            # Chart card
            ui.div(
                ui.div(
                    ui.h3("Visualization", class_="card-title"),
                    class_="card-header"
                ),
                ui.div(
                    output_widget("ai_insight_chart"),
                    class_="card-body"
                ),
                class_="card chart-section"
            ),
            style="margin-top: 24px;"
        )
    
    # Render filters summary
    @render.ui
    def ai_filters_summary():
        response = ai_response.get()
        if response is None or response.error or not response.filters:
            return ui.div()
        
        filters = response.filters
        filter_parts = []
        
        if 'year' in filters:
            filter_parts.append(f"Year: {filters['year']}")
        if 'regions' in filters and filters['regions']:
            filter_parts.append(f"Regions: {', '.join(filters['regions'])}")
        if 'sizes' in filters and filters['sizes']:
            filter_parts.append(f"Sizes: {', '.join(filters['sizes'])}")
        if 'institutions' in filters and filters['institutions']:
            inst_list = filters['institutions'][:3]
            if len(filters['institutions']) > 3:
                inst_list.append(f"+{len(filters['institutions']) - 3} more")
            filter_parts.append(f"Institutions: {', '.join(inst_list)}")
        
        if not filter_parts:
            return ui.div()
        
        return ui.div(
            ui.tags.span("Filters applied: ", style="font-weight: 600; color: #475569;"),
            " | ".join(filter_parts),
            style="margin-top: 12px; font-size: 12px; color: #64748B;"
        )
    
    # Render the AI-generated chart
    @render_widget
    def ai_insight_chart():
        if not is_active():
            return _create_empty_chart("Navigate to AI Insights to view chart")
        
        response = ai_response.get()
        if response is None or response.error:
            return _create_empty_chart("Generate an insight to see visualization")
        
        chart_spec = response.chart
        filters = response.filters
        
        # Generate chart based on specification
        chart_type = chart_spec.get('type', 'bar')
        x_col = chart_spec.get('x', 'institution_name')
        y_col = chart_spec.get('y', 'yield_rate')
        sort_order = chart_spec.get('sort', 'desc')
        top_n = chart_spec.get('top_n', 10)
        color_col = chart_spec.get('color')

        try:
            if y_col in {DERIVED_GROWTH_PCT, DERIVED_GROWTH_ABS}:
                df = full_data()
                df = _apply_ai_filters(df, _drop_year_filter(filters))
                if df.empty:
                    return _create_empty_chart("No data matches the specified filters")
                return _create_enrollment_growth_chart(
                    df,
                    y_col=y_col,
                    sort_order=sort_order,
                    top_n=top_n,
                    color_col=color_col,
                    target_year=filters.get("year")
                )

            # Get and filter data for standard charts
            df = full_data()
            df = _apply_ai_filters(df, filters)
            
            if df.empty:
                return _create_empty_chart("No data matches the specified filters")

            if chart_type == 'bar':
                return _create_ai_bar_chart(df, x_col, y_col, sort_order, top_n, color_col)
            elif chart_type == 'line':
                return _create_ai_line_chart(df, x_col, y_col, color_col)
            elif chart_type == 'scatter':
                return _create_ai_scatter_chart(df, x_col, y_col, color_col)
            else:
                return _create_ai_bar_chart(df, x_col, y_col, sort_order, top_n, color_col)
        except Exception as e:
            return _create_empty_chart(f"Error creating chart: {str(e)[:50]}")


def _apply_ai_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """Apply AI-specified filters to the dataframe."""
    if not filters:
        return df
    
    # Year filter
    if 'year' in filters and filters['year']:
        year = filters['year']
        if isinstance(year, int):
            df = df[df['year'] == year]
        elif isinstance(year, list) and year:
            df = df[df['year'].isin(year)]
    
    # Region filter
    if 'regions' in filters and filters['regions']:
        regions = filters['regions']
        if isinstance(regions, list) and regions:
            df = df[df['region'].isin(regions)]
    
    # Size filter
    if 'sizes' in filters and filters['sizes']:
        sizes = filters['sizes']
        if isinstance(sizes, list) and sizes:
            df = df[df['institution_size'].isin(sizes)]
    
    # Institution filter
    if 'institutions' in filters and filters['institutions']:
        institutions = filters['institutions']
        if isinstance(institutions, list) and institutions:
            df = df[df['institution_name'].isin(institutions)]
    
    return df


def _drop_year_filter(filters: dict) -> dict:
    """Remove year filter for derived metrics that require prior-year data."""
    if not filters:
        return {}
    return {key: value for key, value in filters.items() if key != "year"}


def _create_empty_chart(message: str) -> go.Figure:
    """Create an empty chart with a message."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=14, color=COLORS['muted'])
    )
    fig.update_layout(
        **LAYOUT_DEFAULTS,
        height=350,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )
    return fig


def _create_enrollment_growth_chart(
    df: pd.DataFrame,
    y_col: str,
    sort_order: str = 'desc',
    top_n: int = 10,
    color_col: str = None,
    target_year: int = None
) -> go.Figure:
    """Create a bar chart for enrollment growth between years."""
    if 'year' not in df.columns or 'enrolled_total' not in df.columns:
        return _create_empty_chart("Enrollment growth requires year and enrolled_total data")

    year = None
    if isinstance(target_year, int):
        year = target_year
    elif isinstance(target_year, list) and target_year:
        year = max([y for y in target_year if isinstance(y, int)], default=None)

    if year is None:
        year = int(df['year'].max())

    prev_year = year - 1
    df = df[df['year'].isin([prev_year, year])]
    if df.empty:
        return _create_empty_chart(f"No data found for {prev_year} and {year}")

    meta_cols = {}
    for col in ['region', 'institution_size', 'state']:
        if col in df.columns:
            meta_cols[col] = 'first'

    agg_cols = {'enrolled_total': 'sum'}
    if meta_cols:
        agg_cols.update(meta_cols)

    agg_df = df.groupby(['institution_name', 'year']).agg(agg_cols).reset_index()
    pivot = agg_df.pivot(index='institution_name', columns='year', values='enrolled_total')
    if prev_year not in pivot.columns or year not in pivot.columns:
        return _create_empty_chart(f"Missing enrollment totals for {prev_year} or {year}")
    pivot = pivot.dropna(subset=[prev_year, year], how='any').reset_index()

    if pivot.empty:
        return _create_empty_chart(f"Not enough data to compute growth for {prev_year} → {year}")

    pivot['enrollment_growth_abs'] = pivot[year] - pivot[prev_year]
    pivot['enrollment_growth_pct'] = (pivot['enrollment_growth_abs'] / pivot[prev_year]) * 100
    pivot['enrolled_prev'] = pivot[prev_year]
    pivot['enrolled_curr'] = pivot[year]

    if meta_cols:
        meta_df = df.groupby('institution_name').agg(meta_cols).reset_index()
        pivot = pivot.merge(meta_df, on='institution_name', how='left')

    plot_df = pivot.sort_values(y_col, ascending=sort_order != 'desc')
    if top_n and len(plot_df) > top_n:
        plot_df = plot_df.head(top_n) if sort_order == 'desc' else plot_df.tail(top_n)

    color_col = color_col if color_col in plot_df.columns else None
    text_fmt = "{:.1f}%" if y_col == DERIVED_GROWTH_PCT else "{:,.0f}"
    hover_template = (
        f"<b>%{{y}}</b>"
        f"<br>Enrollment {prev_year}: %{{customdata[0]:,.0f}}"
        f"<br>Enrollment {year}: %{{customdata[1]:,.0f}}"
        f"<br>Change: %{{customdata[2]:+,.0f}}"
        f"<br>Growth: %{{customdata[3]:.1f}}%<extra></extra>"
    )

    if color_col:
        fig = px.bar(
            plot_df,
            x=y_col,
            y='institution_name',
            color=color_col,
            orientation='h',
            color_discrete_sequence=CHART_PALETTE,
            custom_data=['enrolled_prev', 'enrolled_curr', 'enrollment_growth_abs', 'enrollment_growth_pct'],
            text=plot_df[y_col].apply(lambda x: text_fmt.format(x))
        )
        fig.update_traces(hovertemplate=hover_template, textposition='outside')
    else:
        fig = go.Figure(go.Bar(
            x=plot_df[y_col],
            y=plot_df['institution_name'],
            orientation='h',
            marker_color=COLORS['accent'],
            text=plot_df[y_col].apply(lambda x: text_fmt.format(x)),
            textposition='outside',
            customdata=plot_df[['enrolled_prev', 'enrolled_curr', 'enrollment_growth_abs', 'enrollment_growth_pct']].to_numpy(),
            hovertemplate=hover_template
        ))

    max_val = plot_df[y_col].max() if not plot_df.empty else 0
    min_val = plot_df[y_col].min() if not plot_df.empty else 0
    x_padding = max_val * 0.25 if max_val else 1
    x_min = min(0, min_val)

    fig.update_layout(
        **LAYOUT_DEFAULTS,
        title=None,
        xaxis=dict(
            title=_format_column_name(y_col),
            range=[x_min, max_val + x_padding],
        ),
        yaxis=dict(
            title=None,
            autorange='reversed',
            tickfont=dict(size=11)
        ),
        height=max(350, len(plot_df) * 35),
        margin={'l': 200, 'r': 60, 't': 20, 'b': 50},
    )

    return fig


def _create_ai_bar_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    sort_order: str = 'desc',
    top_n: int = 10,
    color_col: str = None
) -> go.Figure:
    """Create a bar chart based on AI specification."""
    # Validate columns exist
    if x_col not in df.columns:
        x_col = 'institution_name'
    if y_col not in df.columns:
        y_col = 'yield_rate' if 'yield_rate' in df.columns else df.columns[0]
    
    # Aggregate if needed (for institution-level metrics)
    if x_col == 'institution_name':
        agg_cols = ['applicants', 'admissions', 'enrolled_total']
        agg_dict = {col: 'sum' for col in agg_cols if col in df.columns}
        rate_cols = ['admit_rate', 'yield_rate', 'diversity_index']
        for col in rate_cols:
            if col in df.columns:
                agg_dict[col] = 'mean'
        
        if agg_dict:
            plot_df = df.groupby(x_col).agg(agg_dict).reset_index()
        else:
            plot_df = df.copy()
    elif x_col == 'region' or x_col == 'institution_size':
        agg_dict = {}
        if y_col in ['applicants', 'admissions', 'enrolled_total']:
            agg_dict[y_col] = 'sum'
        else:
            agg_dict[y_col] = 'mean'
        plot_df = df.groupby(x_col).agg(agg_dict).reset_index()
    else:
        plot_df = df.copy()
    
    # Sort and limit
    ascending = sort_order != 'desc'
    if y_col in plot_df.columns:
        plot_df = plot_df.sort_values(y_col, ascending=ascending)
    
    if top_n and len(plot_df) > top_n:
        plot_df = plot_df.head(top_n) if not ascending else plot_df.tail(top_n)
    
    # Create chart
    fig = go.Figure(go.Bar(
        x=plot_df[y_col],
        y=plot_df[x_col],
        orientation='h',
        marker_color=COLORS['accent'],
        text=plot_df[y_col].apply(lambda x: f"{x:.1f}%" if 'rate' in y_col or 'pct' in y_col else f"{x:,.0f}"),
        textposition='outside',
        hovertemplate=f"<b>%{{y}}</b><br>{y_col}: %{{x:.1f}}<extra></extra>"
    ))
    
    # Calculate x-axis range with padding
    max_val = plot_df[y_col].max() if not plot_df.empty else 100
    x_padding = max_val * 0.25
    
    fig.update_layout(
        **LAYOUT_DEFAULTS,
        title=None,
        xaxis=dict(
            title=_format_column_name(y_col),
            range=[0, max_val + x_padding],
        ),
        yaxis=dict(
            title=None,
            autorange='reversed',
            tickfont=dict(size=11)
        ),
        height=max(350, len(plot_df) * 35),
        margin={'l': 200, 'r': 60, 't': 20, 'b': 50},
    )
    
    return fig


def _create_ai_line_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: str = None
) -> go.Figure:
    """Create a line chart based on AI specification."""
    # Validate columns
    if x_col not in df.columns:
        x_col = 'year'
    if y_col not in df.columns:
        y_col = 'yield_rate' if 'yield_rate' in df.columns else df.columns[0]
    
    fig = go.Figure()
    
    if color_col and color_col in df.columns:
        # Multiple lines by group
        groups = df[color_col].unique()
        for i, group in enumerate(groups[:7]):  # Limit to 7 groups
            group_df = df[df[color_col] == group]
            
            # Aggregate by x column
            if y_col in ['applicants', 'admissions', 'enrolled_total']:
                agg_df = group_df.groupby(x_col)[y_col].sum().reset_index()
            else:
                agg_df = group_df.groupby(x_col)[y_col].mean().reset_index()
            
            agg_df = agg_df.sort_values(x_col)
            
            fig.add_trace(go.Scatter(
                x=agg_df[x_col],
                y=agg_df[y_col],
                mode='lines+markers',
                name=str(group),
                line=dict(color=CHART_PALETTE[i % len(CHART_PALETTE)], width=2),
                marker=dict(size=8),
                hovertemplate=f"<b>{group}</b><br>{x_col}: %{{x}}<br>{y_col}: %{{y:.1f}}<extra></extra>"
            ))
    else:
        # Single line - aggregate all data
        if y_col in ['applicants', 'admissions', 'enrolled_total']:
            agg_df = df.groupby(x_col)[y_col].sum().reset_index()
        else:
            agg_df = df.groupby(x_col)[y_col].mean().reset_index()
        
        agg_df = agg_df.sort_values(x_col)
        
        fig.add_trace(go.Scatter(
            x=agg_df[x_col],
            y=agg_df[y_col],
            mode='lines+markers',
            name=_format_column_name(y_col),
            line=dict(color=COLORS['accent'], width=2),
            marker=dict(size=8),
            hovertemplate=f"{x_col}: %{{x}}<br>{y_col}: %{{y:.1f}}<extra></extra>"
        ))
    
    fig.update_layout(
        **LAYOUT_DEFAULTS,
        title=None,
        xaxis=dict(
            title=_format_column_name(x_col),
            gridcolor=COLORS['border'],
        ),
        yaxis=dict(
            title=_format_column_name(y_col),
            gridcolor=COLORS['border'],
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='left',
            x=0
        ),
        height=400,
        margin={'l': 60, 'r': 30, 't': 40, 'b': 50},
        hovermode='x unified',
    )
    
    return fig


def _create_ai_scatter_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: str = None
) -> go.Figure:
    """Create a scatter chart based on AI specification."""
    # Validate columns
    if x_col not in df.columns:
        x_col = 'applicants'
    if y_col not in df.columns:
        y_col = 'yield_rate'
    
    # Aggregate to institution level if needed
    if 'institution_name' in df.columns:
        agg_cols = {x_col: 'sum' if x_col in ['applicants', 'admissions', 'enrolled_total'] else 'mean',
                    y_col: 'sum' if y_col in ['applicants', 'admissions', 'enrolled_total'] else 'mean'}
        
        if color_col and color_col in df.columns:
            agg_cols[color_col] = 'first'
        
        plot_df = df.groupby('institution_name').agg(agg_cols).reset_index()
    else:
        plot_df = df.copy()
    
    fig = go.Figure()
    
    if color_col and color_col in plot_df.columns:
        groups = plot_df[color_col].unique()
        for i, group in enumerate(groups[:7]):
            group_df = plot_df[plot_df[color_col] == group]
            fig.add_trace(go.Scatter(
                x=group_df[x_col],
                y=group_df[y_col],
                mode='markers',
                name=str(group),
                marker=dict(
                    size=10,
                    color=CHART_PALETTE[i % len(CHART_PALETTE)],
                    opacity=0.7,
                    line=dict(width=1, color='white')
                ),
                text=group_df.get('institution_name', ''),
                hovertemplate=f"<b>%{{text}}</b><br>{x_col}: %{{x:,.0f}}<br>{y_col}: %{{y:.1f}}<extra></extra>"
            ))
    else:
        fig.add_trace(go.Scatter(
            x=plot_df[x_col],
            y=plot_df[y_col],
            mode='markers',
            marker=dict(
                size=10,
                color=COLORS['accent'],
                opacity=0.7,
                line=dict(width=1, color='white')
            ),
            text=plot_df.get('institution_name', ''),
            hovertemplate=f"<b>%{{text}}</b><br>{x_col}: %{{x:,.0f}}<br>{y_col}: %{{y:.1f}}<extra></extra>"
        ))
    
    fig.update_layout(
        **LAYOUT_DEFAULTS,
        title=None,
        xaxis=dict(
            title=_format_column_name(x_col),
            gridcolor=COLORS['border'],
        ),
        yaxis=dict(
            title=_format_column_name(y_col),
            gridcolor=COLORS['border'],
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='left',
            x=0
        ),
        height=400,
        margin={'l': 60, 'r': 30, 't': 40, 'b': 50},
    )
    
    return fig


def _format_column_name(col_name: str) -> str:
    """Format a column name for display."""
    name_map = {
        'institution_name': 'Institution',
        'year': 'Year',
        'applicants': 'Applicants',
        'admissions': 'Admissions',
        'enrolled_total': 'Total Enrolled',
        'admit_rate': 'Admit Rate (%)',
        'yield_rate': 'Yield Rate (%)',
        'diversity_index': 'Diversity Index',
        'pct_hispanic': 'Hispanic (%)',
        'pct_white': 'White (%)',
        'pct_black': 'Black (%)',
        'pct_asian': 'Asian (%)',
        'pct_other': 'Other (%)',
        'region': 'Region',
        'institution_size': 'Institution Size',
        'state': 'State',
        'enrollment_growth_pct': 'Enrollment Growth (%)',
        'enrollment_growth_abs': 'Enrollment Growth (Count)',
    }
    return name_map.get(col_name, col_name.replace('_', ' ').title())
