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