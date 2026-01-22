"""Institution comparison visualization component."""

import plotly.graph_objects as go
import pandas as pd
from utils.styling import CARNEGIE_COLORS, get_plotly_template


def create_comparison_chart(top_institutions: pd.DataFrame, metric: str = 'yield_rate') -> go.Figure:
    """Create a horizontal bar chart comparing top institutions."""
    
    if top_institutions.empty:
        return _create_empty_chart("No institution data available")
    
    template = get_plotly_template()
    
    # Metric display configuration
    metric_config = {
        'yield_rate': {
            'title': 'Top Institutions by Yield Rate',
            'format': '.1f',
            'suffix': '%',
            'color_scale': [[0, CARNEGIE_COLORS['info']], [1, CARNEGIE_COLORS['primary']]]
        },
        'enrolled_total': {
            'title': 'Top Institutions by Total Enrollment',
            'format': ',',
            'suffix': '',
            'color_scale': [[0, '#FF9E6D'], [1, CARNEGIE_COLORS['secondary']]]
        },
        'admit_rate': {
            'title': 'Top Institutions by Admit Rate',
            'format': '.1f',
            'suffix': '%',
            'color_scale': [[0, '#7BC8A4'], [1, '#28A745']]
        }
    }
    
    config = metric_config.get(metric, metric_config['yield_rate'])
    
    # Sort data
    df_sorted = top_institutions.sort_values(metric, ascending=True).tail(10)
    
    # Truncate long institution names
    df_sorted['display_name'] = df_sorted['institution_name'].apply(
        lambda x: x[:35] + '...' if len(x) > 35 else x
    )
    
    # Create color gradient based on values
    values = df_sorted[metric]
    normalized = (values - values.min()) / (values.max() - values.min() + 0.001)
    colors = [f"rgba(27, 54, 93, {0.4 + 0.6 * n})" for n in normalized]
    
    fig = go.Figure(go.Bar(
        x=df_sorted[metric],
        y=df_sorted['display_name'],
        orientation='h',
        marker=dict(
            color=colors,
            line=dict(color=CARNEGIE_COLORS['primary'], width=1)
        ),
        text=df_sorted[metric].apply(
            lambda x: f"{x:{config['format']}}{config['suffix']}"
        ),
        textposition='outside',
        textfont=dict(size=11, color=CARNEGIE_COLORS['neutral_dark']),
        hovertemplate="<b>%{y}</b><br>" +
                      f"{metric.replace('_', ' ').title()}: %{{x:{config['format']}}}{config['suffix']}<br>" +
                      "<extra></extra>",
        customdata=df_sorted['institution_name']
    ))
    
    # Calculate insight
    if metric == 'yield_rate':
        avg_rate = top_institutions['yield_rate'].mean()
        max_rate = top_institutions['yield_rate'].max()
        insight = f"Top performers achieve yield rates above {max_rate:.0f}%, significantly higher than the average of {avg_rate:.1f}%"
    elif metric == 'enrolled_total':
        total = top_institutions['enrolled_total'].sum()
        insight = f"Top 10 institutions account for {total:,} total enrollments"
    else:
        insight = ""
    
    fig.update_layout(
        title=dict(
            text=config['title'],
            font=dict(size=16, color=CARNEGIE_COLORS['primary']),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title=metric.replace('_', ' ').title() + (f" ({config['suffix']})" if config['suffix'] else ""),
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)',
            range=[0, 105] if metric == 'yield_rate' or metric == 'admit_rate' else None,
            tickfont=dict(size=10)
        ),
        yaxis=dict(
            title="",
            tickfont=dict(size=10)
        ),
        font=template['layout']['font'],
        paper_bgcolor=template['layout']['paper_bgcolor'],
        plot_bgcolor=template['layout']['plot_bgcolor'],
        margin=dict(l=180, r=60, t=50, b=80),
        height=400,
        showlegend=False,
        autosize=True
    )
    
    if insight:
        fig.add_annotation(
            text=f"<b>Insight:</b> {insight}",
            xref="paper",
            yref="paper",
            x=0.5,
            y=-0.25,
            showarrow=False,
            font=dict(size=11, color=CARNEGIE_COLORS['neutral_dark']),
            align="center"
        )
    
    return fig


def _create_empty_chart(message: str) -> go.Figure:
    """Create an empty chart with a message."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=14, color=CARNEGIE_COLORS['neutral_dark'])
    )
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=450
    )
    return fig
