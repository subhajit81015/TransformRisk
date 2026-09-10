from pathlib import Path
import sys

from sqlalchemy import URL, create_engine, text
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")


def main():
    host = "localhost"
    port = 5432
    user = "postgres"
    password = __import__("os").getenv("DB_PASSWORD")

    if not password:
        raise RuntimeError(
            "DB_PASSWORD is not configured."
        )

    admin_url = URL.create(
        drivername="postgresql+psycopg2",
        username=user,
        password=password,
        host=host,
        port=port,
        database="postgres",
    )

    engine = create_engine(
        admin_url,
        isolation_level="AUTOCOMMIT",
    )

    with engine.connect() as connection:
        exists = connection.execute(
            text(
                """
                SELECT 1
                FROM pg_database
                WHERE datname = 'transformrisk'
                """
            )
        ).scalar()

        if exists:
            print("Database already exists: transformrisk")
        else:
            connection.execute(
                text("CREATE DATABASE transformrisk")
            )
            print("Database created: transformrisk")


if __name__ == "__main__":
    main()
