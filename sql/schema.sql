-- This table will hold the combined data from all NHANES files

CREATE TABLE IF NOT EXISTS raw_patient_data (
    SEQN INTEGER PRIMARY KEY,        -- Unique Patient ID
    age INTEGER,                     -- Age in years
    gender INTEGER,                  -- 1 = Male, 2 = Female
    systolic_bp DOUBLE,              -- Systolic Blood Pressure (mmHg)
    diastolic_bp DOUBLE,             -- Diastolic Blood Pressure (mmHg)
    hba1c DOUBLE,                    -- Metabolic: Glycohemoglobin (%)
    triglycerides DOUBLE,            -- Metabolic: Lipids (mg/dL)
    serum_creatinine DOUBLE          -- Renal: Kidney function marker (mg/dL)
);