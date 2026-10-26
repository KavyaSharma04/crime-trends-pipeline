
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# Load database credentials
project_root = Path(__file__).resolve().parent.parent
load_dotenv(project_root / ".env")

# Connect to PostgreSQL
connection_url = URL.create(
    drivername="postgresql+psycopg",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    database=os.getenv("DB_NAME"),
)

engine = create_engine(connection_url)

# Check the data types of the two date columns
query = text("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'crime_reports'
      AND column_name IN ('date_of_report', 'crime_date_time')
    ORDER BY column_name;
""")

try:
    with engine.connect() as connection:
        results = connection.execute(query).fetchall()

    print("\nColumn data types:")
    for column_name, data_type in results:
        print(f"{column_name}: {data_type}")

finally:
    engine.dispose()
