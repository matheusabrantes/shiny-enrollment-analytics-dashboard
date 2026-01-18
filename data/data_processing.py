"""
Process IPEDS data files and prepare for dashboard.
Transforms wide-format data to long format with state information.
"""

import pandas as pd
import numpy as np
from pathlib import Path


def process_ipeds_data():
    """Process IPEDS data and save as cleaned CSV."""
    
    data_dir = Path(__file__).parent
    input_file = data_dir / 'Data_1-18-2026---386.csv'
    output_file = data_dir / 'ipeds_enrollment_data.csv'
    
    print("Loading raw IPEDS data...")
    df_wide = pd.read_csv(input_file, low_memory=False)
    
    print(f"Raw data shape: {df_wide.shape}")
    print(f"Columns: {list(df_wide.columns)}")
    
    # Transform to long format
    records = []
    
    year_configs = [
        (2024, 'DRVEF2024', 'ADM2024', 'HD2024'),
        (2023, 'DRVEF2023_RV', 'ADM2023_RV', 'HD2023'),
        (2022, 'DRVEF2022_RV', 'ADM2022_RV', 'HD2022'),
    ]
    
    for _, row in df_wide.iterrows():
        unit_id = row['UnitID']
        institution_name = row['Institution Name']
        
        for year, demo_suffix, adm_suffix, hd_suffix in year_configs:
            try:
                record = {
                    'unit_id': unit_id,
                    'institution_name': institution_name,
                    'year': year,
                    
                    # Location data
                    'state': _safe_str(row.get(f'STABBR ({hd_suffix})', '')),
                    'city': _safe_str(row.get(f'CITY ({hd_suffix})', '')),
                    'zip_code': _safe_str(row.get(f'ZIP ({hd_suffix})', '')),
                    
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
            except Exception as e:
                print(f"Error processing {institution_name} for year {year}: {e}")
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
    
    # Filter out rows with no state
    df_long = df_long[df_long['state'].notna() & (df_long['state'] != '')]
    
    # Save processed data
    df_long.to_csv(output_file, index=False)
    
    print(f"\n✅ Data processed successfully!")
    print(f"Total rows: {len(df_long)}")
    print(f"Institutions: {df_long['unit_id'].nunique()}")
    print(f"Years: {sorted(df_long['year'].unique())}")
    print(f"States: {df_long['state'].nunique()}")
    print(f"\nTop 10 states by institutions:")
    print(df_long.groupby('state')['unit_id'].nunique().sort_values(ascending=False).head(10))
    
    return df_long


def _safe_float(value) -> float:
    """Safely convert value to float."""
    try:
        if pd.isna(value):
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def _safe_int(value) -> int:
    """Safely convert value to int."""
    try:
        if pd.isna(value):
            return 0
        return int(float(value))
    except (ValueError, TypeError):
        return 0


def _safe_str(value) -> str:
    """Safely convert value to string."""
    try:
        if pd.isna(value):
            return ''
        return str(value).strip()
    except (ValueError, TypeError):
        return ''


if __name__ == "__main__":
    process_ipeds_data()
