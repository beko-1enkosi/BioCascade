-- Step 1: Drop if exists to allow re-runs
DROP TABLE IF EXISTS labeled_patients;

-- Step 2: Create a table where we calculate the 'Risk Score'
CREATE TABLE labeled_patients AS
SELECT 
    *,
    -- Calculate how many 'Red Flags' a patient has
    (
        (systolic_bp > 140)::INT + 
        (hba1c > 6.5)::INT + 
        (serum_creatinine > 1.2)::INT
    ) as risk_factor_count,
    
    -- If they have 2 or more flags, they are 'High Risk' (Target = 1)
    CASE 
        WHEN (
            (systolic_bp > 140)::INT + 
            (hba1c > 6.5)::INT + 
            (serum_creatinine > 1.2)::INT
        ) >= 2 THEN 1 
        ELSE 0 
    END as is_high_risk
FROM raw_patient_data
-- We only label patients who have all three readings (Quality Control)
WHERE systolic_bp IS NOT NULL 
  AND hba1c IS NOT NULL 
  AND serum_creatinine IS NOT NULL;