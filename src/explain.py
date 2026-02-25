import pandas as pd
import joblib
import shap
import matplotlib.pyplot as plt
import os

def generate_interpretability():
    """
    Generates Global and Local SHAP explanations for the BioCascade model.

    Utilizes the TreeExplainer to decompose model predictions on held-out test data.
    Produces a summary plot for global feature importance and a waterfall plot 
    for individual patient case studies.

    Outputs:
        - app/static/plots/shap_summary.png
        - app/static/plots/patient_explanation.png
    """
    
    model_path = 'data/processed/biocascade_model.joblib'
    test_data_path = 'data/processed/X_test.csv'
    output_dir = 'app/static/plots'
    os.makedirs(output_dir, exist_ok=True)

    pipeline = joblib.load(model_path)
    X_test = pd.read_csv(test_data_path)
    
    rf_model = pipeline.named_steps['rf']
    
    explainer = shap.TreeExplainer(rf_model)
    
    shap_values = explainer(X_test, check_additivity=False)

    plt.figure(figsize=(10, 6))
    shap.summary_plot(shap_values[:, :, 1], X_test, show=False)
    plt.tight_layout()
    
    summary_path = os.path.join(output_dir, 'shap_summary.png')
    plt.savefig(summary_path)
    print(f"📊 Global SHAP Summary saved to {summary_path}")

    plt.figure(figsize=(10, 6))
    shap.plots.waterfall(shap_values[0, :, 1], show=False)
    plt.tight_layout()
    
    waterfall_path = os.path.join(output_dir, 'patient_explanation.png')
    plt.savefig(waterfall_path)
    print(f"🧪 Individual Patient Waterfall Plot saved to {waterfall_path}")

if __name__ == "__main__":
    generate_interpretability()