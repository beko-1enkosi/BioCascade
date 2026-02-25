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