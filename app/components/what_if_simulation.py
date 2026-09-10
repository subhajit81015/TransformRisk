from __future__ import annotations

import pandas as pd
import streamlit as st
import plotly.express as px


RISK_BANDS = [
    (17, 25, "Critical"),
    (13, 16, "High"),
    (9, 12, "Medium"),
    (5, 8, "Low"),
    (0, 4, "Very Low"),
]


def calculate_residual_risk(
    inherent_risk: float,
    control_effectiveness: float,
) -> float:
    """
    Calculate simulated residual risk.

    Residual Risk =
        Inherent Risk × (1 - Control Effectiveness / 100)
    """

    effectiveness = max(
        0.0,
        min(100.0, float(control_effectiveness)),
    )

    return inherent_risk * (
        1 - effectiveness / 100
    )


def get_risk_band(
    residual_risk: float,
) -> str:

    score = float(residual_risk)

    for minimum, maximum, band in RISK_BANDS:
        if minimum <= score <= maximum:
            return band

    return "Very Low"


def simulate_risk_scenario(
    risk_df: pd.DataFrame,
    control_effectiveness_change: float,
) -> pd.DataFrame:

    if risk_df.empty:
        return pd.DataFrame()

    simulated = risk_df.copy()

    simulated["simulated_control_effectiveness"] = (
        simulated["control_effectiveness"].astype(float)
        + float(control_effectiveness_change)
    ).clip(0, 100)

    simulated["simulated_residual_risk"] = (
        simulated.apply(
            lambda row: calculate_residual_risk(
                row["inherent_risk_score"],
                row["simulated_control_effectiveness"],
            ),
            axis=1,
        )
    )

    simulated["simulated_residual_band"] = (
        simulated["simulated_residual_risk"]
        .apply(get_risk_band)
    )

    simulated["risk_reduction"] = (
        simulated["residual_risk_score"].astype(float)
        - simulated["simulated_residual_risk"]
    )

    simulated["risk_reduction_percentage"] = (
        simulated["risk_reduction"]
        / simulated["residual_risk_score"].replace(0, 1)
        * 100
    )

    simulated["band_changed"] = (
        simulated["residual_risk_band"]
        != simulated["simulated_residual_band"]
    )

    return simulated


def summarize_scenario(
    risk_df: pd.DataFrame,
    simulated_df: pd.DataFrame,
) -> dict:
    """Return executive-level before/after scenario metrics."""

    if risk_df.empty or simulated_df.empty:
        return {
            "current_average": 0.0,
            "simulated_average": 0.0,
            "current_maximum": 0.0,
            "simulated_maximum": 0.0,
            "average_reduction": 0.0,
            "average_reduction_percentage": 0.0,
            "maximum_reduction": 0.0,
            "critical_before": 0,
            "critical_after": 0,
            "high_before": 0,
            "high_after": 0,
            "risks_improved": 0,
            "band_improvements": 0,
            "total_risks": 0,
        }

    current = risk_df["residual_risk_score"].astype(float)
    simulated = simulated_df["simulated_residual_risk"].astype(float)

    average_reduction = current.mean() - simulated.mean()

    average_reduction_percentage = (
        (average_reduction / current.mean()) * 100
        if current.mean() > 0
        else 0.0
    )

    return {
        "current_average": current.mean(),
        "simulated_average": simulated.mean(),
        "current_maximum": current.max(),
        "simulated_maximum": simulated.max(),
        "average_reduction": average_reduction,
        "average_reduction_percentage": average_reduction_percentage,
        "maximum_reduction": current.max() - simulated.max(),
        "critical_before": (
            risk_df["residual_risk_band"] == "Critical"
        ).sum(),
        "critical_after": (
            simulated_df["simulated_residual_band"] == "Critical"
        ).sum(),
        "high_before": (
            risk_df["residual_risk_band"] == "High"
        ).sum(),
        "high_after": (
            simulated_df["simulated_residual_band"] == "High"
        ).sum(),
        "risks_improved": (
            simulated_df["risk_reduction"] > 0
        ).sum(),
        "band_improvements": (
            simulated_df["band_changed"]
        ).sum(),
        "total_risks": len(risk_df),
    }


def render_what_if_simulation(
    risk_df: pd.DataFrame,
    current_decision: str,
):

    st.subheader("What-If Risk Simulation")

    st.caption(
        "Simulate the effect of improving control effectiveness "
        "without changing the underlying database."
    )

    if risk_df.empty:
        st.info(
            "No risk data is available for simulation."
        )
        return

    # =====================================================
    # CONTROL IMPROVEMENT INPUT
    # =====================================================

    st.markdown("#### Control Effectiveness Scenario")

    control_change = st.slider(
        "Improve control effectiveness by",
        min_value=0,
        max_value=50,
        value=15,
        step=5,
        format="+%d%%",
        help=(
            "This change is applied to each risk's current "
            "control effectiveness for simulation only."
        ),
    )

    simulated_df = simulate_risk_scenario(
        risk_df,
        control_change,
    )

    summary = summarize_scenario(
        risk_df,
        simulated_df,
    )

    # =====================================================
    # SCENARIO IMPACT
    # =====================================================

    st.markdown("#### Scenario Impact")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Average Residual Risk",
            f"{summary['simulated_average']:.2f}",
            delta=(
                f"-{summary['average_reduction']:.2f}"
                if summary["average_reduction"] > 0
                else None
            ),
            delta_color="inverse",
        )

    with col2:
        st.metric(
            "Maximum Residual Risk",
            f"{summary['simulated_maximum']:.2f}",
            delta=(
                f"-{summary['maximum_reduction']:.2f}"
                if summary["maximum_reduction"] > 0
                else None
            ),
            delta_color="inverse",
        )

    with col3:
        st.metric(
            "Average Risk Reduction",
            f"{summary['average_reduction_percentage']:.1f}%",
        )

    with col4:
        st.metric(
            "Risk Bands Improved",
            int(summary["band_improvements"]),
        )

    # =====================================================
    # BEFORE / AFTER TABLE
    # =====================================================

    st.markdown("#### Risk Scenario Comparison")

    comparison_df = simulated_df[
        [
            "risk_id",
            "risk_name",
            "risk_domain",
            "inherent_risk_score",
            "control_effectiveness",
            "simulated_control_effectiveness",
            "residual_risk_score",
            "simulated_residual_risk",
            "residual_risk_band",
            "simulated_residual_band",
            "risk_reduction",
            "band_changed",
        ]
    ].copy()

    comparison_df = comparison_df.rename(
        columns={
            "risk_id": "Risk ID",
            "risk_name": "Risk",
            "risk_domain": "Risk Domain",
            "inherent_risk_score": "Inherent Risk",
            "control_effectiveness": "Current Control Effectiveness",
            "simulated_control_effectiveness": "Scenario Control Effectiveness",
            "residual_risk_score": "Current Residual Risk",
            "simulated_residual_risk": "Scenario Residual Risk",
            "residual_risk_band": "Current Risk Band",
            "simulated_residual_band": "Scenario Risk Band",
            "risk_reduction": "Risk Reduction",
            "band_changed": "Risk Band Improved",
        }
    )

    for column in [
        "Inherent Risk",
        "Current Residual Risk",
        "Scenario Residual Risk",
        "Risk Reduction",
    ]:
        comparison_df[column] = comparison_df[column].round(2)

    for column in [
        "Current Control Effectiveness",
        "Scenario Control Effectiveness",
    ]:
        comparison_df[column] = comparison_df[column].round(1)

    comparison_df = comparison_df.sort_values(
        "Current Residual Risk",
        ascending=False,
    )

    st.dataframe(
        comparison_df,
        width="stretch",
        hide_index=True,
    )

    # =====================================================
    # RISK REDUCTION CHART
    # =====================================================

    st.markdown("#### Residual Risk: Before vs Scenario")

    chart_df = simulated_df[
        [
            "risk_id",
            "residual_risk_score",
            "simulated_residual_risk",
        ]
    ].copy()

    chart_df = chart_df.melt(
        id_vars=["risk_id"],
        value_vars=[
            "residual_risk_score",
            "simulated_residual_risk",
        ],
        var_name="scenario",
        value_name="residual_risk",
    )

    chart_df["scenario"] = chart_df[
        "scenario"
    ].map(
        {
            "residual_risk_score": "Current",
            "simulated_residual_risk": "Simulated",
        }
    )

    scenario_chart = px.bar(
        chart_df,
        x="risk_id",
        y="residual_risk",
        color="scenario",
        barmode="group",
        title="Current vs Simulated Residual Risk",
    )

    scenario_chart.update_layout(
        xaxis_title="Risk",
        yaxis_title="Residual Risk",
        height=430,
    )

    st.plotly_chart(
        scenario_chart,
        width="stretch",
    )

    # =====================================================
    # DECISION IMPACT
    # =====================================================

    st.markdown("#### Decision Impact")

    critical_after = summary["critical_after"]
    high_after = summary["high_after"]

    if critical_after > 0:

        st.error(
            "Scenario result: critical residual risk remains. "
            "The transformation should not be considered "
            "ready based on risk exposure alone."
        )

    elif high_after >= 3:

        st.warning(
            "Scenario result: multiple high residual risks remain. "
            "Proceeding would require explicit management conditions."
        )

    elif high_after > 0:

        st.warning(
            "Scenario result: high residual risk remains. "
            "Management should review the affected risks before rollout."
        )

    else:

        st.success(
            "Scenario result: no Critical or High residual risks "
            "remain under the simulated control improvement."
        )

    if current_decision == "PROCEED":

        st.info(
            "Current governance decision: PROCEED. "
            "The simulation is a scenario analysis and does not "
            "modify or override the underlying governance decision."
        )

    elif current_decision == "PROCEED WITH CONDITIONS":

        st.warning(
            "Current governance decision: PROCEED WITH CONDITIONS. "
            "The scenario can be used to evaluate whether risk "
            "conditions may be reduced."
        )

    else:

        st.info(
            f"Current governance decision: {current_decision}. "
            "Use the scenario to evaluate potential risk reduction "
            "before changing the underlying governance assessment."
        )

    # =====================================================
    # MANAGEMENT INTERPRETATION
    # =====================================================

    st.markdown("#### Scenario Interpretation")

    reduction_pct = summary["average_reduction_percentage"]

    if summary["average_reduction"] > 0:
        if reduction_pct >= 30:
            st.success(
                f"A {control_change}% improvement in control effectiveness "
                f"reduces average residual risk from "
                f"{summary['current_average']:.2f} to "
                f"{summary['simulated_average']:.2f}, representing an "
                f"estimated {reduction_pct:.1f}% reduction in average "
                "residual exposure. This indicates that targeted control "
                "strengthening could materially reduce transformation risk."
            )
        elif reduction_pct >= 15:
            st.warning(
                f"A {control_change}% improvement in control effectiveness "
                f"reduces average residual risk from "
                f"{summary['current_average']:.2f} to "
                f"{summary['simulated_average']:.2f}, representing an "
                f"estimated {reduction_pct:.1f}% reduction in average "
                "residual exposure. Targeted control improvements may "
                "provide meaningful risk reduction."
            )
        else:
            st.info(
                f"A {control_change}% improvement in control effectiveness "
                f"reduces average residual risk by an estimated "
                f"{reduction_pct:.1f}%. Management should assess whether "
                "additional control investment is justified by the "
                "remaining exposure."
            )
    else:
        st.info(
            "The selected scenario does not produce a measurable "
            "reduction in residual risk."
        )

    st.caption(
        "Simulation assumptions are illustrative. Results are "
        "calculated in memory using the project's residual-risk "
        "formula and do not alter source data."
    )