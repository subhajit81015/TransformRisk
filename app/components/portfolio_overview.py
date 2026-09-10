import pandas as pd
import plotly.express as px
import streamlit as st

def render_portfolio_overview(
    portfolio_df,
    portfolio_kpis,
):
    if portfolio_df.empty or portfolio_kpis.empty:
        st.info("Portfolio data is not available.")
        return

    kpi = portfolio_kpis.iloc[0]

    st.subheader("Executive Portfolio View")

    # ============================================================
    # PORTFOLIO KPI STRIP
    # ============================================================

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Initiatives",
        int(kpi["total_initiatives"]),
    )

    col2.metric(
        "DO NOT PROCEED",
        int(kpi["do_not_proceed"]),
    )

    col3.metric(
        "Proceed with Conditions",
        int(kpi["proceed_with_conditions"]),
    )

    col4.metric(
        "Proceed",
        int(kpi["proceed"]),
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Critical-Risk Initiatives",
        int(kpi["initiatives_with_critical_risk"]),
    )

    col2.metric(
        "High-Risk Initiatives",
        int(kpi["initiatives_with_high_risk"]),
    )

    col3.metric(
        "Not-Ready Initiatives",
        int(kpi["initiatives_not_ready"]),
    )

    col4.metric(
        "Overdue-Action Initiatives",
        int(kpi["initiatives_with_overdue_actions"]),
    )

    st.divider()

    # ============================================================
    # PORTFOLIO GOVERNANCE DISTRIBUTION
    # ============================================================

    st.markdown("### Governance Decision Distribution")

    decision_counts = (
        portfolio_df["transformation_decision"]
        .value_counts()
        .rename_axis("decision")
        .reset_index(name="initiative_count")
    )

    decision_order = [
        "DO NOT PROCEED",
        "REMEDIATE BEFORE PROCEEDING",
        "PROCEED WITH CONDITIONS",
        "PROCEED",
    ]

    decision_counts["decision"] = pd.Categorical(
        decision_counts["decision"],
        categories=decision_order,
        ordered=True,
    )

    decision_counts = decision_counts.sort_values("decision")

    figure = px.bar(
        decision_counts,
        x="decision",
        y="initiative_count",
        text="initiative_count",
        title="Transformation Governance Decisions",
    )

    figure.update_layout(
        xaxis_title="Governance Decision",
        yaxis_title="Initiative Count",
        height=430,
    )

    figure.update_traces(
        textposition="outside",
    )

    st.plotly_chart(
        figure,
        width="stretch",
    )

    # ============================================================
    # PORTFOLIO RISK VS READINESS
    # ============================================================

    st.markdown("### Risk vs Readiness Portfolio Map")

    scatter_df = portfolio_df.copy()

    figure = px.scatter(
        scatter_df,
        x="minimum_readiness_score",
        y="maximum_residual_risk",
        size="total_risks",
        hover_name="initiative_name",
        hover_data=[
            "initiative_id",
            "business_unit",
            "transformation_type",
            "transformation_decision",
            "overall_readiness_score",
            "average_control_effectiveness",
        ],
        title="Initiative Risk Exposure vs Minimum Readiness",
    )

    figure.add_vline(
        x=50,
        line_dash="dash",
        annotation_text="Readiness Threshold",
    )

    figure.update_layout(
        xaxis_title="Minimum Readiness Score",
        yaxis_title="Maximum Residual Risk",
        height=550,
    )

    st.plotly_chart(
        figure,
        width="stretch",
    )

    # ============================================================
    # PORTFOLIO HEALTH
    # ============================================================

    st.markdown("### Portfolio Health Indicators")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Average Readiness",
        f'{float(kpi["average_portfolio_readiness"]):.1f}',
    )

    col2.metric(
        "Average Control Effectiveness",
        f'{float(kpi["average_portfolio_control_effectiveness"]):.1f}%',
    )

    col3.metric(
        "Average Residual Risk",
        f'{float(kpi["average_portfolio_residual_risk"]):.2f}',
    )

    # ============================================================
    # MANAGEMENT ATTENTION QUEUE
    # ============================================================

    st.markdown("### Management Attention Queue")

    attention_df = portfolio_df[
        portfolio_df["transformation_decision"].isin(
            [
                "DO NOT PROCEED",
                "REMEDIATE BEFORE PROCEEDING",
                "PROCEED WITH CONDITIONS",
            ]
        )
    ].copy()

    attention_df = attention_df[
        [
            "initiative_id",
            "initiative_name",
            "transformation_decision",
            "maximum_residual_risk",
            "minimum_readiness_score",
            "average_control_effectiveness",
            "overdue_actions",
        ]
    ]

    attention_df = attention_df.sort_values(
        by=[
            "maximum_residual_risk",
            "minimum_readiness_score",
        ],
        ascending=[
            False,
            True,
        ],
    )

    st.dataframe(
        attention_df,
        width="stretch",
        hide_index=True,
    )

    # ============================================================
    # EXECUTIVE INTERPRETATION
    # ============================================================

    st.markdown("### Executive Interpretation")

    do_not_proceed = int(kpi["do_not_proceed"])
    remediate = int(kpi["remediate_before_proceeding"])
    conditional = int(kpi["proceed_with_conditions"])
    not_ready = int(kpi["initiatives_not_ready"])

    if do_not_proceed > 0:
        st.warning(
            f"{do_not_proceed} initiative(s) currently require "
            "a DO NOT PROCEED decision based on critical residual risk."
        )

    if remediate > 0:
        st.warning(
            f"{remediate} initiative(s) require remediation "
            "before transformation execution."
        )

    if conditional > 0:
        st.info(
            f"{conditional} initiative(s) are eligible only for "
            "PROCEED WITH CONDITIONS under the current governance logic."
        )

    if not_ready > 0:
        st.info(
            f"{not_ready} initiative(s) have minimum readiness below "
            "50 and require readiness improvement at the execution level."
        )

    st.caption(
        "Portfolio analytics are based on the synthetic transformation "
        "governance dataset. They are illustrative and do not represent "
        "real enterprise decisions."
    )