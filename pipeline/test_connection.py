import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load database settings from the .env file
load_dotenv()

host = os.getenv("DB_HOST", "localhost")
port = os.getenv("DB_PORT", "5432")
database = os.getenv("DB_NAME", "crime_trends")
user = os.getenv("DB_USER", "crime_user")
password = os.getenv("DB_PASSWORD")

if not password:
    raise ValueError("DB_PASSWORD is missing. Check your .env file.")

# Create the PostgreSQL connection
connection_url = (
    f"postgresql+psycopg://{user}:{password}"
    f"@{host}:{port}/{database}"
)

engine = create_engine(connection_url)

# Test the connection
try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version();"))
        print("Connected to PostgreSQL successfully!")
        print(result.scalar())
except Exception as error:
    print("Database connection failed.")
    print(error)
    raise
finally:
    engine.dispose()