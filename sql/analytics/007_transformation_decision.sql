CREATE OR REPLACE VIEW analytics.transformation_decision AS

WITH risk_metrics AS (
    SELECT
        initiative_id,

        COUNT(*) AS total_risks,

        COUNT(*) FILTER (
            WHERE residual_risk_band = 'Critical'
        ) AS critical_residual_risks,

        COUNT(*) FILTER (
            WHERE residual_risk_band = 'High'
        ) AS high_residual_risks,

        ROUND(
            AVG(residual_risk_score)::numeric,
            2
        ) AS average_residual_risk,

        ROUND(
            MAX(residual_risk_score)::numeric,
            2
        ) AS maximum_residual_risk,

        ROUND(
            AVG(control_effectiveness)::numeric,
            2
        ) AS average_control_effectiveness

    FROM analytics.risk_scoring

    GROUP BY initiative_id
),

mitigation_metrics AS (
    SELECT
        r.initiative_id,

        COUNT(a.action_id) AS total_mitigation_actions,

        COUNT(a.action_id) FILTER (
            WHERE a.due_date < CURRENT_DATE
              AND COALESCE(a.completion_percentage, 0) < 100
        ) AS overdue_actions,

        COUNT(a.action_id) FILTER (
            WHERE COALESCE(a.completion_percentage, 0) = 100
        ) AS completed_actions,

        ROUND(
            AVG(COALESCE(a.completion_percentage, 0))::numeric,
            2
        ) AS average_mitigation_completion

    FROM raw.mitigation_actions a

    INNER JOIN raw.transformation_risks r
        ON a.risk_id = r.risk_id

    GROUP BY r.initiative_id
)

SELECT
    i.initiative_id,
    i.initiative_name,
    i.transformation_type,
    i.business_unit,
    i.owner,
    i.strategic_priority,
    i.criticality,
    i.budget,
    i.target_completion_date,
    i.status,

    COALESCE(rm.total_risks, 0) AS total_risks,
    COALESCE(rm.critical_residual_risks, 0)
        AS critical_residual_risks,
    COALESCE(rm.high_residual_risks, 0)
        AS high_residual_risks,
    COALESCE(rm.average_residual_risk, 0)
        AS average_residual_risk,
    COALESCE(rm.maximum_residual_risk, 0)
        AS maximum_residual_risk,
    COALESCE(rm.average_control_effectiveness, 0)
        AS average_control_effectiveness,

    COALESCE(rd.overall_readiness_score, 0)
        AS overall_readiness_score,
    COALESCE(rd.technology_readiness, 0)
        AS technology_readiness,
    COALESCE(rd.data_readiness, 0)
        AS data_readiness,
    COALESCE(rd.process_readiness, 0)
        AS process_readiness,
    COALESCE(rd.people_readiness, 0)
        AS people_readiness,
    COALESCE(rd.governance_readiness, 0)
        AS governance_readiness,
    COALESCE(rd.minimum_dimension_score, 0)
        AS minimum_readiness_score,

    rd.readiness_band,
    rd.readiness_gap_status,

    COALESCE(mm.total_mitigation_actions, 0)
        AS total_mitigation_actions,
    COALESCE(mm.overdue_actions, 0)
        AS overdue_actions,
    COALESCE(mm.completed_actions, 0)
        AS completed_mitigation_actions,
    COALESCE(mm.average_mitigation_completion, 0)
        AS average_mitigation_completion,

    CASE
        WHEN COALESCE(rm.critical_residual_risks, 0) > 0
            THEN 'DO NOT PROCEED'

        WHEN COALESCE(rd.overall_readiness_score, 0) < 50
            THEN 'REMEDIATE BEFORE PROCEEDING'

        WHEN COALESCE(rm.high_residual_risks, 0) >= 3
            THEN 'PROCEED WITH CONDITIONS'

        WHEN COALESCE(rd.overall_readiness_score, 0) < 65
            THEN 'PROCEED WITH CONDITIONS'

        WHEN COALESCE(mm.overdue_actions, 0) >= 3
            THEN 'PROCEED WITH CONDITIONS'

        WHEN COALESCE(rm.average_control_effectiveness, 0) < 50
            THEN 'PROCEED WITH CONDITIONS'

        ELSE 'PROCEED'
    END AS transformation_decision,

    CASE
        WHEN COALESCE(rm.critical_residual_risks, 0) > 0
            THEN 'Critical residual risk remains open.'

        WHEN COALESCE(rd.overall_readiness_score, 0) < 50
            THEN 'Overall transformation readiness is below the minimum threshold.'

        WHEN COALESCE(rm.high_residual_risks, 0) >= 3
            THEN 'Multiple high residual risks require management conditions.'

        WHEN COALESCE(rd.overall_readiness_score, 0) < 65
            THEN 'Readiness is below the preferred execution threshold.'

        WHEN COALESCE(mm.overdue_actions, 0) >= 3
            THEN 'Multiple mitigation actions are overdue.'

        WHEN COALESCE(rm.average_control_effectiveness, 0) < 50
            THEN 'Average control effectiveness is weak.'

        ELSE 'Risk, readiness and control indicators are within acceptable thresholds.'
    END AS decision_rationale

FROM raw.transformation_initiatives i

LEFT JOIN risk_metrics rm
    ON i.initiative_id = rm.initiative_id

LEFT JOIN analytics.readiness_summary rd
    ON i.initiative_id = rd.initiative_id

LEFT JOIN mitigation_metrics mm
    ON i.initiative_id = mm.initiative_id;