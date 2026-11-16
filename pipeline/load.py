
import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url

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
            "DB_HOST", "DB_PORT", "DB_NAME",
            "DB_USER", "DB_PASSWORD"
        ]

        missing = [key for key in required_env if not os.getenv(key)]

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
        url = url.set(drivername="postgresql+psycopg")

        query = dict(url.query)
        query.setdefault("sslmode", "require")

        return url.set(query=query)

    else:
        raise ValueError("Invalid DB_TARGET. Use 'local' or 'render'.")


def load_crime_data():
    """Safely insert or update crime records using file_number."""

    target = os.getenv("DB_TARGET", "local").strip().lower()
    print(f"Loading cleaned crime data into {target.upper()} PostgreSQL...")

    if not CLEANED_FILE.exists():
        raise FileNotFoundError(
            f"Cleaned data not found: {CLEANED_FILE}. "
            "Run the cleaning step first."
        )

    df = pd.read_csv(CLEANED_FILE)

    if df.empty:
        raise ValueError("The cleaned dataset is empty.")

    required_columns = [
        "file_number", "date_of_report", "crime_date_time",
        "crime", "reporting_area", "neighborhood", "location",
        "reporting_area_lat", "reporting_area_lon",
        "reporting_area_location", "crime_date_time_original",
        "crime_year", "crime_month", "crime_day_of_week",
        "crime_hour"
    ]

    if list(df.columns) != required_columns:
        raise ValueError(
            "CSV columns do not match the expected database schema."
        )

    if df["file_number"].isna().any():
        raise ValueError("Missing file_number values found.")

    if df["file_number"].duplicated().any():
        raise ValueError("Duplicate file_number values found in CSV.")

    for column in ["date_of_report", "crime_date_time"]:
        df[column] = pd.to_datetime(df[column], errors="coerce")

    connection_url = get_database_url()
    engine = create_engine(connection_url, pool_pre_ping=True)

    columns = ", ".join(f'"{col}"' for col in required_columns)
    placeholders = ", ".join(f":{col}" for col in required_columns)

    update_columns = [
        col for col in required_columns if col != "file_number"
    ]

    update_clause = ", ".join(
        f'"{col}" = EXCLUDED."{col}"' for col in update_columns
    )

    upsert_query = text(f"""
        INSERT INTO public.crime_reports ({columns})
        VALUES ({placeholders})
        ON CONFLICT (file_number)
        DO UPDATE SET {update_clause}
    """)

    records = df.astype(object).where(pd.notna(df), None).to_dict(
        orient="records"
    )

    try:
        with engine.begin() as connection:
            # Verify that file_number is unique in the target table.
            unique_check = connection.execute(text("""
                SELECT COUNT(*)
                FROM (
                    SELECT file_number
                    FROM public.crime_reports
                    GROUP BY file_number
                    HAVING COUNT(*) > 1
                ) duplicates
            """)).scalar_one()

            if unique_check:
                raise RuntimeError(
                    "Existing table contains duplicate file_number values."
                )

            # A unique constraint/index is required for ON CONFLICT.
            connection.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS
                idx_crime_reports_file_number
                ON public.crime_reports (file_number)
            """))

            connection.execute(upsert_query, records)

            count = connection.execute(text("""
                SELECT COUNT(*) FROM public.crime_reports
            """)).scalar_one()

        print(f"Records in cleaned CSV: {len(df)}")
        print(f"Records in PostgreSQL: {count}")
        print(f"Data safely loaded into {target.upper()}!")

    finally:
        engine.dispose()

