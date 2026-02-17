import pandas as pd
import duckdb

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, roc_auc_score

def train_biocascade_model():
    db_path = 'data/processed/biocascade.db'
    con = duckdb.connect(db_path)

    # 1. Load our engineered features
    df = con.execute("SELECT * FROM feature_matrix_raw").df()
    
    # 2. Define Features (X) and Target (y)
    # We exclude SEQN (ID) and any 'flag' columns that would be cheating
    features = [
        'age', 
        'gender', 
        'diastolic_bp', 
        'triglycerides',
        'pulse_pressure',      
        'vasc_metabolic_load', 
        'renal_age_index',     
        'log_triglycerides'    
    ]
    X = df[features]
    y = df['is_high_risk']

    # 3. Train-Test Split (80% Study, 20% Final Exam)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # 4. Build the Leakage-Safe Pipeline
    # Scaling happens INSIDE the pipeline, safely.
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('rf', RandomForestClassifier(n_estimators=100, random_state=42))
    ])

    print("🧠 Training the BioCascade Random Forest...")
    pipeline.fit(X_train, y_train)

    # 5. Evaluation
    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    print("\n📋 Model Performance Report:")
    print(classification_report(y_test, y_pred))
    print(f"🏆 ROC-AUC Score: {roc_auc_score(y_test, y_proba):.4f}")

    # Save the model for Phase 5 (Interpretability)
    # (We'll handle saving the model file in a moment)

if __name__ == "__main__":
    train_biocascade_model()