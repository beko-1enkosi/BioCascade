import pandas as pd
import duckdb
import joblib 
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, roc_auc_score, average_precision_score

def train_biocascade_model():
    """
    Trains a leakage-proof Random Forest model to predict BioCascade risk.

    This function extracts engineered features from DuckDB, enforces a strict 
    feature set to prevent target leakage, trains a classifier, and serializes 
    both the model and the held-out test set for downstream evaluation.
    """

    db_path = 'data/processed/biocascade.db'
    con = duckdb.connect(db_path)

    df = con.execute("SELECT * FROM feature_matrix_raw").df()
    
    features = [
        'age',
        'diastolic_bp',
        'log_triglycerides'
    ]
    
    X = df[features]
    y = df['is_high_risk']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    X_test.to_csv("data/processed/X_test.csv", index=False)

    pipeline = Pipeline([
        ('rf', RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced'))
    ])

    print("🧠 Training the HONEST BioCascade Model...")
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    print("\n📋 Final Scientific Performance Report:")
    print(classification_report(y_test, y_pred))
    print(f"🏆 ROC-AUC Score: {roc_auc_score(y_test, y_proba):.4f}")

    print(f"📈 PR-AUC Score:  {average_precision_score(y_test, y_proba):.4f}")

    joblib.dump(pipeline, "data/processed/biocascade_model.joblib")
    print("\n💾 Model saved to data/processed/biocascade_model.joblib")
    
    con.close() 

if __name__ == "__main__":
    train_biocascade_model()