"""
Advanced metrics calculations for enrollment analytics.
Includes YoY deltas, funnel leakage, diversity index, Wilson intervals, 
decomposition analysis, percentiles, and similarity calculations.
"""

import numpy as np
import pandas as pd
from functools import lru_cache
from typing import Tuple, Dict, List, Optional


# =============================================================================
# YoY Delta Calculations
# =============================================================================

def calculate_yoy_delta_count(current: float, previous: float) -> Optional[float]:
    """
    Calculate YoY delta for count metrics as percentage change.
    Returns None if previous is 0 or invalid.
    """
    if previous is None or previous == 0 or pd.isna(previous) or pd.isna(current):
        return None
    return ((current - previous) / previous) * 100


def calculate_yoy_delta_rate(current_rate: float, previous_rate: float) -> Optional[float]:
    """
    Calculate YoY delta for rate metrics as percentage points difference.
    Returns None if values are invalid.
    """
    if pd.isna(current_rate) or pd.isna(previous_rate):
        return None
    return current_rate - previous_rate


def get_yoy_metrics(df: pd.DataFrame, year: int) -> Dict:
    """
    Calculate YoY metrics comparing specified year to previous year.
    
    Returns dict with current values and deltas for key metrics.
    """
    prev_year = year - 1
    
    current_data = df[df['year'] == year]
    prev_data = df[df['year'] == prev_year]
    
    if current_data.empty:
        return {}
    
    # Current aggregates
    curr_applicants = current_data['applicants'].sum()
    curr_admitted = current_data['admissions'].sum()
    curr_enrolled = current_data['enrolled_total'].sum()
    curr_admit_rate = (curr_admitted / curr_applicants * 100) if curr_applicants > 0 else 0
    curr_yield_rate = (curr_enrolled / curr_admitted * 100) if curr_admitted > 0 else 0
    
    # Previous aggregates
    if not prev_data.empty:
        prev_applicants = prev_data['applicants'].sum()
        prev_admitted = prev_data['admissions'].sum()
        prev_enrolled = prev_data['enrolled_total'].sum()
        prev_admit_rate = (prev_admitted / prev_applicants * 100) if prev_applicants > 0 else 0
        prev_yield_rate = (prev_enrolled / prev_admitted * 100) if prev_admitted > 0 else 0
        
        delta_applicants = calculate_yoy_delta_count(curr_applicants, prev_applicants)
        delta_admitted = calculate_yoy_delta_count(curr_admitted, prev_admitted)
        delta_enrolled = calculate_yoy_delta_count(curr_enrolled, prev_enrolled)
        delta_admit_rate = calculate_yoy_delta_rate(curr_admit_rate, prev_admit_rate)
        delta_yield_rate = calculate_yoy_delta_rate(curr_yield_rate, prev_yield_rate)
    else:
        delta_applicants = delta_admitted = delta_enrolled = None
        delta_admit_rate = delta_yield_rate = None
    
    return {
        'year': year,
        'prev_year': prev_year if not prev_data.empty else None,
        'applicants': int(curr_applicants),
        'admitted': int(curr_admitted),
        'enrolled': int(curr_enrolled),
        'admit_rate': round(curr_admit_rate, 2),
        'yield_rate': round(curr_yield_rate, 2),
        'delta_applicants': round(delta_applicants, 2) if delta_applicants is not None else None,
        'delta_admitted': round(delta_admitted, 2) if delta_admitted is not None else None,
        'delta_enrolled': round(delta_enrolled, 2) if delta_enrolled is not None else None,
        'delta_admit_rate': round(delta_admit_rate, 2) if delta_admit_rate is not None else None,
        'delta_yield_rate': round(delta_yield_rate, 2) if delta_yield_rate is not None else None,
    }


# =============================================================================
# Funnel Leakage Calculations
# =============================================================================

def calculate_funnel_leakage(applicants: int, admitted: int, enrolled: int) -> Dict:
    """
    Calculate funnel leakage metrics.
    
    Returns:
        Dict with leakage counts and rates at each stage.
    """
    leakage_stage1 = applicants - admitted  # Rejected/withdrawn
    leakage_stage2 = admitted - enrolled    # Admitted but didn't enroll
    
    selection_rate = (admitted / applicants * 100) if applicants > 0 else 0
    yield_rate = (enrolled / admitted * 100) if admitted > 0 else 0
    overall_conversion = (enrolled / applicants * 100) if applicants > 0 else 0
    
    return {
        'leakage_stage1': int(leakage_stage1),
        'leakage_stage2': int(leakage_stage2),
        'total_leakage': int(leakage_stage1 + leakage_stage2),
        'selection_rate': round(selection_rate, 2),
        'yield_rate': round(yield_rate, 2),
        'overall_conversion': round(overall_conversion, 2),
    }


# =============================================================================
# Diversity Index (Simpson's Index)
# =============================================================================

def calculate_diversity_index(proportions: List[float]) -> float:
    """
    Calculate Simpson's Diversity Index: 1 - sum(p_i^2)
    
    Args:
        proportions: List of proportions (0-1 scale) for each demographic group.
                    Should sum to approximately 1.
    
    Returns:
        Diversity index between 0 (no diversity) and ~1 (high diversity).
    """
    # Filter out NaN and ensure proportions are valid
    valid_props = [p for p in proportions if not pd.isna(p) and p >= 0]
    
    if not valid_props:
        return 0.0
    
    # Normalize to ensure sum = 1
    total = sum(valid_props)
    if total == 0:
        return 0.0
    
    normalized = [p / total for p in valid_props]
    
    # Simpson's index
    sum_squared = sum(p ** 2 for p in normalized)
    return round(1 - sum_squared, 4)


def calculate_institution_diversity(row: pd.Series) -> float:
    """
    Calculate diversity index for an institution row.
    Expects columns: pct_hispanic, pct_white, pct_black, pct_asian, pct_other, pct_nonresident
    """
    demo_cols = ['pct_hispanic', 'pct_white', 'pct_black', 'pct_asian', 'pct_other', 'pct_nonresident']
    
    # Convert percentages to proportions (0-1)
    proportions = []
    for col in demo_cols:
        if col in row.index:
            val = row[col]
            # Handle both 0-100 and 0-1 scales
            if not pd.isna(val):
                prop = val / 100 if val > 1 else val
                proportions.append(prop)
    
    return calculate_diversity_index(proportions)


# =============================================================================
# Wilson Confidence Intervals for Proportions
# =============================================================================

def wilson_interval(successes: int, total: int, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate Wilson score confidence interval for a proportion.
    
    Args:
        successes: Number of successes (e.g., admitted, enrolled)
        total: Total trials (e.g., applicants, admitted)
        confidence: Confidence level (default 0.95)
    
    Returns:
        Tuple of (lower_bound, upper_bound) as percentages (0-100)
    """
    if total == 0:
        return (0.0, 0.0)
    
    from scipy import stats
    
    p = successes / total
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    
    denominator = 1 + z**2 / total
    center = (p + z**2 / (2 * total)) / denominator
    margin = z * np.sqrt((p * (1 - p) + z**2 / (4 * total)) / total) / denominator
    
    lower = max(0, center - margin) * 100
    upper = min(1, center + margin) * 100
    
    return (round(lower, 2), round(upper, 2))


def wilson_interval_simple(successes: int, total: int, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Simplified Wilson interval without scipy dependency.
    Uses z=1.96 for 95% confidence.
    """
    if total == 0:
        return (0.0, 0.0)
    
    z = 1.96 if confidence == 0.95 else 2.576 if confidence == 0.99 else 1.645
    
    p = successes / total
    denominator = 1 + z**2 / total
    center = (p + z**2 / (2 * total)) / denominator
    margin = z * np.sqrt((p * (1 - p) + z**2 / (4 * total)) / total) / denominator
    
    lower = max(0, center - margin) * 100
    upper = min(1, center + margin) * 100
    
    return (round(lower, 2), round(upper, 2))


# =============================================================================
# Decomposition of Enrolled Variation (Waterfall)
# =============================================================================

def decompose_enrolled_variation(
    applicants_base: int, admit_rate_base: float, yield_rate_base: float,
    applicants_compare: int, admit_rate_compare: float, yield_rate_compare: float
) -> Dict:
    """
    Decompose the change in enrolled students into component effects.
    
    Formula: Enrolled = Applicants × AdmitRate × YieldRate
    
    Decomposition:
        effect_applicants = (A1 - A0) × r0 × y0
        effect_admit_rate = A1 × (r1 - r0) × y0
        effect_yield = A1 × r1 × (y1 - y0)
    
    Args:
        applicants_base, admit_rate_base, yield_rate_base: Base year values (rates as decimals 0-1)
        applicants_compare, admit_rate_compare, yield_rate_compare: Compare year values
    
    Returns:
        Dict with effect sizes and total delta
    """
    # Convert rates to decimals if they're percentages
    r0 = admit_rate_base / 100 if admit_rate_base > 1 else admit_rate_base
    y0 = yield_rate_base / 100 if yield_rate_base > 1 else yield_rate_base
    r1 = admit_rate_compare / 100 if admit_rate_compare > 1 else admit_rate_compare
    y1 = yield_rate_compare / 100 if yield_rate_compare > 1 else yield_rate_compare
    
    A0, A1 = applicants_base, applicants_compare
    
    # Calculate enrolled for each period
    enrolled_base = A0 * r0 * y0
    enrolled_compare = A1 * r1 * y1
    delta_enrolled = enrolled_compare - enrolled_base
    
    # Decomposition effects
    effect_applicants = (A1 - A0) * r0 * y0
    effect_admit_rate = A1 * (r1 - r0) * y0
    effect_yield = A1 * r1 * (y1 - y0)
    
    # Residual (should be ~0 due to decomposition method)
    residual = delta_enrolled - (effect_applicants + effect_admit_rate + effect_yield)
    
    return {
        'enrolled_base': round(enrolled_base),
        'enrolled_compare': round(enrolled_compare),
        'delta_enrolled': round(delta_enrolled),
        'effect_applicants': round(effect_applicants),
        'effect_admit_rate': round(effect_admit_rate),
        'effect_yield': round(effect_yield),
        'residual': round(residual),
        'primary_driver': _identify_primary_driver(effect_applicants, effect_admit_rate, effect_yield),
    }


def _identify_primary_driver(effect_app: float, effect_admit: float, effect_yield: float) -> str:
    """Identify the primary driver of enrollment change."""
    effects = {
        'applicants': abs(effect_app),
        'admit_rate': abs(effect_admit),
        'yield_rate': abs(effect_yield),
    }
    primary = max(effects, key=effects.get)
    
    # Get the actual effect value (with sign)
    actual_effects = {
        'applicants': effect_app,
        'admit_rate': effect_admit,
        'yield_rate': effect_yield,
    }
    
    direction = 'increase' if actual_effects[primary] > 0 else 'decrease'
    return f"{primary}_{direction}"


# =============================================================================
# Percentiles and Ranks
# =============================================================================

def calculate_percentiles(values: pd.Series) -> Dict[str, float]:
    """
    Calculate key percentiles for a series of values.
    
    Returns:
        Dict with p10, p25, p50 (median), p75, p90
    """
    if values.empty:
        return {'p10': 0, 'p25': 0, 'p50': 0, 'p75': 0, 'p90': 0}
    
    return {
        'p10': round(values.quantile(0.10), 2),
        'p25': round(values.quantile(0.25), 2),
        'p50': round(values.quantile(0.50), 2),
        'p75': round(values.quantile(0.75), 2),
        'p90': round(values.quantile(0.90), 2),
    }


def calculate_rank_and_percentile(value: float, all_values: pd.Series) -> Dict:
    """
    Calculate rank and percentile for a value within a distribution.
    
    Returns:
        Dict with rank (1-indexed), total, and percentile
    """
    if all_values.empty or pd.isna(value):
        return {'rank': None, 'total': 0, 'percentile': None}
    
    sorted_vals = all_values.sort_values(ascending=False)
    total = len(sorted_vals)
    
    # Find rank (1-indexed, higher is better)
    rank = (sorted_vals > value).sum() + 1
    
    # Percentile (what % of values are below this value)
    percentile = ((all_values < value).sum() / total) * 100
    
    return {
        'rank': int(rank),
        'total': int(total),
        'percentile': round(percentile, 1),
    }


# =============================================================================
# Similarity / kNN for Peer Groups
# =============================================================================

def calculate_institution_features(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """
    Create feature matrix for institution similarity calculation.
    
    Features: applicants, admit_rate, yield_rate, enrolled, diversity_index,
              demographic composition
    """
    year_data = df[df['year'] == year].copy()
    
    if year_data.empty:
        return pd.DataFrame()
    
    # Calculate diversity index for each institution
    year_data['diversity_index'] = year_data.apply(calculate_institution_diversity, axis=1)
    
    # Select features for similarity
    feature_cols = ['applicants', 'admit_rate', 'yield_rate', 'enrolled_total', 'diversity_index',
                    'pct_hispanic', 'pct_white', 'pct_black', 'pct_asian']
    
    features = year_data[['institution_name', 'unit_id'] + feature_cols].copy()
    
    # Fill NaN with 0 for calculation
    for col in feature_cols:
        features[col] = features[col].fillna(0)
    
    return features


@lru_cache(maxsize=128)
def find_similar_institutions_cached(target_id: int, year: int, k: int, data_hash: str) -> List[str]:
    """
    Cached wrapper for finding similar institutions.
    data_hash is used to invalidate cache when data changes.
    """
    # This is a placeholder - actual implementation would need the dataframe
    return []


def find_similar_institutions(
    df: pd.DataFrame, 
    target_institution: str, 
    year: int, 
    k: int = 15
) -> pd.DataFrame:
    """
    Find k most similar institutions using standardized features and Euclidean distance.
    
    Args:
        df: Full dataset
        target_institution: Name of target institution
        year: Year for comparison
        k: Number of similar institutions to return
    
    Returns:
        DataFrame with similar institutions and their distances
    """
    features = calculate_institution_features(df, year)
    
    if features.empty or target_institution not in features['institution_name'].values:
        return pd.DataFrame()
    
    # Get target features
    target_row = features[features['institution_name'] == target_institution].iloc[0]
    
    # Feature columns for similarity
    feature_cols = ['applicants', 'admit_rate', 'yield_rate', 'enrolled_total', 'diversity_index',
                    'pct_hispanic', 'pct_white', 'pct_black', 'pct_asian']
    
    # Standardize features
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    
    feature_matrix = features[feature_cols].values
    scaled_features = scaler.fit_transform(feature_matrix)
    
    # Get target index and features
    target_idx = features[features['institution_name'] == target_institution].index[0]
    target_idx_pos = features.index.get_loc(target_idx)
    target_scaled = scaled_features[target_idx_pos]
    
    # Calculate Euclidean distances
    distances = np.sqrt(((scaled_features - target_scaled) ** 2).sum(axis=1))
    
    features_copy = features.copy()
    features_copy['distance'] = distances
    
    # Exclude target and get top k
    similar = features_copy[features_copy['institution_name'] != target_institution]
    similar = similar.nsmallest(k, 'distance')
    
    return similar[['institution_name', 'unit_id', 'distance', 'applicants', 
                    'admit_rate', 'yield_rate', 'enrolled_total', 'diversity_index']]


def find_similar_institutions_simple(
    df: pd.DataFrame, 
    target_institution: str, 
    year: int, 
    k: int = 15
) -> pd.DataFrame:
    """
    Simplified version without sklearn dependency.
    Uses manual standardization.
    """
    features = calculate_institution_features(df, year)
    
    if features.empty or target_institution not in features['institution_name'].values:
        return pd.DataFrame()
    
    feature_cols = ['applicants', 'admit_rate', 'yield_rate', 'enrolled_total', 'diversity_index']
    
    # Manual standardization
    for col in feature_cols:
        mean = features[col].mean()
        std = features[col].std()
        if std > 0:
            features[f'{col}_scaled'] = (features[col] - mean) / std
        else:
            features[f'{col}_scaled'] = 0
    
    scaled_cols = [f'{col}_scaled' for col in feature_cols]
    
    # Get target values
    target_row = features[features['institution_name'] == target_institution].iloc[0]
    target_scaled = target_row[scaled_cols].values
    
    # Calculate distances
    def calc_distance(row):
        row_scaled = row[scaled_cols].values
        return np.sqrt(((row_scaled - target_scaled) ** 2).sum())
    
    features['distance'] = features.apply(calc_distance, axis=1)
    
    # Exclude target and get top k
    similar = features[features['institution_name'] != target_institution]
    similar = similar.nsmallest(k, 'distance')
    
    return similar[['institution_name', 'unit_id', 'distance', 'applicants', 
                    'admit_rate', 'yield_rate', 'enrolled_total', 'diversity_index']]


# =============================================================================
# Insight Generation
# =============================================================================

def generate_insights(
    institution_data: Dict,
    peer_percentiles: Dict,
    yoy_metrics: Dict
) -> List[Dict]:
    """
    Generate dynamic insights based on institution performance vs peers.
    
    Returns:
        List of insight dicts with type, message, and severity
    """
    insights = []
    
    # Yield insights
    if 'yield_rate' in institution_data and 'yield_rate' in peer_percentiles:
        yield_val = institution_data['yield_rate']
        p75 = peer_percentiles['yield_rate'].get('p75', 0)
        p25 = peer_percentiles['yield_rate'].get('p25', 0)
        
        if yield_val > p75:
            insights.append({
                'type': 'success',
                'metric': 'yield_rate',
                'message': f"Strong yield rate ({yield_val:.1f}%) above 75th percentile ({p75:.1f}%)",
                'detail': "Indicates strong student intent and institutional attractiveness"
            })
        elif yield_val < p25:
            insights.append({
                'type': 'warning',
                'metric': 'yield_rate',
                'message': f"Yield rate ({yield_val:.1f}%) below 25th percentile ({p25:.1f}%)",
                'detail': "Consider strategies to improve conversion of admitted students"
            })
    
    # Admit rate insights
    if 'admit_rate' in institution_data and 'admit_rate' in peer_percentiles:
        admit_val = institution_data['admit_rate']
        p25 = peer_percentiles['admit_rate'].get('p25', 0)
        
        if admit_val < p25:
            insights.append({
                'type': 'info',
                'metric': 'admit_rate',
                'message': f"High selectivity with {admit_val:.1f}% admit rate",
                'detail': "Below 25th percentile indicates competitive admissions"
            })
    
    # YoY enrolled change
    if yoy_metrics and yoy_metrics.get('delta_enrolled') is not None:
        delta = yoy_metrics['delta_enrolled']
        if delta < -5:
            driver = yoy_metrics.get('primary_driver', '')
            # Provide clear fallback message if driver is unknown or empty
            if driver and driver != 'unknown':
                driver_text = driver.replace('_', ' ').title()
                detail_msg = f"Primary driver: {driver_text}"
            else:
                detail_msg = "Insufficient data to compute drivers for this institution"
            insights.append({
                'type': 'danger',
                'metric': 'enrolled',
                'message': f"Enrollment declined {abs(delta):.1f}% year-over-year",
                'detail': detail_msg
            })
        elif delta > 10:
            insights.append({
                'type': 'success',
                'metric': 'enrolled',
                'message': f"Strong enrollment growth of {delta:.1f}% year-over-year",
                'detail': "Positive momentum in student recruitment"
            })
    
    # Diversity insights
    if 'diversity_index' in institution_data and 'diversity_index' in peer_percentiles:
        div_val = institution_data['diversity_index']
        p75 = peer_percentiles['diversity_index'].get('p75', 0)
        
        if div_val > p75:
            insights.append({
                'type': 'info',
                'metric': 'diversity',
                'message': f"High diversity composition (index: {div_val:.3f})",
                'detail': "Above 75th percentile relative to peers"
            })
    
    return insights[:6]  # Limit to 6 insights
