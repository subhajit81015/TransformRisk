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
        return pd.read_sql(text(query), connection, params=params)


def get_portfolio_summary() -> pd.DataFrame:
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
            minimum_readiness_score,
            readiness_band,

            total_mitigation_actions,
            overdue_actions,
            completed_mitigation_actions,
            average_mitigation_completion,

            transformation_decision

        FROM analytics.transformation_decision

        ORDER BY
            CASE transformation_decision
                WHEN 'DO NOT PROCEED' THEN 1
                WHEN 'REMEDIATE BEFORE PROCEEDING' THEN 2
                WHEN 'PROCEED WITH CONDITIONS' THEN 3
                WHEN 'PROCEED' THEN 4
                ELSE 5
            END,
            maximum_residual_risk DESC,
            minimum_readiness_score ASC;
    """

    return run_query(query)


def get_portfolio_kpis() -> pd.DataFrame:
    query = """
        SELECT
            COUNT(*) AS total_initiatives,

            COUNT(*) FILTER (
                WHERE transformation_decision = 'DO NOT PROCEED'
            ) AS do_not_proceed,

            COUNT(*) FILTER (
                WHERE transformation_decision =
                    'REMEDIATE BEFORE PROCEEDING'
            ) AS remediate_before_proceeding,

            COUNT(*) FILTER (
                WHERE transformation_decision =
                    'PROCEED WITH CONDITIONS'
            ) AS proceed_with_conditions,

            COUNT(*) FILTER (
                WHERE transformation_decision = 'PROCEED'
            ) AS proceed,

            COUNT(*) FILTER (
                WHERE critical_residual_risks > 0
            ) AS initiatives_with_critical_risk,

            COUNT(*) FILTER (
                WHERE high_residual_risks > 0
            ) AS initiatives_with_high_risk,

            COUNT(*) FILTER (
                WHERE minimum_readiness_score < 50
            ) AS initiatives_not_ready,

            COUNT(*) FILTER (
                WHERE overdue_actions > 0
            ) AS initiatives_with_overdue_actions,

            ROUND(
                AVG(overall_readiness_score)::numeric,
                1
            ) AS average_portfolio_readiness,

            ROUND(
                AVG(average_control_effectiveness)::numeric,
                1
            ) AS average_portfolio_control_effectiveness,

            ROUND(
                AVG(average_residual_risk)::numeric,
                2
            ) AS average_portfolio_residual_risk

        FROM analytics.transformation_decision;
    """

    return run_query(query)