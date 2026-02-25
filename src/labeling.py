import duckdb

def label_data():
    """
    Applies clinical proxy definitions to patients in the DuckDB database.

    This function executes the SQL-based labeling logic to categorize patients 
    into 'High Risk' (BioCascade phenotype) or 'Low Risk' based on vascular, 
    metabolic, and renal thresholds. It also outputs a distribution summary 
    of the resulting classes.

    Clinical Triad Thresholds (defined in SQL):
        - Vascular: Systolic BP > 140 mmHg
        - Metabolic: HbA1c >= 6.5%
        - Renal: Sex-aware Creatinine (M > 1.3, F > 1.1 mg/dL)
    """

    db_path = 'data/processed/biocascade.db'
    con = duckdb.connect(db_path)

    print("🩺 Step 1: Running Clinical Labeling Logic...")
    
    with open('sql/label_definition.sql', 'r') as f:
        con.execute(f.read())

    stats = con.execute("""
        SELECT 
            is_high_risk, 
            COUNT(*) as patient_count,
            ROUND(AVG(age), 1) as avg_age
        FROM labeled_patients 
        GROUP BY is_high_risk
    """).fetchall()

    print("\n📊 Phase 2 Results Summary:")
    for row in stats:
        risk_label = "🔴 High Risk" if row[0] == 1 else "🟢 Low Risk"
        print(f"   {risk_label}: {row[1]} patients (Avg Age: {row[2]})")

    print("\n✅ Labeling Complete! Data is ready for feature engineering.")

if __name__ == "__main__":
    label_data()