import pandas as pd
import duckdb
import joblib 
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, roc_auc_score, average_precision_score

def train_biocascade_model():
    db_path = 'data/processed/biocascade.db'
    con = duckdb.connect(db_path)
    df = con.execute("SELECT * FROM feature_matrix_raw").df()
    
    # === COMPREHENSIVE FEATURE SET ===
    features = [
        # Demographics
        'age', 'gender',
        
        # Blood Pressure
        'systolic_bp', 'diastolic_bp', 'pulse_pressure', 'mean_arterial_pressure',
        
        # Anthropometrics
        'bmi', 'waist_cm', 'waist_height_ratio',
        
        # Glucose Metabolism
        'hba1c', 'fasting_glucose',
        
        # Lipids
        'triglycerides', 'log_triglycerides', 'hdl_cholesterol', 'ldl_cholesterol',
        'tg_hdl_ratio', 'total_hdl_ratio', 'non_hdl',
        
        # Renal
        'serum_creatinine', 'egfr', 'bun', 'bun_cr_ratio', 'uric_acid', 'log_uric_acid',
        
        # Electrolytes
        'sodium', 'potassium',
        
        # Inflammatory
        'hscrp', 'log_hscrp', 'neutrophil_lymphocyte_ratio',
        
        # Hematology
        'hemoglobin', 'hematocrit', 'rdw',
        
        # Composite Scores
        'mets_score', 'cmi',
        
        # Interactions (BioCascade!)
        'vasc_metabolic_load', 'metabolic_renal_stress'
    ]
    
    # Remove features with too much missing data
    features_to_use = [f for f in features if f in df.columns and df[f].notna().sum() > len(df) * 0.7]
    
    X = df[features_to_use]
    y = df['is_high_risk']
    
    # Handle missing data
    from sklearn.impute import SimpleImputer
    imputer = SimpleImputer(strategy='median')
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Impute
    X_train_imputed = pd.DataFrame(
        imputer.fit_transform(X_train),
        columns=X_train.columns,
        index=X_train.index
    )
    X_test_imputed = pd.DataFrame(
        imputer.transform(X_test),
        columns=X_test.columns,
        index=X_test.index
    )
    
    X_test_imputed.to_csv("data/processed/X_test.csv", index=False)
    
    # Train model
    pipeline = Pipeline([
        ('rf', RandomForestClassifier(
            n_estimators=200,  # Increased from 100
            max_depth=15,      # Allow deeper trees with more features
            min_samples_split=20,
            min_samples_leaf=10,
            random_state=42,
            class_weight='balanced',
            n_jobs=-1
        ))
    ])
    
    print(f"🧠 Training BioCascade Model with {len(features_to_use)} features...")
    print(f"   Features: {features_to_use}")
    
    pipeline.fit(X_train_imputed, y_train)
    
    y_pred = pipeline.predict(X_test_imputed)
    y_proba = pipeline.predict_proba(X_test_imputed)[:, 1]
    
    print("\n📋 Final Performance Report:")
    print(classification_report(y_test, y_pred))
    print(f"🏆 ROC-AUC Score: {roc_auc_score(y_test, y_proba):.4f}")
    print(f"📈 PR-AUC Score:  {average_precision_score(y_test, y_proba):.4f}")
    
    # Feature importance
    importances = pipeline.named_steps['rf'].feature_importances_
    feature_imp = pd.DataFrame({
        'feature': features_to_use,
        'importance': importances
    }).sort_values('importance', ascending=False)
    
    print("\n🔝 Top 10 Most Important Features:")
    print(feature_imp.head(10))
    
    joblib.dump(pipeline, "data/processed/biocascade_model.joblib")
    joblib.dump(imputer, "data/processed/imputer.joblib")  # Save imputer too!
    print("\n💾 Model and imputer saved!")
    
    con.close()

if __name__ == "__main__":
    train_biocascade_model()