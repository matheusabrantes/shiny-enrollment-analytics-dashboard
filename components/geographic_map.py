"""Geographic distribution map visualization component."""

import plotly.graph_objects as go
import pandas as pd
from utils.styling import CARNEGIE_COLORS, get_plotly_template


def create_state_map(df: pd.DataFrame, metric: str = 'yield_rate') -> go.Figure:
    """
    Create choropleth map showing enrollment metrics by state.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Enrollment data with 'state' column
    metric : str
        Metric to visualize ('yield_rate', 'enrolled_total', 'admit_rate')
    
    Returns:
    --------
    plotly.graph_objects.Figure
    """
    
    if df.empty or 'state' not in df.columns:
        return _create_empty_chart("No geographic data available")
    
    # Aggregate data by state
    state_data = df.groupby('state').agg({
        'applicants': 'sum',
        'admissions': 'sum',
        'enrolled_total': 'sum',
        'unit_id': 'nunique'
    }).reset_index()
    
    state_data.rename(columns={'unit_id': 'num_institutions'}, inplace=True)
    
    # Calculate metrics
    state_data['admit_rate'] = (
        state_data['admissions'] / state_data['applicants'].replace(0, 1) * 100
    ).round(1)
    
    state_data['yield_rate'] = (
        state_data['enrolled_total'] / state_data['admissions'].replace(0, 1) * 100
    ).round(1)
    
    # Metric configuration
    metric_config = {
        'yield_rate': {
            'title': 'Yield Rate by State',
            'colorbar_title': 'Yield Rate (%)',
            'format': '.1f',
            'suffix': '%'
        },
        'enrolled_total': {
            'title': 'Total Enrollment by State',
            'colorbar_title': 'Students Enrolled',
            'format': ',',
            'suffix': ''
        },
        'admit_rate': {
            'title': 'Admit Rate by State',
            'colorbar_title': 'Admit Rate (%)',
            'format': '.1f',
            'suffix': '%'
        },
        'num_institutions': {
            'title': 'Institutions by State',
            'colorbar_title': 'Number of Institutions',
            'format': 'd',
            'suffix': ''
        }
    }
    
    config = metric_config.get(metric, metric_config['yield_rate'])
    
    # Create hover text
    hover_text = []
    for _, row in state_data.iterrows():
        text = (
            f"<b>{row['state']}</b><br>"
            f"Institutions: {row['num_institutions']}<br>"
            f"Total Enrolled: {row['enrolled_total']:,}<br>"
            f"Yield Rate: {row['yield_rate']:.1f}%<br>"
            f"Admit Rate: {row['admit_rate']:.1f}%"
        )
        hover_text.append(text)
    
    state_data['hover_text'] = hover_text
    
    # Create choropleth map
    fig = go.Figure(data=go.Choropleth(
        locations=state_data['state'],
        z=state_data[metric],
        locationmode='USA-states',
        colorscale=[
            [0, '#E8F4F8'],
            [0.25, '#B4D7E8'],
            [0.5, '#5A9BC5'],
            [0.75, '#1B6B9A'],
            [1, CARNEGIE_COLORS['primary']]
        ],
        colorbar=dict(
            title=dict(
                text=config['colorbar_title'],
                font=dict(size=12)
            ),
            thickness=15,
            len=0.7,
            x=0.92,
            tickfont=dict(size=10)
        ),
        marker_line_color='white',
        marker_line_width=1,
        hovertemplate='%{customdata}<extra></extra>',
        customdata=state_data['hover_text']
    ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=config['title'],
            font=dict(size=18, color=CARNEGIE_COLORS['primary']),
            x=0.5,
            xanchor='center'
        ),
        geo=dict(
            scope='usa',
            projection=dict(type='albers usa'),
            showlakes=True,
            lakecolor='rgb(255, 255, 255)',
            bgcolor='rgba(0,0,0,0)',
            showframe=False
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=450,
        margin=dict(l=0, r=0, t=50, b=30)
    )
    
    # Add insight annotation
    top_state = state_data.nlargest(1, metric).iloc[0]
    
    if metric == 'yield_rate':
        # Calculate true national yield rate (total enrolled / total admitted)
        national_yield = (state_data['enrolled_total'].sum() / state_data['admitted_total'].sum()) * 100
        insight = f"Highest yield: {top_state['state']} ({top_state['yield_rate']:.1f}%) | National avg: {national_yield:.1f}%"
    elif metric == 'enrolled_total':
        insight = f"Most enrolled: {top_state['state']} ({top_state['enrolled_total']:,}) | Total: {state_data['enrolled_total'].sum():,}"
    elif metric == 'admit_rate':
        # Calculate true national admit rate (total admitted / total applicants)
        national_admit = (state_data['admitted_total'].sum() / state_data['applicants_total'].sum()) * 100
        insight = f"Highest admit rate: {top_state['state']} ({top_state['admit_rate']:.1f}%) | National avg: {national_admit:.1f}%"
    else:
        insight = f"Most institutions: {top_state['state']} ({top_state['num_institutions']})"
    
    fig.add_annotation(
        text=f"<b>Insight:</b> {insight}",
        xref="paper",
        yref="paper",
        x=0.5,
        y=-0.05,
        showarrow=False,
        font=dict(size=11, color=CARNEGIE_COLORS['neutral_dark']),
        align="center"
    )
    
    return fig


def get_state_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Get summary statistics by state for table display."""
    
    if df.empty or 'state' not in df.columns:
        return pd.DataFrame()
    
    state_summary = df.groupby('state').agg({
        'applicants': 'sum',
        'admissions': 'sum',
        'enrolled_total': 'sum',
        'unit_id': 'nunique',
        'institution_name': lambda x: ', '.join(x.unique()[:3]) + ('...' if len(x.unique()) > 3 else '')
    }).reset_index()
    
    state_summary.columns = ['State', 'Applicants', 'Admissions', 'Enrolled', 'Institutions', 'Sample Institutions']
    
    state_summary['Yield Rate'] = (
        state_summary['Enrolled'] / state_summary['Admissions'].replace(0, 1) * 100
    ).round(1)
    
    return state_summary.sort_values('Enrolled', ascending=False)


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
