from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from app.queries.dashboard_queries import (
    get_decision_summary,
    get_portfolio_summary,
    get_priority_initiatives,
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


st.set_page_config(
    page_title="TransformRisk",
    page_icon="⚠️",
    layout="wide",
)


st.title("TransformRisk")
st.caption(
    "Transformation Risk, Readiness & Decision Intelligence"
)

st.divider()


# ------------------------------------------------------------------
# Portfolio KPIs
# ------------------------------------------------------------------

portfolio = get_portfolio_summary()

if not portfolio.empty:

    metrics = portfolio.iloc[0]

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        render_kpi(
            "Initiatives",
            int(metrics["total_initiatives"]),
        )

    with col2:
        render_kpi(
            "Do Not Proceed",
            int(metrics["do_not_proceed"]),
        )

    with col3:
        render_kpi(
            "Remediate",
            int(metrics["remediate"]),
        )

    with col4:
        render_kpi(
            "Avg Readiness",
            f"{metrics['average_readiness']:.1f}",
        )

    with col5:
        render_kpi(
            "Overdue Actions",
            int(metrics["overdue_actions"]),
        )


st.divider()


# ------------------------------------------------------------------
# Charts
# ------------------------------------------------------------------

col1, col2 = st.columns(2)

with col1:
    decision_data = get_decision_summary()
    render_decision_chart(decision_data)

with col2:
    readiness_data = get_readiness_summary()
    render_readiness_chart(readiness_data)


st.divider()


risk_data = get_risk_domain_summary()

render_risk_domain_chart(risk_data)


st.divider()


# ------------------------------------------------------------------
# Priority initiatives
# ------------------------------------------------------------------

st.subheader("Priority Transformation Initiatives")

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
        width='stretch',
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

st.caption(
    "TransformRisk analytical thresholds are prototype decision policies "
    "designed for portfolio demonstration and should be calibrated against "
    "organizational risk appetite before enterprise use."
) 

