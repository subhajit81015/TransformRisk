CREATE OR REPLACE VIEW analytics.risk_scoring AS
SELECT
    r.risk_id,
    r.initiative_id,
    i.initiative_name,
    i.transformation_type,
    i.business_unit,
    i.owner AS initiative_owner,
    i.criticality,
    i.strategic_priority,

    r.risk_name,
    r.risk_domain,
    r.description,

    r.likelihood,
    r.impact,

    -- Inherent risk before controls
    (r.likelihood * r.impact) AS inherent_risk_score,

    CASE
        WHEN (r.likelihood * r.impact) >= 17 THEN 'Critical'
        WHEN (r.likelihood * r.impact) >= 13 THEN 'High'
        WHEN (r.likelihood * r.impact) >= 9 THEN 'Medium'
        WHEN (r.likelihood * r.impact) >= 5 THEN 'Low'
        ELSE 'Very Low'
    END AS inherent_risk_band,

    r.control_effectiveness,

    -- Residual risk after considering control effectiveness
    ROUND(
        (
            r.likelihood
            * r.impact
            * (1 - COALESCE(r.control_effectiveness, 0) / 100.0)
        )::numeric,
        2
    ) AS residual_risk_score,

    CASE
        WHEN (
            r.likelihood
            * r.impact
            * (1 - COALESCE(r.control_effectiveness, 0) / 100.0)
        ) >= 17 THEN 'Critical'

        WHEN (
            r.likelihood
            * r.impact
            * (1 - COALESCE(r.control_effectiveness, 0) / 100.0)
        ) >= 13 THEN 'High'

        WHEN (
            r.likelihood
            * r.impact
            * (1 - COALESCE(r.control_effectiveness, 0) / 100.0)
        ) >= 9 THEN 'Medium'

        WHEN (
            r.likelihood
            * r.impact
            * (1 - COALESCE(r.control_effectiveness, 0) / 100.0)
        ) >= 5 THEN 'Low'

        ELSE 'Very Low'
    END AS residual_risk_band,

    CASE
        WHEN (
            r.likelihood
            * r.impact
            * (1 - COALESCE(r.control_effectiveness, 0) / 100.0)
        ) >= 17 THEN TRUE
        ELSE FALSE
    END AS is_critical_residual_risk,

    CASE
        WHEN (
            r.likelihood
            * r.impact
            * (1 - COALESCE(r.control_effectiveness, 0) / 100.0)
        ) >= 13 THEN TRUE
        ELSE FALSE
    END AS is_high_residual_risk,

    r.status AS risk_status

FROM raw.transformation_risks r
INNER JOIN raw.transformation_initiatives i
    ON r.initiative_id = i.initiative_id;