from pathlib import Path

import numpy as np
import pandas as pd

csv_path = Path("data/airport_traffic_2025.csv")


def load_data():
    # Create a dataframe from csv file
    df = pd.read_csv(csv_path)
    # FLT_TOT_1 = total flights for row
    df["FLT_TOT_1"] = pd.to_numeric(df["FLT_TOT_1"], errors="coerce").fillna(0)
    return df


print("Loading airport dataset...\n")
df = load_data()

airport_totals = (
    # group by airport name
    df.groupby("APT_NAME")["FLT_TOT_1"]
    # add up all flight total for each airport
    .sum()
    .sort_values(ascending=False)
)

# Take top 10 airports with most flights and turn into column
top_airports = airport_totals.head(10).reset_index()
top_airports.columns = ["Airport", "Total Flights"]

print("Top 10 busiest airports:")
print(top_airports.to_string(index=False))

values = airport_totals.to_numpy()
print("\nSummary:")
print(f"Average flights per airport: {np.mean(values):,.2f}")
print(f"Highest airport total: {np.max(values):,.0f}")
print(f"Airports analyzed: {len(values)}")