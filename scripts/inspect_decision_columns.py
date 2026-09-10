from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text
from app.utils.db import engine


query = """
SELECT
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'analytics'
  AND table_name = 'transformation_decision'
ORDER BY ordinal_position;
"""


with engine.connect() as connection:
    rows = connection.execute(text(query)).fetchall()

print("\nTRANSFORMRISK DECISION VIEW COLUMNS")
print("=" * 60)

for column_name, data_type in rows:
    print(f"{column_name:35} {data_type}")

print("=" * 60)
print(f"TOTAL COLUMNS: {len(rows)}") 