CREATE OR REPLACE VIEW analytics.control_summary AS
SELECT
    c.control_id,
    c.risk_id,

    rs.initiative_id,
    rs.initiative_name,

    rs.risk_name,
    rs.risk_domain,
    rs.inherent_risk_score,
    rs.residual_risk_score,
    rs.residual_risk_band,

    c.control_name,
    c.control_type,
    c.control_owner,
    c.control_frequency,
    c.effectiveness_score,
    c.control_status,
    c.description,

    CASE
        WHEN COALESCE(c.effectiveness_score, 0) >= 80
            THEN 'Strong'

        WHEN COALESCE(c.effectiveness_score, 0) >= 60
            THEN 'Moderate'

        WHEN COALESCE(c.effectiveness_score, 0) >= 40
            THEN 'Weak'

        ELSE 'Critical Weakness'
    END AS control_strength

FROM raw.risk_controls c

INNER JOIN analytics.risk_scoring rs
    ON c.risk_id = rs.risk_id;