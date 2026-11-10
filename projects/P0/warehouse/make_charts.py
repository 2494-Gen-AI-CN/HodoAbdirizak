"""Creates charts to answer business questions. """

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
#import pgeocode
from google.cloud import bigquery

PROJECT = "desk-thanujanndayaparan"
DATASET = "ems_dw"
os.makedirs("charts", exist_ok=True)

client = bigquery.Client(project=PROJECT)

def run(sql):
    """Run a query and return the result as a pandas table."""
    return client.query(sql).to_dataframe()

# Q1: Response time by year (bar chart)
q1 = run(f"SELECT * FROM (SELECT * FROM `{PROJECT}.{DATASET}.v_q1_response_by_year` ORDER BY year DESC LIMIT 10) AS subquery ORDER BY year ASC;")
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


# Q4: Response times by hour and day of week

q4 = run("""
SELECT d.day_name , t.hour, ROUND(AVG(f.response_seconds)/60, 2) as response_time_min, COUNT(f.response_seconds) AS serious_incidents
FROM `desk-thanujanndayaparan.ems_dw.fact_ems_incident` AS f
JOIN `desk-thanujanndayaparan.ems_dw.dim_date` AS d on f.date_key = d.date_key 
JOIN `desk-thanujanndayaparan.ems_dw.dim_time` AS t on f.hour_key = t.hour_key
JOIN `desk-thanujanndayaparan.ems_dw.dim_call` AS c on f.call_type_key = c.call_type_key
WHERE c.is_most_serious = TRUE
GROUP BY t.hour, d.day_name
ORDER BY response_time_min DESC
""")

days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
hours_order = list(range(24))
hour_labels = [f"{h % 12 or 12} {'AM' if h < 12 else 'PM'}" for h in hours_order]


heatmap_data = q4.pivot_table(
    index="day_name", 
    columns="hour", 
    values="response_time_min", 
    aggfunc="mean"
).reindex(index=days_order, columns=hours_order)

fig, ax = plt.subplots(figsize=(10, 5))
im = ax.imshow(heatmap_data, cmap="YlOrRd", aspect="auto")

ax.set_title("Response time heatmap by day and hour", pad=10)
ax.set_xlabel("Hour of day")
ax.set_ylabel("Day of week")

ax.set_xticks(range(24))
ax.set_xticklabels(hour_labels)
ax.tick_params(axis="x", labelrotation=45)
ax.set_yticks(range(7))
ax.set_yticklabels(days_order)

fig.colorbar(im, ax=ax, label="Average response time (minutes)")
fig.tight_layout()
fig.savefig("charts/q4_response_by_hour_and_day.png", dpi=200)

# Q5: Ambulance capacity increase
q5 = run("""
WITH pilot AS (
  SELECT MIN(effective_from) AS pilot_start
  FROM `desk-thanujanndayaparan.ems_dw.dim_dispatch_area_capacity`
  WHERE pilot_flag = TRUE AND is_current = TRUE
)
SELECT 
  ca.pilot_flag, 
  IF(f.incident_date < p.pilot_start, 'before pilot', 'after pilot') AS period, 
  COUNT(f.response_seconds) AS incidents,
  -- 50th percentile: half of incidents took this long or less.
  ROUND(APPROX_QUANTILES(f.response_seconds, 100)[OFFSET(50)] / 60,2) AS median_min,
  -- 90% of incidents took this long or less; the slowest 10% took longer.
  ROUND(APPROX_QUANTILES(f.response_seconds, 100)[OFFSET(90)] / 60,2) AS `90p_min`
FROM `desk-thanujanndayaparan.ems_dw.fact_ems_incident` AS f
JOIN `desk-thanujanndayaparan.ems_dw.dim_dispatch_area_capacity` AS ca ON f.capacity_key = ca.capacity_key
CROSS JOIN pilot AS p
WHERE f.response_seconds IS NOT NULL
GROUP BY 1, 2 -- Groups results by pilot status and time period.
ORDER BY 1, 2;
""")

chart_data = q5.pivot(
    index="pilot_flag",
    columns="period",
    values="median_min"
)

x = np.arange(len(chart_data))
width = 0.35

fig, ax = plt.subplots(figsize=(10, 5))

bars1 = ax.bar(x - width/2, chart_data["before pilot"], width, label="Before")
bars2 = ax.bar(x + width/2, chart_data["after pilot"], width, label="After")
ax.bar_label(bars1, fmt="%.2f", padding=2)
ax.bar_label(bars2, fmt="%.2f", padding=2)

ax.set_title("Median response time before and after capacity increase")
ax.set_xlabel("Area type")
ax.set_ylabel("Median response time (minutes)")

ax.set_xticks(x)
ax.set_xticklabels(["Non-pilot areas", "Pilot areas"])
ax.legend()

fig.tight_layout()
fig.savefig("charts/q5_capacity_comparison.png", dpi=200)

print("Done. Charts saved in the charts/ folder.")
plt.show()