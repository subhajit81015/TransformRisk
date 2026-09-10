from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st
import plotly.express as px

from app.queries.decision_center_queries import (
    get_initiative_list,
    get_initiative_decision,
    get_initiative_risks,
    get_initiative_mitigations,
)

from app.queries.action_prioritization_queries import (
    get_management_action_priorities,
)

from app.queries.risk_intelligence_queries import (
    get_weak_controls_for_risks,
)

from app.queries.traceability_queries import (
    get_risk_control_mitigation_trace,
)

from app.queries.portfolio_queries import (
    get_portfolio_summary,
    get_portfolio_kpis,
)

from app.queries.portfolio_priority_queries import (
    get_portfolio_priority_queue,
    get_portfolio_priority_summary,
)

from app.components.risk_matrix import render_risk_matrix

from app.components.risk_traceability import (
    render_risk_traceability,
)

from app.components.what_if_simulation import (
    render_what_if_simulation,
)

from app.components.portfolio_priority_queue import (
    render_portfolio_priority_queue,
)

from app.components.portfolio_overview import (
    render_portfolio_overview,
)

from app.components.management_action_queue import (
    render_management_action_queue,
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="TransformRisk | Decision Center",
    page_icon="🎯",
    layout="wide",
)


# =========================================================
# HELPERS
# =========================================================

DECISION_CONFIG = {
    "DO NOT PROCEED": {
        "icon": "⛔",
        "message_type": "error",
    },
    "REMEDIATE BEFORE PROCEEDING": {
        "icon": "⚠️",
        "message_type": "warning",
    },
    "PROCEED WITH CONDITIONS": {
        "icon": "⚠️",
        "message_type": "warning",
    },
    "PROCEED": {
        "icon": "✓",
        "message_type": "success",
    },
}


def safe_float(value, default=0.0):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value, default=0):
    try:
        if pd.isna(value):
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def get_weakest_readiness_dimension(initiative):
    dimensions = {
        "Technology": safe_float(initiative["technology_readiness"]),
        "Data": safe_float(initiative["data_readiness"]),
        "Process": safe_float(initiative["process_readiness"]),
        "People": safe_float(initiative["people_readiness"]),
        "Governance": safe_float(initiative["governance_readiness"]),
    }

    return min(dimensions.items(), key=lambda item: item[1])


def build_management_recommendations(
    risk_df,
    weak_controls_df,
    mitigation_df,
    initiative,
):
    recommendations = []

    # -----------------------------------------------------
    # Critical residual risk
    # -----------------------------------------------------

    critical = risk_df[
        risk_df["residual_risk_band"] == "Critical"
    ] if not risk_df.empty else pd.DataFrame()

    if not critical.empty:
        risk = critical.sort_values(
            "residual_risk_score",
            ascending=False,
        ).iloc[0]

        recommendations.append(
            {
                "priority": "P1",
                "category": "Risk Exposure",
                "title": "Address critical residual risk",
                "message": (
                    f"{risk['risk_id']} ({risk['risk_name']}) has "
                    f"a residual risk score of "
                    f"{safe_float(risk['residual_risk_score']):.2f}. "
                    "Establish remediation and governance approval "
                    "before transformation execution."
                ),
            }
        )

    # -----------------------------------------------------
    # High residual risk
    # -----------------------------------------------------

    high = risk_df[
        risk_df["residual_risk_band"] == "High"
    ] if not risk_df.empty else pd.DataFrame()

    if not high.empty:
        risk = high.sort_values(
            "residual_risk_score",
            ascending=False,
        ).iloc[0]

        recommendations.append(
            {
                "priority": "P1",
                "category": "Risk Exposure",
                "title": "Reduce high residual risk",
                "message": (
                    f"{risk['risk_id']} ({risk['risk_name']}) has "
                    f"a residual risk score of "
                    f"{safe_float(risk['residual_risk_score']):.2f}. "
                    "Review the associated controls and mitigation "
                    "actions before major rollout."
                ),
            }
        )

    # -----------------------------------------------------
    # Weak controls
    # -----------------------------------------------------

    if not weak_controls_df.empty:
        weakest = (
            weak_controls_df
            .sort_values(
                by=["residual_risk_score", "effectiveness_score"],
                ascending=[False, True],
            )
            .iloc[0]
        )

        priority = (
            "P1"
            if (
                weakest["control_strength"] == "Critical Weakness"
                or safe_float(weakest["residual_risk_score"]) >= 9
            )
            else "P2"
        )

        recommendations.append(
            {
                "priority": priority,
                "category": "Control Effectiveness",
                "title": "Strengthen the weakest control",
                "message": (
                    f"Control {weakest['control_id']} supports "
                    f"{weakest['risk_id']} with residual risk "
                    f"{safe_float(weakest['residual_risk_score']):.2f}, "
                    f"while control effectiveness is only "
                    f"{safe_float(weakest['effectiveness_score']):.1f}%. "
                    "Prioritize control strengthening and confirm ownership."
                ),
            }
        )

    # -----------------------------------------------------
    # Readiness gap
    # -----------------------------------------------------

    minimum_readiness = safe_float(
        initiative["minimum_readiness_score"]
    )

    weakest_dimension, weakest_score = (
        get_weakest_readiness_dimension(initiative)
    )

    if minimum_readiness < 50:
        recommendations.append(
            {
                "priority": "P1",
                "category": "Transformation Readiness",
                "title": "Remediate the weakest readiness dimension",
                "message": (
                    f"{weakest_dimension} readiness is "
                    f"{weakest_score:.1f}. "
                    "Remediation should be tracked as a prerequisite "
                    "for transformation execution."
                ),
            }
        )

    elif minimum_readiness < 65:
        recommendations.append(
            {
                "priority": "P2",
                "category": "Transformation Readiness",
                "title": "Improve readiness before major rollout",
                "message": (
                    f"{weakest_dimension} is the weakest readiness "
                    f"dimension at {weakest_score:.1f}. "
                    "Management should address this capability gap "
                    "before major rollout."
                ),
            }
        )

    # -----------------------------------------------------
    # Mitigation execution
    # -----------------------------------------------------

    overdue = safe_int(initiative["overdue_actions"])

    if overdue > 0:
        recommendations.append(
            {
                "priority": "P1",
                "category": "Mitigation Execution",
                "title": "Resolve overdue mitigation actions",
                "message": (
                    f"{overdue} mitigation action(s) are overdue. "
                    "Confirm owners, revised due dates and execution status."
                ),
            }
        )
    elif not mitigation_df.empty:
        completion = safe_float(
            initiative["average_mitigation_completion"]
        )

        if completion < 50:
            recommendations.append(
                {
                    "priority": "P2",
                    "category": "Mitigation Execution",
                    "title": "Accelerate mitigation execution",
                    "message": (
                        f"Average mitigation completion is "
                        f"{completion:.1f}%. "
                        "Management should accelerate execution "
                        "before transformation scale-up."
                    ),
                }
            )

    # -----------------------------------------------------
    # Overall control environment
    # -----------------------------------------------------

    control_effectiveness = safe_float(
        initiative["average_control_effectiveness"]
    )

    if control_effectiveness < 50:
        recommendations.append(
            {
                "priority": "P1",
                "category": "Control Environment",
                "title": "Strengthen the control environment",
                "message": (
                    f"Average control effectiveness is "
                    f"{control_effectiveness:.1f}%. "
                    "Review control design, ownership and operating "
                    "effectiveness."
                ),
            }
        )
    elif control_effectiveness < 60:
        recommendations.append(
            {
                "priority": "P2",
                "category": "Control Environment",
                "title": "Improve control effectiveness",
                "message": (
                    f"Average control effectiveness is "
                    f"{control_effectiveness:.1f}%. "
                    "Targeted control improvements are recommended."
                ),
            }
        )

    priority_order = {"P1": 1, "P2": 2, "P3": 3}

    return sorted(
        recommendations,
        key=lambda item: priority_order.get(item["priority"], 99),
    )


def render_recommendations(recommendations):
    if not recommendations:
        st.success(
            "No material management recommendations were generated "
            "from the current risk, readiness and mitigation indicators."
        )
        return

    for item in recommendations:
        message = (
            f"**{item['priority']} | {item['category']} | "
            f"{item['title']}**\n\n"
            f"{item['message']}"
        )

        if item["priority"] == "P1":
            st.error(message)
        elif item["priority"] == "P2":
            st.warning(message)
        else:
            st.info(message)


# =========================================================
# HEADER
# =========================================================

st.title("Executive Decision Center")

st.caption(
    "Portfolio-level transformation governance, management attention "
    "and initiative-level decision intelligence."
)

# =========================================================
# EXECUTIVE PORTFOLIO VIEW
# =========================================================

portfolio_df = get_portfolio_summary()
portfolio_kpis = get_portfolio_kpis()

portfolio_priority_df = get_portfolio_priority_queue()
portfolio_priority_summary = get_portfolio_priority_summary()

render_portfolio_overview(
    portfolio_df,
    portfolio_kpis,
)

render_portfolio_priority_queue(
    portfolio_priority_df,
    portfolio_priority_summary,
)

st.divider()


# =========================================================
# INITIATIVE SELECTOR
# =========================================================

initiative_list = get_initiative_list()

if initiative_list.empty:
    st.warning("No transformation initiatives are available.")
    st.stop()

initiative_options = {
    f"{row.initiative_id} | {row.initiative_name}": str(row.initiative_id)
    for row in initiative_list.itertuples()
}

initiative_labels = list(initiative_options.keys())
initiative_ids = list(initiative_options.values())


# =========================================================
# PORTFOLIO → INITIATIVE NAVIGATION
# =========================================================
# The Portfolio Drill-Down component writes a one-time
# navigation target. Consume it before creating the
# Streamlit selectbox so the widget opens on that initiative.

portfolio_target = st.session_state.pop(
    "portfolio_navigation_target",
    None,
)

if portfolio_target is not None:
    portfolio_target = str(portfolio_target)

    if portfolio_target in initiative_ids:
        target_index = initiative_ids.index(
            portfolio_target
        )

        st.session_state["initiative_selector"] = (
            initiative_labels[target_index]
        )


# =========================================================
# INITIATIVE SELECTOR
# =========================================================

selected_label = st.selectbox(
    "Select Transformation Initiative",
    options=initiative_labels,
    key="initiative_selector",
)

selected_id = initiative_options[selected_label]


# =========================================================
# ACTIVE INITIATIVE STATE
# =========================================================

st.session_state["active_initiative_id"] = selected_id

# =========================================================
# LOAD DATA
# =========================================================

decision_df = get_initiative_decision(selected_id)
risk_df = get_initiative_risks(selected_id)
mitigation_df = get_initiative_mitigations(selected_id)
weak_controls_df = get_weak_controls_for_risks(selected_id)

traceability_df = get_risk_control_mitigation_trace(
    selected_id
)

action_priority_df = get_management_action_priorities(
    selected_id
)

if decision_df.empty:
    st.error(
        "Decision data could not be found for the selected initiative."
    )
    st.stop()

initiative = decision_df.iloc[0]


# =========================================================
# INITIATIVE PROFILE
# =========================================================

st.subheader("Initiative Profile")

profile_col1, profile_col2, profile_col3, profile_col4 = st.columns(4)

with profile_col1:
    st.caption("Business Unit")
    st.write(initiative["business_unit"])

with profile_col2:
    st.caption("Transformation Type")
    st.write(initiative["transformation_type"])

with profile_col3:
    st.caption("Criticality")
    st.write(initiative["criticality"])

with profile_col4:
    st.caption("Strategic Priority")
    st.write(initiative["strategic_priority"])

st.caption(
    f"Owner: {initiative['owner']} • "
    f"Target Completion: {initiative['target_completion_date']} • "
    f"Status: {initiative['status']}"
)

st.divider()


# =========================================================
# EXECUTIVE DECISION
# =========================================================

decision = str(initiative["transformation_decision"])

config = DECISION_CONFIG.get(
    decision,
    {
        "icon": "•",
        "message_type": "info",
    },
)

st.subheader("Transformation Decision")

decision_message = (
    f"{config['icon']} **{decision}**\n\n"
    f"**Management Rationale:** "
    f"{initiative['decision_rationale']}"
)

if config["message_type"] == "error":
    st.error(decision_message)
elif config["message_type"] == "warning":
    st.warning(decision_message)
elif config["message_type"] == "success":
    st.success(decision_message)
else:
    st.info(decision_message)


# =========================================================
# DECISION DRIVERS
# =========================================================

st.subheader("Decision Drivers")

driver1, driver2, driver3, driver4 = st.columns(4)

with driver1:
    st.metric(
        "Critical Residual Risks",
        safe_int(initiative["critical_residual_risks"]),
    )

with driver2:
    st.metric(
        "High Residual Risks",
        safe_int(initiative["high_residual_risks"]),
    )

with driver3:
    st.metric(
        "Minimum Readiness",
        f"{safe_float(initiative['minimum_readiness_score']):.1f}",
    )

with driver4:
    st.metric(
        "Overdue Mitigations",
        safe_int(initiative["overdue_actions"]),
    )

st.divider()


# =========================================================
# EXECUTIVE KPI STRIP
# =========================================================

st.subheader("Executive Risk & Readiness Indicators")

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    st.metric(
        "Average Residual Risk",
        f"{safe_float(initiative['average_residual_risk']):.2f}",
    )

with kpi2:
    st.metric(
        "Maximum Risk",
        f"{safe_float(initiative['maximum_residual_risk']):.2f}",
    )

with kpi3:
    st.metric(
        "Overall Readiness",
        f"{safe_float(initiative['overall_readiness_score']):.1f}",
    )

with kpi4:
    st.metric(
        "Control Effectiveness",
        f"{safe_float(initiative['average_control_effectiveness']):.1f}%",
    )

with kpi5:
    st.metric(
        "Overdue Actions",
        safe_int(initiative["overdue_actions"]),
    )

st.divider()


# =========================================================
# RISK INTELLIGENCE
# =========================================================

st.subheader("Risk Intelligence")

st.caption(
    "Residual risk reflects estimated exposure remaining after "
    "control effectiveness."
)

risk_col1, risk_col2, risk_col3, risk_col4 = st.columns(4)

with risk_col1:
    st.metric(
        "Total Risks",
        safe_int(initiative["total_risks"]),
    )

with risk_col2:
    st.metric(
        "Critical Residual Risks",
        safe_int(initiative["critical_residual_risks"]),
    )

with risk_col3:
    st.metric(
        "High Residual Risks",
        safe_int(initiative["high_residual_risks"]),
    )

with risk_col4:
    st.metric(
        "Maximum Residual Risk",
        f"{safe_float(initiative['maximum_residual_risk']):.2f}",
    )


# =========================================================
# RISK EXPOSURE MATRIX
# =========================================================

st.subheader("Risk Exposure Matrix")

st.caption(
    "Risk concentration across likelihood and impact dimensions."
)

render_risk_matrix(risk_df)

st.divider()


# =========================================================
# TOP RESIDUAL RISKS
# =========================================================

st.subheader("Top Residual Risks")

if not risk_df.empty:
    top_risks = (
        risk_df
        .sort_values("residual_risk_score", ascending=False)
        .head(10)
        .copy()
    )

    risk_chart = px.bar(
        top_risks,
        x="risk_name",
        y="residual_risk_score",
        text="residual_risk_score",
        hover_data=[
            "risk_id",
            "risk_domain",
            "likelihood",
            "impact",
            "control_effectiveness",
            "residual_risk_band",
        ],
        title="Highest Residual Risk Exposures",
    )

    risk_chart.update_layout(
        xaxis_title="Risk",
        yaxis_title="Residual Risk Score",
        xaxis_tickangle=-45,
        showlegend=False,
        height=450,
    )

    st.plotly_chart(
        risk_chart,
        width="stretch",
    )
else:
    st.info("No risks found for this initiative.")


# =========================================================
# RISK DETAIL TABLE
# =========================================================

if not risk_df.empty:
    risk_display = risk_df[
        [
            "risk_id",
            "risk_name",
            "risk_domain",
            "likelihood",
            "impact",
            "inherent_risk_score",
            "control_effectiveness",
            "residual_risk_score",
            "residual_risk_band",
        ]
    ].copy()

    risk_display["inherent_risk_score"] = (
        risk_display["inherent_risk_score"].round(2)
    )

    risk_display["control_effectiveness"] = (
        risk_display["control_effectiveness"].round(1)
    )

    risk_display["residual_risk_score"] = (
        risk_display["residual_risk_score"].round(2)
    )

    st.dataframe(
        risk_display,
        width="stretch",
        hide_index=True,
    )


# =========================================================
# MANAGEMENT PRIORITY
# =========================================================

st.divider()

st.subheader("Management Priority")

if not risk_df.empty:
    priority_risk = (
        risk_df
        .sort_values(
            by="residual_risk_score",
            ascending=False,
        )
        .iloc[0]
    )

    priority_col1, priority_col2, priority_col3 = st.columns(3)

    with priority_col1:
        st.metric(
            "Priority Risk",
            priority_risk["risk_id"],
        )

    with priority_col2:
        st.metric(
            "Residual Risk",
            f"{safe_float(priority_risk['residual_risk_score']):.2f}",
        )

    with priority_col3:
        st.metric(
            "Control Effectiveness",
            f"{safe_float(priority_risk['control_effectiveness']):.1f}%",
        )

    st.info(
        f"**{priority_risk['risk_name']}**\n\n"
        f"Risk ID: **{priority_risk['risk_id']}**\n\n"
        f"Domain: **{priority_risk['risk_domain']}**\n\n"
        f"Likelihood: **{priority_risk['likelihood']}**  \n"
        f"Impact: **{priority_risk['impact']}**\n\n"
        f"Residual Risk Band: **{priority_risk['residual_risk_band']}**\n\n"
        "**Management Focus:** Review the controls and mitigation "
        "actions associated with this risk first because it represents "
        "the highest current residual exposure for the selected initiative."
    )
else:
    st.info("No management priority could be calculated.")


# =========================================================
# WEAK CONTROL DETECTION
# =========================================================

st.divider()

st.subheader("Weak Control Detection")

st.caption(
    "Controls below the target effectiveness threshold and their "
    "associated residual risk exposure."
)

if weak_controls_df.empty:
    st.success(
        "No weak controls were detected for this initiative."
    )
else:
    weak_col1, weak_col2, weak_col3 = st.columns(3)

    with weak_col1:
        st.metric(
            "Weak Controls",
            len(weak_controls_df),
        )

    with weak_col2:
        critical_weaknesses = (
            weak_controls_df["control_strength"]
            == "Critical Weakness"
        ).sum()

        st.metric(
            "Critical Weaknesses",
            int(critical_weaknesses),
        )

    with weak_col3:
        average_weak_effectiveness = (
            weak_controls_df["effectiveness_score"]
            .mean()
        )

        st.metric(
            "Average Effectiveness",
            f"{average_weak_effectiveness:.1f}%",
        )

    weak_display = weak_controls_df[
        [
            "control_id",
            "risk_id",
            "risk_name",
            "risk_domain",
            "residual_risk_score",
            "residual_risk_band",
            "control_name",
            "control_type",
            "control_owner",
            "effectiveness_score",
            "control_strength",
            "control_status",
        ]
    ].copy()

    weak_display["residual_risk_score"] = (
        weak_display["residual_risk_score"].round(2)
    )

    weak_display["effectiveness_score"] = (
        weak_display["effectiveness_score"].round(1)
    )

    st.dataframe(
        weak_display,
        width="stretch",
        hide_index=True,
    )


# =========================================================
# MANAGEMENT RECOMMENDATIONS
# =========================================================

st.divider()

st.subheader("Management Recommendations")

st.caption(
    "Evidence-based actions generated from residual risk, "
    "control effectiveness, readiness and mitigation execution."
)

recommendations = build_management_recommendations(
    risk_df=risk_df,
    weak_controls_df=weak_controls_df,
    mitigation_df=mitigation_df,
    initiative=initiative,
)

render_recommendations(recommendations)


# =========================================================
# TRANSFORMATION READINESS
# =========================================================

st.divider()

st.subheader("Transformation Readiness")

st.caption(
    "Readiness identifies capability gaps that may constrain "
    "transformation execution."
)

readiness_data = {
    "Dimension": [
        "Technology",
        "Data",
        "Process",
        "People",
        "Governance",
    ],
    "Score": [
        safe_float(initiative["technology_readiness"]),
        safe_float(initiative["data_readiness"]),
        safe_float(initiative["process_readiness"]),
        safe_float(initiative["people_readiness"]),
        safe_float(initiative["governance_readiness"]),
    ],
}

readiness_df = pd.DataFrame(readiness_data)

readiness_chart = px.bar(
    readiness_df,
    x="Dimension",
    y="Score",
    text="Score",
    title="Readiness by Dimension",
)

readiness_chart.update_layout(
    yaxis_title="Readiness Score",
    xaxis_title="Dimension",
    yaxis_range=[0, 100],
    showlegend=False,
    height=420,
)

st.plotly_chart(
    readiness_chart,
    width="stretch",
)

readiness_col1, readiness_col2, readiness_col3 = st.columns(3)

with readiness_col1:
    st.metric(
        "Overall Readiness",
        f"{safe_float(initiative['overall_readiness_score']):.1f}",
    )

with readiness_col2:
    st.metric(
        "Minimum Dimension",
        f"{safe_float(initiative['minimum_readiness_score']):.1f}",
    )

with readiness_col3:
    st.metric(
        "Readiness Band",
        initiative["readiness_band"],
    )


# =========================================================
# READINESS GAP SIGNAL
# =========================================================

minimum_readiness = safe_float(
    initiative["minimum_readiness_score"]
)

weakest_dimension, weakest_score = (
    get_weakest_readiness_dimension(initiative)
)

if minimum_readiness < 50:
    st.error(
        f"Readiness Gap: {weakest_dimension} is the weakest "
        f"dimension at {weakest_score:.1f}. "
        "Targeted remediation is required before transformation execution."
    )

elif minimum_readiness < 65:
    st.warning(
        f"Readiness Gap: {weakest_dimension} is the weakest "
        f"dimension at {weakest_score:.1f}. "
        "Management should address this capability before major rollout."
    )

else:
    st.success(
        f"Readiness Gap: weakest dimension is {weakest_dimension} "
        f"at {weakest_score:.1f}. "
        "No material readiness threshold breach is currently detected."
    )


# =========================================================
# DECISION / READINESS RECONCILIATION
# =========================================================

if decision == "PROCEED" and minimum_readiness < 50:
    st.warning(
        f"Governance Decision: **PROCEED**. "
        f"Management condition: remediate {weakest_dimension} "
        f"readiness ({weakest_score:.1f}) before major rollout. "
        "The readiness signal does not override the prototype "
        "decision policy; it identifies an execution condition."
    )


# =========================================================
# MITIGATION EXECUTION
# =========================================================

st.divider()

st.subheader("Mitigation Execution")

mit_col1, mit_col2, mit_col3, mit_col4 = st.columns(4)

with mit_col1:
    st.metric(
        "Total Actions",
        safe_int(initiative["total_mitigation_actions"]),
    )

with mit_col2:
    st.metric(
        "Completed",
        safe_int(initiative["completed_mitigation_actions"]),
    )

with mit_col3:
    st.metric(
        "Completion",
        f"{safe_float(initiative['average_mitigation_completion']):.1f}%",
    )

with mit_col4:
    st.metric(
        "Overdue",
        safe_int(initiative["overdue_actions"]),
    )

if not mitigation_df.empty:
    mitigation_display = mitigation_df[
        [
            "action_id",
            "risk_id",
            "action_name",
            "action_owner",
            "priority",
            "execution_status",
            "due_date",
            "completion_percentage",
            "expected_risk_reduction",
        ]
    ].copy()

    mitigation_display["completion_percentage"] = (
        mitigation_display["completion_percentage"].round(1)
    )

    mitigation_display["expected_risk_reduction"] = (
        mitigation_display["expected_risk_reduction"].round(2)
    )

    st.dataframe(
        mitigation_display,
        width="stretch",
        hide_index=True,
    )
else:
    st.info("No mitigation actions found.")


# =========================================================
# WHAT-IF RISK SIMULATION
# =========================================================

st.divider()

render_what_if_simulation(
    risk_df=risk_df,
    current_decision=decision,
)

st.divider()

# =========================================================
# RISK → CONTROL → MITIGATION TRACEABILITY
# =========================================================

st.divider()

render_risk_traceability(
    trace_df=traceability_df,
)

st.divider()

# =========================================================
# MANAGEMENT ACTION PRIORITIZATION
# =========================================================

render_management_action_queue(
    action_df=action_priority_df,
)

st.divider()



# =========================================================
# MANAGEMENT INTERPRETATION
# =========================================================

st.divider()

st.subheader("Management Interpretation")

if decision == "DO NOT PROCEED":
    st.error(
        "Immediate management intervention is recommended. "
        "Critical residual risk remains above the prototype "
        "decision threshold."
    )

elif decision == "REMEDIATE BEFORE PROCEEDING":
    st.warning(
        "The initiative should address identified remediation "
        "requirements before transformation execution proceeds."
    )

elif decision == "PROCEED WITH CONDITIONS":
    st.warning(
        "Transformation may continue subject to defined risk, "
        "readiness or mitigation conditions."
    )

else:
    if minimum_readiness < 50:
        st.warning(
            f"The prototype governance policy currently returns "
            f"PROCEED, but {weakest_dimension} readiness is only "
            f"{weakest_score:.1f}. Management should treat targeted "
            "readiness remediation as an execution condition."
        )
    else:
        st.success(
            "Current risk, readiness and mitigation indicators "
            "support proceeding under the prototype decision policy."
        )


# =========================================================
# GOVERNANCE DISCLAIMER
# =========================================================

st.caption(
    "TransformRisk decision policies are prototype governance "
    "thresholds for portfolio demonstration and should be "
    "calibrated against organizational risk appetite before "
    "enterprise deployment."
)
