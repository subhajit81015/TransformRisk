from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text
from app.utils.db import engine


QUERY = """
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
ORDER BY
    residual_risk_score DESC,
    effectiveness_score ASC
LIMIT 15;
"""


def main():
    print("High/Critical residual-risk controls")
    print("=" * 70)

    with engine.connect() as connection:
        rows = connection.execute(text(QUERY))

        for row in rows:
            print(dict(row._mapping))

    print("=" * 70)


if __name__ == "__main__":
    main()
