
import requests
import pandas as pd
from pathlib import Path

# Cambridge Police Department public crime reports API
API_URL = "https://data.cambridgema.gov/resource/xuad-73uj.json"

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def extract_crime_data(limit=5000):
    """Fetch crime records from the public API."""

    params = {
        "$limit": limit,
        "$order": "date_of_report DESC",
    }

    print("Fetching crime data from Cambridge's public API...")

    response = requests.get(API_URL, params=params, timeout=60)
    response.raise_for_status()

    records = response.json()
    df = pd.DataFrame(records)

    if df.empty:
        print("No records were returned.")
        return df

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    output_file = RAW_DATA_DIR / "crime_reports_raw.csv"
    df.to_csv(output_file, index=False)

    print(f"Records fetched: {len(df)}")
    print(f"Columns found: {list(df.columns)}")
    print(f"Raw data saved to: {output_file}")

    return df


if __name__ == "__main__":
    extract_crime_data()
