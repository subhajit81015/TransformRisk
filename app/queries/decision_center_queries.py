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
            params=params
        )


def get_initiative_list() -> pd.DataFrame:
    query = """
        SELECT
            initiative_id,
            initiative_name
        FROM analytics.transformation_decision
        ORDER BY initiative_id;
    """

    return run_query(query)


def get_initiative_decision(initiative_id: str) -> pd.DataFrame:
    query = """
        SELECT
            initiative_id,
            initiative_name,
            transformation_type,
            business_unit,
            owner,
            strategic_priority,
            criticality,
            budget,
            target_completion_date,
            status,

            total_risks,
            critical_residual_risks,
            high_residual_risks,
            average_residual_risk,
            maximum_residual_risk,

            average_control_effectiveness,

            overall_readiness_score,
            technology_readiness,
            data_readiness,
            process_readiness,
            people_readiness,
            governance_readiness,
            minimum_readiness_score,
            readiness_band,
            readiness_gap_status,

            total_mitigation_actions,
            overdue_actions,
            completed_mitigation_actions,
            average_mitigation_completion,

            transformation_decision,
            decision_rationale

        FROM analytics.transformation_decision
        WHERE initiative_id = :initiative_id;
    """

    return run_query(
        query,
        {"initiative_id": initiative_id}
    )


def get_initiative_risks(initiative_id: str) -> pd.DataFrame:
    query = """
        SELECT
            risk_id,
            risk_name,
            risk_domain,
            likelihood,
            impact,
            inherent_risk_score,
            inherent_risk_band,
            control_effectiveness,
            residual_risk_score,
            residual_risk_band,
            risk_status
        FROM analytics.risk_scoring
        WHERE initiative_id = :initiative_id
        ORDER BY residual_risk_score DESC;
    """

    return run_query(
        query,
        {"initiative_id": initiative_id}
    )


def get_initiative_mitigations(initiative_id: str) -> pd.DataFrame:
    query = """
        SELECT
            action_id,
            risk_id,
            risk_name,
            action_name,
            action_owner,
            priority,
            status,
            due_date,
            completion_percentage,
            expected_risk_reduction,
            is_overdue,
            execution_status
        FROM analytics.mitigation_summary
        WHERE initiative_id = :initiative_id
        ORDER BY
            is_overdue DESC,
            completion_percentage ASC,
            due_date ASC;
    """

    return run_query(
        query,
        {"initiative_id": initiative_id}
    )