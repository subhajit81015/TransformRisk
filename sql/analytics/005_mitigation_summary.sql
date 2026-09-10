CREATE OR REPLACE VIEW analytics.mitigation_summary AS
SELECT
    a.action_id,
    a.risk_id,

    r.initiative_id,
    i.initiative_name,
    i.business_unit,

    r.risk_name,
    r.risk_domain,
    r.inherent_risk_score,
    r.residual_risk_score,
    r.residual_risk_band,

    a.action_name,
    a.action_owner,
    a.priority,
    a.status,
    a.due_date,
    a.completion_percentage,
    a.expected_risk_reduction,

    CASE
        WHEN a.due_date < CURRENT_DATE
             AND COALESCE(a.completion_percentage, 0) < 100
            THEN TRUE
        ELSE FALSE
    END AS is_overdue,

    CASE
        WHEN COALESCE(a.completion_percentage, 0) = 100
            THEN 'Completed'

        WHEN a.due_date < CURRENT_DATE
             AND COALESCE(a.completion_percentage, 0) < 100
            THEN 'Overdue'

        WHEN COALESCE(a.completion_percentage, 0) = 0
            THEN 'Not Started'

        WHEN COALESCE(a.completion_percentage, 0) < 100
            THEN 'In Progress'

        ELSE 'Completed'
    END AS execution_status

FROM raw.mitigation_actions a

INNER JOIN analytics.risk_scoring r
    ON a.risk_id = r.risk_id

INNER JOIN raw.transformation_initiatives i
    ON r.initiative_id = i.initiative_id;