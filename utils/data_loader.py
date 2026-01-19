"""Data loading and preprocessing utilities for IPEDS enrollment data."""

import pandas as pd
import numpy as np
from pathlib import Path


# US Census Bureau regions mapping
STATE_TO_REGION = {
    # Northeast
    'CT': 'Northeast', 'ME': 'Northeast', 'MA': 'Northeast', 'NH': 'Northeast',
    'RI': 'Northeast', 'VT': 'Northeast', 'NJ': 'Northeast', 'NY': 'Northeast', 'PA': 'Northeast',
    # Midwest
    'IL': 'Midwest', 'IN': 'Midwest', 'MI': 'Midwest', 'OH': 'Midwest', 'WI': 'Midwest',
    'IA': 'Midwest', 'KS': 'Midwest', 'MN': 'Midwest', 'MO': 'Midwest', 'NE': 'Midwest',
    'ND': 'Midwest', 'SD': 'Midwest',
    # South
    'DE': 'South', 'FL': 'South', 'GA': 'South', 'MD': 'South', 'NC': 'South',
    'SC': 'South', 'VA': 'South', 'DC': 'South', 'WV': 'South', 'AL': 'South',
    'KY': 'South', 'MS': 'South', 'TN': 'South', 'AR': 'South', 'LA': 'South',
    'OK': 'South', 'TX': 'South',
    # West
    'AZ': 'West', 'CO': 'West', 'ID': 'West', 'MT': 'West', 'NV': 'West',
    'NM': 'West', 'UT': 'West', 'WY': 'West', 'AK': 'West', 'CA': 'West',
    'HI': 'West', 'OR': 'West', 'WA': 'West',
    # Territories
    'PR': 'Territories', 'VI': 'Territories', 'GU': 'Territories', 
    'AS': 'Territories', 'MP': 'Territories',
}


def load_ipeds_data() -> pd.DataFrame:
    """Load pre-processed IPEDS enrollment data."""
    data_path = Path(__file__).parent.parent / 'data' / 'ipeds_enrollment_data.csv'
    df = pd.read_csv(data_path)
    
    # Verify required columns exist
    required_cols = ['unit_id', 'institution_name', 'state', 'year', 
                     'applicants', 'admissions', 'enrolled_total']
    
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Add region column
    df['region'] = df['state'].map(STATE_TO_REGION).fillna('Other')
    
    # Calculate institution size (porte) based on percentiles of enrolled_total
    df = _calculate_institution_size(df)
    
    print(f"✅ Loaded {len(df)} rows from {df['unit_id'].nunique()} institutions")
    print(f"   States: {df['state'].nunique()}")
    print(f"   Regions: {df['region'].nunique()}")
    print(f"   Years: {sorted(df['year'].unique())}")
    
    return df


def _calculate_institution_size(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate institution size category based on p33/p66 percentiles of enrolled_total."""
    # Calculate percentiles based on the most recent year's data per institution
    latest_year = df['year'].max()
    latest_data = df[df['year'] == latest_year].copy()
    
    # Calculate percentiles
    p33 = latest_data['enrolled_total'].quantile(0.33)
    p66 = latest_data['enrolled_total'].quantile(0.66)
    
    print(f"   Size thresholds: Small < {p33:.0f} | Medium < {p66:.0f} | Large >= {p66:.0f}")
    
    # Create size mapping per institution
    def categorize_size(row):
        enrolled = row['enrolled_total']
        if enrolled < p33:
            return 'Small'
        elif enrolled < p66:
            return 'Medium'
        else:
            return 'Large'
    
    df['institution_size'] = df.apply(categorize_size, axis=1)
    
    return df


def get_unique_years(df: pd.DataFrame) -> list:
    """Get sorted list of unique years."""
    return sorted(df['year'].unique().tolist(), reverse=True)


def get_unique_institutions(df: pd.DataFrame) -> list:
    """Get sorted list of unique institution names."""
    return sorted(df['institution_name'].unique().tolist())


def get_state_from_name(institution_name: str) -> str:
    """Extract state abbreviation from institution name if present."""
    # This is a placeholder - actual implementation would need state data
    return "Unknown"


def get_unique_states(df: pd.DataFrame) -> list:
    """Get sorted list of unique states."""
    return sorted(df['state'].dropna().unique().tolist())


def get_unique_regions(df: pd.DataFrame) -> list:
    """Get sorted list of unique regions."""
    return sorted(df['region'].dropna().unique().tolist())


def get_unique_sizes(df: pd.DataFrame) -> list:
    """Get list of institution sizes in order."""
    return ['Small', 'Medium', 'Large']


def get_states_by_region(df: pd.DataFrame) -> dict:
    """Get dictionary mapping regions to their states."""
    result = {}
    for region in df['region'].unique():
        states = sorted(df[df['region'] == region]['state'].unique().tolist())
        result[region] = states
    return result
