import pandas as pd
import duckdb
import numpy as np

def engineer_features():
    """
    Performs biologically-motivated feature engineering on patient biomarkers.

    This function extracts labeled patient data from DuckDB and constructs 
    new physiological indicators including vascular stiffness proxies, 
    metabolic load interactions, and renal stress indices. The resulting 
    feature matrix is stored back to DuckDB for modeling.

    Features Created:
        - pulse_pressure: SBP - DBP (Proxy for arterial stiffness).
        - vasc_metabolic_load: SBP * HbA1c (Synergistic vascular-glucose stress).
        - renal_age_index: Creatinine / (Age + 1) (Age-adjusted renal stress).
        - log_triglycerides: log1p transformation of triglycerides (Handles skewness).
    """

    db_path = 'data/processed/biocascade.db'
    con = duckdb.connect(db_path)

    df = con.execute("SELECT * FROM labeled_patients").df()
    print(f"📈 Engineering features for {len(df)} patients...")

    df['pulse_pressure'] = df['systolic_bp'] - df['diastolic_bp']
    
    df['vasc_metabolic_load'] = df['systolic_bp'] * df['hba1c']
    
    df['renal_age_index'] = df['serum_creatinine'] / (df['age'] + 1)
    
    df['log_triglycerides'] = np.log1p(df['triglycerides'])

    con.execute("DROP TABLE IF EXISTS feature_matrix_raw")
    con.register('df_final', df)
    con.execute("CREATE TABLE feature_matrix_raw AS SELECT * FROM df_final")
    
    print("✅ Raw Feature Matrix created.")
    print("📊 Pulse Pressure added as a proxy for vascular stiffness.")

if __name__ == "__main__":
    engineer_features()