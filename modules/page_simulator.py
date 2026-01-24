"""
Scenario Simulator page module.
Provides what-if analysis for enrollment projections.
"""

from shiny import ui, reactive, render, module
from shinywidgets import output_widget, render_widget
import pandas as pd
import plotly.graph_objects as go

from .components_kpis import create_kpi_card
from utils.data_model import simulate_enrollment, calculate_goal_recommendations


def simulator_ui():
    """Create the Simulator page UI."""
    return ui.div(
        # Page header with Export PDF button
        ui.div(
            ui.div(
                ui.h2("Scenario Simulator", class_="section-title", style="margin: 0;"),
                ui.tags.button(
                    "📄 Export PDF",
                    onclick="exportPageAsPDF()",
                    class_="btn-export-pdf",
                    style="margin-left: auto;"
                ),
                style="display: flex; justify-content: space-between; align-items: center; gap: 24px;"
            ),
            ui.p("Project enrollment outcomes based on changes to funnel metrics", 
                 class_="section-subtitle"),
            class_="section-header",
            style="margin-bottom: 24px;"
        ),
        
        ui.div(
            # Left column: Controls
            ui.div(
                # Base Settings Card
                ui.div(
                    ui.div(
                        ui.h3("Base Settings", class_="card-title"),
                        class_="card-header"
                    ),
                    ui.div(
                        # Institution selector
                        ui.div(
                            ui.div("Target Institution", class_="filter-label"),
                            ui.output_ui("sim_institution_selector"),
                            class_="filter-group",
                            style="margin-bottom: 16px;"
                        ),
                        
                        # Base year
                        ui.div(
                            ui.div("Base Year", class_="filter-label"),
                            ui.output_ui("sim_year_selector"),
                            class_="filter-group",
                            style="margin-bottom: 16px;"
                        ),
                        
                        # Current metrics display
                        ui.output_ui("sim_base_metrics"),
                        
                        class_="card-body"
                    ),
                    class_="card",
                    style="margin-bottom: 16px;"
                ),
                
                # Scenario Sliders Card
                ui.div(
                    ui.div(
                        ui.h3("Scenario Adjustments", class_="card-title"),
                        class_="card-header"
                    ),
                    ui.div(
                        # Applicants change
                        ui.div(
                            ui.div(
                                ui.span("Applicants Change", class_="slider-name"),
                                ui.output_text("sim_applicants_value", inline=True),
                                class_="slider-label"
                            ),
                            ui.input_slider(
                                "sim_applicants_change",
                                None,
                                min=-30,
                                max=30,
                                value=0,
                                step=1,
                                post="%"
                            ),
                            class_="slider-group"
                        ),
                        
                        # Admit rate change
                        ui.div(
                            ui.div(
                                ui.span("Admit Rate Change", class_="slider-name"),
                                ui.output_text("sim_admit_value", inline=True),
                                class_="slider-label"
                            ),
                            ui.input_slider(
                                "sim_admit_change",
                                None,
                                min=-10,
                                max=10,
                                value=0,
                                step=0.5,
                                post=" pp"
                            ),
                            class_="slider-group"
                        ),
                        
                        # Yield rate change
                        ui.div(
                            ui.div(
                                ui.span("Yield Rate Change", class_="slider-name"),
                                ui.output_text("sim_yield_value", inline=True),
                                class_="slider-label"
                            ),
                            ui.input_slider(
                                "sim_yield_change",
                                None,
                                min=-10,
                                max=10,
                                value=0,
                                step=0.5,
                                post=" pp"
                            ),
                            class_="slider-group"
                        ),
                        
                        # Reset button
                        ui.input_action_button(
                            "sim_reset",
                            "↻ Reset Sliders",
                            class_="btn btn-secondary",
                            style="width: 100%; margin-top: 16px;"
                        ),
                        
                        class_="card-body"
                    ),
                    class_="card",
                    style="margin-bottom: 16px;"
                ),
                
                # Goal Setting Card
                ui.div(
                    ui.div(
                        ui.h3("Enrollment Goal", class_="card-title"),
                        class_="card-header"
                    ),
                    ui.div(
                        ui.div(
                            ui.div("Target Enrollment", class_="filter-label"),
                            ui.input_numeric(
                                "sim_goal",
                                None,
                                value=None,
                                min=0,
                                step=100
                            ),
                            # Explanatory text for enrollment goal
                            ui.p("Enter a target enrollment. The simulator will compute whether the goal is achievable under the current scenario.",
                                 style="font-size: 11px; color: var(--color-text-muted); margin-top: 8px;"),
                            class_="filter-group"
                        ),
                        ui.output_ui("sim_goal_recommendations"),
                        class_="card-body"
                    ),
                    class_="card"
                ),
                
                style="width: 320px; flex-shrink: 0;"
            ),
            
            # Right column: Results
            ui.div(
                # Projected KPIs
                ui.output_ui("sim_projected_kpis"),
                
                # Comparison Chart
                ui.div(
                    ui.div(
                        ui.h3("Base vs Projected Comparison", class_="card-title"),
                        class_="card-header"
                    ),
                    ui.div(
                        output_widget("sim_comparison_chart"),
                        class_="card-body"
                    ),
                    class_="card chart-section"
                ),
                
                # Sensitivity Analysis
                ui.div(
                    ui.div(
                        ui.h3("Sensitivity Analysis", class_="card-title"),
                        ui.p("How enrollment changes with each lever", class_="section-subtitle", style="margin: 0;"),
                        class_="card-header"
                    ),
                    ui.div(
                        output_widget("sim_sensitivity_chart"),
                        # Caption explaining how to interpret the chart
                        ui.p("Each line shows how projected enrollment changes as you adjust one lever while holding others constant.",
                             style="font-size: 11px; color: var(--color-text-muted); margin-top: 12px; text-align: center;"),
                        class_="card-body"
                    ),
                    class_="card chart-section"
                ),
                
                style="flex: 1; min-width: 0;"
            ),
            
            style="display: flex; gap: 24px; align-items: flex-start;"
        ),
        
        class_="page-content"
    )


def simulator_server(input, output, session, filtered_data, full_data,
                     selected_years, selected_institution, latest_year, institutions_list):
    """Server logic for the Simulator page."""
    
    # Institution selector
    @render.ui
    def sim_institution_selector():
        inst = selected_institution()
        return ui.input_selectize(
            "sim_institution",
            None,
            choices=[""] + institutions_list,
            selected=inst if inst else "",
            options={"placeholder": "Select institution..."}
        )
    
    # Year selector
    @render.ui
    def sim_year_selector():
        years = selected_years()
        if not years:
            years = [2024, 2023, 2022]
        
        year = latest_year() or max(years)
        
        return ui.input_select(
            "sim_year",
            None,
            choices={str(y): str(y) for y in sorted(years, reverse=True)},
            selected=str(year)
        )
    
    # Reactive: Get base data for selected institution and year
    @reactive.calc
    def base_data():
        inst = input.sim_institution()
        year_str = input.sim_year()
        
        if not inst or not year_str:
            return None
        
        year = int(year_str)
        df = full_data()
        
        inst_data = df[(df['institution_name'] == inst) & (df['year'] == year)]
        
        if inst_data.empty:
            return None
        
        row = inst_data.iloc[0]
        return {
            'applicants': int(row['applicants']),
            'admit_rate': float(row['admit_rate']),
            'yield_rate': float(row['yield_rate']),
            'enrolled': int(row['enrolled_total']),
            'admitted': int(row['admissions']),
        }
    
    # Base metrics display
    @render.ui
    def sim_base_metrics():
        base = base_data()
        
        if not base:
            return ui.p("Select an institution to see base metrics",
                       style="color: var(--color-text-muted); text-align: center; padding: 16px;")
        
        return ui.div(
            ui.div(
                ui.div("Current Metrics", class_="filter-label", style="margin-bottom: 8px;"),
                ui.div(
                    ui.span(f"Applicants: ", style="color: var(--color-text-muted);"),
                    ui.strong(f"{base['applicants']:,}"),
                    style="margin-bottom: 4px;"
                ),
                ui.div(
                    ui.span(f"Admit Rate: ", style="color: var(--color-text-muted);"),
                    ui.strong(f"{base['admit_rate']:.1f}%"),
                    style="margin-bottom: 4px;"
                ),
                ui.div(
                    ui.span(f"Yield Rate: ", style="color: var(--color-text-muted);"),
                    ui.strong(f"{base['yield_rate']:.1f}%"),
                    style="margin-bottom: 4px;"
                ),
                ui.div(
                    ui.span(f"Enrolled: ", style="color: var(--color-text-muted);"),
                    ui.strong(f"{base['enrolled']:,}"),
                ),
            ),
            style="padding: 12px; background: var(--color-bg); border-radius: 8px; margin-top: 16px;"
        )
    
    # Slider value displays
    @render.text
    def sim_applicants_value():
        val = input.sim_applicants_change()
        return f"{val:+d}%"
    
    @render.text
    def sim_admit_value():
        val = input.sim_admit_change()
        return f"{val:+.1f}pp"
    
    @render.text
    def sim_yield_value():
        val = input.sim_yield_change()
        return f"{val:+.1f}pp"
    
    # Reset sliders
    @reactive.effect
    @reactive.event(input.sim_reset)
    def reset_sliders():
        ui.update_slider("sim_applicants_change", value=0)
        ui.update_slider("sim_admit_change", value=0)
        ui.update_slider("sim_yield_change", value=0)
    
    # Reactive: Calculate projected values
    @reactive.calc
    def projected_data():
        base = base_data()
        
        if not base:
            return None
        
        return simulate_enrollment(
            base_applicants=base['applicants'],
            base_admit_rate=base['admit_rate'],
            base_yield_rate=base['yield_rate'],
            applicants_change_pct=input.sim_applicants_change(),
            admit_rate_change_pp=input.sim_admit_change(),
            yield_rate_change_pp=input.sim_yield_change()
        )
    
    # Projected KPIs
    @render.ui
    def sim_projected_kpis():
        proj = projected_data()
        base = base_data()
        
        if not proj or not base:
            return ui.div(
                ui.p("Configure scenario to see projections",
                     style="color: var(--color-text-muted); text-align: center; padding: 24px;"),
                class_="kpi-grid"
            )
        
        cards = []
        
        # Projected Enrolled (main KPI)
        delta_pct = proj['delta_enrolled_pct']
        cards.append(create_kpi_card(
            label="Projected Enrolled",
            value=proj['proj_enrolled'],
            delta=delta_pct,
            delta_type="percent",
            subtext=f"vs base: {proj['delta_enrolled']:+,}",
            card_type="enrolled"
        ))
        
        # Projected Applicants
        cards.append(create_kpi_card(
            label="Projected Applicants",
            value=proj['proj_applicants'],
            delta=input.sim_applicants_change(),
            delta_type="percent",
            subtext=f"Base: {base['applicants']:,}",
            card_type="applicants"
        ))
        
        # Projected Admit Rate
        cards.append(create_kpi_card(
            label="Projected Admit Rate",
            value=proj['proj_admit_rate'],
            delta=input.sim_admit_change(),
            delta_type="pp",
            subtext=f"Base: {base['admit_rate']:.1f}%",
            card_type="admit"
        ))
        
        # Projected Yield Rate
        cards.append(create_kpi_card(
            label="Projected Yield Rate",
            value=proj['proj_yield_rate'],
            delta=input.sim_yield_change(),
            delta_type="pp",
            subtext=f"Base: {base['yield_rate']:.1f}%",
            card_type="yield"
        ))
        
        # Overall Conversion
        base_conversion = (base['enrolled'] / base['applicants'] * 100) if base['applicants'] > 0 else 0
        cards.append(create_kpi_card(
            label="Overall Conversion",
            value=proj['proj_conversion'],
            delta=proj['proj_conversion'] - base_conversion,
            delta_type="pp",
            subtext=f"Base: {base_conversion:.1f}%",
            card_type="default"
        ))
        
        return ui.div(*cards, class_="kpi-grid")
    
    # Comparison Chart
    @render_widget
    def sim_comparison_chart():
        proj = projected_data()
        base = base_data()
        
        if not proj or not base:
            fig = go.Figure()
            fig.update_layout(
                annotations=[dict(
                    text="Select an institution to see comparison",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=14, color="#64748B")
                )],
                height=300
            )
            return fig
        
        categories = ['Applicants', 'Admitted', 'Enrolled']
        base_values = [base['applicants'], base['admitted'], base['enrolled']]
        proj_values = [proj['proj_applicants'], proj['proj_admitted'], proj['proj_enrolled']]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Base',
            x=categories,
            y=base_values,
            marker_color='#94A3B8',
            text=[f"{v:,.0f}" for v in base_values],
            textposition='outside',
        ))
        
        fig.add_trace(go.Bar(
            name='Projected',
            x=categories,
            y=proj_values,
            marker_color='#2563EB',
            text=[f"{v:,.0f}" for v in proj_values],
            textposition='outside',
        ))
        
        # Calculate y-axis max to accommodate labels above bars - increased padding
        max_val = max(max(base_values), max(proj_values)) * 1.30  # 30% padding for labels
        
        fig.update_layout(
            font={'family': 'Inter, sans-serif', 'size': 12},
            paper_bgcolor='#FFFFFF',
            plot_bgcolor='#FFFFFF',
            margin={'l': 60, 'r': 40, 't': 100, 'b': 50},  # Increased margins for labels
            barmode='group',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
            xaxis=dict(title=None),
            yaxis=dict(title='Count', gridcolor='#E2E8F0', range=[0, max_val]),
            height=400,  # Taller to accommodate labels
        )
        
        return fig
    
    # Sensitivity Chart
    @render_widget
    def sim_sensitivity_chart():
        base = base_data()
        
        if not base:
            fig = go.Figure()
            fig.update_layout(height=300)
            return fig
        
        # Calculate sensitivity for each lever
        scenarios = []
        
        # Applicants sensitivity
        for change in [-20, -10, 0, 10, 20]:
            result = simulate_enrollment(
                base['applicants'], base['admit_rate'], base['yield_rate'],
                applicants_change_pct=change, admit_rate_change_pp=0, yield_rate_change_pp=0
            )
            scenarios.append({
                'lever': 'Applicants',
                'change': change,
                'enrolled': result['proj_enrolled']
            })
        
        # Admit rate sensitivity
        for change in [-5, -2.5, 0, 2.5, 5]:
            result = simulate_enrollment(
                base['applicants'], base['admit_rate'], base['yield_rate'],
                applicants_change_pct=0, admit_rate_change_pp=change, yield_rate_change_pp=0
            )
            scenarios.append({
                'lever': 'Admit Rate',
                'change': change,
                'enrolled': result['proj_enrolled']
            })
        
        # Yield sensitivity
        for change in [-5, -2.5, 0, 2.5, 5]:
            result = simulate_enrollment(
                base['applicants'], base['admit_rate'], base['yield_rate'],
                applicants_change_pct=0, admit_rate_change_pp=0, yield_rate_change_pp=change
            )
            scenarios.append({
                'lever': 'Yield Rate',
                'change': change,
                'enrolled': result['proj_enrolled']
            })
        
        df = pd.DataFrame(scenarios)
        
        fig = go.Figure()
        
        colors = {'Applicants': '#0F172A', 'Admit Rate': '#2563EB', 'Yield Rate': '#10B981'}
        
        for lever in ['Applicants', 'Admit Rate', 'Yield Rate']:
            lever_df = df[df['lever'] == lever]
            fig.add_trace(go.Scatter(
                x=lever_df['change'],
                y=lever_df['enrolled'],
                mode='lines+markers',
                name=lever,
                line=dict(color=colors[lever], width=2),
                marker=dict(size=8),
            ))
        
        # Add base line
        fig.add_hline(
            y=base['enrolled'],
            line_dash="dash",
            line_color="#94A3B8",
            annotation_text=f"Base: {base['enrolled']:,}",
            annotation_position="right"
        )
        
        fig.update_layout(
            font={'family': 'Inter, sans-serif', 'size': 12},
            paper_bgcolor='#FFFFFF',
            plot_bgcolor='#FFFFFF',
            margin={'l': 50, 'r': 80, 't': 40, 'b': 50},
            xaxis=dict(
                title='Change (% for Applicants, pp for Rates)',
                gridcolor='#E2E8F0',
                zeroline=True,
                zerolinecolor='#94A3B8',
            ),
            yaxis=dict(title='Projected Enrolled', gridcolor='#E2E8F0'),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
            height=350,
            hovermode='x unified',
        )
        
        return fig
    
    # Goal Recommendations
    @render.ui
    def sim_goal_recommendations():
        base = base_data()
        goal = input.sim_goal()
        
        if not base or not goal:
            return ui.div()
        
        recs = calculate_goal_recommendations(
            base['applicants'],
            base['admit_rate'],
            base['yield_rate'],
            goal
        )
        
        if recs.get('goal_met') and not recs.get('recommendations'):
            return ui.div(
                ui.p("✅ Current trajectory meets or exceeds goal!",
                     style="color: var(--color-success); font-weight: 500;"),
                style="padding: 12px; background: var(--color-success-bg); border-radius: 8px; margin-top: 16px;"
            )
        
        rec_items = []
        for rec in recs.get('recommendations', []):
            priority_badge = f"P{rec['priority']}"
            rec_items.append(ui.div(
                ui.span(priority_badge, class_="badge badge-info", style="margin-right: 8px;"),
                ui.span(rec['message']),
                style="margin-bottom: 8px;"
            ))
        
        status_color = "var(--color-success)" if recs.get('goal_met') else "var(--color-warning)"
        status_text = "Goal achievable" if recs.get('goal_met') else "Goal may be challenging"
        
        return ui.div(
            ui.p(f"📋 Recommendations to reach {goal:,} enrolled:",
                 style="font-weight: 600; margin-bottom: 12px;"),
            *rec_items,
            ui.p(
                f"Status: {status_text}",
                style=f"color: {status_color}; font-weight: 500; margin-top: 12px;"
            ),
            style="padding: 16px; background: var(--color-bg); border-radius: 8px; margin-top: 16px;"
        )
