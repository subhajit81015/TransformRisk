CREATE OR REPLACE VIEW analytics.initiative_risk_summary AS
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

    COUNT(r.risk_id) AS total_risks,

    COUNT(*) FILTER (
        WHERE r.inherent_risk_band = 'Critical'
    ) AS critical_inherent_risks,

    COUNT(*) FILTER (
        WHERE r.inherent_risk_band = 'High'
    ) AS high_inherent_risks,

    COUNT(*) FILTER (
        WHERE r.residual_risk_band = 'Critical'
    ) AS critical_residual_risks,

    COUNT(*) FILTER (
        WHERE r.residual_risk_band = 'High'
    ) AS high_residual_risks,

    COUNT(*) FILTER (
        WHERE r.residual_risk_band = 'Medium'
    ) AS medium_residual_risks,

    ROUND(
        AVG(r.inherent_risk_score)::numeric,
        2
    ) AS average_inherent_risk,

    ROUND(
        AVG(r.residual_risk_score)::numeric,
        2
    ) AS average_residual_risk,

    ROUND(
        MAX(r.residual_risk_score)::numeric,
        2
    ) AS maximum_residual_risk,

    ROUND(
        AVG(r.control_effectiveness)::numeric,
        2
    ) AS average_control_effectiveness,

    COUNT(*) FILTER (
        WHERE r.is_critical_residual_risk = TRUE
    ) AS critical_risk_exposure,

    COUNT(*) FILTER (
        WHERE r.is_high_residual_risk = TRUE
    ) AS high_risk_exposure,

    CASE
        WHEN COUNT(*) FILTER (
            WHERE r.is_critical_residual_risk = TRUE
        ) > 0
            THEN 'DO NOT PROCEED'

        WHEN COUNT(*) FILTER (
            WHERE r.is_high_residual_risk = TRUE
        ) >= 3
            THEN 'PROCEED WITH CONDITIONS'

        WHEN AVG(r.residual_risk_score) >= 9
            THEN 'PROCEED WITH CONDITIONS'

        ELSE 'PROCEED'
    END AS preliminary_decision

FROM raw.transformation_initiatives i
LEFT JOIN analytics.risk_scoring r
    ON i.initiative_id = r.initiative_id

GROUP BY
    i.initiative_id,
    i.initiative_name,
    i.transformation_type,
    i.business_unit,
    i.owner,
    i.strategic_priority,
    i.criticality,
    i.budget,
    i.target_completion_date,
    i.status;