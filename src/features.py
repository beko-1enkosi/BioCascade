import pandas as pd
import duckdb
import numpy as np

def engineer_features():
    db_path = 'data/processed/biocascade.db'
    con = duckdb.connect(db_path)
    df = con.execute("SELECT * FROM labeled_patients").df()
    
    print(f"📈 Engineering features for {len(df)} patients...")
    
    # === METABOLIC SYNDROME MARKERS ===
    df['tg_hdl_ratio'] = df['triglycerides'] / df['hdl_cholesterol']
    df['total_hdl_ratio'] = df['total_cholesterol'] / df['hdl_cholesterol']
    df['non_hdl'] = df['total_cholesterol'] - df['hdl_cholesterol']
    df['waist_height_ratio'] = df['waist_cm'] / df['height_cm']
    
    # Cardiometabolic Index
    df['cmi'] = (df['triglycerides'] / df['hdl_cholesterol']) * df['waist_height_ratio']
    
    # === RENAL FUNCTION ===
    # Proper eGFR calculation (CKD-EPI formula simplified)
    def calculate_egfr(row):
        cr = row['serum_creatinine']
        age = row['age']
        is_female = (row['gender'] == 2)
        
        if pd.isna(cr) or pd.isna(age):
            return np.nan
            
        # Simplified CKD-EPI
        k = 0.7 if is_female else 0.9
        a = -0.329 if is_female else -0.411
        female_factor = 1.018 if is_female else 1.0
        
        egfr = 141 * min(cr/k, 1)**a * max(cr/k, 1)**(-1.209) * 0.993**age * female_factor
        return egfr
    
    df['egfr'] = df.apply(calculate_egfr, axis=1)
    df['bun_cr_ratio'] = df['bun'] / df['serum_creatinine']
    
    # === BLOOD PRESSURE DERIVATIVES ===
    df['pulse_pressure'] = df['systolic_bp'] - df['diastolic_bp']
    df['mean_arterial_pressure'] = df['diastolic_bp'] + (df['pulse_pressure'] / 3)
    
    # === INTERACTIONS (Your BioCascade Concept!) ===
    df['vasc_metabolic_load'] = df['systolic_bp'] * df['hba1c']
    df['metabolic_renal_stress'] = df['hba1c'] * (1 / (df['egfr'] + 1))
    
    # === INFLAMMATORY ===
    df['neutrophil_lymphocyte_ratio'] = df['neutrophil_pct'] / df['lymphocyte_pct']
    df['log_hscrp'] = np.log1p(df['hscrp'])
    
    # === METABOLIC SYNDROME SCORE (ATP III Criteria) ===
    def calc_mets_score(row):
        score = 0
        # Waist (gender-specific)
        if row['gender'] == 1 and row['waist_cm'] > 102:
            score += 1
        elif row['gender'] == 2 and row['waist_cm'] > 88:
            score += 1
        # Triglycerides
        if row['triglycerides'] >= 150:
            score += 1
        # HDL (gender-specific)
        if row['gender'] == 1 and row['hdl_cholesterol'] < 40:
            score += 1
        elif row['gender'] == 2 and row['hdl_cholesterol'] < 50:
            score += 1
        # Blood Pressure
        if row['systolic_bp'] >= 130 or row['diastolic_bp'] >= 85:
            score += 1
        # Glucose
        if row['fasting_glucose'] >= 100:
            score += 1
        return score
    
    df['mets_score'] = df.apply(calc_mets_score, axis=1)
    
    # === LOG TRANSFORMS FOR SKEWED DATA ===
    df['log_triglycerides'] = np.log1p(df['triglycerides'])
    df['log_uric_acid'] = np.log1p(df['uric_acid'])
    
    # Save to database
    con.execute("DROP TABLE IF EXISTS feature_matrix_raw")
    con.register('df_final', df)
    con.execute("CREATE TABLE feature_matrix_raw AS SELECT * FROM df_final")
    
    print(f"✅ Enhanced Feature Matrix created with {len(df.columns)} total columns!")

if __name__ == "__main__":
    engineer_features()