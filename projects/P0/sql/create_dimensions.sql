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
