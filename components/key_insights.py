"""Key Insights component showing institution rankings."""

from shiny import ui
from utils.styling import CARNEGIE_COLORS


def create_key_insights_ui():
    """Create the Key Insights panel UI placeholder (horizontal layout below KPIs)."""
    return ui.div(
        ui.output_ui("key_insights_content"),
        class_="key-insights-row"
    )


def render_key_insights(rankings: dict, institution_name: str) -> ui.TagList:
    """Render Key Insights content with rankings in horizontal grid format.
    
    Args:
        rankings: Dictionary with ranking data for each metric
        institution_name: Name of the selected institution
    
    Returns:
        UI TagList with formatted insights in 4-column grid
    """
    if not rankings or not institution_name:
        return ui.div(
            ui.p("Select a single institution to view rankings", 
                 style="color: #888; text-align: center; padding: 8px; font-size: 12px;"),
            class_="insights-placeholder-horizontal"
        )
    
    def create_insight_card(metric_name: str, card_type: str, data: dict) -> ui.Tag:
        """Create a single insight card with rankings."""
        if not data:
            return ui.div()
        
        national_rank = data.get('national_rank', '-')
        national_total = data.get('national_total', '-')
        state_rank = data.get('state_rank', '-')
        state_total = data.get('state_total', '-')
        region_rank = data.get('region_rank', '-')
        region_total = data.get('region_total', '-')
        state_name = data.get('state', '')
        region_name = data.get('region', '')
        
        return ui.div(
            ui.div(
                ui.span(metric_name, class_="insight-label"),
                class_="insight-card-header"
            ),
            ui.div(
                ui.div(
                    ui.span("🇺🇸", class_="badge-icon"),
                    ui.span(f"#{national_rank}", class_="badge-rank"),
                    ui.span(f"of {national_total}", class_="badge-total"),
                    class_="insight-badge national"
                ),
                ui.div(
                    ui.span("📍", class_="badge-icon"),
                    ui.span(f"#{region_rank}", class_="badge-rank"),
                    ui.span(f"of {region_total} ({region_name})", class_="badge-total"),
                    class_="insight-badge region"
                ),
                ui.div(
                    ui.span("🏛️", class_="badge-icon"),
                    ui.span(f"#{state_rank}", class_="badge-rank"),
                    ui.span(f"of {state_total} ({state_name})", class_="badge-total"),
                    class_="insight-badge state"
                ),
                class_="insight-badges"
            ),
            class_=f"insight-card insight-card-{card_type}"
        )
    
    short_name = institution_name[:30] + "..." if len(institution_name) > 30 else institution_name
    
    return ui.TagList(
        ui.div(
            ui.div(
                ui.span("📊 Rankings: ", class_="insights-title"),
                ui.span(short_name, class_="insights-institution"),
                class_="insights-header-row"
            ),
            ui.div(
                create_insight_card("Applicants", "applicants", rankings.get('applicants', {})),
                create_insight_card("Admitted", "admitted", rankings.get('admissions', {})),
                create_insight_card("Enrolled", "enrolled", rankings.get('enrolled_total', {})),
                create_insight_card("Yield Rate", "yield", rankings.get('yield_rate', {})),
                class_="insights-grid"
            ),
            class_="insights-container-horizontal"
        )
    )


def calculate_rankings(df, institution_name: str, year: int = None) -> dict:
    """Calculate rankings for a specific institution.
    
    Args:
        df: Full DataFrame with all institutions
        institution_name: Name of the institution to rank
        year: Optional year filter (uses latest if not specified)
    
    Returns:
        Dictionary with rankings for each metric
    """
    import pandas as pd
    
    if df.empty or not institution_name:
        return {}
    
    # Use latest year if not specified
    if year is None:
        year = df['year'].max()
    
    # Filter to the specific year and aggregate by institution
    year_data = df[df['year'] == year].copy()
    
    if year_data.empty:
        return {}
    
    # Get institution data
    inst_data = year_data[year_data['institution_name'] == institution_name]
    if inst_data.empty:
        return {}
    
    inst_row = inst_data.iloc[0]
    inst_state = inst_row['state']
    inst_region = inst_row['region']
    
    # Aggregate by institution for ranking
    agg_data = year_data.groupby('institution_name').agg({
        'applicants': 'sum',
        'admissions': 'sum',
        'enrolled_total': 'sum',
        'state': 'first',
        'region': 'first'
    }).reset_index()
    
    # Calculate yield rate
    agg_data['yield_rate'] = (agg_data['enrolled_total'] / agg_data['admissions'] * 100).fillna(0)
    
    rankings = {}
    
    for metric in ['applicants', 'admissions', 'enrolled_total', 'yield_rate']:
        # National ranking (descending - higher is better)
        national_sorted = agg_data.sort_values(metric, ascending=False).reset_index(drop=True)
        national_rank = national_sorted[national_sorted['institution_name'] == institution_name].index
        
        if len(national_rank) > 0:
            national_rank = national_rank[0] + 1
        else:
            continue
        
        # State ranking
        state_data = agg_data[agg_data['state'] == inst_state].sort_values(metric, ascending=False).reset_index(drop=True)
        state_rank_idx = state_data[state_data['institution_name'] == institution_name].index
        state_rank = state_rank_idx[0] + 1 if len(state_rank_idx) > 0 else '-'
        
        # Region ranking
        region_data = agg_data[agg_data['region'] == inst_region].sort_values(metric, ascending=False).reset_index(drop=True)
        region_rank_idx = region_data[region_data['institution_name'] == institution_name].index
        region_rank = region_rank_idx[0] + 1 if len(region_rank_idx) > 0 else '-'
        
        rankings[metric] = {
            'national_rank': national_rank,
            'national_total': len(agg_data),
            'state_rank': state_rank,
            'state_total': len(state_data),
            'region_rank': region_rank,
            'region_total': len(region_data),
            'state': inst_state,
            'region': inst_region
        }
    
    return rankings
