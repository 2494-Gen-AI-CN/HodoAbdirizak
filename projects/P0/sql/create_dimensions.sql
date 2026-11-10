CREATE OR REPLACE TABLE `desk-thanujanndayaparan.ems_dw.dim_date`
 AS (
    WITH date_range AS (
        SELECT
            DATE(MIN(PARSE_DATETIME('%m/%d/%Y %I:%M:%S %p', INCIDENT_DATETIME))) AS start_date,
            DATE(MAX(PARSE_DATETIME('%m/%d/%Y %I:%M:%S %p', INCIDENT_DATETIME))) AS end_date
        FROM `desk-thanujanndayaparan.ems_raw.ems_incidents`
    )
    SELECT 
        CAST(FORMAT_DATE('%Y%m%d', full_date) AS INT64) AS date_key,
        full_date,
        EXTRACT (YEAR FROM full_date) AS year,
        EXTRACT (QUARTER FROM full_date) AS quarter,
        EXTRACT (MONTH FROM full_date) AS month_num,
        FORMAT_DATE('%B', full_date) AS month_name,
        EXTRACT (DAY FROM full_date) AS day_of_month,
        FORMAT_DATE('%A', full_date) AS day_name,
        EXTRACT(DAYOFWEEK FROM full_date) IN (1, 7) AS is_weekend        
    FROM date_range,
    UNNEST(GENERATE_DATE_ARRAY(start_date, end_date)) AS full_date
);
ALTER TABLE ems_dw.dim_date
ADD PRIMARY KEY (date_key) NOT ENFORCED;

CREATE OR REPLACE TABLE `desk-thanujanndayaparan.ems_dw.dim_time` AS (
    SELECT 
        hour AS hour_key,
        hour ,
        CASE 
            WHEN hour BETWEEN 0 AND 5 THEN 'Night'
            WHEN hour BETWEEN 6 AND 11 THEN 'Morning'
            WHEN hour BETWEEN 12 AND 17 THEN 'Afternoon'
            WHEN hour BETWEEN 18 AND 23 THEN 'Evening'
        END AS time_bucket
    FROM UNNEST(GENERATE_ARRAY(0,23)) AS hour
);
ALTER TABLE ems_dw.dim_time
ADD PRIMARY KEY (hour_key) NOT ENFORCED;

CREATE OR REPLACE TABLE `desk-thanujanndayaparan.ems_dw.dim_call` (
    call_type_key INT64,
    initial_call_type STRING,
    initial_severity_level_code INT64,
    final_call_type STRING,
    final_severity_level_code INT64,
    is_most_serious BOOL,
    PRIMARY KEY (call_type_key) NOT ENFORCED
);

CREATE OR REPLACE TABLE `desk-thanujanndayaparan.ems_dw.dim_location` (
    location_key INT64,
    borough STRING,
    incident_dispatch_area STRING,
    PRIMARY KEY (location_key) NOT ENFORCED
);

CREATE OR REPLACE TABLE `desk-thanujanndayaparan.ems_dw.dim_dispatch_area_capacity` (
    capacity_key INT64,
    location_key INT64,
    incident_dispatch_area STRING,
    ambulance_tours INT64,
    effective_from DATE,
    effective_to DATE,
    is_current BOOL,
    pilot_flag BOOL,
    PRIMARY KEY (capacity_key) NOT ENFORCED
);
