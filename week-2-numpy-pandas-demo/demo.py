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

def select_country(countries):
    """Choosing a country from the list of countries """
    while True:
        choice = input("\nEnter the number of your choice: ").strip()

        # Checking if choice is valid
        if choice.isdigit() and 1 <= int(choice) <= len(countries):
            choice = countries[int(choice) - 1]
            break

        print("Invalid selection. Please enter a number from the list.")
    
    return choice

def display_country(countries):
    """Displays a numbered list of countries"""

    print("\nSelect a country:\n")

    for i, country in enumerate(countries, start=1):
        print(f"{i}. {country}")

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

fig, ax = plt.subplots(figsize=(14, 8))
bars = ax.bar(
    y_pos,
    top_airports["Total Flights"],
    width=0.8,
    color="#5b7cff",
    edgecolor="#1e3a8a"
)

ax.set_xticks(y_pos)
ax.set_xticklabels(top_airports["Airport"], rotation=45, ha="right")

ax.set_title("Top 10 Busiest Airports", fontsize=18, fontweight="bold")
ax.set_ylabel("Total Flights")
ax.grid(axis="y", linestyle="--", alpha=0.4)

for bar, value in zip(bars, top_airports["Total Flights"]):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        value + 1000,
        f"{value:,.0f}",
        ha="center",
        va="bottom",
        fontsize=9
    )

plt.tight_layout()
plt.show()

# Displaying monthly traffic by country
countries = sorted(df["STATE_NAME"].dropna().unique())

print("\n=== Monthly Airport Traffic ===")

display_country(countries)
choice = select_country(countries)

# Filter the dataframe for the selected country 
country_df = df[df["STATE_NAME"].str.upper() == choice.upper()]

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

# Comparing two countries total flights 

print("\nCountry comparison:")

display_country(countries)
country_one = select_country(countries)
country_two = select_country(countries)

while country_one == country_two:
    print("You must pick a different country")
    country_two = select_country(countries)

country_one_df = df[df["STATE_NAME"].str.upper() == country_one.upper()]
country_two_df = df[df["STATE_NAME"].str.upper() == country_two.upper()]

monthly_totals_one = country_one_df.groupby("MONTH_NUM")["FLT_TOT_1"].sum().sort_index()
monthly_totals_two = country_two_df.groupby("MONTH_NUM")["FLT_TOT_1"].sum().sort_index()

fig, ax = plt.subplots(figsize=(12, 6))

ax.plot(monthly_totals_one.index, monthly_totals_one.values, label=country_one, marker='o')
ax.plot(monthly_totals_two.index, monthly_totals_two.values, label=country_two, marker='s')

ax.set_title(f"Monthly traffic comparison: {country_one} vs {country_two}")
ax.set_xlabel("Month")
ax.set_ylabel("Total Flights")
ax.legend()

plt.tight_layout()
plt.show()

# Finding the busiest month
monthly_totals = df.groupby("MONTH_MON")["FLT_TOT_1"].sum()
busiest_month = monthly_totals.idxmax()

print(f"The busiest month is {busiest_month} with a total of {monthly_totals.max()} flights.")


