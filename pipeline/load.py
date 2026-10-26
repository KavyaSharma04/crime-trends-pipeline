import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url

# Load environment variables from the project .env file.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

CLEANED_FILE = (
    PROJECT_ROOT / "data" / "processed" / "crime_reports_cleaned.csv"
)


def get_database_url():
    """Choose the local or Render PostgreSQL database."""

    target = os.getenv("DB_TARGET", "local").strip().lower()

    if target == "local":
        required_env = [
            "DB_HOST",
            "DB_PORT",
            "DB_NAME",
            "DB_USER",
            "DB_PASSWORD",
        ]

        missing = [
            key for key in required_env
            if not os.getenv(key)
        ]

        if missing:
            raise ValueError(
                f"Missing environment variables: {', '.join(missing)}"
            )

        return URL.create(
            drivername="postgresql+psycopg",
            username=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT")),
            database=os.getenv("DB_NAME"),
        )

    elif target == "render":
        render_url = os.getenv("RENDER_DATABASE_URL")

        if not render_url:
            raise ValueError(
                "DB_TARGET is 'render', but RENDER_DATABASE_URL is missing."
            )

        url = make_url(render_url)

        # Use psycopg, which is the driver used by this project.
        url = url.set(drivername="postgresql+psycopg")

        # Render PostgreSQL connections require SSL.
        query = dict(url.query)
        query.setdefault("sslmode", "require")
        url = url.set(query=query)

        return url

    else:
        raise ValueError(
            "Invalid DB_TARGET. Use 'local' or 'render'."
        )


def load_crime_data():
    """Load cleaned crime records into the selected PostgreSQL database."""

    target = os.getenv("DB_TARGET", "local").strip().lower()
    print(f"Loading cleaned crime data into {target.upper()} PostgreSQL...")

    if not CLEANED_FILE.exists():
        raise FileNotFoundError(
            f"Cleaned data not found: {CLEANED_FILE}. "
            "Run the cleaning step first."
        )

    df = pd.read_csv(CLEANED_FILE)

    # Convert date columns into actual datetime values.
    df["date_of_report"] = pd.to_datetime(
        df["date_of_report"], errors="coerce"
    )
    df["crime_date_time"] = pd.to_datetime(
        df["crime_date_time"], errors="coerce"
    )

    if df.empty:
        raise ValueError("The cleaned dataset is empty.")

    connection_url = get_database_url()
    engine = create_engine(connection_url, pool_pre_ping=True)

    try:
        # NOTE: replace recreates the crime_reports table on each run.
        df.to_sql(
            name="crime_reports",
            con=engine,
            schema="public",
            if_exists="replace",
            index=False,
            chunksize=500,
            method="multi",
        )

        with engine.connect() as connection:
            count = connection.execute(
                text("SELECT COUNT(*) FROM public.crime_reports")
            ).scalar_one()

        print(f"Records in cleaned CSV: {len(df)}")
        print(f"Records loaded into PostgreSQL: {count}")

        if count != len(df):
            raise RuntimeError(
                "Record count mismatch between CSV and PostgreSQL."
            )

        print(f"Data loaded and verified successfully in {target.upper()}!")

    finally:
        engine.dispose()


if __name__ == "__main__":
    load_crime_data()