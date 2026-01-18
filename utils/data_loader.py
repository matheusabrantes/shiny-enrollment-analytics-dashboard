"""Data loading and preprocessing utilities for IPEDS enrollment data."""

import pandas as pd
import numpy as np
from pathlib import Path


def load_ipeds_data() -> pd.DataFrame:
    """Load and preprocess IPEDS enrollment data into long format."""
    data_path = Path(__file__).parent.parent / 'data' / 'ipeds_enrollment_data.csv'
    df_wide = pd.read_csv(data_path)
    
    # Drop the unnamed column
    df_wide = df_wide.drop(columns=['Unnamed: 82'], errors='ignore')
    
    # Transform to long format
    df_long = transform_to_long_format(df_wide)
    
    return df_long


def transform_to_long_format(df_wide: pd.DataFrame) -> pd.DataFrame:
    """Transform wide-format IPEDS data to long format for easier analysis."""
    
    records = []
    
    # Define year mappings
    year_configs = [
        (2024, 'DRVEF2024', 'ADM2024'),
        (2023, 'DRVEF2023_RV', 'ADM2023_RV'),
        (2022, 'DRVEF2022_RV', 'ADM2022_RV'),
    ]
    
    for _, row in df_wide.iterrows():
        unit_id = row['UnitID']
        institution_name = row['Institution Name']
        
        for year, demo_suffix, adm_suffix in year_configs:
            try:
                record = {
                    'unit_id': unit_id,
                    'institution_name': institution_name,
                    'year': year,
                    
                    # Demographics (percentages)
                    'pct_hispanic': _safe_float(row.get(f'PctEnrHS ({demo_suffix})', 0)),
                    'pct_white': _safe_float(row.get(f'PctEnrWh ({demo_suffix})', 0)),
                    'pct_black': _safe_float(row.get(f'PctEnrBK ({demo_suffix})', 0)),
                    'pct_asian': _safe_float(row.get(f'PCTENRAS ({demo_suffix})', 0)),
                    'pct_american_indian': _safe_float(row.get(f'PctEnrAN ({demo_suffix})', 0)),
                    'pct_pacific_islander': _safe_float(row.get(f'PctEnrAP ({demo_suffix})', 0)),
                    'pct_native_hawaiian': _safe_float(row.get(f'PCTENRNH ({demo_suffix})', 0)),
                    'pct_unknown': _safe_float(row.get(f'PctEnrUn ({demo_suffix})', 0)),
                    'pct_nonresident': _safe_float(row.get(f'PctEnrNr ({demo_suffix})', 0)),
                    'pct_two_or_more': _safe_float(row.get(f'PCTENR2M ({demo_suffix})', 0)),
                    
                    # Funnel metrics
                    'admissions': _safe_int(row.get(f'ADMSSN ({adm_suffix})', 0)),
                    'applicants': _safe_int(row.get(f'APPLCN ({adm_suffix})', 0)),
                    'enrolled_total': _safe_int(row.get(f'ENRLT ({adm_suffix})', 0)),
                    'enrolled_male': _safe_int(row.get(f'ENRLM ({adm_suffix})', 0)),
                    'enrolled_female': _safe_int(row.get(f'ENRLW ({adm_suffix})', 0)),
                }
                records.append(record)
            except Exception:
                continue
    
    df_long = pd.DataFrame(records)
    
    # Calculate derived metrics
    df_long['admit_rate'] = np.where(
        df_long['applicants'] > 0,
        (df_long['admissions'] / df_long['applicants'] * 100).round(1),
        0
    )
    
    df_long['yield_rate'] = np.where(
        df_long['admissions'] > 0,
        (df_long['enrolled_total'] / df_long['admissions'] * 100).round(1),
        0
    )
    
    # Group demographics for simplified view
    df_long['pct_other'] = (
        df_long['pct_american_indian'] + 
        df_long['pct_pacific_islander'] + 
        df_long['pct_native_hawaiian'] + 
        df_long['pct_two_or_more'] +
        df_long['pct_unknown']
    ).round(1)
    
    return df_long


def _safe_float(value) -> float:
    """Safely convert value to float, returning 0 on failure."""
    try:
        if pd.isna(value):
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def _safe_int(value) -> int:
    """Safely convert value to int, returning 0 on failure."""
    try:
        if pd.isna(value):
            return 0
        return int(float(value))
    except (ValueError, TypeError):
        return 0


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
