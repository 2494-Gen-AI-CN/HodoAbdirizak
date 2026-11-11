"""Creates charts to answer business questions. """

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import geopandas as gpd
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
plt.show()

# Q2: Choropleth map of boroughs (slowest for the most serious calls)
CRS = "EPSG:2263"   # NYC state plane (feet): correct proportions, easy area filtering

q2 = run(f"SELECT * FROM `{PROJECT}.{DATASET}.v_q2_slowest_boroughs`")

# ---- clean (same as before) ----------------------------------------------
q2["borough"] = (
    q2["borough"].astype(str).str.strip().str.title()
      .replace({"Richmond / Staten Island": "Staten Island"})
)
q2["incident_dispatch_area"] = q2["incident_dispatch_area"].astype(str).str.strip()
q2["zipcode"] = q2["zipcode"].astype("string").str.strip().str.zfill(5)
for c in ["avg_response_min", "borough_avg_response_min", "zip_avg_response_min"]:
    q2[c] = pd.to_numeric(q2[c], errors="coerce")

borough_metrics = q2.drop_duplicates("borough")[
    ["borough", "borough_serious_incidents", "borough_avg_response_min", "borough_slowest_rank"]
]
area_metrics = q2.drop_duplicates(["borough", "incident_dispatch_area"])[
    ["borough", "incident_dispatch_area", "serious_incidents", "avg_response_min"]
]
zip_metrics = (
    q2.dropna(subset=["zipcode", "zip_avg_response_min"])
      .drop_duplicates("zipcode")[["zipcode", "zip_serious_incidents", "zip_avg_response_min"]]
)

BOROUGH_GEOJSON = (
    "https://data.cityofnewyork.us/api/v3/views/gthc-hcne/query.geojson?accessType=DOWNLOAD"
)

ZIP_GEOJSON = (
    "https://data.cityofnewyork.us/api/geospatial/pri4-ifjk"
    "?method=export&format=GeoJSON"
)

# ---- boundaries ----------------------------------------------------------
boroughs_raw = gpd.read_file(BOROUGH_GEOJSON).to_crs(CRS)
boroughs_raw["borough"] = boroughs_raw["boroname"].astype(str).str.strip().str.title()

zips = gpd.read_file(ZIP_GEOJSON).to_crs(CRS)
zips["zipcode"] = zips["label"].astype(str).str.split(",")
zips = zips.explode("zipcode")
zips["zipcode"] = zips["zipcode"].str.strip()
zips = (
    zips.merge(zip_metrics, on="zipcode", how="left")
        .sort_values("zip_serious_incidents", ascending=False)
        .drop_duplicates("modzcta")
)

# Tag each ZIP polygon with its borough (nearest borough to its interior point)
pts = zips[["modzcta", "geometry"]].copy()
pts["geometry"] = pts.geometry.representative_point()
pts = (
    gpd.sjoin_nearest(pts, boroughs_raw[["borough", "geometry"]], how="left")
       [["modzcta", "borough"]].drop_duplicates("modzcta")
)
zips = zips.merge(pts, on="modzcta", how="left")

# Land-only borough shapes: dissolve ZIPs, drop tiny fragments
boro_land = zips.dissolve(by="borough").reset_index()[["borough", "geometry"]]
boro_land = boro_land.explode(index_parts=False)
boro_land = boro_land[boro_land.area > 5e6]          # ~0.18 sq mi; removes specks
boro_land = boro_land.dissolve(by="borough").reset_index()
boro_land = boro_land.merge(borough_metrics, on="borough", how="left")

# ---- colour scale --------------------------------------------------------
vmin = zips["zip_avg_response_min"].quantile(0.05)
vmax = zips["zip_avg_response_min"].quantile(0.95)
norm = Normalize(vmin=vmin, vmax=vmax)
cmap = "YlOrRd"

halo = [pe.withStroke(linewidth=3, foreground="white")]

# ---- figure --------------------------------------------------------------
fig = plt.figure(figsize=(15, 9))
gs = fig.add_gridspec(2, 2, width_ratios=[1.5, 1], height_ratios=[1, 1.9])
ax_map = fig.add_subplot(gs[:, 0])
ax_bor = fig.add_subplot(gs[0, 1])
ax_area = fig.add_subplot(gs[1, 1])

# ZIP choropleth: thin white seams, light grey where there is too little data
zips.plot(column="zip_avg_response_min", cmap=cmap, norm=norm,
          edgecolor="white", linewidth=0.4, ax=ax_map,
          missing_kwds={"color": "#ececec", "edgecolor": "white", "linewidth": 0.4})

# Borough outlines: thin charcoal, land only
boro_land.boundary.plot(ax=ax_map, color="#333333", linewidth=1.1, zorder=3)

# 8 slowest ZIPs: numbered markers instead of cramped labels
slow = zips.dropna(subset=["zip_avg_response_min"]).nlargest(8, "zip_avg_response_min").reset_index(drop=True)
slow.boundary.plot(ax=ax_map, color="#3b0a0a", linewidth=0.9, zorder=4)
for i, r in slow.iterrows():
    p = r.geometry.representative_point()
    ax_map.scatter(p.x, p.y, s=230, facecolor="white", edgecolor="#222222",
                   linewidth=1, zorder=5, clip_on=False)
    ax_map.text(p.x, p.y, str(i + 1), ha="center", va="center",
                fontsize=8, fontweight="bold", zorder=6)

# Key for the numbered ZIPs, in the empty space at the bottom right
key_lines = ["Slowest ZIP codes"] + [
    f'{i + 1}. {r["zipcode"]}  {r["borough"]:<13} {r["zip_avg_response_min"]:.1f} min'
    for i, r in slow.iterrows()
]
ax_map.text(0.01, 0.50, "\n".join(key_lines), transform=ax_map.transAxes,
            ha="left", va="center", fontsize=7.5, family="monospace",
            bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="#bbbbbb", alpha=0.95))

# Borough labels with a white halo (no boxes covering the data)
def label_point(g):
    if g.geom_type == "MultiPolygon":
        g = max(g.geoms, key=lambda part: part.area)
    return g.representative_point()

offsets = {"Manhattan": (-60000, 25000)}   # push Manhattan's label out over the water
for _, r in boro_land.iterrows():
    if pd.isna(r["borough_avg_response_min"]):
        continue
    p = label_point(r.geometry)
    text = f'{r["borough"].upper()}\n{r["borough_avg_response_min"]:.1f} min avg'
    if r["borough"] in offsets:
        dx, dy = offsets[r["borough"]]
        ax_map.annotate(text, xy=(p.x, p.y), xytext=(p.x + dx, p.y + dy),
                        ha="center", va="center", fontsize=9, fontweight="bold",
                        path_effects=halo,
                        arrowprops=dict(arrowstyle="-", color="#666666", lw=0.8), zorder=7)
    else:
        ax_map.annotate(text, (p.x, p.y), ha="center", va="center", fontsize=9,
                        fontweight="bold", path_effects=halo, zorder=7)

# Compact colour bar tucked into the empty top-left corner
cax = ax_map.inset_axes([0.03, 0.93, 0.36, 0.02])
cbar = fig.colorbar(ScalarMappable(norm=norm, cmap=cmap), cax=cax,
                    orientation="horizontal", extend="both")
cbar.set_label("Avg response time by ZIP, most serious calls (min)", fontsize=8)
cbar.ax.tick_params(labelsize=8)

ax_map.set_title("Where Are Response Times Slowest?", fontsize=13, fontweight="bold")
ax_map.set_axis_off()
ax_map.margins(0.04)

# ---- panel: boroughs -----------------------------------------------------
b = boro_land.dropna(subset=["borough_avg_response_min"]).sort_values("borough_avg_response_min")
bars = ax_bor.barh(b["borough"], b["borough_avg_response_min"],
                   color=[plt.get_cmap(cmap)(norm(v)) for v in b["borough_avg_response_min"]],
                   edgecolor="#333333", linewidth=0.8, height=0.65)
ax_bor.bar_label(bars, labels=[f"{v:.1f} min" for v in b["borough_avg_response_min"]],
                 padding=4, fontsize=9)
ax_bor.set_title("Boroughs: Slowest at Top", fontsize=12, fontweight="bold")
ax_bor.spines[["top", "right", "left"]].set_visible(False)
ax_bor.margins(x=0.2)
ax_bor.set_xlabel("Average response time (minutes)")

# ---- panel: dispatch areas ----------------------------------------------
a = area_metrics.nlargest(15, "avg_response_min").sort_values("avg_response_min")
labels = a["incident_dispatch_area"] + "  |  " + a["borough"]
bars = ax_area.barh(labels, a["avg_response_min"],
                    color=[plt.get_cmap(cmap)(norm(v)) for v in a["avg_response_min"]],
                    edgecolor="#333333", linewidth=0.8, height=0.72)
ax_area.bar_label(bars, labels=[f"{v:.1f} min" for v in a["avg_response_min"]],
                  padding=4, fontsize=8)
ax_area.set_title("15 Slowest Dispatch Areas (citywide)", fontsize=12, fontweight="bold")
ax_area.spines[["top", "right", "left"]].set_visible(False)
ax_area.tick_params(axis="y", labelsize=8)
ax_area.margins(x=0.2)
ax_area.set_xlabel("Average response time (minutes)")

fig.suptitle("Which Boroughs and Dispatch Areas Are Slowest for the Most Serious Calls?",
             fontsize=16, fontweight="bold", y=0.985)
fig.text(0.5, 0.012,
         "Map shading = each ZIP's average response time across all dispatch areas serving it "
         "(grey = under 30 serious incidents). Dispatch areas have no published boundaries, so they are "
         "ranked in the bar chart. Colour scale clipped at the 5th/95th percentile.",
         ha="center", fontsize=8, color="dimgray", wrap=True)

fig.tight_layout(rect=[0, 0.03, 1, 0.95])
fig.savefig("charts/q2_slowest_boroughs_zip.png", dpi=300, bbox_inches="tight")
plt.show()


# Q3: Choropleth map of boroughs (slowest for the most serious calls)
q3 = run(f"SELECT * FROM `{PROJECT}.{DATASET}.v_q3_dispatch_vs_travel`")

q3["borough"] = (
    q3["borough"].astype(str).str.strip().str.title()
      .replace({"Richmond / Staten Island": "Staten Island", "All Nyc": "All NYC"})
)
q3["incident_dispatch_area"] = q3["incident_dispatch_area"].astype("string").str.strip()
for c in ["avg_dispatch_min", "avg_travel_min", "avg_total_min",
          "dispatch_share_pct", "travel_share_pct"]:
    q3[c] = pd.to_numeric(q3[c], errors="coerce")

city = q3[q3["level"] == "citywide"].iloc[0]
bor  = q3[q3["level"] == "borough"].sort_values("avg_total_min")
area = q3[q3["level"] == "dispatch_area"].nlargest(12, "avg_total_min").sort_values("avg_total_min")

C_DISP, C_TRAVEL, C_TEXT, C_MUTED = "#E07B00", "#1F6FAE", "#222222", "#6b6b6b"
BAR_H = 0.62

def stacked(ax, df, ypos, labels, bold_last=False):
    ax.barh(ypos, df["avg_dispatch_min"], color=C_DISP, height=BAR_H,
            edgecolor="white", linewidth=1.0)
    ax.barh(ypos, df["avg_travel_min"], left=df["avg_dispatch_min"], color=C_TRAVEL,
            height=BAR_H, edgecolor="white", linewidth=1.0)
    for y, r in zip(ypos, df.itertuples()):
        # travel value sits inside the wide segment
        ax.text(r.avg_dispatch_min + r.avg_travel_min / 2, y, f"{r.avg_travel_min:.1f}",
                ha="center", va="center", color="white", fontsize=9.5, fontweight="bold")
        # total + dispatch detail outside the bar, so nothing has to fit in the thin segment
        ax.text(r.avg_total_min + 0.15, y, f"{r.avg_total_min:.1f} min",
                ha="left", va="center", fontsize=9.5, fontweight="bold", color=C_TEXT)
        ax.text(r.avg_total_min + 0.15, y - 0.25, f"{r.avg_dispatch_min:.1f} dispatch · {r.travel_share_pct:.0f}% travel",
                ha="left", va="center", fontsize=7.5, color=C_MUTED)
    ax.set_yticks(ypos)
    ax.set_yticklabels(labels, fontsize=10)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#bbbbbb")
    ax.tick_params(axis="y", length=0, pad=8)
    ax.tick_params(axis="x", colors=C_MUTED, labelsize=9)
    ax.grid(axis="x", color="#e6e6e6", linewidth=0.8)
    ax.set_axisbelow(True)

fig, (ax_b, ax_a) = plt.subplots(
    1, 2, figsize=(15, 8.5), sharex=True, gridspec_kw={"width_ratios": [1, 1.2]}
)
# explicit margins: nothing is auto-squeezed, header gets its own band
fig.subplots_adjust(left=0.085, right=0.985, top=0.76, bottom=0.12, wspace=0.50)

# ---- left panel: boroughs + citywide benchmark ---------------------------
bor_df = pd.concat([bor, city.to_frame().T], ignore_index=True)
for c in ["avg_dispatch_min", "avg_travel_min", "avg_total_min", "travel_share_pct"]:
    bor_df[c] = pd.to_numeric(bor_df[c])
ypos_b = list(range(len(bor))) + [len(bor) + 0.9]          # gap above the citywide bar
stacked(ax_b, bor_df, ypos_b, list(bor["borough"]) + ["All NYC"])
ax_b.axhline(len(bor) - 0.1 + 0.45, color="#cccccc", linewidth=0.8, linestyle=(0, (3, 3)))
ax_b.get_yticklabels()[-1].set_fontweight("bold")
ax_b.set_ylim(-0.6, len(bor) + 1.5)
ax_b.set_title("By borough", fontsize=13, fontweight="bold", loc="left", pad=14)

# ---- right panel: slowest dispatch areas ---------------------------------
area_labels = area["incident_dispatch_area"] + "  ·  " + area["borough"]
stacked(ax_a, area, list(range(len(area))), list(area_labels))
ax_a.set_ylim(-0.6, len(area) - 0.4)
ax_a.set_title("12 slowest dispatch areas", fontsize=13, fontweight="bold", loc="left", pad=14)

for ax in (ax_b, ax_a):
    ax.set_xlabel("Average minutes from call to ambulance on scene", fontsize=9.5,
                  color=C_MUTED, labelpad=10)
ax_b.set_xlim(0, area["avg_total_min"].max() * 1.5)

# ---- header band: title, takeaway, legend --------------------------------
fig.text(0.085, 0.945, "Is the delay in dispatching or in travel?",
         fontsize=19, fontweight="bold", ha="left", va="center", color=C_TEXT)
fig.text(0.085, 0.895,
         f"Travel accounts for {city['travel_share_pct']:.0f}% of the {city['avg_total_min']:.1f}-minute average "
         f"response to the most serious calls. Dispatch takes about {city['avg_dispatch_min'] * 60:.0f} seconds.",
         fontsize=11.5, ha="left", va="center", color="#444444")

handles = [plt.Rectangle((0, 0), 1, 1, color=C_DISP), plt.Rectangle((0, 0), 1, 1, color=C_TRAVEL)]
fig.legend(handles,
           ["Dispatch: call received → ambulance assigned",
            "Travel: ambulance assigned → on scene"],
           loc="center left", bbox_to_anchor=(0.078, 0.835), ncol=2, frameon=False,
           fontsize=10, handlelength=1.2, columnspacing=2.5)

fig.text(0.085, 0.04,
         "Most serious calls only (final severity < 3); valid response times only. "
         "Dispatch areas with fewer than 30 incidents excluded. "
         "Travel includes crew turnout after assignment.",
         fontsize=8, color=C_MUTED, ha="left", va="center")

fig.savefig("charts/q3_dispatch_vs_travel.png", dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig)

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
