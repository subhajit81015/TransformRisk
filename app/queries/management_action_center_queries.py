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


def get_management_action_queue() -> pd.DataFrame:
    """
    Build a risk-level management action queue.

    The score is explainable rather than predictive. It combines:
    residual-risk severity, control weakness, mitigation weakness,
    execution urgency, and initiative criticality.

    Maximum score = 100.
    """

    query = """
        WITH controls AS (
            SELECT
                risk_id,
                COUNT(*) AS control_count,
                ROUND(AVG(effectiveness_score)::numeric, 1)
                    AS avg_control_effectiveness
            FROM analytics.control_summary
            GROUP BY risk_id
        ),

        mitigations AS (
            SELECT
                risk_id,
                COUNT(*) AS mitigation_count,
                ROUND(AVG(completion_percentage)::numeric, 1)
                    AS mitigation_completion,
                COUNT(*) FILTER (
                    WHERE is_overdue = TRUE
                ) AS overdue_mitigations
            FROM analytics.mitigation_summary
            GROUP BY risk_id
        ),

        base AS (
            SELECT
                r.risk_id,
                r.initiative_id,
                r.initiative_name,
                r.transformation_type,
                r.business_unit,
                r.initiative_owner,
                r.criticality,
                r.risk_name,
                r.risk_domain,
                r.description,
                r.likelihood,
                r.impact,
                r.inherent_risk_score,
                r.inherent_risk_band,
                r.control_effectiveness,
                r.residual_risk_score,
                r.residual_risk_band,
                r.is_critical_residual_risk,
                r.is_high_residual_risk,
                r.risk_status,

                COALESCE(
                    c.control_count,
                    0
                ) AS control_count,

                COALESCE(
                    c.avg_control_effectiveness,
                    0
                ) AS avg_control_effectiveness,

                COALESCE(
                    m.mitigation_count,
                    0
                ) AS mitigation_count,

                COALESCE(
                    m.mitigation_completion,
                    0
                ) AS mitigation_completion,

                COALESCE(
                    m.overdue_mitigations,
                    0
                ) AS overdue_mitigations

            FROM analytics.risk_scoring r

            LEFT JOIN controls c
                ON r.risk_id = c.risk_id

            LEFT JOIN mitigations m
                ON r.risk_id = m.risk_id
        ),

        scored AS (
            SELECT
                b.*,

                CASE
                    WHEN b.is_critical_residual_risk THEN 30
                    WHEN b.residual_risk_score >= 13 THEN 26
                    WHEN b.residual_risk_score >= 9 THEN 20
                    WHEN b.residual_risk_score >= 5 THEN 12
                    ELSE 5
                END AS severity_points,

                CASE
                    WHEN b.control_count = 0 THEN 20
                    WHEN b.avg_control_effectiveness < 40 THEN 16
                    WHEN b.avg_control_effectiveness < 50 THEN 12
                    WHEN b.avg_control_effectiveness < 60 THEN 8
                    WHEN b.avg_control_effectiveness < 75 THEN 4
                    ELSE 1
                END AS control_gap_points,

                CASE
                    WHEN b.mitigation_count = 0 THEN 20
                    WHEN b.overdue_mitigations > 0 THEN 15
                    WHEN b.mitigation_completion < 50 THEN 10
                    WHEN b.mitigation_completion < 80 THEN 5
                    ELSE 1
                END AS mitigation_gap_points,

                CASE
                    WHEN b.residual_risk_score >= 17 THEN 20
                    WHEN b.residual_risk_score >= 13 THEN 16
                    WHEN b.residual_risk_score >= 9 THEN 12
                    WHEN b.residual_risk_score >= 5 THEN 7
                    ELSE 3
                END AS urgency_points,

                CASE
                    WHEN LOWER(
                        COALESCE(b.criticality, '')
                    ) = 'critical' THEN 10

                    WHEN LOWER(
                        COALESCE(b.criticality, '')
                    ) = 'high' THEN 8

                    WHEN LOWER(
                        COALESCE(b.criticality, '')
                    ) = 'medium' THEN 5

                    WHEN LOWER(
                        COALESCE(b.criticality, '')
                    ) = 'low' THEN 2

                    ELSE 0
                END AS criticality_points,

                CASE
                    WHEN b.is_critical_residual_risk
                         OR b.residual_risk_score >= 13
                    THEN 'P1 - Immediate Management Attention'

                    WHEN b.is_high_residual_risk
                         OR b.residual_risk_score >= 9
                         OR b.control_count = 0
                         OR b.mitigation_count = 0
                         OR b.avg_control_effectiveness < 50
                         OR b.overdue_mitigations > 0
                    THEN 'P2 - Management Action Required'

                    WHEN b.residual_risk_score >= 5
                         OR b.avg_control_effectiveness < 60
                         OR b.mitigation_completion < 50
                    THEN 'P3 - Controlled Monitoring'

                    ELSE 'P4 - Routine Monitoring'
                END AS action_priority

            FROM base b
        )

        SELECT
            s.risk_id,
            s.initiative_id,
            s.initiative_name,
            s.transformation_type,
            s.business_unit,
            s.initiative_owner,
            s.criticality,
            s.risk_name,
            s.risk_domain,
            s.description,
            s.likelihood,
            s.impact,
            s.inherent_risk_score,
            s.inherent_risk_band,
            s.control_effectiveness,
            s.residual_risk_score,
            s.residual_risk_band,
            s.is_critical_residual_risk,
            s.is_high_residual_risk,
            s.risk_status,
            s.control_count,
            s.avg_control_effectiveness,
            s.mitigation_count,
            s.mitigation_completion,
            s.overdue_mitigations,
            s.action_priority,

            CASE
                WHEN s.is_critical_residual_risk THEN
                    'Escalate immediately. Critical residual risk requires executive risk acceptance or remediation before transformation proceeds.'

                WHEN s.residual_risk_score >= 13
                     AND s.control_count = 0 THEN
                    'Establish and assign a compensating control immediately for the high-exposure risk.'

                WHEN s.residual_risk_score >= 13 THEN
                    'Escalate the high residual exposure and require a documented remediation plan.'

                WHEN s.mitigation_count = 0
                     AND s.control_count = 0 THEN
                    'Establish a control and define an owned mitigation action before relying on continued execution.'

                WHEN s.mitigation_count = 0 THEN
                    'Define and assign a mitigation action. Controls exist, but treatment activity is not mapped to this risk.'

                WHEN s.overdue_mitigations > 0 THEN
                    'Escalate overdue mitigation actions to the initiative owner and establish a recovery date.'

                WHEN s.control_count = 0 THEN
                    'Establish and assign a control owner before further transformation execution.'

                WHEN s.avg_control_effectiveness < 40 THEN
                    'Strengthen ineffective controls and perform a control effectiveness reassessment.'

                WHEN s.avg_control_effectiveness < 50 THEN
                    'Improve control effectiveness and track remediation through the initiative governance process.'

                WHEN s.mitigation_completion < 50 THEN
                    'Accelerate mitigation execution and review completion against the agreed target date.'

                WHEN s.residual_risk_score >= 9 THEN
                    'Require management review of residual exposure and confirm the risk treatment plan.'

                WHEN s.residual_risk_score >= 5 THEN
                    'Continue controlled monitoring with periodic review of risk, controls and mitigation execution.'

                ELSE
                    'Maintain routine monitoring and reassess if exposure or control effectiveness changes.'
            END AS recommended_management_action,

            LEAST(
                100,
                s.severity_points
                + s.control_gap_points
                + s.mitigation_gap_points
                + s.urgency_points
                + s.criticality_points
            ) AS management_priority_score,

            CONCAT_WS(
                ' | ',

                CASE
                    WHEN s.is_critical_residual_risk THEN
                        'Critical residual risk'

                    WHEN s.residual_risk_score >= 13 THEN
                        'High residual exposure'

                    WHEN s.residual_risk_score >= 9 THEN
                        'Elevated residual exposure'

                    ELSE NULL
                END,

                CASE
                    WHEN s.control_count = 0 THEN
                        'No mapped controls'

                    WHEN s.avg_control_effectiveness < 50 THEN
                        'Weak control effectiveness'

                    WHEN s.avg_control_effectiveness < 60 THEN
                        'Moderate control weakness'

                    ELSE NULL
                END,

                CASE
                    WHEN s.mitigation_count = 0 THEN
                        'No mapped mitigation'

                    WHEN s.overdue_mitigations > 0 THEN
                        'Overdue mitigation'

                    WHEN s.mitigation_completion < 50 THEN
                        'Low mitigation completion'

                    ELSE NULL
                END
            ) AS priority_drivers

        FROM scored s

        ORDER BY
            management_priority_score DESC,
            s.residual_risk_score DESC,
            s.risk_id;
    """

    return run_query(query)


def get_management_action_summary() -> pd.DataFrame:
    """
    Return portfolio-level counts for the management action queue.
    """

    query = """
        WITH queue AS (
            SELECT
                r.risk_id,
                r.residual_risk_score,
                r.is_critical_residual_risk,
                r.is_high_residual_risk,

                COALESCE(
                    c.control_count,
                    0
                ) AS control_count,

                COALESCE(
                    c.avg_control_effectiveness,
                    0
                ) AS avg_control_effectiveness,

                COALESCE(
                    m.mitigation_count,
                    0
                ) AS mitigation_count,

                COALESCE(
                    m.mitigation_completion,
                    0
                ) AS mitigation_completion,

                COALESCE(
                    m.overdue_mitigations,
                    0
                ) AS overdue_mitigations

            FROM analytics.risk_scoring r

            LEFT JOIN (
                SELECT
                    risk_id,
                    COUNT(*) AS control_count,
                    AVG(effectiveness_score)
                        AS avg_control_effectiveness
                FROM analytics.control_summary
                GROUP BY risk_id
            ) c
                ON r.risk_id = c.risk_id

            LEFT JOIN (
                SELECT
                    risk_id,
                    COUNT(*) AS mitigation_count,
                    AVG(completion_percentage)
                        AS mitigation_completion,
                    COUNT(*) FILTER (
                        WHERE is_overdue = TRUE
                    ) AS overdue_mitigations
                FROM analytics.mitigation_summary
                GROUP BY risk_id
            ) m
                ON r.risk_id = m.risk_id
        )

        SELECT
            COUNT(*) AS total_risks,

            COUNT(*) FILTER (
                WHERE
                    is_critical_residual_risk
                    OR residual_risk_score >= 13
            ) AS p1_risks,

            COUNT(*) FILTER (
                WHERE
                    NOT (
                        is_critical_residual_risk
                        OR residual_risk_score >= 13
                    )
                    AND (
                        is_high_residual_risk
                        OR residual_risk_score >= 9
                        OR control_count = 0
                        OR mitigation_count = 0
                        OR avg_control_effectiveness < 50
                        OR overdue_mitigations > 0
                    )
            ) AS p2_risks,

            COUNT(*) FILTER (
                WHERE
                    NOT (
                        is_critical_residual_risk
                        OR residual_risk_score >= 13
                        OR is_high_residual_risk
                        OR residual_risk_score >= 9
                        OR control_count = 0
                        OR mitigation_count = 0
                        OR avg_control_effectiveness < 50
                        OR overdue_mitigations > 0
                    )
                    AND (
                        residual_risk_score >= 5
                        OR avg_control_effectiveness < 60
                        OR mitigation_completion < 50
                    )
            ) AS p3_risks,

            COUNT(*) FILTER (
                WHERE
                    residual_risk_score < 5
                    AND avg_control_effectiveness >= 60
                    AND mitigation_count > 0
                    AND mitigation_completion >= 50
                    AND overdue_mitigations = 0
                    AND control_count > 0
            ) AS p4_risks,

            COUNT(*) FILTER (
                WHERE overdue_mitigations > 0
            ) AS overdue_mitigations

        FROM queue;
    """

    return run_query(query)