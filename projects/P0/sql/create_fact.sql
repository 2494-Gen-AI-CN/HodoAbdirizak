CREATE OR REPLACE TABLE `desk-thanujanndayaparan.ems_dw.fact_ems_incident` (
  incident_id STRING NOT NULL,
  incident_datetime TIMESTAMP,
  incident_date DATE,
  date_key INT64,
  hour_key INT64,
  location_key INT64,
  call_type_key INT64,
  capacity_key INT64,
  dispatch_seconds INT64,
  travel_seconds FLOAT64,
  response_seconds FLOAT64,
  held_indicator STRING,
  dispatch_share_of_response FLOAT64,
  PRIMARY KEY (incident_id) NOT ENFORCED,
  FOREIGN KEY (date_key) REFERENCES `desk-thanujanndayaparan.ems_dw.dim_date` (date_key) NOT ENFORCED,
  FOREIGN KEY (hour_key) REFERENCES `desk-thanujanndayaparan.ems_dw.dim_time` (hour_key) NOT ENFORCED,
  FOREIGN KEY (location_key) REFERENCES `desk-thanujanndayaparan.ems_dw.dim_location` (location_key) NOT ENFORCED,
  FOREIGN KEY (call_type_key) REFERENCES `desk-thanujanndayaparan.ems_dw.dim_call` (call_type_key) NOT ENFORCED,
  FOREIGN KEY (capacity_key) REFERENCES `desk-thanujanndayaparan.ems_dw.dim_dispatch_area_capacity` (capacity_key) NOT ENFORCED
) AS
WITH cleaned AS (
  SELECT
    incident_id,
    SAFE.PARSE_TIMESTAMP('%m/%d/%Y %I:%M:%S %p', incident_datetime) AS incident_datetime,
    borough,
    incident_dispatch_area,
    initial_call_type,
    SAFE_CAST(initial_severity_level_code AS INT64) AS initial_severity_level_code,
    final_call_type,
    SAFE_CAST(final_severity_level_code AS INT64) AS final_severity_level_code,
    SAFE_CAST(dispatch_response_seconds_qy AS INT64) AS dispatch_seconds,
    SAFE_CAST(incident_travel_tm_seconds_qy AS FLOAT64) AS travel_seconds,
    IF(valid_incident_rspns_time_indc = 'Y',
       SAFE_CAST(incident_response_seconds_qy AS FLOAT64), NULL) AS response_seconds,
    held_indicator
  FROM `desk-thanujanndayaparan.ems_dw.ems_incidents_clean`
),
dated AS (
  SELECT *,
    DATE(incident_datetime) AS incident_date,
    EXTRACT(HOUR FROM incident_datetime) AS incident_hour
  FROM cleaned
)
SELECT
  d.incident_id,
  d.incident_datetime,
  d.incident_date,
  CAST(FORMAT_DATE('%Y%m%d', d.incident_date) AS INT64) AS date_key,
  d.incident_hour AS hour_key,
  COALESCE(loc.location_key, -1) AS location_key,
  COALESCE(call.call_type_key, -1) AS call_type_key,
  cap.capacity_key,
  d.dispatch_seconds,
  d.travel_seconds,
  d.response_seconds,
  d.held_indicator,
  SAFE_DIVIDE(d.dispatch_seconds, d.response_seconds) AS dispatch_share_of_response
FROM dated AS d
LEFT JOIN `desk-thanujanndayaparan.ems_dw.dim_location` AS loc
  ON d.borough = loc.borough
 AND d.incident_dispatch_area = loc.incident_dispatch_area
LEFT JOIN `desk-thanujanndayaparan.ems_dw.dim_call` AS call
  ON d.initial_call_type IS NOT DISTINCT FROM call.initial_call_type
 AND d.initial_severity_level_code IS NOT DISTINCT FROM SAFE_CAST(call.initial_severity_level_code AS INT64)
 AND d.final_call_type IS NOT DISTINCT FROM call.final_call_type
 AND d.final_severity_level_code IS NOT DISTINCT FROM SAFE_CAST(call.final_severity_level_code AS INT64)
LEFT JOIN `desk-thanujanndayaparan.ems_dw.dim_dispatch_area_capacity` AS cap
  ON loc.location_key = cap.location_key
 AND d.incident_date >= cap.effective_from
 AND (d.incident_date <= cap.effective_to OR cap.effective_to IS NULL);

-- Verify row counts match
-- SELECT
--   (SELECT COUNT(*) FROM `desk-thanujanndayaparan.ems_dw.ems_incidents_clean`) AS clean_rows,
--   COUNT(*) AS fact_rows,
--   COUNTIF(incident_datetime IS NULL) AS bad_dates,
--   COUNTIF(location_key = -1) AS unknown_locations,
--   COUNTIF(call_type_key = -1) AS unknown_calls,
--   COUNTIF(capacity_key IS NULL) AS no_capacity
-- FROM `desk-thanujanndayaparan.ems_dw.fact_ems_incident`;