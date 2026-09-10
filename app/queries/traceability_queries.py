from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from sqlalchemy import text

from app.utils.db import engine


def run_query(query: str, params=None) -> pd.DataFrame:
    with engine.connect() as connection:
        return pd.read_sql(
            text(query),
            connection,
            params=params,
        )


def get_risk_control_mitigation_trace(
    initiative_id: str,
) -> pd.DataFrame:
    """
    Build an executive traceability chain:

        Risk → Control → Mitigation

    Priority is driven primarily by residual risk exposure,
    followed by control weakness and mitigation execution.
    """

    query = """
        SELECT
            r.risk_id,
            r.risk_name,
            r.risk_domain,
            r.likelihood,
            r.impact,
            r.inherent_risk_score,
            r.residual_risk_score,
            r.residual_risk_band,
            r.risk_status,

            c.control_id,
            c.control_name,
            c.control_type,
            c.control_owner,
            c.effectiveness_score,
            c.control_strength,
            c.control_status,

            m.action_id,
            m.action_name,
            m.action_owner,
            m.priority AS mitigation_priority,
            m.execution_status,
            m.due_date,
            m.completion_percentage,
            m.expected_risk_reduction,
            m.is_overdue

        FROM analytics.risk_scoring r

        LEFT JOIN analytics.control_summary c
            ON r.risk_id = c.risk_id
           AND c.initiative_id = r.initiative_id

        LEFT JOIN analytics.mitigation_summary m
            ON r.risk_id = m.risk_id
           AND m.initiative_id = r.initiative_id

        WHERE r.initiative_id = :initiative_id

        ORDER BY
            CASE r.residual_risk_band
                WHEN 'Critical' THEN 1
                WHEN 'High' THEN 2
                WHEN 'Medium' THEN 3
                WHEN 'Low' THEN 4
                ELSE 5
            END,
            r.residual_risk_score DESC,
            COALESCE(c.effectiveness_score, 0) ASC,
            COALESCE(m.is_overdue, FALSE) DESC,
            COALESCE(m.completion_percentage, 0) ASC;
    """

    return run_query(
        query,
        {"initiative_id": initiative_id},
    )


def get_traceability_summary(
    trace_df: pd.DataFrame,
) -> dict:
    """Calculate executive traceability KPIs."""

    if trace_df.empty:
        return {
            "risks": 0,
            "controls": 0,
            "mitigations": 0,
            "uncontrolled_risks": 0,
            "unmitigated_risks": 0,
            "overdue_actions": 0,
        }

    risk_count = trace_df["risk_id"].nunique()

    control_count = (
        trace_df["control_id"]
        .dropna()
        .nunique()
    )

    mitigation_count = (
        trace_df["action_id"]
        .dropna()
        .nunique()
    )

    risks_with_controls = (
        trace_df.loc[
            trace_df["control_id"].notna(),
            "risk_id",
        ]
        .nunique()
    )

    risks_with_mitigations = (
        trace_df.loc[
            trace_df["action_id"].notna(),
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

    return {
        "risks": risk_count,
        "controls": control_count,
        "mitigations": mitigation_count,
        "uncontrolled_risks": (
            risk_count - risks_with_controls
        ),
        "unmitigated_risks": (
            risk_count - risks_with_mitigations
        ),
        "overdue_actions": overdue_actions,
    }