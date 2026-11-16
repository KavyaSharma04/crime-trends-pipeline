from sqlalchemy import create_engine, text
from pipeline.load import get_database_url

engine = create_engine(get_database_url())

try:
    with engine.connect() as connection:
        query = text("""
            SELECT
                COUNT(*) AS total_records,
                MIN(date_of_report) AS earliest_report,
                MAX(date_of_report) AS latest_report
            FROM public.crime_reports
        """)

        result = connection.execute(query).one()

        print("Total records:", result.total_records)
        print("Earliest report:", result.earliest_report)
        print("Latest report:", result.latest_report)

finally:
    engine.dispose()
