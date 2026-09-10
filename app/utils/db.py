import os

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, text


PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
    )
)

load_dotenv(
    os.path.join(
        PROJECT_ROOT,
        ".env",
    )
)


def get_database_url() -> URL:
    host = os.getenv(
        "DB_HOST",
        "localhost",
    )

    port = int(
        os.getenv(
            "DB_PORT",
            "5432",
        )
    )

    database = os.getenv(
        "DB_NAME",
        "transformrisk",
    )

    user = os.getenv(
        "DB_USER",
        "postgres",
    )

    password = os.getenv(
        "DB_PASSWORD"
    )

    if not password:
        raise RuntimeError(
            "DB_PASSWORD is not configured "
            "in the .env file."
        )

    return URL.create(
        drivername="postgresql+psycopg2",
        username=user,
        password=password,
        host=host,
        port=port,
        database=database,
    )


engine = create_engine(
    get_database_url(),
    pool_pre_ping=True,
)


def test_connection() -> bool:
    with engine.connect() as connection:
        connection.execute(
            text("SELECT 1")
        )

    return True
