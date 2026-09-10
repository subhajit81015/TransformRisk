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


def get_management_action_priorities(
    initiative_id: str,
) -> pd.DataFrame:

    query = """
        WITH risk_base AS (
            SELECT
                risk_id,
                risk_name,
                risk_domain,
                likelihood,
                impact,
                inherent_risk_score,
                residual_risk_score,
                residual_risk_band,
                risk_status
            FROM analytics.risk_scoring
            WHERE initiative_id = :initiative_id
        ),

        control_coverage AS (
            SELECT
                risk_id,
                COUNT(control_id) AS control_count,
                ROUND(
                    AVG(effectiveness_score)::numeric,
                    2
                ) AS average_control_effectiveness
            FROM analytics.control_summary
            WHERE initiative_id = :initiative_id
            GROUP BY risk_id
        ),

        mitigation_coverage AS (
            SELECT
                risk_id,
                COUNT(action_id) AS mitigation_count,
                ROUND(
                    AVG(completion_percentage)::numeric,
                    2
                ) AS average_mitigation_completion,
                COUNT(*) FILTER (
                    WHERE is_overdue = TRUE
                ) AS overdue_mitigation_count
            FROM analytics.mitigation_summary
            WHERE initiative_id = :initiative_id
            GROUP BY risk_id
        ),

        enriched AS (
            SELECT
                r.*,

                COALESCE(
                    c.control_count,
                    0
                ) AS control_count,

                COALESCE(
                    c.average_control_effectiveness,
                    0
                ) AS average_control_effectiveness,

                COALESCE(
                    m.mitigation_count,
                    0
                ) AS mitigation_count,

                COALESCE(
                    m.average_mitigation_completion,
                    0
                ) AS average_mitigation_completion,

                COALESCE(
                    m.overdue_mitigation_count,
                    0
                ) AS overdue_mitigation_count

            FROM risk_base r

            LEFT JOIN control_coverage c
                ON r.risk_id = c.risk_id

            LEFT JOIN mitigation_coverage m
                ON r.risk_id = m.risk_id
        ),

        scored AS (
            SELECT
                *,

                /*
                 * Exposure Component: 0-40
                 *
                 * Residual risk is capped at 10 for
                 * normalization because the prototype
                 * residual-risk range can exceed 5.
                 */
                LEAST(
                    residual_risk_score / 10.0,
                    1.0
                ) * 40.0
                AS exposure_score,

                /*
                 * Control Coverage Component: 0-20
                 *
                 * No mapped control = maximum concern.
                 * At least one control = lower concern.
                 */
                CASE
                    WHEN control_count = 0
                        THEN 20.0

                    WHEN average_control_effectiveness < 50
                        THEN 15.0

                    WHEN average_control_effectiveness < 60
                        THEN 10.0

                    ELSE 0.0
                END
                AS control_gap_score,

                /*
                 * Mitigation Coverage Component: 0-20
                 */
                CASE
                    WHEN mitigation_count = 0
                        THEN 20.0

                    WHEN average_mitigation_completion < 50
                        THEN 12.0

                    WHEN overdue_mitigation_count > 0
                        THEN 10.0

                    ELSE 0.0
                END
                AS mitigation_gap_score,

                /*
                 * Execution Component: 0-10
                 */
                CASE
                    WHEN overdue_mitigation_count > 0
                        THEN 10.0

                    WHEN average_mitigation_completion < 50
                        THEN 7.0

                    ELSE 0.0
                END
                AS execution_score,

                /*
                 * Risk-band escalation component: 0-10
                 */
                CASE
                    WHEN residual_risk_band = 'Critical'
                        THEN 10.0

                    WHEN residual_risk_band = 'High'
                        THEN 8.0

                    WHEN residual_risk_band = 'Medium'
                        THEN 5.0

                    WHEN residual_risk_band = 'Low'
                        THEN 2.0

                    ELSE 0.0
                END
                AS severity_score

            FROM enriched
        ),

        final_score AS (
            SELECT
                *,

                ROUND(
                    LEAST(
                        exposure_score
                        + control_gap_score
                        + mitigation_gap_score
                        + execution_score
                        + severity_score,
                        100.0
                    )::numeric,
                    1
                ) AS management_priority_score

            FROM scored
        )

        SELECT
            risk_id,
            risk_name,
            risk_domain,
            likelihood,
            impact,
            inherent_risk_score,
            residual_risk_score,
            residual_risk_band,
            risk_status,

            control_count,
            average_control_effectiveness,

            mitigation_count,
            average_mitigation_completion,
            overdue_mitigation_count,

            exposure_score,
            control_gap_score,
            mitigation_gap_score,
            execution_score,
            severity_score,

            management_priority_score,

            CASE
                WHEN management_priority_score >= 75
                    THEN 'P1 - Immediate Management Attention'

                WHEN management_priority_score >= 50
                    THEN 'P2 - Management Action Required'

                WHEN management_priority_score >= 25
                    THEN 'P3 - Controlled Monitoring'

                ELSE 'P4 - Routine Monitoring'
            END AS management_priority,

            CASE
                WHEN control_count = 0
                     AND mitigation_count = 0
                    THEN
                        'Establish both control coverage and a mitigation action before transformation execution.'

                WHEN residual_risk_score >= 6
                     AND mitigation_count = 0
                    THEN
                        'Define and assign a mitigation action for this high-exposure risk.'

                WHEN control_count = 0
                    THEN
                        'Map an appropriate preventive or detective control to this risk.'

                WHEN mitigation_count = 0
                    THEN
                        'Create and assign a mitigation action to reduce remaining exposure.'

                WHEN average_control_effectiveness < 50
                    THEN
                        'Strengthen control design or operating effectiveness.'

                WHEN overdue_mitigation_count > 0
                    THEN
                        'Escalate overdue mitigation actions and confirm accountable ownership.'

                WHEN average_mitigation_completion < 50
                    THEN
                        'Accelerate mitigation execution and confirm accountable ownership.'

                ELSE
                    'Continue monitoring risk, control and mitigation performance.'
            END AS recommended_management_action

        FROM final_score

        ORDER BY
            management_priority_score DESC,
            residual_risk_score DESC;
    """

    return run_query(
        query,
        {"initiative_id": initiative_id},
    )