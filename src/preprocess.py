import pandas as pd
import duckdb
import os

def load_to_duckdb():
    """
    Ingests raw NHANES CSV data into a structured DuckDB relational database.

    This function performs the initial ETL (Extract, Transform, Load) process:
    1. Initializes the database schema.
    2. Loads Demographic, Examination, and Laboratory CSV files.
    3. Performs an integrity check for duplicate patient identifiers (SEQN).
    4. Executes a SQL-based join to unify patient fragments.
    5. Filters for adult participants (Age >= 18) to ensure clinical relevance.
    """

    db_path = 'data/processed/biocascade.db'
    con = duckdb.connect(db_path)
    
    print("🔨 Step 1: Building the database tables from schema...")

    con.execute("DROP TABLE IF EXISTS raw_patient_data")
    with open('sql/schema.sql', 'r') as f:
        con.execute(f.read())

    print("🧬 Step 2: Loading NHANES CSV files into memory...")
    df_demo = pd.read_csv('data/raw/demographics.csv')
    df_exam = pd.read_csv('data/raw/examination.csv')
    df_lab = pd.read_csv('data/raw/laboratory.csv')

    print(f"🔍 Integrity Check - Duplicates found:")
    print(f"   Demographics: {df_demo['SEQN'].duplicated().sum()}")
    print(f"   Examination:  {df_exam['SEQN'].duplicated().sum()}")
    print(f"   Laboratory:   {df_lab['SEQN'].duplicated().sum()}")


    print("🔗 Step 3: Joining patient fragments using SQL...")
    # EXPANDED QUERY - Use 30+ features instead of 7
    join_query = """
    INSERT INTO raw_patient_data
    SELECT 
        d.SEQN,
        
        -- DEMOGRAPHICS
        d.RIDAGEYR as age,
        d.RIAGENDR as gender,
        d.RIDRETH3 as race_ethnicity,
        
        -- BLOOD PRESSURE
        e.BPXSY1 as systolic_bp,
        e.BPXDI1 as diastolic_bp,
        
        -- ANTHROPOMETRICS
        e.BMXBMI as bmi,
        e.BMXWAIST as waist_cm,
        e.BMXHT as height_cm,
        e.BMXWT as weight_kg,
        
        -- GLUCOSE METABOLISM
        l.LBXGH as hba1c,
        l.LBXGLU as fasting_glucose,
        
        -- LIPIDS (CRITICAL FOR METABOLIC SYNDROME!)
        l.LBXTR as triglycerides,      
        l.LBXTC as total_cholesterol,
        l.LBDHDD as hdl_cholesterol,   
        l.LBDLDL as ldl_cholesterol,
        
        -- RENAL FUNCTION
        l.LBXSCR as serum_creatinine,
        l.LBXSBU as bun,
        l.LBXSUA as uric_acid,
        
        -- ELECTROLYTES
        l.LBXSNASI as sodium,
        l.LBXSKSI as potassium,
        
        -- INFLAMMATORY MARKERS
        l.LBXHSCRP as hscrp,
        
        -- HEMATOLOGY
        l.LBXHGB as hemoglobin,
        l.LBXHCT as hematocrit,
        l.LBXRDW as rdw,
        l.LBXWBCSI as wbc_count,
        l.LBXLYPCT as lymphocyte_pct,
        l.LBXNEPCT as neutrophil_pct,
        
        -- IRON
        l.LBXFER as ferritin,
        l.LBXIRN as serum_iron
        
    FROM df_demo d
    JOIN df_exam e ON d.SEQN = e.SEQN
    JOIN df_lab l ON d.SEQN = l.SEQN
    WHERE d.RIDAGEYR >= 18;
    """
    
    con.execute(join_query)
    count = con.execute("SELECT count(*) FROM raw_patient_data").fetchone()[0]
    print(f"✅ Success! BioCascade DB updated with {count} adult patients.")

if __name__ == "__main__":
    load_to_duckdb()