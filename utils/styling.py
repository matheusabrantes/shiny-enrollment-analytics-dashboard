"""Carnegie brand colors and Plotly styling utilities."""

CARNEGIE_COLORS = {
    'primary': '#002633',
    'secondary': '#FF6B35',
    'neutral_light': '#F5F5F5',
    'neutral_dark': '#333333',
    'white': '#FFFFFF',
    'success': '#28A745',
    'info': '#17A2B8',
}

CHART_PALETTE = [
    '#002633',  # Navy (primary)
    '#FF6B35',  # Orange (secondary)
    '#4A90E2',  # Light blue
    '#50C878',  # Emerald
    '#9B59B6',  # Purple
    '#F39C12',  # Gold
    '#1ABC9C',  # Teal
    '#E74C3C',  # Red
]

DEMOGRAPHICS_PALETTE = {
    'Hispanic/Latino': '#FF6B35',   # Carnegie orange (brand alignment)
    'White': '#5C6BC0',             # Indigo blue (neutral, professional)
    'Black': '#66BB6A',             # Green (positive, no negative connotation)
    'Asian': '#FFA726',             # Warm orange (distinguishable)
    'Other': '#BDBDBD',             # Gray (residual category)
}


def get_plotly_template():
    """Return custom Plotly template with Carnegie styling."""
    return {
        'layout': {
            'font': {
                'family': 'Inter, Arial, sans-serif',
                'size': 12,
                'color': CARNEGIE_COLORS['neutral_dark']
            },
            'plot_bgcolor': CARNEGIE_COLORS['white'],
            'paper_bgcolor': CARNEGIE_COLORS['white'],
            'colorway': CHART_PALETTE,
            'margin': {'l': 60, 'r': 30, 't': 50, 'b': 50},
            'hoverlabel': {
                'bgcolor': CARNEGIE_COLORS['primary'],
                'font_size': 12,
                'font_family': 'Inter, Arial, sans-serif'
            }
        }
    }


def get_kpi_card_style():
    """Return CSS style dict for KPI cards."""
    return {
        'background': CARNEGIE_COLORS['white'],
        'border_radius': '8px',
        'padding': '20px',
        'box_shadow': '0 2px 4px rgba(0,0,0,0.1)',
        'text_align': 'center'
    }
