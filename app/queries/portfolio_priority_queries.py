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


def get_portfolio_priority_queue() -> pd.DataFrame:

    query = """
        WITH scored AS (
            SELECT
                initiative_id,
                initiative_name,
                transformation_type,
                business_unit,
                owner,
                strategic_priority,
                criticality,
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

                transformation_decision,

                CASE
                    WHEN transformation_decision = 'DO NOT PROCEED'
                        THEN 30
                    WHEN transformation_decision =
                        'REMEDIATE BEFORE PROCEEDING'
                        THEN 25
                    WHEN transformation_decision =
                        'PROCEED WITH CONDITIONS'
                        THEN 15
                    ELSE 0
                END AS decision_score,

                CASE
                    WHEN critical_residual_risks > 0
                        THEN 25
                    WHEN high_residual_risks > 0
                        THEN 18
                    WHEN maximum_residual_risk >= 9
                        THEN 12
                    WHEN maximum_residual_risk >= 5
                        THEN 6
                    ELSE 0
                END AS risk_score,

                CASE
                    WHEN minimum_readiness_score < 40
                        THEN 20
                    WHEN minimum_readiness_score < 50
                        THEN 15
                    WHEN minimum_readiness_score < 65
                        THEN 8
                    ELSE 0
                END AS readiness_score,

                CASE
                    WHEN overdue_actions >= 3
                        THEN 15
                    WHEN overdue_actions > 0
                        THEN 10
                    WHEN average_mitigation_completion < 50
                        THEN 6
                    ELSE 0
                END AS execution_score,

                CASE
                    WHEN average_control_effectiveness < 40
                        THEN 10
                    WHEN average_control_effectiveness < 50
                        THEN 8
                    WHEN average_control_effectiveness < 60
                        THEN 4
                    ELSE 0
                END AS control_score

            FROM analytics.transformation_decision
        )

        SELECT
            *,
            LEAST(
                decision_score
                + risk_score
                + readiness_score
                + execution_score
                + control_score,
                100
            ) AS portfolio_priority_score,

            CASE
                WHEN LEAST(
                    decision_score
                    + risk_score
                    + readiness_score
                    + execution_score
                    + control_score,
                    100
                ) >= 75
                    THEN 'P1 - Immediate Management Attention'

                WHEN LEAST(
                    decision_score
                    + risk_score
                    + readiness_score
                    + execution_score
                    + control_score,
                    100
                ) >= 50
                    THEN 'P2 - Management Action Required'

                WHEN LEAST(
                    decision_score
                    + risk_score
                    + readiness_score
                    + execution_score
                    + control_score,
                    100
                ) >= 25
                    THEN 'P3 - Controlled Monitoring'

                ELSE 'P4 - Routine Monitoring'
            END AS portfolio_priority

        FROM scored

        ORDER BY
            portfolio_priority_score DESC,
            maximum_residual_risk DESC,
            minimum_readiness_score ASC;
    """

    return run_query(query)


def get_portfolio_priority_summary() -> pd.DataFrame:

    query = """
        WITH portfolio AS (
            SELECT
                transformation_decision,
                critical_residual_risks,
                high_residual_risks,
                maximum_residual_risk,
                minimum_readiness_score,
                overdue_actions,
                average_mitigation_completion,
                average_control_effectiveness

            FROM analytics.transformation_decision
        ),

        scored AS (
            SELECT
                *,
                LEAST(
                    CASE
                        WHEN transformation_decision =
                            'DO NOT PROCEED'
                            THEN 30
                        WHEN transformation_decision =
                            'REMEDIATE BEFORE PROCEEDING'
                            THEN 25
                        WHEN transformation_decision =
                            'PROCEED WITH CONDITIONS'
                            THEN 15
                        ELSE 0
                    END
                    +
                    CASE
                        WHEN critical_residual_risks > 0
                            THEN 25
                        WHEN high_residual_risks > 0
                            THEN 18
                        WHEN maximum_residual_risk >= 9
                            THEN 12
                        WHEN maximum_residual_risk >= 5
                            THEN 6
                        ELSE 0
                    END
                    +
                    CASE
                        WHEN minimum_readiness_score < 40
                            THEN 20
                        WHEN minimum_readiness_score < 50
                            THEN 15
                        WHEN minimum_readiness_score < 65
                            THEN 8
                        ELSE 0
                    END
                    +
                    CASE
                        WHEN overdue_actions >= 3
                            THEN 15
                        WHEN overdue_actions > 0
                            THEN 10
                        WHEN average_mitigation_completion < 50
                            THEN 6
                        ELSE 0
                    END
                    +
                    CASE
                        WHEN average_control_effectiveness < 40
                            THEN 10
                        WHEN average_control_effectiveness < 50
                            THEN 8
                        WHEN average_control_effectiveness < 60
                            THEN 4
                        ELSE 0
                    END,
                    100
                ) AS priority_score

            FROM portfolio
        )

        SELECT
            COUNT(*) AS total_initiatives,

            COUNT(*) FILTER (
                WHERE priority_score >= 75
            ) AS p1_initiatives,

            COUNT(*) FILTER (
                WHERE priority_score >= 50
                  AND priority_score < 75
            ) AS p2_initiatives,

            COUNT(*) FILTER (
                WHERE priority_score >= 25
                  AND priority_score < 50
            ) AS p3_initiatives,

            COUNT(*) FILTER (
                WHERE priority_score < 25
            ) AS p4_initiatives,

            ROUND(
                AVG(priority_score)::numeric,
                1
            ) AS average_priority_score,

            ROUND(
                MAX(priority_score)::numeric,
                1
            ) AS maximum_priority_score

        FROM scored;
    """

    return run_query(query)