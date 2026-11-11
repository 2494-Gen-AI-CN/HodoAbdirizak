"""Load configured raw data sources into BigQuery and clean selected sources."""

import io
from pathlib import Path

import pandas as pd
from google.cloud import bigquery

from cleansing import add_typed_columns, split_good_and_rejects
from job_config import load_config, load_source_dataframe


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config.yaml"


def upload_dataframe(client, df, table_id):
    """Upload a Pandas DataFrame to BigQuery through an in-memory CSV."""
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    schema = []
    for column in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[column]):
            field_type = "TIMESTAMP"
        elif pd.api.types.is_integer_dtype(df[column]):
            field_type = "INT64"
        elif pd.api.types.is_float_dtype(df[column]):
            field_type = "FLOAT64"
        elif pd.api.types.is_bool_dtype(df[column]):
            field_type = "BOOL"
        else:
            field_type = "STRING"
        schema.append(bigquery.SchemaField(column, field_type, mode="NULLABLE"))

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    job = client.load_table_from_file(
        io.BytesIO(csv_buffer.getvalue().encode("utf-8")),
        table_id,
        job_config=job_config,
    )
    job.result()
    print(f"Loaded {job.output_rows} rows into {table_id}.")


def load_raw_source(client, source, source_path, project, dataset):
    """Load one configured CSV or newline-delimited JSON source."""
    table_id = f"{project}.{dataset}.{source['name']}"
    if source["format"] == "csv":
        columns = pd.read_csv(source_path, nrows=0).columns
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.CSV,
            skip_leading_rows=1,
            schema=[
                bigquery.SchemaField(column, "STRING", mode="NULLABLE")
                for column in columns
            ],
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        )
    else:
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            autodetect=True,
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        )

    with source_path.open("rb") as source_file:
        job = client.load_table_from_file(
            source_file,
            table_id,
            job_config=job_config,
        )
    job.result()
    print(f"Loaded {job.output_rows} raw rows into {table_id}.")


def clean_ems_source(client, source, source_path, project, dataset):
    """Apply the existing EMS cleansing rules and write clean/rejected rows."""
    df = load_source_dataframe(source_path, source["format"])
    df = add_typed_columns(df)
    good, rejects = split_good_and_rejects(df)

    good = good.rename(columns={"incident_datetime": "incident_datetime_parsed"})
    rejects = rejects.rename(
        columns={"incident_datetime": "incident_datetime_parsed"}
    )
    print(f"Valid rows: {len(good)}")
    print(f"Rejected rows: {len(rejects)}")

    upload_dataframe(
        client,
        good,
        f"{project}.{dataset}.{source['clean_table']}",
    )
    upload_dataframe(
        client,
        rejects,
        f"{project}.{dataset}.{source['reject_table']}",
    )


def main():
    config = load_config(CONFIG_PATH)
    project = config["bigquery"]["project"]
    client = bigquery.Client(project=project)

    for source in config["sources"]:
        source_path = (CONFIG_PATH.parent / source["file"]).resolve()
        if not source_path.is_file():
            raise FileNotFoundError(
                f"Configured source file does not exist: {source_path}"
            )

        load_raw_source(
            client,
            source,
            source_path,
            project,
            config["bigquery"]["raw_dataset"],
        )
        if source.get("transform") == "ems_incidents":
            clean_ems_source(
                client,
                source,
                source_path,
                project,
                config["bigquery"]["warehouse_dataset"],
            )


if __name__ == "__main__":
    main()
