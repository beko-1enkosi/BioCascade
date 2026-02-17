-- sql/label_definition.sql
DROP TABLE IF EXISTS labeled_patients;

-- We use a Common Table Expression (CTE) to calculate flags separately
-- This is cleaner and more professional
CREATE TABLE labeled_patients AS
WITH flag_calculation AS (
  SELECT
    *,
    (systolic_bp > 140)::INT AS bp_flag,
    (hba1c >= 6.5)::INT AS a1c_flag,
    (
      CASE
        WHEN gender = 1 AND serum_creatinine > 1.3 THEN 1
        WHEN gender = 2 AND serum_creatinine > 1.1 THEN 1
        ELSE 0
      END
    ) AS renal_flag
  FROM raw_patient_data
  WHERE systolic_bp IS NOT NULL
    AND hba1c IS NOT NULL
    AND serum_creatinine IS NOT NULL
)
SELECT
  *,
  (bp_flag + a1c_flag + renal_flag) AS risk_factor_count,
  -- The Proxy Target: ≥2 indicates systemic BioCascade risk
  CASE 
    WHEN (bp_flag + a1c_flag + renal_flag) >= 2 THEN 1 
    ELSE 0 
  END AS is_high_risk
FROM flag_calculation;