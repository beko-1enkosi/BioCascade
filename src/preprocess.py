import pandas as pd
import duckdb
import os

def load_to_duckdb():
    # 1. Define paths
    db_path = 'data/processed/biocascade.db'
    
    # 2. Connect to DuckDB (it will create the file if it doesn't exist)
    con = duckdb.connect(db_path)
    
    print("🔨 Step 1: Building the database tables from schema...")
    # This reads your sql/schema.sql file to create the table
    with open('sql/schema.sql', 'r') as f:
        con.execute(f.read())

    print("🧬 Step 2: Loading Kaggle CSV files into memory...")
    # We use Pandas because it's the gold standard for reading CSVs
    # Make sure these files are in your data/raw/ folder!
    df_demo = pd.read_csv('data/raw/demographics.csv')
    df_exam = pd.read_csv('data/raw/examination.csv')
    df_lab = pd.read_csv('data/raw/laboratory.csv')

    print("🔗 Step 3: Joining patient fragments using SQL...")
    # DuckDB will look at the DataFrames in your RAM and join them
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
    print(f"✅ Success! BioCascade DB is ready with {count} adult patients.")

if __name__ == "__main__":
    load_to_duckdb()