"""Data loading and preprocessing utilities for IPEDS enrollment data."""

import pandas as pd
from pathlib import Path


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
    
    print(f"✅ Loaded {len(df)} rows from {df['unit_id'].nunique()} institutions")
    print(f"   States: {df['state'].nunique()}")
    print(f"   Years: {sorted(df['year'].unique())}")
    
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
