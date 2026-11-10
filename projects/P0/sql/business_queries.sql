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