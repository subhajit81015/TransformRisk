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


def get_risk_matrix(initiative_id: str) -> pd.DataFrame:
    query = """
        SELECT
            risk_id,
            risk_name,
            risk_domain,
            likelihood,
            impact,
            inherent_risk_score,
            control_effectiveness,
            residual_risk_score,
            residual_risk_band,
            risk_status
        FROM analytics.risk_scoring
        WHERE initiative_id = :initiative_id
        ORDER BY
            likelihood DESC,
            impact DESC,
            residual_risk_score DESC;
    """

    return run_query(
        query,
        {"initiative_id": initiative_id},
    )


def get_risk_domain_breakdown(initiative_id: str) -> pd.DataFrame:
    query = """
        SELECT
            risk_domain,
            COUNT(*) AS total_risks,
            ROUND(AVG(inherent_risk_score)::numeric, 2)
                AS average_inherent_risk,
            ROUND(AVG(residual_risk_score)::numeric, 2)
                AS average_residual_risk,
            ROUND(AVG(control_effectiveness)::numeric, 2)
                AS average_control_effectiveness,
            COUNT(*) FILTER (
                WHERE residual_risk_band = 'Critical'
            ) AS critical_residual_risks,
            COUNT(*) FILTER (
                WHERE residual_risk_band = 'High'
            ) AS high_residual_risks
        FROM analytics.risk_scoring
        WHERE initiative_id = :initiative_id
        GROUP BY risk_domain
        ORDER BY average_residual_risk DESC;
    """

    return run_query(
        query,
        {"initiative_id": initiative_id},
    )


def get_priority_risks(
    initiative_id: str,
    limit: int = 5,
) -> pd.DataFrame:
    query = """
        SELECT
            risk_id,
            risk_name,
            risk_domain,
            likelihood,
            impact,
            inherent_risk_score,
            control_effectiveness,
            residual_risk_score,
            residual_risk_band,
            risk_status
        FROM analytics.risk_scoring
        WHERE initiative_id = :initiative_id
        ORDER BY
            CASE residual_risk_band
                WHEN 'Critical' THEN 1
                WHEN 'High' THEN 2
                WHEN 'Medium' THEN 3
                WHEN 'Low' THEN 4
                ELSE 5
            END,
            residual_risk_score DESC,
            inherent_risk_score DESC
        LIMIT :limit;
    """

    return run_query(
        query,
        {
            "initiative_id": initiative_id,
            "limit": limit,
        },
    )


def get_weak_controls_for_risks(
    initiative_id: str,
) -> pd.DataFrame:
    query = """
        SELECT
            control_id,
            risk_id,
            risk_name,
            risk_domain,
            residual_risk_score,
            residual_risk_band,
            control_name,
            control_type,
            control_owner,
            effectiveness_score,
            control_strength,
            control_status
        FROM analytics.control_summary
        WHERE initiative_id = :initiative_id
          AND COALESCE(effectiveness_score, 0) < 60
        ORDER BY
            CASE residual_risk_band
                WHEN 'Critical' THEN 1
                WHEN 'High' THEN 2
                WHEN 'Medium' THEN 3
                WHEN 'Low' THEN 4
                ELSE 5
            END,
            residual_risk_score DESC,
            effectiveness_score ASC;
    """

    return run_query(
        query,
        {"initiative_id": initiative_id},
    )