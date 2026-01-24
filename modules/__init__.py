"""
Shiny modules for Higher Education Enrollment Funnel Analytics.
"""

from .filters import create_global_filters, filters_server
from .page_overview import overview_ui, overview_server
from .page_benchmarking import benchmarking_ui, benchmarking_server
from .page_institution_profile import profile_ui, profile_server
from .page_simulator import simulator_ui, simulator_server
from .components_charts import (
    create_funnel_chart,
    create_trends_chart,
    create_demographics_chart,
    create_distribution_chart,
    create_scatter_chart,
    create_waterfall_chart,
    create_state_map,
)
from .components_kpis import create_kpi_card, create_delta_badge, create_insight_card
from .components_tables import create_data_table, create_peer_table

__all__ = [
    'create_global_filters',
    'filters_server',
    'overview_ui',
    'overview_server',
    'benchmarking_ui',
    'benchmarking_server',
    'profile_ui',
    'profile_server',
    'simulator_ui',
    'simulator_server',
    'create_funnel_chart',
    'create_trends_chart',
    'create_demographics_chart',
    'create_distribution_chart',
    'create_scatter_chart',
    'create_waterfall_chart',
    'create_state_map',
    'create_kpi_card',
    'create_delta_badge',
    'create_insight_card',
    'create_data_table',
    'create_peer_table',
]
