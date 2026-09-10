import pandas as pd
import plotly.express as px
import streamlit as st

from app.queries.management_action_center_queries import (
    get_management_action_queue,
)


PRIORITY_ORDER = [
    "P1 - Immediate Management Attention",
    "P2 - Management Action Required",
    "P3 - Controlled Monitoring",
    "P4 - Routine Monitoring",
]


def render_management_action_center():

    st.header("Management Action Center")

    st.caption(
        "Risk-level management queue translating residual exposure, "
        "control coverage, mitigation execution and business criticality "
        "into explainable management priorities."
    )

    # =========================================================
    # LOAD
    # =========================================================

    action_df = get_management_action_queue()

    if action_df.empty:
        st.info("No management action data is available.")
        return

    # =========================================================
    # FILTERS
    # =========================================================

    st.subheader("Action Filters")

    col1, col2, col3, col4 = st.columns(4)

    initiative_options = ["All"] + sorted(
        action_df["initiative_id"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    selected_initiative = col1.selectbox(
        "Initiative",
        initiative_options,
        key="mac_initiative",
    )

    selected_priority = col2.selectbox(
        "Priority",
        ["All"] + PRIORITY_ORDER,
        key="mac_priority",
    )

    domain_options = ["All"] + sorted(
        action_df["risk_domain"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    selected_domain = col3.selectbox(
        "Risk Domain",
        domain_options,
        key="mac_domain",
    )

    band_options = ["All"] + sorted(
        action_df["residual_risk_band"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    selected_band = col4.selectbox(
        "Residual Risk Band",
        band_options,
        key="mac_band",
    )

    filtered_df = action_df.copy()

    if selected_initiative != "All":
        filtered_df = filtered_df[
            filtered_df["initiative_id"].astype(str)
            == selected_initiative
        ]

    if selected_priority != "All":
        filtered_df = filtered_df[
            filtered_df["action_priority"]
            == selected_priority
        ]

    if selected_domain != "All":
        filtered_df = filtered_df[
            filtered_df["risk_domain"]
            == selected_domain
        ]

    if selected_band != "All":
        filtered_df = filtered_df[
            filtered_df["residual_risk_band"]
            == selected_band
        ]

    # =========================================================
    # KPI STRIP
    # =========================================================

    p1 = (
        filtered_df["action_priority"]
        == "P1 - Immediate Management Attention"
    ).sum()

    p2 = (
        filtered_df["action_priority"]
        == "P2 - Management Action Required"
    ).sum()

    p3 = (
        filtered_df["action_priority"]
        == "P3 - Controlled Monitoring"
    ).sum()

    overdue = int(
        filtered_df["overdue_mitigations"].sum()
    )

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(
        "Risks in Queue",
        len(filtered_df),
    )

    col2.metric(
        "P1 Immediate",
        int(p1),
    )

    col3.metric(
        "P2 Action Required",
        int(p2),
    )

    col4.metric(
        "P3 Monitoring",
        int(p3),
    )

    col5.metric(
        "Overdue Mitigations",
        overdue,
    )

    st.divider()

    # =========================================================
    # PRIORITY DISTRIBUTION
    # =========================================================

    st.subheader("Management Attention Distribution")

    priority_counts = (
        filtered_df["action_priority"]
        .value_counts()
        .reindex(
            PRIORITY_ORDER,
            fill_value=0,
        )
        .rename_axis("priority")
        .reset_index(
            name="risk_count"
        )
    )

    figure = px.bar(
        priority_counts,
        x="priority",
        y="risk_count",
        text="risk_count",
        title="Risk-Level Management Priority",
    )

    figure.update_layout(
        xaxis_title="Management Priority",
        yaxis_title="Risk Count",
        height=420,
    )

    figure.update_traces(
        textposition="outside"
    )

    st.plotly_chart(
        figure,
        width="stretch",
    )

    # =========================================================
    # TOP ACTION QUEUE
    # =========================================================

    st.subheader("Top Management Action Queue")

    queue_columns = [
        "risk_id",
        "initiative_id",
        "initiative_name",
        "risk_name",
        "risk_domain",
        "residual_risk_score",
        "residual_risk_band",
        "control_count",
        "avg_control_effectiveness",
        "mitigation_count",
        "mitigation_completion",
        "overdue_mitigations",
        "action_priority",
        "management_priority_score",
    ]

    queue_df = (
        filtered_df[queue_columns]
        .sort_values(
            [
                "management_priority_score",
                "residual_risk_score",
            ],
            ascending=False,
        )
        .head(25)
        .copy()
    )

    st.dataframe(
        queue_df,
        width="stretch",
        hide_index=True,
    )

    # =========================================================
    # RISK INVESTIGATION
    # =========================================================

    st.subheader("Risk Investigation")

    investigation_df = (
        filtered_df
        .sort_values(
            [
                "management_priority_score",
                "residual_risk_score",
            ],
            ascending=False,
        )
        .copy()
    )

    if investigation_df.empty:
        st.info(
            "No risks match the selected filters."
        )
        return

    investigation_df["display_name"] = (
        investigation_df["risk_id"].astype(str)
        + " | "
        + investigation_df["initiative_id"].astype(str)
        + " | "
        + investigation_df["risk_name"].astype(str)
    )

    selected_risk_display = st.selectbox(
        "Select a risk for detailed investigation",
        investigation_df["display_name"].tolist(),
        key="mac_risk_selector",
    )

    selected_risk = investigation_df[
        investigation_df["display_name"]
        == selected_risk_display
    ].iloc[0]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Priority",
        selected_risk["action_priority"],
    )

    col2.metric(
        "Priority Score",
        f'{float(selected_risk["management_priority_score"]):.1f}',
    )

    col3.metric(
        "Residual Risk",
        f'{float(selected_risk["residual_risk_score"]):.2f}',
    )

    col4.metric(
        "Residual Band",
        selected_risk["residual_risk_band"],
    )

    # =========================================================
    # RISK CONTEXT
    # =========================================================

    st.markdown("### Risk Context")

    context_df = pd.DataFrame(
        [
            {
                "Risk ID": selected_risk["risk_id"],
                "Initiative": selected_risk["initiative_name"],
                "Transformation Type": selected_risk[
                    "transformation_type"
                ],
                "Business Unit": selected_risk[
                    "business_unit"
                ],
                "Risk Domain": selected_risk[
                    "risk_domain"
                ],
                "Risk Status": selected_risk[
                    "risk_status"
                ],
                "Likelihood": selected_risk[
                    "likelihood"
                ],
                "Impact": selected_risk[
                    "impact"
                ],
                "Inherent Risk": selected_risk[
                    "inherent_risk_score"
                ],
                "Control Count": selected_risk[
                    "control_count"
                ],
                "Avg Control Effectiveness": (
                    f'{float(selected_risk["avg_control_effectiveness"]):.1f}%'
                ),
                "Mitigation Count": selected_risk[
                    "mitigation_count"
                ],
                "Mitigation Completion": (
                    f'{float(selected_risk["mitigation_completion"]):.1f}%'
                ),
                "Overdue Mitigations": selected_risk[
                    "overdue_mitigations"
                ],
            }
        ]
    )

    st.dataframe(
        context_df,
        width="stretch",
        hide_index=True,
    )

    # =========================================================
    # DESCRIPTION
    # =========================================================

    st.markdown("### Risk Description")

    st.write(
        selected_risk["description"]
    )

    # =========================================================
    # RECOMMENDED ACTION
    # =========================================================

    st.markdown(
        "### Recommended Management Action"
    )

    st.warning(
        selected_risk[
            "recommended_management_action"
        ]
    )

    # =========================================================
    # WHY PRIORITIZED
    # =========================================================

    st.markdown(
        "### Why This Risk Is Prioritized"
    )

    reasons = []

    if bool(
        selected_risk[
            "is_critical_residual_risk"
        ]
    ):
        reasons.append(
            "The risk has critical residual exposure."
        )

    elif bool(
        selected_risk[
            "is_high_residual_risk"
        ]
    ):
        reasons.append(
            "The risk has high residual exposure."
        )

    if int(
        selected_risk["control_count"]
    ) == 0:
        reasons.append(
            "No control coverage is currently recorded."
        )

    elif float(
        selected_risk[
            "avg_control_effectiveness"
        ]
    ) < 50:
        reasons.append(
            "Control effectiveness is below 50%."
        )

    if int(
        selected_risk["mitigation_count"]
    ) == 0:
        reasons.append(
            "No mitigation action is currently recorded."
        )

    if int(
        selected_risk["overdue_mitigations"]
    ) > 0:
        reasons.append(
            "One or more mitigation actions are overdue."
        )

    if float(
        selected_risk["mitigation_completion"]
    ) < 50:
        reasons.append(
            "Mitigation execution is below 50% completion."
        )

    if reasons:
        for reason in reasons:
            st.markdown(
                f"- {reason}"
            )
    else:
        st.markdown(
            "- The risk is currently prioritized for "
            "controlled monitoring based on its residual "
            "exposure and execution indicators."
        )

    st.caption(
        "Management priority is an analytical decision-support "
        "score. Risk appetite, governance policy and accountable "
        "management judgement should remain the final decision "
        "authority."
    )