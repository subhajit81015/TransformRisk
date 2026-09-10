SELECT
    control_id,
    risk_id,
    initiative_id,
    initiative_name,
    risk_domain,
    residual_risk_score,
    residual_risk_band,
    control_name,
    effectiveness_score,
    control_strength
FROM analytics.control_summary
WHERE residual_risk_band IN ('Critical', 'High')
ORDER BY residual_risk_score DESC,
         effectiveness_score ASC
LIMIT 15;