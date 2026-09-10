CREATE OR REPLACE VIEW analytics.readiness_summary AS
SELECT
    i.initiative_id,
    i.initiative_name,
    i.transformation_type,
    i.business_unit,
    i.owner,
    i.criticality,
    i.strategic_priority,
    i.status,

    COUNT(a.readiness_id) AS readiness_assessments,

    ROUND(
        AVG(a.readiness_score)::numeric,
        2
    ) AS overall_readiness_score,

    ROUND(
        AVG(a.readiness_score) FILTER (
            WHERE a.readiness_dimension = 'Technology'
        )::numeric,
        2
    ) AS technology_readiness,

    ROUND(
        AVG(a.readiness_score) FILTER (
            WHERE a.readiness_dimension = 'Data'
        )::numeric,
        2
    ) AS data_readiness,

    ROUND(
        AVG(a.readiness_score) FILTER (
            WHERE a.readiness_dimension = 'Process'
        )::numeric,
        2
    ) AS process_readiness,

    ROUND(
        AVG(a.readiness_score) FILTER (
            WHERE a.readiness_dimension = 'People'
        )::numeric,
        2
    ) AS people_readiness,

    ROUND(
        AVG(a.readiness_score) FILTER (
            WHERE a.readiness_dimension = 'Governance'
        )::numeric,
        2
    ) AS governance_readiness,

    MIN(a.readiness_score) AS minimum_dimension_score,

    CASE
        WHEN AVG(a.readiness_score) >= 80
            THEN 'Ready'

        WHEN AVG(a.readiness_score) >= 65
            THEN 'Ready with Conditions'

        WHEN AVG(a.readiness_score) >= 50
            THEN 'Remediation Required'

        ELSE 'Not Ready'
    END AS readiness_band,

    CASE
        WHEN MIN(a.readiness_score) < 50
            THEN 'Critical Readiness Gap'

        WHEN MIN(a.readiness_score) < 65
            THEN 'Material Readiness Gap'

        WHEN MIN(a.readiness_score) < 80
            THEN 'Moderate Readiness Gap'

        ELSE 'No Major Readiness Gap'
    END AS readiness_gap_status

FROM raw.transformation_initiatives i
LEFT JOIN raw.readiness_assessments a
    ON i.initiative_id = a.initiative_id

GROUP BY
    i.initiative_id,
    i.initiative_name,
    i.transformation_type,
    i.business_unit,
    i.owner,
    i.criticality,
    i.strategic_priority,
    i.status;