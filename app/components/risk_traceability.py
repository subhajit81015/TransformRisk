import pandas as pd
import streamlit as st


def _safe_float(value, default=0.0):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_text(value, default="Not available"):
    if pd.isna(value):
        return default

    text = str(value).strip()

    return text if text else default


def render_risk_traceability(trace_df: pd.DataFrame):

    st.subheader("Risk → Control → Mitigation Traceability")

    st.caption(
        "Connects material risk exposure to the controls protecting it "
        "and the mitigation actions required to reduce remaining exposure."
    )

    if trace_df.empty:
        st.info(
            "No risk, control or mitigation traceability data is "
            "available for this initiative."
        )
        return

    # =========================================================
    # EXECUTIVE TRACEABILITY KPIs
    # =========================================================

    total_risks = trace_df["risk_id"].nunique()

    total_controls = (
        trace_df["control_id"]
        .dropna()
        .nunique()
    )

    total_mitigations = (
        trace_df["action_id"]
        .dropna()
        .nunique()
    )

    uncontrolled_risks = (
        trace_df.loc[
            trace_df["control_id"].isna(),
            "risk_id",
        ]
        .nunique()
    )

    unmitigated_risks = (
        trace_df.loc[
            trace_df["action_id"].isna(),
            "risk_id",
        ]
        .nunique()
    )

    overdue_actions = (
        trace_df.loc[
            trace_df["is_overdue"] == True,
            "action_id",
        ]
        .dropna()
        .nunique()
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Risks",
            total_risks,
        )

    with col2:
        st.metric(
            "Controls",
            total_controls,
        )

    with col3:
        st.metric(
            "Mitigations",
            total_mitigations,
        )

    with col4:
        st.metric(
            "Overdue Actions",
            overdue_actions,
        )

    # =========================================================
    # TRACEABILITY GAPS
    # =========================================================

    if uncontrolled_risks > 0 or unmitigated_risks > 0:
        st.warning(
            f"Traceability gaps detected: "
            f"{uncontrolled_risks} risk(s) without mapped controls "
            f"and {unmitigated_risks} risk(s) without mapped mitigation."
        )
    else:
        st.success(
            "All identified risks have mapped controls and mitigation "
            "actions in the current initiative data."
        )

    # =========================================================
    # PRIORITY TRACEABILITY
    # =========================================================

    st.markdown("#### Priority Risk Action Chain")

    priority_df = trace_df.copy()

    priority_df["residual_risk_score"] = (
        pd.to_numeric(
            priority_df["residual_risk_score"],
            errors="coerce",
        )
        .fillna(0)
    )

    priority_df["effectiveness_score"] = (
        pd.to_numeric(
            priority_df["effectiveness_score"],
            errors="coerce",
        )
    )

    priority_df["completion_percentage"] = (
        pd.to_numeric(
            priority_df["completion_percentage"],
            errors="coerce",
        )
        .fillna(0)
    )

    priority_df["priority_score"] = (
        priority_df["residual_risk_score"]
        + (
            10
            - priority_df["effectiveness_score"].fillna(0) / 10
        )
        + (
            (100 - priority_df["completion_percentage"])
            / 100
        )
    )

    priority_df = priority_df.sort_values(
        [
            "residual_risk_score",
            "effectiveness_score",
            "completion_percentage",
        ],
        ascending=[
            False,
            True,
            True,
        ],
    )

    # Keep one representative chain per risk.
    priority_df = (
        priority_df
        .drop_duplicates(
            subset=["risk_id"],
            keep="first",
        )
        .head(10)
    )

    display_df = priority_df[
        [
            "risk_id",
            "risk_name",
            "risk_domain",
            "residual_risk_score",
            "residual_risk_band",
            "control_id",
            "control_name",
            "effectiveness_score",
            "action_id",
            "action_name",
            "action_owner",
            "due_date",
            "completion_percentage",
            "expected_risk_reduction",
            "is_overdue",
        ]
    ].copy()

    display_df = display_df.rename(
        columns={
            "risk_id": "Risk ID",
            "risk_name": "Risk",
            "risk_domain": "Domain",
            "residual_risk_score": "Residual Risk",
            "residual_risk_band": "Risk Band",
            "control_id": "Control ID",
            "control_name": "Control",
            "effectiveness_score": "Control Effectiveness",
            "action_id": "Action ID",
            "action_name": "Mitigation Action",
            "action_owner": "Action Owner",
            "due_date": "Due Date",
            "completion_percentage": "Completion %",
            "expected_risk_reduction": "Expected Risk Reduction",
            "is_overdue": "Overdue",
        }
    )

    display_df["Residual Risk"] = (
        display_df["Residual Risk"].round(2)
    )

    display_df["Control Effectiveness"] = (
        display_df["Control Effectiveness"].round(1)
    )

    display_df["Completion %"] = (
        display_df["Completion %"].round(1)
    )

    display_df["Expected Risk Reduction"] = (
        display_df["Expected Risk Reduction"].round(2)
    )

    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
    )

    # =========================================================
    # SELECTED RISK CHAIN
    # =========================================================

    st.markdown("#### Trace a Specific Risk")

    risk_options = (
        priority_df[
            [
                "risk_id",
                "risk_name",
            ]
        ]
        .drop_duplicates()
    )

    risk_lookup = {
        f"{row.risk_id} | {row.risk_name}": row.risk_id
        for row in risk_options.itertuples()
    }

    selected_label = st.selectbox(
        "Select Risk",
        options=list(risk_lookup.keys()),
        key="traceability_risk_selector",
    )

    selected_risk_id = risk_lookup[selected_label]

    selected = trace_df[
        trace_df["risk_id"] == selected_risk_id
    ].copy()

    if selected.empty:
        st.info("No traceability details found.")
        return

    risk = selected.iloc[0]

    # =========================================================
    # RISK
    # =========================================================

    st.markdown("##### 1. Risk Exposure")

    risk_col1, risk_col2, risk_col3, risk_col4 = st.columns(4)

    with risk_col1:
        st.metric(
            "Risk ID",
            _safe_text(risk["risk_id"]),
        )

    with risk_col2:
        st.metric(
            "Residual Risk",
            f"{_safe_float(risk['residual_risk_score']):.2f}",
        )

    with risk_col3:
        st.metric(
            "Risk Band",
            _safe_text(risk["residual_risk_band"]),
        )

    with risk_col4:
        st.metric(
            "Domain",
            _safe_text(risk["risk_domain"]),
        )

    st.info(
        f"**{_safe_text(risk['risk_name'])}**\n\n"
        f"Likelihood: **{_safe_text(risk['likelihood'])}**  \n"
        f"Impact: **{_safe_text(risk['impact'])}**"
    )

    # =========================================================
    # CONTROL
    # =========================================================

    st.markdown("##### ↓ 2. Control Protection")

    controls = selected[
        selected["control_id"].notna()
    ].drop_duplicates(
        subset=["control_id"]
    )

    if controls.empty:
        st.error(
            "No control is currently mapped to this risk."
        )
    else:
        for _, control in controls.iterrows():

            effectiveness = _safe_float(
                control["effectiveness_score"]
            )

            if effectiveness < 50:
                st.error(
                    f"**{_safe_text(control['control_id'])} | "
                    f"{_safe_text(control['control_name'])}**\n\n"
                    f"Effectiveness: **{effectiveness:.1f}%**  \n"
                    f"Strength: **{_safe_text(control['control_strength'])}**  \n"
                    f"Owner: **{_safe_text(control['control_owner'])}**"
                )

            elif effectiveness < 60:
                st.warning(
                    f"**{_safe_text(control['control_id'])} | "
                    f"{_safe_text(control['control_name'])}**\n\n"
                    f"Effectiveness: **{effectiveness:.1f}%**  \n"
                    f"Strength: **{_safe_text(control['control_strength'])}**  \n"
                    f"Owner: **{_safe_text(control['control_owner'])}**"
                )

            else:
                st.success(
                    f"**{_safe_text(control['control_id'])} | "
                    f"{_safe_text(control['control_name'])}**\n\n"
                    f"Effectiveness: **{effectiveness:.1f}%**  \n"
                    f"Strength: **{_safe_text(control['control_strength'])}**  \n"
                    f"Owner: **{_safe_text(control['control_owner'])}**"
                )

    # =========================================================
    # MITIGATION
    # =========================================================

    st.markdown("##### ↓ 3. Mitigation Action")

    mitigations = selected[
        selected["action_id"].notna()
    ].drop_duplicates(
        subset=["action_id"]
    )

    if mitigations.empty:
        st.error(
            "No mitigation action is currently mapped to this risk."
        )
    else:
        for _, mitigation in mitigations.iterrows():

            completion = _safe_float(
                mitigation["completion_percentage"]
            )

            overdue = bool(
                mitigation["is_overdue"]
            )

            action_text = (
                f"**{_safe_text(mitigation['action_id'])} | "
                f"{_safe_text(mitigation['action_name'])}**\n\n"
                f"Owner: **{_safe_text(mitigation['action_owner'])}**  \n"
                f"Due Date: **{_safe_text(mitigation['due_date'])}**  \n"
                f"Completion: **{completion:.1f}%**  \n"
                f"Expected Risk Reduction: "
                f"**{_safe_float(mitigation['expected_risk_reduction']):.2f}**"
            )

            if overdue:
                st.error(
                    action_text
                    + "\n\n⚠️ **OVERDUE**"
                )
            elif completion < 50:
                st.warning(action_text)
            else:
                st.info(action_text)

    # =========================================================
    # MANAGEMENT ACTION
    # =========================================================

    st.markdown("##### ↓ 4. Management Action")

    effectiveness_values = pd.to_numeric(
        selected["effectiveness_score"],
        errors="coerce",
    )

    weakest_control = (
        effectiveness_values.min()
        if not effectiveness_values.dropna().empty
        else None
    )

    has_overdue = (
        selected["is_overdue"]
        .fillna(False)
        .astype(bool)
        .any()
    )

    if has_overdue:
        st.error(
            "Management action: resolve overdue mitigation "
            "ownership and execution before transformation scale-up."
        )

    elif weakest_control is not None and weakest_control < 50:
        st.warning(
            "Management action: strengthen the mapped control "
            "before relying on the current risk treatment."
        )

    elif (
        weakest_control is not None
        and weakest_control < 60
    ):
        st.warning(
            "Management action: improve control effectiveness "
            "and monitor mitigation completion."
        )

    else:
        st.success(
            "Management action: continue monitoring the risk, "
            "control effectiveness and mitigation execution."
        )