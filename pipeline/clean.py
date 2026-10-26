
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_FILE = PROJECT_ROOT / "data" / "raw" / "crime_reports_raw.csv"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def clean_crime_data():
    """Clean and validate the raw crime dataset."""

    print("Loading raw crime data...")

    if not RAW_FILE.exists():
        raise FileNotFoundError(f"Raw dataset not found: {RAW_FILE}")

    df = pd.read_csv(RAW_FILE)

    print(f"Records before cleaning: {len(df)}")

    # Standardize column names.
    df.columns = df.columns.str.strip().str.lower()

    # Remove exact duplicate rows only.
    before = len(df)
    df = df.drop_duplicates()
    duplicates_removed = before - len(df)

    # Preserve the original crime timestamp for reference.
    df["crime_date_time_original"] = df["crime_date_time"]

    # Extract the beginning of a crime time interval.
    # Example: "09/27/2026 08:40 - 09/28/2026 23:47"
    # becomes "09/27/2026 08:40".
    start_time = (
        df["crime_date_time"]
        .astype("string")
        .str.extract(
            r"^\s*(\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2})",
            expand=False,
        )
    )

    df["crime_date_time"] = pd.to_datetime(
        start_time,
        format="%m/%d/%Y %H:%M",
        errors="coerce",
    )

    # Parse the report date separately.
    df["date_of_report"] = pd.to_datetime(
        df["date_of_report"],
        errors="coerce",
    )

    # Remove records missing essential fields or an interpretable
    # crime start date/time.
    before = len(df)

    df = df.dropna(
        subset=["file_number", "crime", "crime_date_time"]
    )

    invalid_removed = before - len(df)

    # Standardize text fields.
    for column in ["crime", "neighborhood"]:
        df[column] = df[column].astype("string").str.strip()

    # Add features for trend analysis.
    df["crime_year"] = df["crime_date_time"].dt.year
    df["crime_month"] = df["crime_date_time"].dt.month
    df["crime_day_of_week"] = df["crime_date_time"].dt.day_name()
    df["crime_hour"] = df["crime_date_time"].dt.hour

    # Save the cleaned data.
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    output_file = PROCESSED_DIR / "crime_reports_cleaned.csv"
    df.to_csv(output_file, index=False)

    print(f"Exact duplicate rows removed: {duplicates_removed}")
    print(f"Records removed for invalid required fields: {invalid_removed}")
    print(f"Records after cleaning: {len(df)}")
    print(f"Records retained: {len(df) / 5000 * 100:.2f}%")
    print(f"Cleaned data saved to: {output_file}")

    return df


if __name__ == "__main__":
    clean_crime_data()
