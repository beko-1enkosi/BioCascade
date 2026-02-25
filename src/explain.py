import pandas as pd
import joblib
import shap
import matplotlib.pyplot as plt
import os

def generate_interpretability():
    # 1. Setup paths
    model_path = 'data/processed/biocascade_model.joblib'
    test_data_path = 'data/processed/X_test.csv'
    output_dir = 'app/static/plots'
    os.makedirs(output_dir, exist_ok=True)

    # 2. Load Model and HELD-OUT Test Data
    # Using X_test ensures we are explaining generalization, not memorization
    pipeline = joblib.load(model_path)
    X_test = pd.read_csv(test_data_path)
    
    # Extract the Random Forest from the pipeline
    rf_model = pipeline.named_steps['rf']
    
    # 3. Initialize SHAP TreeExplainer
    # We use the TreeExplainer optimized for ensemble tree models
    explainer = shap.TreeExplainer(rf_model)
    
    # Calculate SHAP values for the test set
    # check_additivity=False handles minor rounding differences in tree math
    shap_values = explainer(X_test, check_additivity=False)

    # 4. Generate Summary Plot (The Global View)
    # This shows the importance ranking of all independent features
    plt.figure(figsize=(10, 6))
    # We slice for [:, :, 1] to get the impact on the "High Risk" class
    shap.summary_plot(shap_values[:, :, 1], X_test, show=False)
    plt.tight_layout()
    
    summary_path = os.path.join(output_dir, 'shap_summary.png')
    plt.savefig(summary_path)
    print(f"📊 Global SHAP Summary saved to {summary_path}")

    # 5. Generate Waterfall Plot (The Individual View)
    # This explains why a SPECIFIC patient was flagged as high risk
    plt.figure(figsize=(10, 6))
    # Let's explain the first patient in the test set (index 0)
    shap.plots.waterfall(shap_values[0, :, 1], show=False)
    plt.tight_layout()
    
    waterfall_path = os.path.join(output_dir, 'patient_explanation.png')
    plt.savefig(waterfall_path)
    print(f"🧪 Individual Patient Waterfall Plot saved to {waterfall_path}")

if __name__ == "__main__":
    generate_interpretability()