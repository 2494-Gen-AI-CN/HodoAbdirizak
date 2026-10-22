from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

csv_path = Path("data/airport_traffic_2025.csv")

def load_data():
    # Create a dataframe from csv file
    df = pd.read_csv(csv_path)
    # FLT_TOT_1 holds the arrivals and departures for each day at each airport
    df["FLT_TOT_1"] = pd.to_numeric(df["FLT_TOT_1"], errors="coerce").fillna(0)
    return df

df = load_data()

# Create a table of the first 10 sorted results
airport_totals = (
    # Group by airport name
    df.groupby("APT_NAME")["FLT_TOT_1"]
    # Add up the flight totals for each airport
    .sum()
    .sort_values(ascending=False)
)

# Take top 10 airports with most flights and turn into column
top_airports = airport_totals.head(10).reset_index()
top_airports.columns = ["Airport", "Total Flights"]


y_pos = np.arange(len(top_airports["Airport"]))

fig, ax = plt.subplots(figsize=(12, 6))

ax.bar(y_pos, top_airports["Total Flights"], width=0.8, color="#466ee5")

ax.set_xticks(y_pos)
ax.set_xticklabels(top_airports["Airport"], rotation=45, ha="right")

ax.set_title("Top 10 Busiest Airports")
ax.set_ylabel("Total Flights")

plt.tight_layout()
plt.show()

# Displaying monthly traffic by country
countries = [country for country in df["STATE_NAME"].unique()]
choice = input(f"Select a country: {countries}").upper()

# Filter the dataframe for the selected country 
country_df = df[df["STATE_NAME"].str.upper() == choice]

if country_df.empty:
    print("Country not found. Please select a country from the list.")

else:
    monthly_cols = country_df.groupby("MONTH_NUM")["FLT_TOT_1"].sum().sort_index()
    # Get the month names for the x-axis labels
    month_names = country_df.drop_duplicates("MONTH_NUM")["MONTH_MON"]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(monthly_cols.index, monthly_cols.values)

    ax.set_title(f"Monthly traffic for {choice}")

    ax.set_xticks(monthly_cols.index)
    ax.set_xticklabels(month_names)

    ax.set_xlabel("Month")
    ax.set_ylabel("Total Flights")

    plt.tight_layout()
    plt.show()