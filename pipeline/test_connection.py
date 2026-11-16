
from sqlalchemy import create_engine, text
from pipeline.load import get_database_url

engine = create_engine(
    get_database_url(),
    pool_pre_ping=True
)

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version();"))
        print("Connected to PostgreSQL successfully!")
        print("Database connection is working.")

finally:
    engine.dispose()
