import os
from dotenv import load_dotenv
import io
import pandas as pd
from google.cloud import bigquery
from cleansing import add_typed_columns, split_good_and_rejects

load_dotenv()

# Connect to BigQuery
client = bigquery.Client(
    project=os.environ["DESK_GCP_PROJECT"]
)

raw_table_id = "desk-thanujanndayaparan.ems_raw.ems_incidents"
clean_table_id = "desk-thanujanndayaparan.ems_dw.ems_incidents_clean"
reject_table_id = "desk-thanujanndayaparan.ems_dw.ems_incidents_rejected"

def upload_dataframe(df, table_id):
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

        schema.append(
            bigquery.SchemaField(column, field_type, mode="NULLABLE")
        )

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
    )

    job = client.load_table_from_file(
        io.BytesIO(csv_buffer.getvalue().encode("utf-8")),
        table_id,
        job_config=job_config
    )

    job.result()

    print(f"Loaded {job.output_rows} rows into {table_id}.")

# Define all CSV columns
columns = [
    "INCIDENT_ID",
    "INCIDENT_DATETIME",
    "INITIAL_CALL_TYPE",
    "INITIAL_SEVERITY_LEVEL_CODE",
    "FINAL_CALL_TYPE",
    "FINAL_SEVERITY_LEVEL_CODE",
    "FIRST_ASSIGNMENT_DATETIME",
    "VALID_DISPATCH_RSPNS_TIME_INDC",
    "DISPATCH_RESPONSE_SECONDS_QY",
    "FIRST_ACTIVATION_DATETIME",
    "FIRST_ON_SCENE_DATETIME",
    "VALID_INCIDENT_RSPNS_TIME_INDC",
    "INCIDENT_RESPONSE_SECONDS_QY",
    "INCIDENT_TRAVEL_TM_SECONDS_QY",
    "FIRST_TO_HOSP_DATETIME",
    "FIRST_HOSP_ARRIVAL_DATETIME",
    "INCIDENT_CLOSE_DATETIME",
    "HELD_INDICATOR",
    "INCIDENT_DISPOSITION_CODE",
    "BOROUGH",
    "INCIDENT_DISPATCH_AREA",
    "ZIPCODE",
    "POLICEPRECINCT",
    "CITYCOUNCILDISTRICT",
    "COMMUNITYDISTRICT",
    "COMMUNITYSCHOOLDISTRICT",
    "CONGRESSIONALDISTRICT",
    "REOPEN_INDICATOR",
    "SPECIAL_EVENT_INDICATOR",
    "STANDBY_INDICATOR",
    "TRANSFER_INDICATOR"
]

# Generate BigQuery schema for raw CSV
schema = [
    bigquery.SchemaField(column, "STRING", mode="NULLABLE")
    for column in columns
]

raw_job_config = bigquery.LoadJobConfig(
    source_format=bigquery.SourceFormat.CSV,
    skip_leading_rows=1,
    schema=schema,
    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
)

file_path = "data/ems_incidents.csv"

df = pd.read_csv(file_path, dtype=str)

with open(file_path, "rb") as source_file:
    raw_job = client.load_table_from_file(
        source_file,
        raw_table_id,
        job_config=raw_job_config
    )

raw_job.result()

print(f"Loaded {raw_job.output_rows} raw rows into {raw_table_id}.")

df = add_typed_columns(df)
good, rejects = split_good_and_rejects(df)

good = good.rename(columns={"incident_datetime": "incident_datetime_parsed"})
rejects = rejects.rename(columns={"incident_datetime": "incident_datetime_parsed"})

print(f"Valid rows: {len(good)}")
print(f"Rejected rows: {len(rejects)}")

# Upload cleaned and rejected records
upload_dataframe(good, clean_table_id)
upload_dataframe(rejects, reject_table_id)
