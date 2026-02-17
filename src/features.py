import pandas as pd
import duckdb
import numpy as np
from sklearn.preprocessing import StandardScaler

def engineer_features():
    db_path = 'data/processed/biocascade.db'
    con = duckdb.connect(db_path)

    # 1. Load the labeled data
    df = con.execute("SELECT * FROM labeled_patients").df()
    print(f"📈 Processing {len(df)} patients for feature engineering...")

    # 2. FEATURE ENGINEERING: Creating 'Deep' Biocascade Features
    # This prevents 'cheating' by forcing the AI to look at relationships
    
    # Vascular-Metabolic Load (Interaction)
    df['vasc_metabolic_load'] = df['systolic_bp'] * df['hba1c']
    
    # Age-Adjusted Renal Stress (Renal-Efficiency)
    # We use a small epsilon (1e-6) to avoid division by zero
    df['renal_age_index'] = df['serum_creatinine'] / (df['age'] + 1)
    
    # 3. HANDLING OUTLIERS: Log Transformation
    # Medical markers like Triglycerides often have extreme spikes
    df['log_triglycerides'] = np.log1p(df['triglycerides'])

    # 4. SCALING: Bringing all numbers to the same 'size'
    # AI struggles if one column is 0-1 and another is 0-200.
    features_to_scale = [
        'age', 'systolic_bp', 'diastolic_bp', 'hba1c', 
        'serum_creatinine', 'vasc_metabolic_load', 
        'renal_age_index', 'log_triglycerides'
    ]
    
    scaler = StandardScaler()
    df[features_to_scale] = scaler.fit_transform(df[features_to_scale])

    # 5. SAVE: Store the final matrix back to DuckDB
    con.execute("DROP TABLE IF EXISTS feature_matrix")
    con.register('df_final', df)
    con.execute("CREATE TABLE feature_matrix AS SELECT * FROM df_final")
    
    print("✅ Feature Matrix created and scaled.")
    print(f"🛠️ Engineered Features: vasc_metabolic_load, renal_age_index, log_triglycerides")

if __name__ == "__main__":
    engineer_features()