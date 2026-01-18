"""Enrollment funnel visualization component."""

import plotly.graph_objects as go
from utils.styling import CARNEGIE_COLORS, get_plotly_template


def create_funnel_chart(funnel_data: dict) -> go.Figure:
    """Create an enrollment funnel chart."""
    
    stages = funnel_data['stages']
    values = funnel_data['values']
    percentages = funnel_data['percentages']
    stage_rates = funnel_data['stage_rates']
    
    # Create custom text for each stage
    text_labels = []
    for i, (stage, val, pct) in enumerate(zip(stages, values, percentages)):
        if i == 0:
            text_labels.append(f"{val:,}<br><span style='font-size:12px'>100% of applicants</span>")
        elif i == 1:
            text_labels.append(f"{val:,}<br><span style='font-size:12px'>{stage_rates[i]}% admit rate</span>")
        else:
            text_labels.append(f"{val:,}<br><span style='font-size:14px'>{stage_rates[i]}%</span><br><span style='font-size:11px'>yield rate</span>")
    
    # Funnel colors from light to dark
    colors = [CARNEGIE_COLORS['primary'], CARNEGIE_COLORS['info'], CARNEGIE_COLORS['secondary']]
    
    fig = go.Figure(go.Funnel(
        y=stages,
        x=values,
        textinfo="text",
        text=text_labels,
        textposition="inside",
        textfont=dict(size=16, color="white"),
        marker=dict(
            color=colors,
            line=dict(width=2, color="white")
        ),
        connector=dict(
            line=dict(color=CARNEGIE_COLORS['neutral_light'], width=2)
        ),
        hovertemplate="<b>%{y}</b><br>" +
                      "Count: %{x:,}<br>" +
                      "<extra></extra>"
    ))
    
    template = get_plotly_template()
    
    fig.update_layout(
        title=dict(
            text="Enrollment Funnel Overview",
            font=dict(size=18, color=CARNEGIE_COLORS['primary']),
            x=0.5,
            xanchor='center'
        ),
        font=template['layout']['font'],
        paper_bgcolor=template['layout']['paper_bgcolor'],
        plot_bgcolor=template['layout']['plot_bgcolor'],
        margin=dict(l=20, r=20, t=60, b=20),
        height=350,
        showlegend=False,
    )
    
    # Add annotation with key insight
    total_conversion = (values[2] / values[0] * 100) if values[0] > 0 else 0
    admit_rate = stage_rates[1] if stage_rates[1] else 0
    yield_rate = stage_rates[2] if stage_rates[2] else 0
    
    fig.add_annotation(
        text=f"<b>Key Insight:</b> {admit_rate}% admit rate → {yield_rate}% yield rate → {total_conversion:.1f}% overall conversion",
        xref="paper",
        yref="paper",
        x=0.5,
        y=-0.08,
        showarrow=False,
        font=dict(size=11, color=CARNEGIE_COLORS['neutral_dark']),
        align="center"
    )
    
    return fig
