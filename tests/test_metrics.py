"""
Tests for metrics calculations.
"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.metrics import (
    calculate_yoy_delta_count,
    calculate_yoy_delta_rate,
    calculate_diversity_index,
    wilson_interval_simple,
    decompose_enrolled_variation,
    calculate_funnel_leakage,
    calculate_percentiles,
    calculate_rank_and_percentile,
)


class TestYoYDeltas:
    """Tests for YoY delta calculations."""
    
    def test_yoy_delta_count_positive(self):
        """Test positive growth."""
        result = calculate_yoy_delta_count(110, 100)
        assert result == 10.0
    
    def test_yoy_delta_count_negative(self):
        """Test negative growth."""
        result = calculate_yoy_delta_count(90, 100)
        assert result == -10.0
    
    def test_yoy_delta_count_zero_previous(self):
        """Test with zero previous value."""
        result = calculate_yoy_delta_count(100, 0)
        assert result is None
    
    def test_yoy_delta_rate_positive(self):
        """Test rate increase in pp."""
        result = calculate_yoy_delta_rate(35.0, 30.0)
        assert result == 5.0
    
    def test_yoy_delta_rate_negative(self):
        """Test rate decrease in pp."""
        result = calculate_yoy_delta_rate(25.0, 30.0)
        assert result == -5.0


class TestDiversityIndex:
    """Tests for Simpson's Diversity Index."""
    
    def test_diversity_index_uniform(self):
        """Test with uniform distribution (max diversity)."""
        # 5 equal groups of 20% each
        proportions = [0.2, 0.2, 0.2, 0.2, 0.2]
        result = calculate_diversity_index(proportions)
        # Simpson's index for uniform: 1 - 5*(0.2^2) = 1 - 0.2 = 0.8
        assert abs(result - 0.8) < 0.001
    
    def test_diversity_index_single_group(self):
        """Test with single dominant group (no diversity)."""
        proportions = [1.0, 0.0, 0.0, 0.0, 0.0]
        result = calculate_diversity_index(proportions)
        # Simpson's index: 1 - 1^2 = 0
        assert result == 0.0
    
    def test_diversity_index_two_groups(self):
        """Test with two equal groups."""
        proportions = [0.5, 0.5]
        result = calculate_diversity_index(proportions)
        # Simpson's index: 1 - 2*(0.5^2) = 1 - 0.5 = 0.5
        assert abs(result - 0.5) < 0.001
    
    def test_diversity_index_empty(self):
        """Test with empty proportions."""
        result = calculate_diversity_index([])
        assert result == 0.0
    
    def test_diversity_index_with_nan(self):
        """Test handling of NaN values."""
        proportions = [0.5, np.nan, 0.5]
        result = calculate_diversity_index(proportions)
        # Should ignore NaN and normalize remaining
        assert abs(result - 0.5) < 0.001


class TestWilsonInterval:
    """Tests for Wilson confidence intervals."""
    
    def test_wilson_interval_50_percent(self):
        """Test interval for 50% success rate."""
        lower, upper = wilson_interval_simple(50, 100)
        # 50% with n=100 should give roughly [40%, 60%] at 95% CI
        assert 38 < lower < 42
        assert 58 < upper < 62
    
    def test_wilson_interval_zero(self):
        """Test interval with zero successes."""
        lower, upper = wilson_interval_simple(0, 100)
        assert lower == 0.0
        assert 0 < upper < 5  # Upper bound should be small but positive
    
    def test_wilson_interval_all_success(self):
        """Test interval with 100% success."""
        lower, upper = wilson_interval_simple(100, 100)
        assert 95 < lower < 100
        assert upper == 100.0
    
    def test_wilson_interval_zero_total(self):
        """Test with zero total."""
        lower, upper = wilson_interval_simple(0, 0)
        assert lower == 0.0
        assert upper == 0.0


class TestDecomposition:
    """Tests for enrollment decomposition."""
    
    def test_decomposition_sum_equals_delta(self):
        """Test that effects sum to total delta."""
        result = decompose_enrolled_variation(
            applicants_base=1000,
            admit_rate_base=50,  # 50%
            yield_rate_base=40,  # 40%
            applicants_compare=1100,
            admit_rate_compare=52,  # 52%
            yield_rate_compare=42,  # 42%
        )
        
        # Base enrolled: 1000 * 0.5 * 0.4 = 200
        # Compare enrolled: 1100 * 0.52 * 0.42 = 240.24
        # Delta: ~40
        
        effects_sum = (
            result['effect_applicants'] + 
            result['effect_admit_rate'] + 
            result['effect_yield']
        )
        
        # Sum of effects should approximately equal delta_enrolled
        assert abs(effects_sum - result['delta_enrolled']) < 5  # Allow small rounding error
    
    def test_decomposition_no_change(self):
        """Test with no changes."""
        result = decompose_enrolled_variation(
            applicants_base=1000,
            admit_rate_base=50,
            yield_rate_base=40,
            applicants_compare=1000,
            admit_rate_compare=50,
            yield_rate_compare=40,
        )
        
        assert result['delta_enrolled'] == 0
        assert result['effect_applicants'] == 0
        assert result['effect_admit_rate'] == 0
        assert result['effect_yield'] == 0
    
    def test_decomposition_identifies_primary_driver(self):
        """Test primary driver identification."""
        # Large applicant change
        result = decompose_enrolled_variation(
            applicants_base=1000,
            admit_rate_base=50,
            yield_rate_base=40,
            applicants_compare=1500,  # 50% increase
            admit_rate_compare=50,
            yield_rate_compare=40,
        )
        
        assert 'applicants' in result['primary_driver']


class TestFunnelLeakage:
    """Tests for funnel leakage calculations."""
    
    def test_funnel_leakage_basic(self):
        """Test basic leakage calculation."""
        result = calculate_funnel_leakage(
            applicants=1000,
            admitted=500,
            enrolled=200
        )
        
        assert result['leakage_stage1'] == 500  # 1000 - 500
        assert result['leakage_stage2'] == 300  # 500 - 200
        assert result['total_leakage'] == 800
        assert result['selection_rate'] == 50.0
        assert result['yield_rate'] == 40.0
        assert result['overall_conversion'] == 20.0
    
    def test_funnel_leakage_zero_applicants(self):
        """Test with zero applicants."""
        result = calculate_funnel_leakage(0, 0, 0)
        
        assert result['selection_rate'] == 0
        assert result['yield_rate'] == 0
        assert result['overall_conversion'] == 0


class TestPercentiles:
    """Tests for percentile calculations."""
    
    def test_calculate_percentiles(self):
        """Test percentile calculation."""
        values = pd.Series(range(1, 101))  # 1 to 100
        result = calculate_percentiles(values)
        
        assert result['p10'] == 10.9  # 10th percentile
        assert result['p50'] == 50.5  # Median
        assert result['p90'] == 90.1  # 90th percentile
    
    def test_calculate_percentiles_empty(self):
        """Test with empty series."""
        result = calculate_percentiles(pd.Series([]))
        
        assert result['p50'] == 0
    
    def test_rank_and_percentile(self):
        """Test rank and percentile calculation."""
        values = pd.Series([10, 20, 30, 40, 50])
        
        # Test value at top
        result = calculate_rank_and_percentile(50, values)
        assert result['rank'] == 1
        assert result['percentile'] == 80.0  # 4 out of 5 are below
        
        # Test value at bottom
        result = calculate_rank_and_percentile(10, values)
        assert result['rank'] == 5
        assert result['percentile'] == 0.0  # None are below


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
