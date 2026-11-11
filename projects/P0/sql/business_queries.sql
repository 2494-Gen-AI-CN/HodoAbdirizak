-- Question 1: How have response times for the most serious calls changed year by year?
CREATE OR REPLACE VIEW `desk-thanujanndayaparan.ems_dw.v_q1_response_by_year` AS
SELECT
  d.year,
  COUNT(*) AS serious_incidents,
  ROUND(AVG(f.response_seconds) / 60, 2) AS avg_response_min
FROM `desk-thanujanndayaparan.ems_dw.fact_ems_incident` AS f
JOIN `desk-thanujanndayaparan.ems_dw.dim_date` AS d ON f.date_key = d.date_key
JOIN `desk-thanujanndayaparan.ems_dw.dim_call` AS c ON f.call_type_key = c.call_type_key
WHERE c.is_most_serious
  AND f.response_seconds IS NOT NULL
GROUP BY d.year
ORDER BY d.year;

-- Question 2: Which boroughs and dispatch areas are slowest for the most serious calls?
CREATE OR REPLACE VIEW `desk-thanujanndayaparan.ems_dw.v_q2_slowest_boroughs` AS

WITH base AS (
  SELECT
    l.borough,
    l.incident_dispatch_area,
    z.zipcode,
    f.response_seconds
  FROM `desk-thanujanndayaparan.ems_dw.fact_ems_incident` f
  JOIN `desk-thanujanndayaparan.ems_dw.dim_location` l ON f.location_key = l.location_key
  JOIN `desk-thanujanndayaparan.ems_dw.dim_call` c     ON f.call_type_key = c.call_type_key
  LEFT JOIN `desk-thanujanndayaparan.ems_dw.dim_zip` z
         ON f.zip_key = z.zip_key AND z.zip_key <> -1
  WHERE c.is_most_serious = TRUE
    AND f.response_seconds IS NOT NULL
    AND l.location_key <> -1
    AND l.borough IS NOT NULL
),

area_stats AS (
  SELECT
    borough,
    incident_dispatch_area,
    COUNT(*) AS serious_incidents,
    ROUND(AVG(response_seconds) / 60, 2) AS avg_response_min
  FROM base
  WHERE incident_dispatch_area IS NOT NULL
  GROUP BY borough, incident_dispatch_area
  HAVING COUNT(*) >= 30
),

borough_stats AS (
  SELECT
    borough,
    COUNT(*) AS borough_serious_incidents,
    ROUND(AVG(response_seconds) / 60, 2) AS borough_avg_response_min
  FROM base
  GROUP BY borough
),

zip_stats AS (
  SELECT
    zipcode,
    COUNT(*) AS zip_serious_incidents,
    ROUND(AVG(response_seconds) / 60, 2) AS zip_avg_response_min
  FROM base
  WHERE zipcode IS NOT NULL
  GROUP BY zipcode
  HAVING COUNT(*) >= 30
),

zip_area AS (
  SELECT
    zipcode,
    borough,
    incident_dispatch_area,
    COUNT(*) AS area_zip_incidents,
    ROW_NUMBER() OVER (PARTITION BY zipcode ORDER BY COUNT(*) DESC) = 1 AS is_primary_area
  FROM base
  WHERE zipcode IS NOT NULL
    AND incident_dispatch_area IS NOT NULL
  GROUP BY zipcode, borough, incident_dispatch_area
)

SELECT
  a.borough,
  a.incident_dispatch_area,
  a.serious_incidents,
  a.avg_response_min,
  b.borough_serious_incidents,
  b.borough_avg_response_min,

  za.zipcode,
  za.area_zip_incidents,
  za.is_primary_area,
  zs.zip_serious_incidents,
  zs.zip_avg_response_min,

  DENSE_RANK() OVER (ORDER BY b.borough_avg_response_min DESC)                  AS borough_slowest_rank,
  DENSE_RANK() OVER (PARTITION BY a.borough ORDER BY a.avg_response_min DESC)   AS dispatch_area_slowest_rank,
  DENSE_RANK() OVER (ORDER BY a.avg_response_min DESC)                          AS dispatch_area_slowest_rank_citywide

FROM area_stats a
JOIN borough_stats b ON a.borough = b.borough
LEFT JOIN zip_area za
       ON a.borough = za.borough
      AND a.incident_dispatch_area = za.incident_dispatch_area
LEFT JOIN zip_stats zs
       ON za.zipcode = zs.zipcode;

-- Question 3: Is the delay in dispatching (call to ambulance assigned) or in travel (assigned to on scene)?
CREATE OR REPLACE VIEW `desk-thanujanndayaparan.ems_dw.v_q3_dispatch_vs_travel` AS

WITH base AS (
  SELECT
    l.borough,
    l.incident_dispatch_area,
    f.dispatch_seconds,
    f.travel_seconds
  FROM `desk-thanujanndayaparan.ems_dw.fact_ems_incident` f
  JOIN `desk-thanujanndayaparan.ems_dw.dim_location` l ON f.location_key = l.location_key
  JOIN `desk-thanujanndayaparan.ems_dw.dim_call` c     ON f.call_type_key = c.call_type_key
  WHERE c.is_most_serious = TRUE
    AND f.response_seconds IS NOT NULL      -- valid response time only
    AND f.dispatch_seconds IS NOT NULL
    AND f.travel_seconds IS NOT NULL
    AND f.dispatch_seconds >= 0
    AND f.travel_seconds >= 0
    AND l.location_key <> -1
    AND l.borough IS NOT NULL
),

combined AS (
  SELECT 'citywide' AS level, 'All NYC' AS borough, CAST(NULL AS STRING) AS incident_dispatch_area,
         COUNT(*) AS incidents,
         AVG(dispatch_seconds) / 60 AS avg_dispatch_min,
         AVG(travel_seconds) / 60   AS avg_travel_min
  FROM base

  UNION ALL

  SELECT 'borough', borough, CAST(NULL AS STRING),
         COUNT(*), AVG(dispatch_seconds) / 60, AVG(travel_seconds) / 60
  FROM base
  GROUP BY borough

  UNION ALL

  SELECT 'dispatch_area', borough, incident_dispatch_area,
         COUNT(*), AVG(dispatch_seconds) / 60, AVG(travel_seconds) / 60
  FROM base
  WHERE incident_dispatch_area IS NOT NULL
  GROUP BY borough, incident_dispatch_area
  HAVING COUNT(*) >= 30
)

SELECT
  level,
  borough,
  incident_dispatch_area,
  incidents,
  ROUND(avg_dispatch_min, 2) AS avg_dispatch_min,
  ROUND(avg_travel_min, 2)   AS avg_travel_min,
  ROUND(avg_dispatch_min + avg_travel_min, 2) AS avg_total_min,
  ROUND(100 * SAFE_DIVIDE(avg_dispatch_min, avg_dispatch_min + avg_travel_min), 1) AS dispatch_share_pct,
  ROUND(100 * SAFE_DIVIDE(avg_travel_min,   avg_dispatch_min + avg_travel_min), 1) AS travel_share_pct
FROM combined;

-- Question 4: When are responses slowest, by hour of day and day of week?
SELECT d.day_name , t.hour, ROUND(AVG(f.response_seconds)/60, 2) as response_time_min, COUNT(f.response_seconds) AS serious_incidents
FROM `desk-thanujanndayaparan.ems_dw.fact_ems_incident` AS f
JOIN `desk-thanujanndayaparan.ems_dw.dim_date` AS d on f.date_key = d.date_key 
JOIN `desk-thanujanndayaparan.ems_dw.dim_time` AS t on f.hour_key = t.hour_key
JOIN `desk-thanujanndayaparan.ems_dw.dim_call` AS c on f.call_type_key = c.call_type_key
WHERE c.is_most_serious = TRUE
GROUP BY t.hour, d.day_name
ORDER BY response_time_min DESC

-- Question 5: Did the areas that received extra ambulance capacity improve afterwards?
-- Find the date when the simulated capacity increase begins.
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