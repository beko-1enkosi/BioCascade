import pandas as pd
import duckdb
import joblib  # Added for saving the model
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, roc_auc_score, average_precision_score

def train_biocascade_model():
    db_path = 'data/processed/biocascade.db'
    con = duckdb.connect(db_path)

    # 1. Load data
    df = con.execute("SELECT * FROM feature_matrix_raw").df()
    
    # 2. OPTION A: Pure Feature Set (No Leakage)
    # We remove all direct and indirect ingredients of the label
    features = [
        'age',
        'diastolic_bp',
        'triglycerides',
        'log_triglycerides'
    ]
    
    X = df[features]
    y = df['is_high_risk']

    # 3. Train-Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # 4. Build Pipeline
    # While RF doesn't strictly need scaling, we keep it for pipeline consistency
    pipeline = Pipeline([
        ('rf', RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced'))
    ])

    print("🧠 Training the HONEST BioCascade Model...")
    pipeline.fit(X_train, y_train)

    # 5. Advanced Evaluation
    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    print("\n📋 Final Scientific Performance Report:")
    print(classification_report(y_test, y_pred))
    print(f"🏆 ROC-AUC Score: {roc_auc_score(y_test, y_proba):.4f}")
    # Added PR-AUC for better rigor with imbalanced data
    print(f"📈 PR-AUC Score:  {average_precision_score(y_test, y_proba):.4f}")

    # 6. Save the model for Phase 5
    joblib.dump(pipeline, "data/processed/biocascade_model.joblib")
    print("\n💾 Model saved to data/processed/biocascade_model.joblib")
    
    con.close() # Clean hygiene

if __name__ == "__main__":
    train_biocascade_model()