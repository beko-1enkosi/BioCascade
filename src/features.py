import pandas as pd
import duckdb
import numpy as np

def engineer_features():
    db_path = 'data/processed/biocascade.db'
    con = duckdb.connect(db_path)

    # 1. Load the labeled data
    df = con.execute("SELECT * FROM labeled_patients").df()
    print(f"📈 Engineering features for {len(df)} patients...")

    # 2. ADD PULSE PRESSURE (Vascular Stiffness Proxy)
    # High pulse pressure is a strong indicator of HFpEF risk
    df['pulse_pressure'] = df['systolic_bp'] - df['diastolic_bp']
    
    # 3. INTERACTION FEATURE (Vascular-Metabolic Load)
    df['vasc_metabolic_load'] = df['systolic_bp'] * df['hba1c']
    
    # 4. EXPLORATORY RENAL INDICATOR (Relative to Age)
    df['renal_age_index'] = df['serum_creatinine'] / (df['age'] + 1)
    
    # 5. LOG TRANSFORM (Handling Skewed Triglycerides)
    df['log_triglycerides'] = np.log1p(df['triglycerides'])

    # 6. SAVE RAW (No Scaling here to avoid Data Leakage!)
    con.execute("DROP TABLE IF EXISTS feature_matrix_raw")
    con.register('df_final', df)
    con.execute("CREATE TABLE feature_matrix_raw AS SELECT * FROM df_final")
    
    print("✅ Raw Feature Matrix created.")
    print("📊 Pulse Pressure added as a proxy for vascular stiffness.")

if __name__ == "__main__":
    engineer_features()