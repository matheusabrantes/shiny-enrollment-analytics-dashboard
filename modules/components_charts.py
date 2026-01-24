"""
Chart components for the enrollment dashboard using Plotly.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Optional, List, Dict

# Design system colors
COLORS = {
    'primary': '#0F172A',
    'accent': '#2563EB',
    'success': '#10B981',
    'warning': '#F97316',
    'danger': '#EF4444',
    'muted': '#64748B',
    'bg': '#F8FAFC',
    'card': '#FFFFFF',
    'border': '#E2E8F0',
}

CHART_PALETTE = ['#0F172A', '#2563EB', '#10B981', '#F97316', '#8B5CF6', '#EC4899', '#06B6D4']

DEMOGRAPHICS_PALETTE = {
    'Hispanic/Latino': '#F97316',
    'White': '#3B82F6',
    'Black': '#10B981',
    'Asian': '#8B5CF6',
    'Other': '#94A3B8',
    'Non-Resident': '#64748B',
}

# Base layout without margin (margin is set per-chart to avoid duplicates)
LAYOUT_DEFAULTS = {
    'font': {'family': 'Inter, sans-serif', 'size': 12, 'color': COLORS['primary']},
    'paper_bgcolor': COLORS['card'],
    'plot_bgcolor': COLORS['card'],
    'hoverlabel': {'bgcolor': COLORS['primary'], 'font_size': 12},
}


def create_funnel_chart(
    applicants: int,
    admitted: int,
    enrolled: int,
    show_leakage: bool = True
) -> go.Figure:
    """
    Create an enrollment funnel chart with conversion rates and leakage.
    """
    # Calculate rates
    admit_rate = (admitted / applicants * 100) if applicants > 0 else 0
    yield_rate = (enrolled / admitted * 100) if admitted > 0 else 0
    overall_rate = (enrolled / applicants * 100) if applicants > 0 else 0
    
    # Leakage
    leakage1 = applicants - admitted
    leakage2 = admitted - enrolled
    
    fig = go.Figure()
    
    # Main funnel
    fig.add_trace(go.Funnel(
        y=['Applicants', 'Admitted', 'Enrolled'],
        x=[applicants, admitted, enrolled],
        textinfo='value+percent initial',
        texttemplate='%{value:,.0f}<br>(%{percentInitial:.1%})',
        textposition='inside',
        marker={
            'color': [COLORS['primary'], COLORS['accent'], COLORS['success']],
            'line': {'width': 0}
        },
        connector={'line': {'color': COLORS['border'], 'width': 1}},
        hovertemplate='<b>%{y}</b><br>Count: %{x:,.0f}<br>%{percentInitial:.1%} of applicants<extra></extra>'
    ))
    
    # Add annotations for conversion rates
    annotations = [
        dict(
            x=0.85, y=0.75,
            text=f"<b>Selection Rate</b><br>{admit_rate:.1f}%",
            showarrow=False,
            font=dict(size=11, color=COLORS['muted']),
            align='left',
            xref='paper', yref='paper'
        ),
        dict(
            x=0.85, y=0.35,
            text=f"<b>Yield Rate</b><br>{yield_rate:.1f}%",
            showarrow=False,
            font=dict(size=11, color=COLORS['muted']),
            align='left',
            xref='paper', yref='paper'
        ),
    ]
    
    if show_leakage:
        annotations.extend([
            dict(
                x=0.85, y=0.55,
                text=f"<span style='color:{COLORS['danger']}'>▼ {leakage1:,.0f} not admitted</span>",
                showarrow=False,
                font=dict(size=10),
                align='left',
                xref='paper', yref='paper'
            ),
            dict(
                x=0.85, y=0.15,
                text=f"<span style='color:{COLORS['danger']}'>▼ {leakage2:,.0f} did not enroll</span>",
                showarrow=False,
                font=dict(size=10),
                align='left',
                xref='paper', yref='paper'
            ),
        ])
    
    fig.update_layout(
        **LAYOUT_DEFAULTS,
        margin={'l': 50, 'r': 30, 't': 40, 'b': 50},
        title=None,
        showlegend=False,
        annotations=annotations,
        height=350,
    )
    
    return fig


def create_trends_chart(
    df: pd.DataFrame,
    metrics: List[str] = ['admit_rate', 'yield_rate', 'overall_rate'],
    show_confidence: bool = False
) -> go.Figure:
    """
    Create a line chart showing trends over time.
    
    Args:
        df: DataFrame with 'year' column and metric columns
        metrics: List of metric column names to plot
        show_confidence: Whether to show confidence bands
    """
    fig = go.Figure()
    
    metric_config = {
        'admit_rate': {'name': 'Admit Rate', 'color': COLORS['accent']},
        'yield_rate': {'name': 'Yield Rate', 'color': COLORS['success']},
        'overall_rate': {'name': 'Overall Conversion', 'color': COLORS['warning']},
        'applicants': {'name': 'Applicants', 'color': COLORS['primary']},
        'admitted': {'name': 'Admitted', 'color': COLORS['accent']},
        'enrolled': {'name': 'Enrolled', 'color': COLORS['success']},
    }
    
    for metric in metrics:
        if metric not in df.columns:
            continue
        
        config = metric_config.get(metric, {'name': metric, 'color': COLORS['muted']})
        
        fig.add_trace(go.Scatter(
            x=df['year'],
            y=df[metric],
            mode='lines+markers',
            name=config['name'],
            line=dict(color=config['color'], width=2),
            marker=dict(size=8),
            hovertemplate=f"<b>{config['name']}</b><br>Year: %{{x}}<br>Value: %{{y:.1f}}%<extra></extra>"
        ))
    
    fig.update_layout(
        **LAYOUT_DEFAULTS,
        margin={'l': 50, 'r': 30, 't': 40, 'b': 50},
        title=None,
        xaxis=dict(
            title=None,
            tickmode='linear',
            dtick=1,
            gridcolor=COLORS['border'],
        ),
        yaxis=dict(
            title='Rate (%)',
            gridcolor=COLORS['border'],
            zeroline=False,
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='left',
            x=0
        ),
        height=300,
        hovermode='x unified',
    )
    
    return fig


def create_demographics_chart(
    df: pd.DataFrame,
    chart_type: str = 'stacked_bar'
) -> go.Figure:
    """
    Create a demographics visualization.
    
    Args:
        df: DataFrame with year and demographic percentage columns
        chart_type: 'stacked_bar' or 'area'
    """
    demo_cols = {
        'pct_hispanic': 'Hispanic/Latino',
        'pct_white': 'White',
        'pct_black': 'Black',
        'pct_asian': 'Asian',
        'pct_other': 'Other',
    }
    
    fig = go.Figure()
    
    for col, name in demo_cols.items():
        if col not in df.columns:
            continue
        
        color = DEMOGRAPHICS_PALETTE.get(name, COLORS['muted'])
        
        if chart_type == 'stacked_bar':
            fig.add_trace(go.Bar(
                x=df['year'],
                y=df[col],
                name=name,
                marker_color=color,
                hovertemplate=f"<b>{name}</b><br>Year: %{{x}}<br>%{{y:.1f}}%<extra></extra>"
            ))
        else:
            fig.add_trace(go.Scatter(
                x=df['year'],
                y=df[col],
                mode='lines',
                name=name,
                fill='tonexty',
                line=dict(color=color, width=0.5),
                hovertemplate=f"<b>{name}</b><br>Year: %{{x}}<br>%{{y:.1f}}%<extra></extra>"
            ))
    
    fig.update_layout(
        **LAYOUT_DEFAULTS,
        margin={'l': 50, 'r': 30, 't': 40, 'b': 50},
        title=None,
        barmode='stack' if chart_type == 'stacked_bar' else None,
        xaxis=dict(
            title=None,
            tickmode='linear',
            dtick=1,
        ),
        yaxis=dict(
            title='Percentage (%)',
            range=[0, 100],
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='left',
            x=0
        ),
        height=300,
    )
    
    return fig


def create_distribution_chart(
    values: pd.Series,
    target_value: Optional[float] = None,
    target_name: str = "Target",
    metric_name: str = "Value",
    chart_type: str = 'box'
) -> go.Figure:
    """
    Create a distribution chart (box or violin) with optional target marker.
    
    Args:
        values: Series of values for the distribution
        target_value: Optional value to highlight
        target_name: Name for the target marker
        metric_name: Name of the metric being displayed
        chart_type: 'box' or 'violin'
    """
    fig = go.Figure()
    
    if chart_type == 'violin':
        fig.add_trace(go.Violin(
            y=values,
            box_visible=True,
            meanline_visible=True,
            fillcolor=COLORS['accent'],
            opacity=0.6,
            line_color=COLORS['primary'],
            name='Distribution',
            hoverinfo='y'
        ))
    else:
        fig.add_trace(go.Box(
            y=values,
            boxmean='sd',
            fillcolor=COLORS['accent'],
            opacity=0.6,
            line_color=COLORS['primary'],
            name='Distribution',
            hoverinfo='y'
        ))
    
    # Add target marker
    if target_value is not None:
        fig.add_trace(go.Scatter(
            x=[0],
            y=[target_value],
            mode='markers',
            marker=dict(
                size=16,
                color=COLORS['warning'],
                symbol='diamond',
                line=dict(color=COLORS['primary'], width=2)
            ),
            name=target_name,
            hovertemplate=f"<b>{target_name}</b><br>{metric_name}: %{{y:.1f}}<extra></extra>"
        ))
    
    # Add percentile annotations
    if not values.empty:
        p25 = values.quantile(0.25)
        p50 = values.quantile(0.50)
        p75 = values.quantile(0.75)
        
        fig.add_annotation(
            x=0.5, y=p50,
            text=f"Median: {p50:.1f}",
            showarrow=True,
            arrowhead=2,
            ax=60, ay=0,
            font=dict(size=10, color=COLORS['muted']),
            xref='paper'
        )
    
    fig.update_layout(
        **LAYOUT_DEFAULTS,
        margin={'l': 50, 'r': 30, 't': 40, 'b': 50},
        title=None,
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='left',
            x=0
        ),
        xaxis=dict(showticklabels=False),
        yaxis=dict(title=metric_name),
        height=300,
    )
    
    return fig


def create_scatter_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: Optional[str] = None,
    size_col: Optional[str] = None,
    target_institution: Optional[str] = None,
    x_label: str = None,
    y_label: str = None
) -> go.Figure:
    """
    Create a scatter plot for benchmarking context.
    
    Args:
        df: DataFrame with data
        x_col: Column for x-axis
        y_col: Column for y-axis
        color_col: Optional column for color coding
        size_col: Optional column for bubble size
        target_institution: Institution to highlight
        x_label, y_label: Axis labels
    """
    fig = go.Figure()
    
    # Prepare size values
    if size_col and size_col in df.columns:
        sizes = df[size_col]
        # Normalize sizes
        size_min, size_max = sizes.min(), sizes.max()
        if size_max > size_min:
            normalized_sizes = 8 + (sizes - size_min) / (size_max - size_min) * 20
        else:
            normalized_sizes = [12] * len(sizes)
    else:
        normalized_sizes = [10] * len(df)
    
    # Color mapping
    if color_col and color_col in df.columns:
        unique_colors = df[color_col].unique()
        color_map = {val: CHART_PALETTE[i % len(CHART_PALETTE)] for i, val in enumerate(unique_colors)}
        colors = df[color_col].map(color_map)
    else:
        colors = [COLORS['accent']] * len(df)
    
    # Non-target points
    if target_institution:
        mask = df['institution_name'] != target_institution
        other_df = df[mask]
        other_sizes = [normalized_sizes[i] for i in range(len(df)) if mask.iloc[i]]
        other_colors = [colors.iloc[i] for i in range(len(df)) if mask.iloc[i]]
    else:
        other_df = df
        other_sizes = list(normalized_sizes)
        other_colors = list(colors)
    
    fig.add_trace(go.Scatter(
        x=other_df[x_col],
        y=other_df[y_col],
        mode='markers',
        marker=dict(
            size=other_sizes,
            color=other_colors,
            opacity=0.6,
            line=dict(width=1, color=COLORS['border'])
        ),
        text=other_df['institution_name'],
        hovertemplate="<b>%{text}</b><br>" + 
                      f"{x_label or x_col}: %{{x:,.0f}}<br>" +
                      f"{y_label or y_col}: %{{y:.1f}}%<extra></extra>",
        name='Institutions'
    ))
    
    # Target institution
    if target_institution and target_institution in df['institution_name'].values:
        target_row = df[df['institution_name'] == target_institution].iloc[0]
        fig.add_trace(go.Scatter(
            x=[target_row[x_col]],
            y=[target_row[y_col]],
            mode='markers',
            marker=dict(
                size=20,
                color=COLORS['warning'],
                symbol='star',
                line=dict(width=2, color=COLORS['primary'])
            ),
            name=target_institution[:30],
            hovertemplate=f"<b>{target_institution}</b><br>" +
                          f"{x_label or x_col}: %{{x:,.0f}}<br>" +
                          f"{y_label or y_col}: %{{y:.1f}}%<extra></extra>"
        ))
    
    fig.update_layout(
        **LAYOUT_DEFAULTS,
        margin={'l': 50, 'r': 30, 't': 40, 'b': 50},
        title=None,
        xaxis=dict(
            title=x_label or x_col,
            gridcolor=COLORS['border'],
        ),
        yaxis=dict(
            title=y_label or y_col,
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
    )
    
    return fig


def create_waterfall_chart(
    base_enrolled: int,
    effect_applicants: int,
    effect_admit_rate: int,
    effect_yield: int,
    final_enrolled: int
) -> go.Figure:
    """
    Create a waterfall chart showing enrollment decomposition.
    """
    fig = go.Figure(go.Waterfall(
        orientation='v',
        measure=['absolute', 'relative', 'relative', 'relative', 'total'],
        x=['Base Enrolled', 'Applicants Effect', 'Admit Rate Effect', 'Yield Effect', 'Final Enrolled'],
        y=[base_enrolled, effect_applicants, effect_admit_rate, effect_yield, final_enrolled],
        text=[f"{base_enrolled:,.0f}", 
              f"{'+' if effect_applicants >= 0 else ''}{effect_applicants:,.0f}",
              f"{'+' if effect_admit_rate >= 0 else ''}{effect_admit_rate:,.0f}",
              f"{'+' if effect_yield >= 0 else ''}{effect_yield:,.0f}",
              f"{final_enrolled:,.0f}"],
        textposition='outside',
        connector={'line': {'color': COLORS['border']}},
        decreasing={'marker': {'color': COLORS['danger']}},
        increasing={'marker': {'color': COLORS['success']}},
        totals={'marker': {'color': COLORS['accent']}},
    ))
    
    fig.update_layout(
        **LAYOUT_DEFAULTS,
        margin={'l': 50, 'r': 30, 't': 40, 'b': 50},
        title=None,
        showlegend=False,
        xaxis=dict(title=None),
        yaxis=dict(title='Enrolled Students'),
        height=350,
    )
    
    return fig


def create_state_map(
    df: pd.DataFrame,
    metric: str = 'yield_rate',
    metric_label: str = None
) -> go.Figure:
    """
    Create a choropleth map of the US by state.
    
    Args:
        df: DataFrame with 'state' column and metric column
        metric: Column name for the metric to display
        metric_label: Display label for the metric
    """
    # Aggregate by state
    state_data = df.groupby('state').agg({
        metric: 'mean' if 'rate' in metric else 'sum',
        'institution_name': 'nunique',
    }).reset_index()
    
    # Add enrolled total separately to handle column name
    enrolled_col = 'enrolled_total' if 'enrolled_total' in df.columns else 'enrolled'
    if enrolled_col in df.columns:
        state_enrolled = df.groupby('state')[enrolled_col].sum().reset_index()
        state_enrolled.columns = ['state', 'total_enrolled']
        state_data = state_data.merge(state_enrolled, on='state', how='left')
    else:
        state_data['total_enrolled'] = 0
    
    state_data.columns = ['state', 'value', 'num_institutions'] + list(state_data.columns[3:])
    
    # Color scale based on metric type
    if 'rate' in metric:
        colorscale = 'Blues'
        format_str = '.1f'
        suffix = '%'
    else:
        colorscale = 'Greens'
        format_str = ',.0f'
        suffix = ''
    
    fig = go.Figure(go.Choropleth(
        locations=state_data['state'],
        z=state_data['value'],
        locationmode='USA-states',
        colorscale=colorscale,
        colorbar=dict(
            title=metric_label or metric,
            thickness=15,
            len=0.7,
        ),
        hovertemplate="<b>%{location}</b><br>" +
                      f"{metric_label or metric}: %{{z:{format_str}}}{suffix}<br>" +
                      "Institutions: %{customdata[0]}<br>" +
                      "Total Enrolled: %{customdata[1]:,.0f}<extra></extra>",
        customdata=state_data[['num_institutions', 'total_enrolled']].values
    ))
    
    fig.update_layout(
        **LAYOUT_DEFAULTS,
        title=None,
        geo=dict(
            scope='usa',
            projection=dict(type='albers usa'),
            showlakes=True,
            lakecolor=COLORS['bg'],
            bgcolor=COLORS['card'],
        ),
        height=400,
        margin={'l': 0, 'r': 0, 't': 20, 'b': 0},  # Map needs special margins
    )
    
    return fig


def create_comparison_bar_chart(
    df: pd.DataFrame,
    metric: str,
    n: int = 10,
    metric_label: str = None,
    highlight_institution: str = None
) -> go.Figure:
    """
    Create a horizontal bar chart for institution comparison.
    """
    # Sort and get top N
    sorted_df = df.nlargest(n, metric)
    
    colors = [
        COLORS['warning'] if inst == highlight_institution else COLORS['accent']
        for inst in sorted_df['institution_name']
    ]
    
    fig = go.Figure(go.Bar(
        x=sorted_df[metric],
        y=sorted_df['institution_name'],
        orientation='h',
        marker_color=colors,
        text=sorted_df[metric].apply(lambda x: f"{x:.1f}%" if 'rate' in metric else f"{x:,.0f}"),
        textposition='outside',
        hovertemplate="<b>%{y}</b><br>" + f"{metric_label or metric}: %{{x:.1f}}<extra></extra>"
    ))
    
    fig.update_layout(
        **LAYOUT_DEFAULTS,
        title=None,
        xaxis=dict(title=metric_label or metric),
        yaxis=dict(
            title=None,
            autorange='reversed',
            tickfont=dict(size=11)
        ),
        height=max(300, n * 35),
        margin={'l': 200, 'r': 50, 't': 20, 'b': 50},  # Bar chart needs wider left margin
    )
    
    return fig


def create_small_multiples_trends(
    institutions: List[str],
    df: pd.DataFrame,
    metric: str = 'yield_rate'
) -> go.Figure:
    """
    Create small multiples showing trends for multiple institutions.
    """
    from plotly.subplots import make_subplots
    
    n_institutions = len(institutions)
    cols = min(3, n_institutions)
    rows = (n_institutions + cols - 1) // cols
    
    fig = make_subplots(
        rows=rows, cols=cols,
        subplot_titles=institutions[:9],  # Limit to 9
        shared_yaxes=True,
        horizontal_spacing=0.08,
        vertical_spacing=0.12
    )
    
    for i, inst in enumerate(institutions[:9]):
        row = i // cols + 1
        col = i % cols + 1
        
        inst_data = df[df['institution_name'] == inst].sort_values('year')
        
        fig.add_trace(
            go.Scatter(
                x=inst_data['year'],
                y=inst_data[metric],
                mode='lines+markers',
                line=dict(color=COLORS['accent'], width=2),
                marker=dict(size=6),
                showlegend=False,
                hovertemplate=f"<b>{inst[:20]}</b><br>Year: %{{x}}<br>{metric}: %{{y:.1f}}%<extra></extra>"
            ),
            row=row, col=col
        )
    
    fig.update_layout(
        **LAYOUT_DEFAULTS,
        margin={'l': 50, 'r': 30, 't': 40, 'b': 50},
        height=150 * rows + 50,
        title=None,
    )
    
    return fig
