"""
KPI card components for the enrollment dashboard.
"""

from shiny import ui
from typing import Optional, Union


def create_kpi_card(
    label: str,
    value: Union[str, int, float],
    delta: Optional[float] = None,
    delta_type: str = "percent",
    subtext: str = "",
    card_type: str = "default"
) -> ui.Tag:
    """
    Create a KPI card with value and optional delta indicator.
    
    Args:
        label: KPI label text
        value: Main value to display
        delta: YoY delta value (None if not available)
        delta_type: "percent" for percentage change, "pp" for percentage points
        subtext: Additional context text
        card_type: One of "applicants", "admitted", "enrolled", "yield", "admit", "default"
    
    Returns:
        UI Tag for the KPI card
    """
    # Format value
    if isinstance(value, (int, float)):
        if value >= 1000000:
            formatted_value = f"{value/1000000:.1f}M"
        elif value >= 1000:
            formatted_value = f"{value:,.0f}"
        elif isinstance(value, float):
            formatted_value = f"{value:.1f}%"
        else:
            formatted_value = f"{value:,}"
    else:
        formatted_value = str(value)
    
    # Create delta badge
    delta_element = None
    if delta is not None:
        delta_element = create_delta_badge(delta, delta_type)
    
    return ui.div(
        ui.div(label, class_="kpi-label"),
        ui.div(formatted_value, class_="kpi-value"),
        delta_element if delta_element else ui.span(),
        ui.div(subtext, class_="kpi-subtext") if subtext else ui.span(),
        class_=f"kpi-card kpi-{card_type}"
    )


def create_delta_badge(
    delta: float,
    delta_type: str = "percent"
) -> ui.Tag:
    """
    Create a delta indicator badge.
    
    Args:
        delta: Delta value
        delta_type: "percent" for %, "pp" for percentage points
    
    Returns:
        UI Tag for the delta badge
    """
    if delta is None:
        return ui.span()
    
    # Determine direction and styling
    if delta > 0.5:
        direction = "positive"
        arrow = "↑"
    elif delta < -0.5:
        direction = "negative"
        arrow = "↓"
    else:
        direction = "neutral"
        arrow = "→"
    
    # Format delta value
    if delta_type == "pp":
        formatted = f"{arrow} {abs(delta):.1f}pp"
    else:
        formatted = f"{arrow} {abs(delta):.1f}%"
    
    return ui.span(
        formatted,
        class_=f"kpi-delta {direction}"
    )


def create_insight_card(
    insight_type: str,
    message: str,
    detail: str = "",
    metric: str = ""
) -> ui.Tag:
    """
    Create an insight card for dynamic insights panel.
    
    Args:
        insight_type: One of "success", "warning", "danger", "info"
        message: Main insight message
        detail: Additional detail text
        metric: Related metric name
    
    Returns:
        UI Tag for the insight card
    """
    return ui.div(
        ui.div(
            ui.p(message, class_="insight-message"),
            ui.p(detail, class_="insight-detail") if detail else ui.span(),
            class_="insight-content"
        ),
        class_=f"insight-item {insight_type}"
    )


def create_ranking_card(
    metric: str,
    rank: int,
    total: int,
    percentile: float,
    scope: str = "national"
) -> ui.Tag:
    """
    Create a ranking card showing position within a group.
    
    Args:
        metric: Metric name
        rank: Current rank (1-indexed)
        total: Total in group
        percentile: Percentile position (0-100)
        scope: "national", "region", or "state"
    
    Returns:
        UI Tag for the ranking card
    """
    # Determine badge color based on percentile
    if percentile >= 75:
        badge_class = "badge-success"
    elif percentile >= 50:
        badge_class = "badge-info"
    elif percentile >= 25:
        badge_class = "badge-warning"
    else:
        badge_class = "badge-neutral"
    
    return ui.div(
        ui.div(metric, class_="ranking-metric"),
        ui.div(f"#{rank}", class_="ranking-value"),
        ui.div(f"of {total} ({percentile:.0f}th percentile)", class_="ranking-percentile"),
        ui.span(
            scope.capitalize(),
            class_=f"ranking-badge {scope}"
        ),
        class_="ranking-card"
    )


def create_kpi_grid(kpis: list) -> ui.Tag:
    """
    Create a grid of KPI cards.
    
    Args:
        kpis: List of dicts with kpi card parameters
    
    Returns:
        UI Tag for the KPI grid
    """
    cards = []
    for kpi in kpis:
        cards.append(create_kpi_card(**kpi))
    
    return ui.div(
        *cards,
        class_="kpi-grid"
    )


def create_insights_panel(insights: list, institution_name: str = None) -> ui.Tag:
    """
    Create the dynamic insights panel.
    
    Args:
        insights: List of insight dicts from generate_insights()
        institution_name: Optional institution name for header
    
    Returns:
        UI Tag for the insights panel
    """
    if not insights:
        return ui.div(
            ui.p("Select an institution to view personalized insights",
                 style="color: var(--color-text-muted); text-align: center; padding: 16px;"),
            class_="insights-panel"
        )
    
    insight_cards = [
        create_insight_card(
            insight_type=ins.get('type', 'info'),
            message=ins.get('message', ''),
            detail=ins.get('detail', ''),
            metric=ins.get('metric', '')
        )
        for ins in insights
    ]
    
    header_text = f"💡 Insights for {institution_name}" if institution_name else "💡 Dynamic Insights"
    
    return ui.div(
        ui.div(
            ui.span("💡", class_="insights-icon"),
            ui.span(header_text, class_="insights-title"),
            class_="insights-header"
        ),
        ui.div(
            *insight_cards,
            class_="insights-grid"
        ),
        class_="insights-panel"
    )
