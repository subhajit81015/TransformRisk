from pathlib import Path
import sys


# ============================================================
# Project root
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.utils.db import engine


# ============================================================
# Execute SQL file
# ============================================================

def execute_sql_file(sql_file: Path):

    if not sql_file.exists():
        raise FileNotFoundError(
            f"SQL file not found: {sql_file}"
        )

    sql = sql_file.read_text(
        encoding="utf-8-sig"
    )

    if not sql.strip():
        raise RuntimeError(
            f"SQL file is empty: {sql_file}"
        )

    connection = engine.raw_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(sql)

        connection.commit()

        cursor.close()

        print(
            f"SQL EXECUTION OK: {sql_file}"
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":

    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python scripts/run_sql.py <sql_file>"
        )

    sql_file = PROJECT_ROOT / sys.argv[1]

    execute_sql_file(sql_file)
