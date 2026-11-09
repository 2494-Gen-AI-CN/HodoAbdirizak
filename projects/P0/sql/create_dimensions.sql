DECLARE data_start DATE;
DECLARE data_end DATE;
DECLARE pilot_start DATE;

SET data_start  = (SELECT MIN(DATE(PARSE_TIMESTAMP('%m/%d/%Y %I:%M:%S %p', incident_datetime))) FROM `desk-thanujanndayaparan.ems_dw.ems_incidents_clean`);
SET data_end    = (SELECT MAX(DATE(PARSE_TIMESTAMP('%m/%d/%Y %I:%M:%S %p', incident_datetime))) FROM `desk-thanujanndayaparan.ems_dw.ems_incidents_clean`);
SET pilot_start = DATE_ADD(data_start, INTERVAL DIV(DATE_DIFF(data_end, data_start, DAY), 2) DAY);

CREATE OR REPLACE TABLE `desk-thanujanndayaparan.ems_dw.dim_date` (
    date_key INT64,
    full_date DATE,
    year INT64,
    quarter INT64,
    month_num INT64,
    month_name STRING,
    day_of_month INT64,
    day_name STRING,
    is_weekend BOOL,
    PRIMARY KEY (date_key) NOT ENFORCED
);

CREATE OR REPLACE TABLE `desk-thanujanndayaparan.ems_dw.dim_time` (
    hour_key INT64,
    hour INT64,
    time_bucket STRING,
    PRIMARY KEY (hour_key) NOT ENFORCED
);

CREATE OR REPLACE TABLE `desk-thanujanndayaparan.ems_dw.dim_call` (
    call_type_key INT64,
    initial_call_type STRING,
    initial_severity_level_code INT64,
    final_call_type STRING,
    final_severity_level_code INT64,
    is_most_serious BOOL,
    PRIMARY KEY (call_type_key) NOT ENFORCED
);

-- Location table

CREATE OR REPLACE TABLE `desk-thanujanndayaparan.ems_dw.dim_location` (
    location_key INT64 NOT NULL,
    borough STRING,
    incident_dispatch_area STRING,
    PRIMARY KEY (location_key) NOT ENFORCED
) AS
SELECT
    -1 AS location_key,
    'UNKNOWN' AS borough,
    'UNKNOWN' AS incident_dispatch_area
UNION ALL
SELECT
    ROW_NUMBER() OVER (ORDER BY borough, incident_dispatch_area) AS location_key,
    borough,
    incident_dispatch_area
FROM (
    SELECT DISTINCT
    borough,
    incident_dispatch_area
    FROM `desk-thanujanndayaparan.ems_dw.ems_incidents_clean`
);

-- Helper table to measure each area before the pilot
CREATE OR REPLACE TABLE `desk-thanujanndayaparan.ems_dw.area_before_pilot` AS
SELECT
  d.location_key,
  d.incident_dispatch_area,
  COUNT(*) AS total_incidents,
  AVG(SAFE_CAST(c.incident_response_seconds_qy AS FLOAT64)) AS avg_response_sec  -- FIX
FROM `desk-thanujanndayaparan.ems_dw.ems_incidents_clean` AS c
JOIN `desk-thanujanndayaparan.ems_dw.dim_location` AS d
  ON c.borough = d.borough
 AND c.incident_dispatch_area = d.incident_dispatch_area
WHERE DATE(PARSE_TIMESTAMP('%m/%d/%Y %I:%M:%S %p', c.incident_datetime)) < pilot_start
  AND c.valid_incident_rspns_time_indc = 'Y'
GROUP BY d.location_key, d.incident_dispatch_area;

-- Capacity table

CREATE OR REPLACE TABLE `desk-thanujanndayaparan.ems_dw.dim_dispatch_area_capacity` (
  capacity_key INT64 NOT NULL,
  location_key INT64,
  incident_dispatch_area STRING,
  ambulance_tours INT64,
  effective_from DATE,
  effective_to DATE,
  is_current BOOL,
  pilot_flag BOOL,
  PRIMARY KEY (capacity_key) NOT ENFORCED,
  FOREIGN KEY (location_key)
    REFERENCES `desk-thanujanndayaparan.ems_dw.dim_location` (location_key) NOT ENFORCED
) AS

WITH plan AS (
  SELECT
    location_key,
    incident_dispatch_area,
    -- baseline ambulances: busier areas get more (about 3 incidents per ambulance per day)
    GREATEST(1, CAST(ROUND(total_incidents / DATE_DIFF(pilot_start, data_start, DAY) / 3) AS INT64)) AS baseline_tours,
    -- pilot areas = the slowest 20% (group 1 of 5)
    NTILE(5) OVER (ORDER BY avg_response_sec DESC) = 1 AS is_pilot
  FROM `desk-thanujanndayaparan.ems_dw.area_before_pilot`
),

history AS (
  -- Row for the "before" period (every area has this)
  SELECT
    location_key,
    incident_dispatch_area,
    baseline_tours AS ambulance_tours,
    data_start AS effective_from,
    IF(is_pilot, DATE_SUB(pilot_start, INTERVAL 1 DAY), NULL) AS effective_to,
    NOT is_pilot AS is_current,
    is_pilot AS pilot_flag
  FROM plan

  UNION ALL

  -- Extra row for pilot areas: 25% more ambulances (at least +1) from the pilot date
  SELECT
    location_key,
    incident_dispatch_area,
    baseline_tours + GREATEST(1, CAST(ROUND(baseline_tours * 0.25) AS INT64)),
    pilot_start,
    NULL,
    TRUE,
    TRUE
  FROM plan
  WHERE is_pilot
)

SELECT
  ROW_NUMBER() OVER (ORDER BY location_key, effective_from) AS capacity_key,
  *
FROM history;