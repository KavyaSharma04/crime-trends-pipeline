
from prefect import flow, task

from pipeline.extract import extract_crime_data
from pipeline.clean import clean_crime_data
from pipeline.load import load_crime_data


@task(name="Extract Crime Data", retries=2, retry_delay_seconds=5)
def extract_task():
    return extract_crime_data()


@task(name="Clean Crime Data")
def clean_task():
    return clean_crime_data()


@task(name="Load Crime Data")
def load_task():
    load_crime_data()


@flow(name="Crime Trends ETL Pipeline", log_prints=True)
def crime_trends_pipeline():
    extract_task()
    clean_task()
    load_task()


if __name__ == "__main__":
    crime_trends_pipeline()
