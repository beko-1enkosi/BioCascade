CREATE TABLE IF NOT EXISTS raw_patient_data (
    SEQN INTEGER PRIMARY KEY,
    
    -- Demographics
    age INTEGER,
    gender INTEGER,
    race_ethnicity INTEGER,
    
    -- Blood Pressure
    systolic_bp DOUBLE,
    diastolic_bp DOUBLE,
    
    -- Anthropometrics
    bmi DOUBLE,
    waist_cm DOUBLE,
    height_cm DOUBLE,
    weight_kg DOUBLE,
    
    -- Glucose Metabolism
    hba1c DOUBLE,
    fasting_glucose DOUBLE,
    
    -- Lipids
    triglycerides DOUBLE,
    total_cholesterol DOUBLE,
    hdl_cholesterol DOUBLE,
    ldl_cholesterol DOUBLE,
    
    -- Renal
    serum_creatinine DOUBLE,
    bun DOUBLE,
    uric_acid DOUBLE,
    
    -- Electrolytes
    sodium DOUBLE,
    potassium DOUBLE,
    
    -- Inflammatory
    hscrp DOUBLE,
    
    -- Hematology
    hemoglobin DOUBLE,
    hematocrit DOUBLE,
    rdw DOUBLE,
    wbc_count DOUBLE,
    lymphocyte_pct DOUBLE,
    neutrophil_pct DOUBLE,
    
    -- Iron
    ferritin DOUBLE,
    serum_iron DOUBLE
);