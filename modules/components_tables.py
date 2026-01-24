"""
Table components for the enrollment dashboard.
"""

from shiny import ui
import pandas as pd
from typing import List, Optional, Dict


def create_data_table(
    df: pd.DataFrame,
    columns: List[str] = None,
    column_labels: Dict[str, str] = None,
    sortable: bool = True,
    page_size: int = 15,
    highlight_institution: str = None
) -> ui.Tag:
    """
    Create an HTML data table with styling.
    
    Args:
        df: DataFrame to display
        columns: List of columns to include (None = all)
        column_labels: Dict mapping column names to display labels
        sortable: Whether to enable sorting
        page_size: Number of rows per page
        highlight_institution: Institution name to highlight
    
    Returns:
        UI Tag for the table
    """
    if df.empty:
        return ui.div(
            ui.p("No data available", style="text-align: center; color: var(--color-text-muted); padding: 24px;"),
            class_="data-table-container"
        )
    
    # Select columns
    if columns:
        display_cols = [c for c in columns if c in df.columns]
    else:
        display_cols = list(df.columns)
    
    # Default labels
    default_labels = {
        'institution_name': 'Institution',
        'year': 'Year',
        'applicants': 'Applicants',
        'admitted': 'Admitted',
        'enrolled': 'Enrolled',
        'enrolled_total': 'Enrolled',
        'admit_rate': 'Admit Rate',
        'yield_rate': 'Yield Rate',
        'overall_conversion': 'Conversion',
        'diversity_index': 'Diversity',
        'state': 'State',
        'region': 'Region',
        'institution_size': 'Size',
        'rank': 'Rank',
        'percentile': 'Percentile',
        'distance': 'Similarity',
    }
    
    if column_labels:
        default_labels.update(column_labels)
    
    # Create header
    header_cells = [
        ui.tags.th(default_labels.get(col, col.replace('_', ' ').title()))
        for col in display_cols
    ]
    
    # Create rows
    rows = []
    for _, row in df.head(page_size).iterrows():
        cells = []
        for col in display_cols:
            value = row[col]
            
            # Format values
            if pd.isna(value):
                formatted = '-'
            elif col in ['applicants', 'admitted', 'enrolled', 'enrolled_total']:
                formatted = f"{int(value):,}"
            elif col in ['admit_rate', 'yield_rate', 'overall_conversion']:
                formatted = f"{value:.1f}%"
            elif col == 'diversity_index':
                formatted = f"{value:.3f}"
            elif col == 'distance':
                formatted = f"{value:.2f}"
            elif col == 'percentile':
                formatted = f"{value:.0f}th"
            elif col == 'rank':
                formatted = f"#{int(value)}"
            else:
                formatted = str(value)
            
            cells.append(ui.tags.td(formatted))
        
        # Highlight row if needed
        row_class = "clickable-row"
        if highlight_institution and row.get('institution_name') == highlight_institution:
            row_class += " highlighted"
        
        rows.append(ui.tags.tr(*cells, class_=row_class))
    
    return ui.div(
        ui.tags.table(
            ui.tags.thead(ui.tags.tr(*header_cells)),
            ui.tags.tbody(*rows),
            class_="data-table"
        ),
        class_="data-table-container"
    )


def create_peer_table(
    df: pd.DataFrame,
    target_institution: str = None,
    metric: str = 'yield_rate',
    show_rank: bool = True,
    top_n: int = 15
) -> ui.Tag:
    """
    Create a peer comparison table with rankings.
    Shows top N institutions, plus the target institution if not in top N.
    
    Args:
        df: DataFrame with peer data
        target_institution: Institution to highlight
        metric: Primary metric for ranking
        show_rank: Whether to show rank column
        top_n: Number of top institutions to display
    """
    if df.empty:
        return ui.div(
            ui.p("No peer data available", style="text-align: center; color: var(--color-text-muted); padding: 24px;"),
            class_="data-table-container"
        )
    
    # Sort by metric and assign ranks
    sorted_df = df.sort_values(metric, ascending=False).reset_index(drop=True)
    sorted_df['rank'] = range(1, len(sorted_df) + 1)
    
    # Get top N
    display_df = sorted_df.head(top_n).copy()
    
    # If target institution is not in top N, append it with a separator
    if target_institution and target_institution in sorted_df['institution_name'].values:
        target_rank = sorted_df[sorted_df['institution_name'] == target_institution]['rank'].iloc[0]
        if target_rank > top_n:
            target_row = sorted_df[sorted_df['institution_name'] == target_institution].copy()
            display_df = pd.concat([display_df, target_row], ignore_index=True)
    
    # Columns to display
    columns = ['rank', 'institution_name', metric, 'enrolled', 'state', 'institution_size']
    if 'diversity_index' in sorted_df.columns:
        columns.append('diversity_index')
    
    # Filter to available columns
    columns = [c for c in columns if c in display_df.columns or c == 'rank']
    
    return create_data_table(
        display_df,
        columns=columns,
        highlight_institution=target_institution
    )


def create_comparison_table(
    institutions: List[str],
    df: pd.DataFrame,
    year: int = None
) -> ui.Tag:
    """
    Create a side-by-side comparison table for selected institutions.
    
    Args:
        institutions: List of institution names to compare
        df: Full dataset
        year: Year to compare (None = latest)
    """
    if not institutions or df.empty:
        return ui.div(
            ui.p("Select institutions to compare", style="text-align: center; color: var(--color-text-muted); padding: 24px;"),
            class_="data-table-container"
        )
    
    # Filter to selected institutions
    if year:
        compare_df = df[(df['institution_name'].isin(institutions)) & (df['year'] == year)]
    else:
        latest_year = df['year'].max()
        compare_df = df[(df['institution_name'].isin(institutions)) & (df['year'] == latest_year)]
    
    if compare_df.empty:
        return ui.div(
            ui.p("No data available for selected institutions", style="text-align: center; color: var(--color-text-muted); padding: 24px;"),
            class_="data-table-container"
        )
    
    # Metrics to compare
    metrics = [
        ('applicants', 'Applicants'),
        ('admitted', 'Admitted'),
        ('enrolled', 'Enrolled'),
        ('admit_rate', 'Admit Rate'),
        ('yield_rate', 'Yield Rate'),
        ('diversity_index', 'Diversity Index'),
    ]
    
    # Build comparison rows
    rows = []
    
    # Header row with institution names
    header_cells = [ui.tags.th('Metric')]
    for inst in institutions[:5]:  # Limit to 5
        short_name = inst[:25] + '...' if len(inst) > 25 else inst
        header_cells.append(ui.tags.th(short_name))
    
    rows.append(ui.tags.tr(*header_cells))
    
    # Metric rows
    for col, label in metrics:
        if col not in compare_df.columns:
            continue
        
        cells = [ui.tags.td(ui.strong(label))]
        
        for inst in institutions[:5]:
            inst_data = compare_df[compare_df['institution_name'] == inst]
            if inst_data.empty:
                cells.append(ui.tags.td('-'))
            else:
                value = inst_data.iloc[0][col]
                if pd.isna(value):
                    formatted = '-'
                elif col in ['applicants', 'admitted', 'enrolled']:
                    formatted = f"{int(value):,}"
                elif col in ['admit_rate', 'yield_rate']:
                    formatted = f"{value:.1f}%"
                elif col == 'diversity_index':
                    formatted = f"{value:.3f}"
                else:
                    formatted = str(value)
                cells.append(ui.tags.td(formatted))
        
        rows.append(ui.tags.tr(*cells))
    
    return ui.div(
        ui.tags.table(
            ui.tags.thead(rows[0]),
            ui.tags.tbody(*rows[1:]),
            class_="data-table"
        ),
        class_="data-table-container"
    )


def create_download_button(button_id: str, label: str = "Download CSV") -> ui.Tag:
    """Create a download button."""
    return ui.download_button(
        button_id,
        label,
        class_="btn btn-secondary btn-sm"
    )
