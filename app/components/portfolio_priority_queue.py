import pandas as pd
import plotly.express as px
import streamlit as st


def render_portfolio_priority_queue(
    priority_df,
    priority_summary,
):
    if priority_df.empty or priority_summary.empty:
        st.info("Portfolio priority data is not available.")
        return

    summary = priority_summary.iloc[0]

    st.subheader("Portfolio Management Attention")

    # ============================================================
    # PRIORITY KPI STRIP
    # ============================================================

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "P1 Immediate",
        int(summary["p1_initiatives"]),
    )

    col2.metric(
        "P2 Action Required",
        int(summary["p2_initiatives"]),
    )

    col3.metric(
        "P3 Monitoring",
        int(summary["p3_initiatives"]),
    )

    col4.metric(
        "P4 Routine",
        int(summary["p4_initiatives"]),
    )

    # ============================================================
    # PRIORITY DISTRIBUTION
    # ============================================================

    st.markdown("### Management Attention Distribution")

    priority_counts = (
        priority_df["portfolio_priority"]
        .value_counts()
        .rename_axis("priority")
        .reset_index(name="initiative_count")
    )

    priority_order = [
        "P1 - Immediate Management Attention",
        "P2 - Management Action Required",
        "P3 - Controlled Monitoring",
        "P4 - Routine Monitoring",
    ]

    priority_counts["priority"] = priority_counts["priority"].astype(
        pd.CategoricalDtype(
            categories=priority_order,
            ordered=True,
        )
    )

    priority_counts = priority_counts.sort_values("priority")

    figure = px.bar(
        priority_counts,
        x="priority",
        y="initiative_count",
        text="initiative_count",
        title="Portfolio Priority Distribution",
    )

    figure.update_layout(
        xaxis_title="Management Priority",
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
    # TOP MANAGEMENT QUEUE
    # ============================================================

    st.markdown("### Top Management Attention Queue")

    queue_columns = [
        "initiative_id",
        "initiative_name",
        "portfolio_priority",
        "portfolio_priority_score",
        "transformation_decision",
        "maximum_residual_risk",
        "minimum_readiness_score",
        "average_control_effectiveness",
        "overdue_actions",
    ]

    queue_df = priority_df[queue_columns].head(20).copy()

    st.dataframe(
        queue_df,
        width="stretch",
        hide_index=True,
    )

    # ============================================================
    # HIGHEST-PRIORITY INITIATIVES
    # ============================================================

    st.markdown("### Highest-Priority Initiatives")

    top_df = priority_df.head(5)

    for _, row in top_df.iterrows():
        priority = row["portfolio_priority"]
        score = float(row["portfolio_priority_score"])

        st.markdown(
            f"**{priority} | {row['initiative_id']} | "
            f"{row['initiative_name']}**"
        )

        st.caption(
            f"Priority Score: {score:.1f}/100 • "
            f"Decision: {row['transformation_decision']} • "
            f"Maximum Residual Risk: "
            f"{float(row['maximum_residual_risk']):.2f} • "
            f"Minimum Readiness: "
            f"{float(row['minimum_readiness_score']):.1f}"
        )

    # ============================================================
    # PORTFOLIO DRILL-DOWN
    # ============================================================

    st.markdown("### Portfolio Drill-Down")

    initiative_options = priority_df[
        [
            "initiative_id",
            "initiative_name",
            "portfolio_priority",
            "portfolio_priority_score",
        ]
    ].copy()

    initiative_options["display_name"] = (
        initiative_options["initiative_id"].astype(str)
        + " | "
        + initiative_options["initiative_name"].astype(str)
    )

    display_options = initiative_options["display_name"].tolist()

    # ------------------------------------------------------------
    # Determine current portfolio selection
    # ------------------------------------------------------------

    current_portfolio_id = st.session_state.get(
        "portfolio_drilldown_initiative_id"
    )

    if current_portfolio_id in initiative_options["initiative_id"].values:
        current_index = initiative_options[
            "initiative_id"
        ].tolist().index(current_portfolio_id)
    else:
        current_index = 0

    selected_portfolio_initiative = st.selectbox(
        "Select an initiative for detailed investigation",
        options=display_options,
        index=current_index,
        key="portfolio_drilldown_initiative",
    )

    selected_row = initiative_options[
        initiative_options["display_name"]
        == selected_portfolio_initiative
    ].iloc[0]

    selected_portfolio_id = selected_row["initiative_id"]

    # Store the current portfolio selection.
    st.session_state["portfolio_drilldown_initiative_id"] = (
        selected_portfolio_id
    )

    # ------------------------------------------------------------
    # Selected initiative metrics
    # ------------------------------------------------------------

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Portfolio Priority",
        selected_row["portfolio_priority"],
    )

    col2.metric(
        "Priority Score",
        f'{float(selected_row["portfolio_priority_score"]):.1f}/100',
    )

    col3.metric(
        "Initiative",
        selected_row["initiative_id"],
    )

    # ------------------------------------------------------------
    # Investigation action
    # ------------------------------------------------------------

    st.caption(
        "Use Investigate to open this initiative in the detailed "
        "Initiative Decision Center."
    )

    investigate = st.button(
        "Investigate Selected Initiative",
        type="primary",
        use_container_width=True,
        key="investigate_portfolio_initiative",
    )

    if investigate:
        st.session_state["selected_initiative_target"] = str(
            selected_portfolio_id
        )

        st.rerun()

    # ============================================================
    # PORTFOLIO PRIORITY SCORE DISTRIBUTION
    # ============================================================

    st.markdown("### Priority Score Distribution")

    figure = px.histogram(
        priority_df,
        x="portfolio_priority_score",
        nbins=20,
        title="Distribution of Portfolio Priority Scores",
    )

    figure.update_layout(
        xaxis_title="Priority Score",
        yaxis_title="Initiative Count",
        height=420,
    )

    st.plotly_chart(
        figure,
        width="stretch",
    )

    # ============================================================
    # MANAGEMENT INTERPRETATION
    # ============================================================

    st.markdown("### Portfolio Priority Interpretation")

    p1 = int(summary["p1_initiatives"])
    p2 = int(summary["p2_initiatives"])
    p3 = int(summary["p3_initiatives"])
    p4 = int(summary["p4_initiatives"])

    total_initiatives = int(summary["total_initiatives"])

    if total_initiatives > 0:
        immediate_share = (
            (p1 + p2)
            / total_initiatives
            * 100
        )
    else:
        immediate_share = 0.0

    if p1 > 0:
        st.warning(
            f"{p1} initiative(s) require immediate management "
            "attention based on the portfolio priority model."
        )

    st.info(
        f"{p1 + p2} of {total_initiatives} initiatives "
        f"({immediate_share:.1f}%) fall into P1 or P2 and should "
        "receive active management attention."
    )

    st.caption(
        "Portfolio priority distribution: "
        f"{p1} P1, {p2} P2, {p3} P3 and {p4} P4 initiatives. "
        "The scoring model is analytical and should be calibrated "
        "against organizational risk appetite before enterprise "
        "deployment."
    )