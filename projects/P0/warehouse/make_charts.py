"""Creates charts to answer business questions. """

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pgeocode
from google.cloud import bigquery

PROJECT = "desk-thanujanndayaparan"
DATASET = "ems_dw"
os.makedirs("charts", exist_ok=True)

client = bigquery.Client(project=PROJECT)

def run(sql):
    """Run a query and return the result as a pandas table."""
    return client.query(sql).to_dataframe()

# Q1: Response time by year (bar chart)
q1 = run(f"SELECT * FROM (SELECT * FROM `{PROJECT}.{DATASET}.v_q1_response_by_year ORDER BY year DESC LIMIT 10) AS subquery ORDER BY year ASC;")
q1["year"] = q1["year"].astype(str)

fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(q1["year"], q1["avg_response_min"], width=0.7, color="#2b6cb0")
ax.bar_label(bars, fmt="%.1f", padding=10)
ax.set_title("Average response time for the most serious calls, by year")
ax.set_xlabel("Year")
ax.set_ylabel("Average response time (minutes)")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig("charts/q1_response_by_year.png", dpi=200)

print("Done. Charts saved in the charts/ folder.")
plt.show()