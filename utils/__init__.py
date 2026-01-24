"""Utility modules for the enrollment dashboard."""

from .data_loader import load_ipeds_data
from .calculations import calculate_metrics, get_top_institutions
from .styling import CARNEGIE_COLORS, CHART_PALETTE, get_plotly_template
from .metrics import (
    calculate_yoy_delta_count,
    calculate_yoy_delta_rate,
    get_yoy_metrics,
    calculate_funnel_leakage,
    calculate_diversity_index,
    wilson_interval_simple,
    decompose_enrolled_variation,
    calculate_percentiles,
    calculate_rank_and_percentile,
    find_similar_institutions_simple,
    generate_insights,
)
from .data_model import (
    create_canonical_dataframes,
    create_facts_by_inst_year,
    get_peer_group,
    calculate_peer_statistics,
    get_aggregate_metrics,
    simulate_enrollment,
    calculate_goal_recommendations,
)
