import os
from google.cloud import bigquery

client = bigquery.Client(
    project=os.environ["DESK_GCP_PROJECT"]
)

sql_files = [
    "create_dimensions.sql",
    "create_fact.sql"
]

for filename in sql_files:
    with open(f"sql/{filename}", "r") as file:
        sql = file.read()

    query_job = client.query(sql)
    query_job.result()

    print(f"Executed {filename} successfully.")