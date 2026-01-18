"""Metric calculations for enrollment analytics."""

import pandas as pd
import numpy as np


def calculate_metrics(df: pd.DataFrame) -> dict:
    """Calculate key enrollment metrics from filtered data."""
    
    total_applicants = df['applicants'].sum()
    total_admissions = df['admissions'].sum()
    total_enrolled = df['enrolled_total'].sum()
    
    # Calculate aggregate rates
    overall_admit_rate = (total_admissions / total_applicants * 100) if total_applicants > 0 else 0
    overall_yield_rate = (total_enrolled / total_admissions * 100) if total_admissions > 0 else 0
    
    # Calculate average rates across institutions
    avg_admit_rate = df[df['admit_rate'] > 0]['admit_rate'].mean()
    avg_yield_rate = df[df['yield_rate'] > 0]['yield_rate'].mean()
    
    return {
        'total_applicants': int(total_applicants),
        'total_admissions': int(total_admissions),
        'total_enrolled': int(total_enrolled),
        'overall_admit_rate': round(overall_admit_rate, 1),
        'overall_yield_rate': round(overall_yield_rate, 1),
        'avg_admit_rate': round(avg_admit_rate, 1) if not pd.isna(avg_admit_rate) else 0,
        'avg_yield_rate': round(avg_yield_rate, 1) if not pd.isna(avg_yield_rate) else 0,
        'institution_count': df['institution_name'].nunique(),
        'year_count': df['year'].nunique(),
    }


def calculate_funnel_data(df: pd.DataFrame) -> dict:
    """Calculate funnel stage data for visualization."""
    
    total_applicants = df['applicants'].sum()
    total_admissions = df['admissions'].sum()
    total_enrolled = df['enrolled_total'].sum()
    
    admit_rate = (total_admissions / total_applicants * 100) if total_applicants > 0 else 0
    yield_rate = (total_enrolled / total_admissions * 100) if total_admissions > 0 else 0
    overall_conversion = (total_enrolled / total_applicants * 100) if total_applicants > 0 else 0
    
    return {
        'stages': ['Applicants', 'Admitted', 'Enrolled'],
        'values': [total_applicants, total_admissions, total_enrolled],
        'percentages': [100, round(admit_rate, 1), round(overall_conversion, 1)],
        'stage_rates': [None, round(admit_rate, 1), round(yield_rate, 1)],
    }


def calculate_trends_by_year(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate aggregate trends by year."""
    
    yearly = df.groupby('year').agg({
        'applicants': 'sum',
        'admissions': 'sum',
        'enrolled_total': 'sum',
        'institution_name': 'nunique'
    }).reset_index()
    
    yearly['admit_rate'] = (yearly['admissions'] / yearly['applicants'] * 100).round(1)
    yearly['yield_rate'] = (yearly['enrolled_total'] / yearly['admissions'] * 100).round(1)
    yearly['overall_rate'] = (yearly['enrolled_total'] / yearly['applicants'] * 100).round(1)
    
    yearly = yearly.rename(columns={'institution_name': 'institution_count'})
    yearly = yearly.sort_values('year')
    
    return yearly


def calculate_demographics_by_year(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate weighted average demographics by year."""
    
    # Weight demographics by enrollment
    demo_cols = ['pct_hispanic', 'pct_white', 'pct_black', 'pct_asian', 'pct_other', 'pct_nonresident']
    
    results = []
    for year in sorted(df['year'].unique()):
        year_df = df[df['year'] == year]
        total_enrolled = year_df['enrolled_total'].sum()
        
        if total_enrolled > 0:
            weighted_demos = {}
            weighted_demos['year'] = year
            
            for col in demo_cols:
                # Weight by enrollment
                weighted_avg = (year_df[col] * year_df['enrolled_total']).sum() / total_enrolled
                weighted_demos[col] = round(weighted_avg, 1)
            
            weighted_demos['total_enrolled'] = total_enrolled
            results.append(weighted_demos)
    
    return pd.DataFrame(results)


def get_top_institutions(df: pd.DataFrame, metric: str = 'yield_rate', n: int = 10) -> pd.DataFrame:
    """Get top N institutions by specified metric."""
    
    # Aggregate by institution across selected years
    agg_df = df.groupby('institution_name').agg({
        'applicants': 'sum',
        'admissions': 'sum',
        'enrolled_total': 'sum',
        'year': 'nunique'
    }).reset_index()
    
    # Calculate rates
    agg_df['admit_rate'] = np.where(
        agg_df['applicants'] > 0,
        (agg_df['admissions'] / agg_df['applicants'] * 100).round(1),
        0
    )
    
    agg_df['yield_rate'] = np.where(
        agg_df['admissions'] > 0,
        (agg_df['enrolled_total'] / agg_df['admissions'] * 100).round(1),
        0
    )
    
    # Filter out institutions with very low data (less than 100 enrolled)
    agg_df = agg_df[agg_df['enrolled_total'] >= 100]
    
    # Sort and get top N
    if metric in agg_df.columns:
        top_df = agg_df.nlargest(n, metric)
    else:
        top_df = agg_df.nlargest(n, 'enrolled_total')
    
    return top_df


def calculate_enrollment_growth(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate enrollment growth between first and last year in data."""
    
    years = sorted(df['year'].unique())
    if len(years) < 2:
        return pd.DataFrame()
    
    first_year = years[0]
    last_year = years[-1]
    
    first_df = df[df['year'] == first_year].groupby('institution_name')['enrolled_total'].sum().reset_index()
    first_df.columns = ['institution_name', 'enrolled_first']
    
    last_df = df[df['year'] == last_year].groupby('institution_name')['enrolled_total'].sum().reset_index()
    last_df.columns = ['institution_name', 'enrolled_last']
    
    merged = first_df.merge(last_df, on='institution_name')
    merged['growth'] = merged['enrolled_last'] - merged['enrolled_first']
    merged['growth_pct'] = np.where(
        merged['enrolled_first'] > 0,
        ((merged['enrolled_last'] - merged['enrolled_first']) / merged['enrolled_first'] * 100).round(1),
        0
    )
    
    return merged
