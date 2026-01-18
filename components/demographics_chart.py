"""Demographics breakdown visualization component."""

import plotly.graph_objects as go
import pandas as pd
from utils.styling import CARNEGIE_COLORS, DEMOGRAPHICS_PALETTE, get_plotly_template


def create_demographics_chart(demo_df: pd.DataFrame, show_percentages: bool = True) -> go.Figure:
    """Create a stacked bar chart showing enrollment demographics over time."""
    
    if demo_df.empty:
        return _create_empty_chart("No demographics data available")
    
    template = get_plotly_template()
    
    # Define demographic categories and their display names
    demo_categories = [
        ('pct_hispanic', 'Hispanic/Latino'),
        ('pct_white', 'White'),
        ('pct_black', 'Black'),
        ('pct_asian', 'Asian'),
        ('pct_other', 'Other'),
    ]
    
    colors = list(DEMOGRAPHICS_PALETTE.values())
    
    fig = go.Figure()
    
    for i, (col, name) in enumerate(demo_categories):
        if col in demo_df.columns:
            fig.add_trace(go.Bar(
                name=name,
                x=[f"Fall {y}" for y in demo_df['year']],
                y=demo_df[col],
                marker_color=colors[i % len(colors)],
                text=demo_df[col].apply(lambda x: f"{x:.1f}%"),
                textposition='inside',
                textfont=dict(size=10, color='white'),
                hovertemplate=f"<b>{name}</b><br>" +
                              "Year: %{x}<br>" +
                              "Percentage: %{y:.1f}%<extra></extra>"
            ))
    
    # Calculate diversity trend for insight
    if len(demo_df) >= 2 and 'pct_hispanic' in demo_df.columns:
        first_hispanic = demo_df.iloc[0]['pct_hispanic']
        last_hispanic = demo_df.iloc[-1]['pct_hispanic']
        hispanic_change = last_hispanic - first_hispanic
        
        if hispanic_change > 0:
            insight = f"Hispanic/Latino enrollment grew from {first_hispanic:.1f}% to {last_hispanic:.1f}% ({hispanic_change:+.1f} pp)"
        else:
            insight = f"Hispanic/Latino enrollment: {last_hispanic:.1f}% in {int(demo_df.iloc[-1]['year'])}"
    else:
        insight = ""
    
    fig.update_layout(
        title=dict(
            text="Enrollment Demographics by Year",
            font=dict(size=18, color=CARNEGIE_COLORS['primary']),
            x=0.5,
            xanchor='center'
        ),
        barmode='stack',
        xaxis=dict(
            title="Academic Year",
            showgrid=False
        ),
        yaxis=dict(
            title="Percentage of Enrollment (%)",
            range=[0, 105],
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
        bargap=0.3
    )
    
    if insight:
        fig.add_annotation(
            text=f"<b>Diversity Trend:</b> {insight}",
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
