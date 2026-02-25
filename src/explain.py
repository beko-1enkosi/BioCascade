import pandas as pd
import duckdb
import joblib
import shap
import matplotlib.pyplot as plt
import os

def generate_interpretability():
    db_path = 'data/processed/biocascade.db'
    model_path = 'data/processed/biocascade_model.joblib'
    output_dir = 'app/static/plots'
    os.makedirs(output_dir, exist_ok=True)

    con = duckdb.connect(db_path)
    df = con.execute("SELECT * FROM feature_matrix_raw").df()
    pipeline = joblib.load(model_path)
    
    # EXACT features used in model.py
    features = ['age', 'diastolic_bp', 'triglycerides', 'log_triglycerides']
    X = df[features]
    
    # Get the actual model from the pipeline
    rf_model = pipeline.named_steps['rf']
    
    # Initialize Explainer
    explainer = shap.TreeExplainer(rf_model)
    
    # Calculate SHAP values
    # check_additivity=False helps bypass minor floating point math errors
    shap_values = explainer.shap_values(X, check_additivity=False)

    plt.figure(figsize=(10, 6))

    # LOGIC FIX:
    # Random Forest returns a list: [shap_for_class_0, shap_for_class_1]
    # We want class 1 (High Risk)
    if isinstance(shap_values, list):
        # This is for older SHAP versions
        target_shap_values = shap_values[1]
    elif len(shap_values.shape) == 3:
        # This is for newer SHAP versions [samples, features, classes]
        target_shap_values = shap_values[:, :, 1]
    else:
        target_shap_values = shap_values

    # Final plot call
    shap.summary_plot(target_shap_values, X, show=False)
    
    plt.tight_layout()
    plot_path = os.path.join(output_dir, 'shap_summary.png')
    plt.savefig(plot_path)
    print(f"📊 SHAP Summary Plot successfully saved to {plot_path}")
    
    con.close()
    
if __name__ == "__main__":
    generate_interpretability()