from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text
from app.utils.db import engine


QUERY = """
SELECT
    transformation_decision,
    COUNT(*) AS initiatives
FROM analytics.transformation_decision
GROUP BY transformation_decision
ORDER BY initiatives DESC;
"""


def main():
    print("TransformRisk Decision Distribution")
    print("=" * 60)

    with engine.connect() as connection:
        rows = connection.execute(text(QUERY))

        for row in rows:
            print(dict(row._mapping))

    print("=" * 60)


if __name__ == "__main__":
    main()
