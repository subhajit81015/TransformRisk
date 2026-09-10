import pandas as pd
import streamlit as st


def _safe_float(value, default=0.0):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value, default=0):
    try:
        if pd.isna(value):
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def render_management_action_queue(
    action_df: pd.DataFrame,
):
    st.subheader("Management Action Prioritization")

    st.caption(
        "Risk exposure and coverage conditions are converted into "
        "a management priority score to identify where intervention "
        "should occur first."
    )

    if action_df.empty:
        st.info(
            "No management actions require prioritization."
        )
        return

    p1_df = action_df[
        action_df["management_priority"].str.startswith(
            "P1",
            na=False,
        )
    ]

    p2_df = action_df[
        action_df["management_priority"].str.startswith(
            "P2",
            na=False,
        )
    ]

    p3_df = action_df[
        action_df["management_priority"].str.startswith(
            "P3",
            na=False,
        )
    ]

    p4_df = action_df[
        action_df["management_priority"].str.startswith(
            "P4",
            na=False,
        )
    ]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "P1 Immediate",
            len(p1_df),
        )

    with col2:
        st.metric(
            "P2 Action Required",
            len(p2_df),
        )

    with col3:
        st.metric(
            "P3 Monitoring",
            len(p3_df),
        )

    with col4:
        st.metric(
            "P4 Routine",
            len(p4_df),
        )

    st.divider()

    st.subheader("Management Priority Ranking")

    display_df = action_df[
        [
            "risk_id",
            "risk_name",
            "risk_domain",
            "residual_risk_score",
            "residual_risk_band",
            "control_count",
            "mitigation_count",
            "management_priority_score",
            "management_priority",
        ]
    ].copy()

    display_df = display_df.rename(
        columns={
            "risk_id": "Risk ID",
            "risk_name": "Risk",
            "risk_domain": "Domain",
            "residual_risk_score": "Residual Risk",
            "residual_risk_band": "Risk Band",
            "control_count": "Controls",
            "mitigation_count": "Mitigations",
            "management_priority_score": "Priority Score",
            "management_priority": "Management Priority",
        }
    )

    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
        column_config={
            "Residual Risk": st.column_config.NumberColumn(
                format="%.2f"
            ),
            "Priority Score": st.column_config.NumberColumn(
                format="%.1f"
            ),
        },
    )

    st.divider()

    st.subheader("Priority Management Actions")

    priority_df = action_df[
        action_df["management_priority"].str.startswith(
            ("P1", "P2"),
            na=False,
        )
    ].copy()

    if priority_df.empty:
        st.success(
            "No P1 or P2 management actions currently require escalation."
        )
        return

    for _, row in priority_df.iterrows():

        priority = str(
            row["management_priority"]
        )

        risk_id = str(
            row["risk_id"]
        )

        risk_name = str(
            row["risk_name"]
        )

        domain = str(
            row["risk_domain"]
        )

        residual_risk = _safe_float(
            row["residual_risk_score"]
        )

        priority_score = _safe_float(
            row["management_priority_score"]
        )

        controls = _safe_int(
            row["control_count"]
        )

        mitigations = _safe_int(
            row["mitigation_count"]
        )

        control_effectiveness = _safe_float(
            row["average_control_effectiveness"]
        )

        mitigation_completion = _safe_float(
            row["average_mitigation_completion"]
        )

        action = str(
            row["recommended_management_action"]
        )

        with st.container(border=True):

            st.markdown(
                f"**{priority} | {risk_id} | {risk_name}**"
            )

            c1, c2, c3, c4, c5 = st.columns(5)

            with c1:
                st.metric(
                    "Priority Score",
                    f"{priority_score:.1f}/100",
                )

            with c2:
                st.metric(
                    "Residual Risk",
                    f"{residual_risk:.2f}",
                )

            with c3:
                st.metric(
                    "Controls",
                    controls,
                )

            with c4:
                st.metric(
                    "Mitigations",
                    mitigations,
                )

            with c5:
                st.metric(
                    "Control Effectiveness",
                    f"{control_effectiveness:.1f}%",
                )

            st.caption(
                f"Domain: {domain} | "
                f"Mitigation Completion: "
                f"{mitigation_completion:.1f}%"
            )

            st.markdown(
                f"**Management Action:** {action}"
            )

    st.caption(
        "The Management Priority Score is a prototype analytical "
        "scoring model. Thresholds and component weights should be "
        "calibrated against organizational risk appetite before "
        "enterprise deployment."
    )