"""
Data model utilities for creating canonical dataframes.
Creates pre-aggregated facts, demographics, and geographic data for performance.
"""

import pandas as pd
import numpy as np
from functools import lru_cache
from typing import Tuple, Dict
from .metrics import calculate_institution_diversity


def create_canonical_dataframes(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Create three canonical dataframes from raw IPEDS data.
    
    Returns:
        Tuple of (facts_by_inst_year, demographics_by_inst_year_group, geo_state_year)
    """
    facts = create_facts_by_inst_year(df)
    demographics = create_demographics_by_inst_year_group(df)
    geo = create_geo_state_year(df)
    
    return facts, demographics, geo


def create_facts_by_inst_year(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create facts table: one row per institution and year.
    
    Columns:
        - unit_id, institution_name, year
        - applicants, admitted, enrolled
        - admit_rate, yield_rate, overall_conversion
        - region, state, city, zip_code, institution_size
        - diversity_index
    """
    # Group by institution and year
    facts = df.groupby(['unit_id', 'institution_name', 'year']).agg({
        'applicants': 'sum',
        'admissions': 'sum',
        'enrolled_total': 'sum',
        'state': 'first',
        'city': 'first',
        'zip_code': 'first',
        'region': 'first',
        'institution_size': 'first',
        'pct_hispanic': 'first',
        'pct_white': 'first',
        'pct_black': 'first',
        'pct_asian': 'first',
        'pct_other': 'first',
        'pct_nonresident': 'first',
    }).reset_index()
    
    # Rename for clarity
    facts = facts.rename(columns={
        'admissions': 'admitted',
        'enrolled_total': 'enrolled'
    })
    
    # Calculate rates with safe division
    facts['admit_rate'] = np.where(
        facts['applicants'] > 0,
        (facts['admitted'] / facts['applicants'] * 100).round(2),
        0
    )
    
    facts['yield_rate'] = np.where(
        facts['admitted'] > 0,
        (facts['enrolled'] / facts['admitted'] * 100).round(2),
        0
    )
    
    facts['overall_conversion'] = np.where(
        facts['applicants'] > 0,
        (facts['enrolled'] / facts['applicants'] * 100).round(2),
        0
    )
    
    # Calculate diversity index
    facts['diversity_index'] = facts.apply(calculate_institution_diversity, axis=1)
    
    # Calculate funnel leakage
    facts['leakage_stage1'] = facts['applicants'] - facts['admitted']
    facts['leakage_stage2'] = facts['admitted'] - facts['enrolled']
    
    return facts


def create_demographics_by_inst_year_group(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create demographics table: one row per institution, year, and demographic group.
    
    Columns:
        - unit_id, institution_name, year
        - demographic_group
        - pct (0-1 scale)
        - count_estimated (enrolled * pct)
    """
    # Demographic columns mapping
    demo_mapping = {
        'pct_hispanic': 'Hispanic/Latino',
        'pct_white': 'White',
        'pct_black': 'Black',
        'pct_asian': 'Asian',
        'pct_other': 'Other',
        'pct_nonresident': 'Non-Resident',
    }
    
    records = []
    
    for _, row in df.iterrows():
        enrolled = row.get('enrolled_total', 0)
        
        for col, group_name in demo_mapping.items():
            pct_value = row.get(col, 0)
            
            # Normalize to 0-1 if in 0-100 scale
            if not pd.isna(pct_value):
                pct = pct_value / 100 if pct_value > 1 else pct_value
            else:
                pct = 0
            
            count_estimated = int(enrolled * pct) if enrolled > 0 else 0
            
            records.append({
                'unit_id': row['unit_id'],
                'institution_name': row['institution_name'],
                'year': row['year'],
                'demographic_group': group_name,
                'pct': round(pct, 4),
                'count_estimated': count_estimated,
            })
    
    return pd.DataFrame(records)


def create_geo_state_year(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create geographic aggregation: one row per state and year.
    
    Columns:
        - state, region, year
        - enrolled_total, applicants_total, admitted_total
        - num_institutions
        - yield_weighted, admit_weighted
    """
    geo = df.groupby(['state', 'region', 'year']).agg({
        'enrolled_total': 'sum',
        'applicants': 'sum',
        'admissions': 'sum',
        'unit_id': 'nunique',
    }).reset_index()
    
    geo = geo.rename(columns={
        'enrolled_total': 'enrolled_total',
        'admissions': 'admitted_total',
        'applicants': 'applicants_total',
        'unit_id': 'num_institutions',
    })
    
    # Calculate weighted rates
    geo['yield_weighted'] = np.where(
        geo['admitted_total'] > 0,
        (geo['enrolled_total'] / geo['admitted_total'] * 100).round(2),
        0
    )
    
    geo['admit_weighted'] = np.where(
        geo['applicants_total'] > 0,
        (geo['admitted_total'] / geo['applicants_total'] * 100).round(2),
        0
    )
    
    return geo


# =============================================================================
# Peer Group Filtering
# =============================================================================

def get_peer_group(
    facts: pd.DataFrame,
    target_institution: str,
    year: int,
    peer_type: str = 'national',
    n: int = 25,
    similar_institutions: pd.DataFrame = None
) -> pd.DataFrame:
    """
    Get peer group based on specified criteria.
    
    Args:
        facts: Facts dataframe
        target_institution: Name of target institution
        year: Year for comparison
        peer_type: One of 'national', 'same_region', 'same_state', 'same_size', 
                   'top_n_applicants', 'similar'
        n: Number for top_n or similar
        similar_institutions: Pre-calculated similar institutions (for 'similar' type)
    
    Returns:
        Filtered DataFrame of peer institutions
    """
    year_data = facts[facts['year'] == year].copy()
    
    if year_data.empty:
        return pd.DataFrame()
    
    # Get target institution info
    target_data = year_data[year_data['institution_name'] == target_institution]
    if target_data.empty:
        return year_data  # Return all if target not found
    
    target_row = target_data.iloc[0]
    
    if peer_type == 'national':
        return year_data
    
    elif peer_type == 'same_region':
        return year_data[year_data['region'] == target_row['region']]
    
    elif peer_type == 'same_state':
        return year_data[year_data['state'] == target_row['state']]
    
    elif peer_type == 'same_size':
        return year_data[year_data['institution_size'] == target_row['institution_size']]
    
    elif peer_type == 'top_n_applicants':
        return year_data.nlargest(n, 'applicants')
    
    elif peer_type == 'similar' and similar_institutions is not None:
        similar_names = similar_institutions['institution_name'].tolist()
        similar_names.append(target_institution)  # Include target
        return year_data[year_data['institution_name'].isin(similar_names)]
    
    return year_data


def calculate_peer_statistics(peer_group: pd.DataFrame, metric: str) -> Dict:
    """
    Calculate statistics for a peer group on a specific metric.
    
    Returns:
        Dict with mean, median, std, percentiles, min, max
    """
    if peer_group.empty or metric not in peer_group.columns:
        return {}
    
    values = peer_group[metric].dropna()
    
    if values.empty:
        return {}
    
    return {
        'mean': round(values.mean(), 2),
        'median': round(values.median(), 2),
        'std': round(values.std(), 2),
        'min': round(values.min(), 2),
        'max': round(values.max(), 2),
        'p10': round(values.quantile(0.10), 2),
        'p25': round(values.quantile(0.25), 2),
        'p50': round(values.quantile(0.50), 2),
        'p75': round(values.quantile(0.75), 2),
        'p90': round(values.quantile(0.90), 2),
        'count': len(values),
    }


# =============================================================================
# YoY Calculations for Facts Table
# =============================================================================

def add_yoy_columns(facts: pd.DataFrame) -> pd.DataFrame:
    """
    Add YoY delta columns to facts table.
    """
    facts = facts.sort_values(['unit_id', 'year'])
    
    # Calculate YoY for each institution
    for col in ['applicants', 'admitted', 'enrolled']:
        facts[f'{col}_yoy'] = facts.groupby('unit_id')[col].pct_change() * 100
    
    # For rates, calculate pp difference
    for col in ['admit_rate', 'yield_rate']:
        facts[f'{col}_yoy'] = facts.groupby('unit_id')[col].diff()
    
    return facts


# =============================================================================
# Aggregation Helpers
# =============================================================================

def aggregate_by_filters(
    facts: pd.DataFrame,
    years: list = None,
    regions: list = None,
    states: list = None,
    sizes: list = None,
    institutions: list = None
) -> pd.DataFrame:
    """
    Apply filters to facts dataframe.
    """
    filtered = facts.copy()
    
    if years:
        filtered = filtered[filtered['year'].isin(years)]
    
    if regions:
        filtered = filtered[filtered['region'].isin(regions)]
    
    if states:
        filtered = filtered[filtered['state'].isin(states)]
    
    if sizes:
        filtered = filtered[filtered['institution_size'].isin(sizes)]
    
    if institutions:
        filtered = filtered[filtered['institution_name'].isin(institutions)]
    
    return filtered


def get_aggregate_metrics(facts: pd.DataFrame) -> Dict:
    """
    Calculate aggregate metrics from filtered facts.
    """
    if facts.empty:
        return {
            'total_applicants': 0,
            'total_admitted': 0,
            'total_enrolled': 0,
            'admit_rate': 0,
            'yield_rate': 0,
            'overall_conversion': 0,
            'institution_count': 0,
            'avg_diversity': 0,
        }
    
    total_applicants = facts['applicants'].sum()
    total_admitted = facts['admitted'].sum()
    total_enrolled = facts['enrolled'].sum()
    
    return {
        'total_applicants': int(total_applicants),
        'total_admitted': int(total_admitted),
        'total_enrolled': int(total_enrolled),
        'admit_rate': round((total_admitted / total_applicants * 100), 2) if total_applicants > 0 else 0,
        'yield_rate': round((total_enrolled / total_admitted * 100), 2) if total_admitted > 0 else 0,
        'overall_conversion': round((total_enrolled / total_applicants * 100), 2) if total_applicants > 0 else 0,
        'institution_count': facts['institution_name'].nunique(),
        'avg_diversity': round(facts['diversity_index'].mean(), 4) if 'diversity_index' in facts.columns else 0,
    }


# =============================================================================
# Scenario Simulation
# =============================================================================

def simulate_enrollment(
    base_applicants: int,
    base_admit_rate: float,
    base_yield_rate: float,
    applicants_change_pct: float = 0,
    admit_rate_change_pp: float = 0,
    yield_rate_change_pp: float = 0
) -> Dict:
    """
    Simulate projected enrollment based on changes to funnel metrics.
    
    Args:
        base_applicants: Current applicants count
        base_admit_rate: Current admit rate (0-100)
        base_yield_rate: Current yield rate (0-100)
        applicants_change_pct: Percentage change in applicants (-30 to +30)
        admit_rate_change_pp: Percentage point change in admit rate (-10 to +10)
        yield_rate_change_pp: Percentage point change in yield rate (-10 to +10)
    
    Returns:
        Dict with projected values and deltas
    """
    # Calculate base enrolled
    base_enrolled = base_applicants * (base_admit_rate / 100) * (base_yield_rate / 100)
    
    # Apply changes
    proj_applicants = base_applicants * (1 + applicants_change_pct / 100)
    proj_admit_rate = max(0, min(100, base_admit_rate + admit_rate_change_pp))
    proj_yield_rate = max(0, min(100, base_yield_rate + yield_rate_change_pp))
    
    # Calculate projected enrolled
    proj_enrolled = proj_applicants * (proj_admit_rate / 100) * (proj_yield_rate / 100)
    proj_admitted = proj_applicants * (proj_admit_rate / 100)
    
    # Overall conversion
    proj_conversion = (proj_enrolled / proj_applicants * 100) if proj_applicants > 0 else 0
    
    return {
        'base_applicants': int(base_applicants),
        'base_admit_rate': round(base_admit_rate, 2),
        'base_yield_rate': round(base_yield_rate, 2),
        'base_enrolled': round(base_enrolled),
        'proj_applicants': round(proj_applicants),
        'proj_admitted': round(proj_admitted),
        'proj_admit_rate': round(proj_admit_rate, 2),
        'proj_yield_rate': round(proj_yield_rate, 2),
        'proj_enrolled': round(proj_enrolled),
        'proj_conversion': round(proj_conversion, 2),
        'delta_enrolled': round(proj_enrolled - base_enrolled),
        'delta_enrolled_pct': round((proj_enrolled - base_enrolled) / base_enrolled * 100, 2) if base_enrolled > 0 else 0,
    }


def calculate_goal_recommendations(
    base_applicants: int,
    base_admit_rate: float,
    base_yield_rate: float,
    enrollment_goal: int
) -> Dict:
    """
    Calculate minimum changes needed to reach enrollment goal.
    Prioritizes yield, then admit rate, then applicants.
    """
    base_enrolled = base_applicants * (base_admit_rate / 100) * (base_yield_rate / 100)
    gap = enrollment_goal - base_enrolled
    
    if gap <= 0:
        return {
            'goal_met': True,
            'message': 'Current trajectory meets or exceeds goal',
            'recommendations': []
        }
    
    recommendations = []
    
    # Try yield improvement first (max +10pp)
    max_yield = min(100, base_yield_rate + 10)
    enrolled_with_max_yield = base_applicants * (base_admit_rate / 100) * (max_yield / 100)
    
    if enrolled_with_max_yield >= enrollment_goal:
        needed_yield = (enrollment_goal / (base_applicants * base_admit_rate / 100)) * 100
        yield_change = needed_yield - base_yield_rate
        recommendations.append({
            'lever': 'yield_rate',
            'change': round(yield_change, 2),
            'unit': 'pp',
            'priority': 1,
            'message': f'Increase yield rate by {yield_change:.1f}pp to {needed_yield:.1f}%'
        })
        return {'goal_met': True, 'recommendations': recommendations}
    
    # Add max yield improvement
    if max_yield > base_yield_rate:
        recommendations.append({
            'lever': 'yield_rate',
            'change': 10,
            'unit': 'pp',
            'priority': 1,
            'message': f'Maximize yield rate to {max_yield:.1f}%'
        })
    
    # Try admit rate improvement (max +10pp)
    max_admit = min(100, base_admit_rate + 10)
    enrolled_with_both = base_applicants * (max_admit / 100) * (max_yield / 100)
    
    if enrolled_with_both >= enrollment_goal:
        # Calculate needed admit rate
        needed_admit = (enrollment_goal / (base_applicants * max_yield / 100)) * 100
        admit_change = needed_admit - base_admit_rate
        recommendations.append({
            'lever': 'admit_rate',
            'change': round(admit_change, 2),
            'unit': 'pp',
            'priority': 2,
            'message': f'Increase admit rate by {admit_change:.1f}pp to {needed_admit:.1f}%'
        })
        return {'goal_met': True, 'recommendations': recommendations}
    
    # Add max admit improvement
    if max_admit > base_admit_rate:
        recommendations.append({
            'lever': 'admit_rate',
            'change': 10,
            'unit': 'pp',
            'priority': 2,
            'message': f'Maximize admit rate to {max_admit:.1f}%'
        })
    
    # Finally, calculate needed applicant increase
    needed_applicants = enrollment_goal / (max_admit / 100) / (max_yield / 100)
    applicants_change = ((needed_applicants - base_applicants) / base_applicants) * 100
    
    recommendations.append({
        'lever': 'applicants',
        'change': round(applicants_change, 2),
        'unit': '%',
        'priority': 3,
        'message': f'Increase applicants by {applicants_change:.1f}% to {int(needed_applicants):,}'
    })
    
    return {
        'goal_met': applicants_change <= 30,
        'recommendations': recommendations,
        'message': 'Combination of improvements needed' if applicants_change <= 30 else 'Goal may be challenging with current constraints'
    }
