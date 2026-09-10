from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text
from app.utils.db import engine


QUERY = """
SELECT
    initiative_id,
    initiative_name,
    business_unit,
    criticality,

    critical_residual_risks,
    high_residual_risks,

    average_residual_risk,
    maximum_residual_risk,

    overall_readiness_score,
    minimum_readiness_score,

    average_control_effectiveness,

    overdue_actions,
    average_mitigation_completion,

    transformation_decision,
    decision_rationale

FROM analytics.transformation_decision

ORDER BY
    CASE transformation_decision
        WHEN 'DO NOT PROCEED' THEN 1
        WHEN 'REMEDIATE BEFORE PROCEEDING' THEN 2
        WHEN 'PROCEED WITH CONDITIONS' THEN 3
        WHEN 'PROCEED' THEN 4
        ELSE 5
    END,
    critical_residual_risks DESC,
    high_residual_risks DESC,
    overall_readiness_score ASC

LIMIT 20;
"""


def main():
    print("TransformRisk Priority Initiatives")
    print("=" * 80)

    with engine.connect() as connection:
        rows = connection.execute(text(QUERY))

        for row in rows:
            print(dict(row._mapping))

    print("=" * 80)


if __name__ == "__main__":
    main()
