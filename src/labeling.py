import duckdb

def label_data():
    db_path = 'data/processed/biocascade.db'
    con = duckdb.connect(db_path)

    print("🩺 Step 1: Running Clinical Labeling Logic...")
    
    # Read and execute the SQL file we just created
    with open('sql/label_definition.sql', 'r') as f:
        con.execute(f.read())

    # Step 2: Get a summary of the results
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