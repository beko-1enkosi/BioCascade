import pandas as pd
import duckdb
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, roc_auc_score, roc_curve
import matplotlib.pyplot as plt

def train_independent_model():
    """
    Train a leakage-controlled model that excludes proxy label ingredients.
    
    This model uses ONLY independent predictors:
    - Demographics (age, gender)
    - Lipids (triglycerides, HDL, LDL, total cholesterol)
    - Anthropometrics (BMI, waist, waist/height ratio)
    - Inflammatory markers (hsCRP, neutrophil/lymphocyte ratio)
    - Hematology (hemoglobin, hematocrit, RDW)
    - Electrolytes (sodium, potassium)
    - Iron markers (ferritin)
    - Metabolic syndrome score (calculated WITHOUT BP or glucose)
    
    EXCLUDED (label ingredients):
    - systolic_bp, diastolic_bp, pulse_pressure, MAP
    - hba1c, fasting_glucose
    - serum_creatinine, eGFR, BUN, BUN/Cr ratio
    - Any interactions containing these (vasc_metabolic_load, metabolic_renal_stress)
    """
    
    db_path = 'data/processed/biocascade.db'
    con = duckdb.connect(db_path)
    df = con.execute("SELECT * FROM feature_matrix_raw").df()
    
    # === INDEPENDENT FEATURES ONLY ===
    independent_features = [
        # Demographics
        'age', 'gender',
        
        # Lipids (INDEPENDENT from label)
        'triglycerides', 'log_triglycerides',
        'hdl_cholesterol', 'ldl_cholesterol', 'total_cholesterol',
        'tg_hdl_ratio', 'total_hdl_ratio', 'non_hdl',
        
        # Anthropometrics (INDEPENDENT)
        'bmi', 'waist_cm', 'waist_height_ratio',
        
        # Inflammatory (INDEPENDENT)
        'hscrp', 'log_hscrp', 
        'neutrophil_lymphocyte_ratio',
        
        # Hematology (INDEPENDENT)
        'hemoglobin', 'hematocrit', 'rdw',
        
        # Electrolytes (INDEPENDENT)
        'sodium', 'potassium',
        
        # Iron (INDEPENDENT)
        'ferritin', 'serum_iron',
        
        # Uric acid (INDEPENDENT)
        'uric_acid', 'log_uric_acid',
        
        # Modified metabolic syndrome score
        # (calculated without BP and glucose components)
        # We'll need to create this in features.py
    ]
    
    # Filter to features that exist and have enough data
    features_to_use = [f for f in independent_features 
                      if f in df.columns and df[f].notna().sum() > len(df) * 0.5]
    
    print(f"🧪 Training LEAKAGE-CONTROLLED Model")
    print(f"   Using {len(features_to_use)} INDEPENDENT features")
    print(f"   EXCLUDED: BP, glucose, creatinine, and their derivatives")
    print(f"\n   Features: {features_to_use}\n")
    
    X = df[features_to_use]
    y = df['is_high_risk']
    
    # Imputation
    imputer = SimpleImputer(strategy='median')
    
    # Split
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
    
    # Train
    pipeline = Pipeline([
        ('rf', RandomForestClassifier(
            n_estimators=200,
            max_depth=12,
            min_samples_split=20,
            random_state=42,
            class_weight='balanced',
            n_jobs=-1
        ))
    ])
    
    print("🧠 Training Independent Model...")
    pipeline.fit(X_train_imputed, y_train)
    
    # Evaluate
    y_pred = pipeline.predict(X_test_imputed)
    y_proba = pipeline.predict_proba(X_test_imputed)[:, 1]
    
    print("\n📋 LEAKAGE-CONTROLLED Model Performance:")
    print(classification_report(y_test, y_pred))
    
    roc_auc = roc_auc_score(y_test, y_proba)
    print(f"🏆 ROC-AUC Score: {roc_auc:.4f}")
    
    # Feature importance
    importances = pipeline.named_steps['rf'].feature_importances_
    feature_imp = pd.DataFrame({
        'feature': features_to_use,
        'importance': importances
    }).sort_values('importance', ascending=False)
    
    print("\n🔝 Top 10 Independent Predictors:")
    print(feature_imp.head(10))
    
    # Plot ROC curves comparing both models
    plt.figure(figsize=(10, 6))
    
    # Plot independent model
    fpr, tpr, _ = roc_curve(y_test, y_proba)
    plt.plot(fpr, tpr, label=f'Independent Model (AUC = {roc_auc:.3f})', linewidth=2)
    
    # Plot reference line
    plt.plot([0, 1], [0, 1], 'k--', label='Random Chance (AUC = 0.50)')
    
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate', fontsize=12)
    plt.ylabel('True Positive Rate', fontsize=12)
    plt.title('ROC Curve: Leakage-Controlled Model', fontsize=14)
    plt.legend(loc="lower right", fontsize=11)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig('app/static/plots/roc_independent.png', dpi=300)
    print("\n📊 ROC curve saved to app/static/plots/roc_independent.png")
    
    # Save model
    joblib.dump(pipeline, "data/processed/biocascade_model_independent.joblib")
    joblib.dump(imputer, "data/processed/imputer_independent.joblib")
    print("\n💾 Independent model saved!")
    
    con.close()
    
    return roc_auc

if __name__ == "__main__":
    train_independent_model()