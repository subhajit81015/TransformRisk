CREATE OR REPLACE VIEW analytics.risk_domain_summary AS
SELECT
    risk_domain,

    COUNT(*) AS total_risks,

    COUNT(*) FILTER (
        WHERE inherent_risk_band = 'Critical'
    ) AS critical_inherent_risks,

    COUNT(*) FILTER (
        WHERE inherent_risk_band = 'High'
    ) AS high_inherent_risks,

    COUNT(*) FILTER (
        WHERE residual_risk_band = 'Critical'
    ) AS critical_residual_risks,

    COUNT(*) FILTER (
        WHERE residual_risk_band = 'High'
    ) AS high_residual_risks,

    COUNT(*) FILTER (
        WHERE residual_risk_band = 'Medium'
    ) AS medium_residual_risks,

    ROUND(
        AVG(inherent_risk_score)::numeric,
        2
    ) AS average_inherent_risk,

    ROUND(
        AVG(residual_risk_score)::numeric,
        2
    ) AS average_residual_risk,

    ROUND(
        AVG(control_effectiveness)::numeric,
        2
    ) AS average_control_effectiveness,

    ROUND(
        (
            COUNT(*) FILTER (
                WHERE residual_risk_band IN ('Critical', 'High')
            ) * 100.0 / NULLIF(COUNT(*), 0)
        )::numeric,
        2
    ) AS high_critical_risk_percentage

FROM analytics.risk_scoring

GROUP BY risk_domain
ORDER BY average_residual_risk DESC;