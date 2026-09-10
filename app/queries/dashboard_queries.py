from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from sqlalchemy import text

from app.utils.db import engine


def run_query(query: str) -> pd.DataFrame:
    with engine.connect() as connection:
        return pd.read_sql(text(query), connection)


def get_decision_summary() -> pd.DataFrame:
    query = """
        SELECT
            transformation_decision,
            COUNT(*) AS initiatives
        FROM analytics.transformation_decision
        GROUP BY transformation_decision
        ORDER BY initiatives DESC;
    """
    return run_query(query)


def get_portfolio_summary() -> pd.DataFrame:
    query = """
        SELECT
            COUNT(*) AS total_initiatives,
            COUNT(*) FILTER (
                WHERE transformation_decision = 'DO NOT PROCEED'
            ) AS do_not_proceed,
            COUNT(*) FILTER (
                WHERE transformation_decision =
                    'REMEDIATE BEFORE PROCEEDING'
            ) AS remediate,
            COUNT(*) FILTER (
                WHERE transformation_decision =
                    'PROCEED WITH CONDITIONS'
            ) AS proceed_with_conditions,
            COUNT(*) FILTER (
                WHERE transformation_decision = 'PROCEED'
            ) AS proceed,

            ROUND(
                AVG(overall_readiness_score)::numeric,
                2
            ) AS average_readiness,

            ROUND(
                AVG(average_residual_risk)::numeric,
                2
            ) AS average_residual_risk,

            SUM(overdue_actions) AS overdue_actions

        FROM analytics.transformation_decision;
    """
    return run_query(query)


def get_risk_domain_summary() -> pd.DataFrame:
    query = """
        SELECT
            risk_domain,
            total_risks,
            critical_residual_risks,
            high_residual_risks,
            average_residual_risk,
            average_control_effectiveness
        FROM analytics.risk_domain_summary
        ORDER BY average_residual_risk DESC;
    """
    return run_query(query)


def get_priority_initiatives() -> pd.DataFrame:
    query = """
        SELECT
            initiative_id,
            initiative_name,
            business_unit,
            criticality,
            critical_residual_risks,
            high_residual_risks,
            average_residual_risk,
            maximum_residual_risk,
            overall_readiness_score,
            minimum_readiness_score,
            average_control_effectiveness,
            overdue_actions,
            average_mitigation_completion,
            transformation_decision,
            decision_rationale
        FROM analytics.transformation_decision

        ORDER BY
            CASE transformation_decision
                WHEN 'DO NOT PROCEED' THEN 1
                WHEN 'REMEDIATE BEFORE PROCEEDING' THEN 2
                WHEN 'PROCEED WITH CONDITIONS' THEN 3
                WHEN 'PROCEED' THEN 4
                ELSE 5
            END,
            critical_residual_risks DESC,
            high_residual_risks DESC,
            overall_readiness_score ASC

        LIMIT 20;
    """
    return run_query(query)


def get_readiness_summary() -> pd.DataFrame:
    query = """
        SELECT
            readiness_band,
            COUNT(*) AS initiatives
        FROM analytics.readiness_summary
        GROUP BY readiness_band
        ORDER BY initiatives DESC;
    """
    return run_query(query)
