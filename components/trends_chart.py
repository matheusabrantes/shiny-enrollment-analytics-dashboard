"""Conversion trends over time visualization component."""

import plotly.graph_objects as go
import pandas as pd
from utils.styling import CARNEGIE_COLORS, CHART_PALETTE, get_plotly_template


def create_trends_chart(trends_df: pd.DataFrame) -> go.Figure:
    """Create a multi-line chart showing conversion trends over time."""
    
    if trends_df.empty:
        return _create_empty_chart("No data available for selected filters")
    
    template = get_plotly_template()
    
    fig = go.Figure()
    
    # Admit Rate line
    fig.add_trace(go.Scatter(
        x=trends_df['year'],
        y=trends_df['admit_rate'],
        name='Admit Rate',
        mode='lines+markers',
        line=dict(color=CARNEGIE_COLORS['primary'], width=3),
        marker=dict(size=10, symbol='circle'),
        hovertemplate="<b>Fall %{x}</b><br>Admit Rate: %{y:.1f}%<extra></extra>"
    ))
    
    # Yield Rate line
    fig.add_trace(go.Scatter(
        x=trends_df['year'],
        y=trends_df['yield_rate'],
        name='Yield Rate',
        mode='lines+markers',
        line=dict(color=CARNEGIE_COLORS['secondary'], width=3),
        marker=dict(size=10, symbol='diamond'),
        hovertemplate="<b>Fall %{x}</b><br>Yield Rate: %{y:.1f}%<extra></extra>"
    ))
    
    # Overall Conversion Rate line
    fig.add_trace(go.Scatter(
        x=trends_df['year'],
        y=trends_df['overall_rate'],
        name='Overall Conversion',
        mode='lines+markers',
        line=dict(color=CHART_PALETTE[2], width=3, dash='dot'),
        marker=dict(size=10, symbol='square'),
        hovertemplate="<b>Fall %{x}</b><br>Overall Conversion: %{y:.1f}%<extra></extra>"
    ))
    
    # Calculate trends for annotation
    if len(trends_df) >= 2:
        first_yield = trends_df.iloc[0]['yield_rate']
        last_yield = trends_df.iloc[-1]['yield_rate']
        yield_change = last_yield - first_yield
        trend_direction = "increased" if yield_change > 0 else "decreased"
        
        insight_text = f"Yield rate {trend_direction} from {first_yield:.1f}% to {last_yield:.1f}% ({yield_change:+.1f} pp)"
    else:
        insight_text = ""
    
    fig.update_layout(
        title=dict(
            text="Conversion Rate Trends Over Time",
            font=dict(size=18, color=CARNEGIE_COLORS['primary']),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title="Academic Year",
            tickmode='array',
            tickvals=trends_df['year'].tolist(),
            ticktext=[f"Fall {y}" for y in trends_df['year']],
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)'
        ),
        yaxis=dict(
            title="Rate (%)",
            range=[0, 100],
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)'
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        font=template['layout']['font'],
        paper_bgcolor=template['layout']['paper_bgcolor'],
        plot_bgcolor=template['layout']['plot_bgcolor'],
        margin=dict(l=60, r=30, t=80, b=80),
        height=400,
        hovermode='x unified'
    )
    
    if insight_text:
        fig.add_annotation(
            text=f"<b>Trend:</b> {insight_text}",
            xref="paper",
            yref="paper",
            x=0.5,
            y=-0.18,
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
        height=400
    )
    return fig
