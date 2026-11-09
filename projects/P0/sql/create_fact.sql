CREATE OR REPLACE TABLE `desk-thanujanndayaparan.ems_dw.fact_ems_incident` (
    incident_id STRING,
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
);