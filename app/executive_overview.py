from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from app.queries.dashboard_queries import (
    get_portfolio_summary,
    get_priority_initiatives,
    get_decision_summary,
    get_readiness_summary,
    get_risk_domain_summary,
)

from app.components.charts import (
    render_decision_chart,
    render_readiness_chart,
    render_risk_domain_chart,
)

from app.components.metrics import render_kpi

from app.components.management_action_center import (
    render_management_action_center,
)


# ------------------------------------------------------------------
# Page configuration
# ------------------------------------------------------------------

st.set_page_config(
    page_title="TransformRisk | Executive Overview",
    page_icon="⚠️",
    layout="wide",
)


# ------------------------------------------------------------------
# Header
# ------------------------------------------------------------------

st.title("TransformRisk")

st.caption(
    "Transformation Risk, Readiness & Decision Intelligence"
)

st.markdown(
    """
    **Executive portfolio view** for evaluating transformation governance,
    organizational readiness, residual risk and management attention.
    """
)

st.divider()


# ------------------------------------------------------------------
# Portfolio data
# ------------------------------------------------------------------

portfolio = get_portfolio_summary()

if portfolio.empty:
    st.warning("Portfolio data is currently unavailable.")
    st.stop()

metrics = portfolio.iloc[0]


# ------------------------------------------------------------------
# Executive KPI layer
# ------------------------------------------------------------------

st.subheader("Executive Portfolio Snapshot")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    render_kpi(
        "Initiatives",
        int(metrics["total_initiatives"]),
        help_text=(
            "Total transformation initiatives currently included "
            "in the portfolio."
        ),
    )

with col2:
    render_kpi(
        "Do Not Proceed",
        int(metrics["do_not_proceed"]),
        help_text=(
            "Initiatives currently triggering the highest-severity "
            "governance outcome."
        ),
    )

with col3:
    render_kpi(
        "Remediate",
        int(metrics["remediate"]),
        help_text=(
            "Initiatives requiring remediation before proceeding."
        ),
    )

with col4:
    render_kpi(
        "Avg Readiness",
        f"{metrics['average_readiness']:.1f}",
        help_text=(
            "Average organizational readiness score across "
            "Technology, Data, Process, People and Governance."
        ),
    )

with col5:
    render_kpi(
        "Overdue Actions",
        int(metrics["overdue_actions"]),
        help_text=(
            "Mitigation actions that have passed their target date."
        ),
    )


st.divider()


# ------------------------------------------------------------------
# Executive portfolio health
# ------------------------------------------------------------------

st.subheader("Portfolio Health")

do_not_proceed = int(metrics["do_not_proceed"])
remediate = int(metrics["remediate"])
average_readiness = float(metrics["average_readiness"])
overdue_actions = int(metrics["overdue_actions"])


if do_not_proceed > 0:
    health_status = "Requires Management Attention"
    health_message = (
        f"{do_not_proceed} initiative(s) currently fall under "
        "the Do Not Proceed governance outcome."
    )

elif remediate > 0:
    health_status = "Requires Remediation"
    health_message = (
        f"{remediate} initiative(s) require remediation before "
        "proceeding."
    )

else:
    health_status = "Controlled Portfolio"
    health_message = (
        "No initiatives currently fall under the highest-severity "
        "governance outcome."
    )


st.markdown(f"### {health_status}")

st.write(health_message)


health_col1, health_col2, health_col3, health_col4 = st.columns(4)

with health_col1:
    st.metric(
        "Do Not Proceed",
        do_not_proceed,
        help=(
            "Initiatives requiring the highest level of "
            "governance intervention."
        ),
    )

with health_col2:
    st.metric(
        "Remediation Required",
        remediate,
        help=(
            "Initiatives requiring remediation before proceeding."
        ),
    )

with health_col3:
    st.metric(
        "Average Readiness",
        f"{average_readiness:.1f}",
        help="Average portfolio readiness score.",
    )

with health_col4:
    st.metric(
        "Overdue Actions",
        overdue_actions,
        help=(
            "Open mitigation actions past their target date."
        ),
    )


st.info(
    f"Management interpretation: the portfolio contains "
    f"{do_not_proceed} Do Not Proceed initiative(s), "
    f"{remediate} remediation initiative(s), and "
    f"{overdue_actions} overdue mitigation action(s). "
    f"Average readiness is {average_readiness:.1f}, indicating that "
    "execution readiness should remain part of transformation governance."
)


# ------------------------------------------------------------------
# Management takeaway
# ------------------------------------------------------------------

st.markdown("#### Management Takeaway")

takeaway_items = []

if do_not_proceed > 0:
    takeaway_items.append(
        f"**{do_not_proceed} initiative(s)** require immediate "
        "governance attention."
    )

if remediate > 0:
    takeaway_items.append(
        f"**{remediate} initiative(s)** require remediation "
        "before proceeding."
    )

if average_readiness < 65:
    takeaway_items.append(
        f"Portfolio readiness is **{average_readiness:.1f}**, "
        "indicating execution capability remains a material "
        "transformation consideration."
    )

if overdue_actions > 0:
    takeaway_items.append(
        f"**{overdue_actions} overdue mitigation action(s)** "
        "require execution follow-up."
    )

if takeaway_items:
    st.markdown(
        "\n".join(
            f"- {item}"
            for item in takeaway_items
        )
    )
else:
    st.success(
        "The portfolio currently shows no immediate "
        "management escalation signals."
    )


st.divider()


# ------------------------------------------------------------------
# Governance and readiness profile
# ------------------------------------------------------------------

st.subheader("Governance & Readiness Profile")

st.caption(
    "The portfolio view combines governance outcomes with organizational "
    "readiness to show where transformation execution may require "
    "management intervention."
)


chart_col1, chart_col2 = st.columns(2)


with chart_col1:

    st.markdown("#### Governance Decision Posture")

    decision_data = get_decision_summary()

    render_decision_chart(decision_data)

    st.caption(
        "Distribution of transformation initiatives across the current "
        "prototype governance decision policy."
    )


with chart_col2:

    st.markdown("#### Portfolio Readiness Profile")

    readiness_data = get_readiness_summary()

    render_readiness_chart(readiness_data)

    st.caption(
        "Distribution of initiatives by readiness band across the "
        "transformation portfolio."
    )


st.divider()


# ------------------------------------------------------------------
# Residual risk by domain
# ------------------------------------------------------------------

st.subheader("Residual Risk by Domain")

st.caption(
    "Average residual risk highlights the transformation domains "
    "requiring greater management attention after control effectiveness "
    "is considered."
)

risk_data = get_risk_domain_summary()

render_risk_domain_chart(risk_data)


st.divider()


# ------------------------------------------------------------------
# Priority transformation initiatives
# ------------------------------------------------------------------

st.subheader("Priority Transformation Initiatives")

st.caption(
    "Initiatives surfaced for management review based on residual risk, "
    "readiness, mitigation execution and governance outcome."
)

priority_data = get_priority_initiatives()


if not priority_data.empty:

    display_columns = [
        "initiative_id",
        "initiative_name",
        "business_unit",
        "critical_residual_risks",
        "high_residual_risks",
        "average_residual_risk",
        "overall_readiness_score",
        "overdue_actions",
        "transformation_decision",
    ]

    st.dataframe(
        priority_data[display_columns],
        width="stretch",
        hide_index=True,
    )

else:
    st.info("No priority initiatives available.")


st.divider()


# ------------------------------------------------------------------
# Management Action Center
# ------------------------------------------------------------------

render_management_action_center()


st.divider()


# ------------------------------------------------------------------
# Prototype governance disclaimer
# ------------------------------------------------------------------

st.caption(
    "TransformRisk analytical thresholds are prototype decision policies "
    "designed for portfolio demonstration and should be calibrated against "
    "organizational risk appetite before enterprise use."
)