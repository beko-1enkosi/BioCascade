import pandas as pd
import duckdb
import os

def load_to_duckdb():
    db_path = 'data/processed/biocascade.db'
    con = duckdb.connect(db_path)
    
    print("🔨 Step 1: Building the database tables from schema...")
    # We use a 'DROP TABLE' first to ensure we don't get Primary Key errors on re-run
    con.execute("DROP TABLE IF EXISTS raw_patient_data")
    with open('sql/schema.sql', 'r') as f:
        con.execute(f.read())

    print("🧬 Step 2: Loading NHANES CSV files into memory...")
    df_demo = pd.read_csv('data/raw/demographics.csv')
    df_exam = pd.read_csv('data/raw/examination.csv')
    df_lab = pd.read_csv('data/raw/laboratory.csv')

    # YOUR FIX: Check for duplicates before joining
    print(f"🔍 Integrity Check - Duplicates found:")
    print(f"   Demographics: {df_demo['SEQN'].duplicated().sum()}")
    print(f"   Examination:  {df_exam['SEQN'].duplicated().sum()}")
    print(f"   Laboratory:   {df_lab['SEQN'].duplicated().sum()}")

    # If there were duplicates, we would add: df_demo = df_demo.drop_duplicates(subset='SEQN') here.

    print("🔗 Step 3: Joining patient fragments using SQL...")
    join_query = """
    INSERT INTO raw_patient_data
    SELECT 
        d.SEQN,
        d.RIDAGEYR as age,
        d.RIAGENDR as gender,
        e.BPXSY1 as systolic_bp,
        e.BPXDI1 as diastolic_bp,
        l.LBXGH as hba1c,
        l.LBXSTR as triglycerides,
        l.LBXSCK as serum_creatinine
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