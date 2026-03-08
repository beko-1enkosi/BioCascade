from flask import Flask, render_template, request, jsonify
import joblib
import pandas as pd
import numpy as np
import shap
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# ============================================================================
# LOAD MODELS AND IMPUTERS ON STARTUP
# ============================================================================

print("🔄 Loading BioCascade models...")

try:
    # Model A (Upper Bound)
    model_a = joblib.load('../data/processed/biocascade_model_upper_bound.joblib')
    imputer_a = joblib.load('../data/processed/imputer_upper_bound.joblib')
    print("✅ Model A (Upper Bound) loaded")
    
    # Model B (Independent)
    model_b = joblib.load('../data/processed/biocascade_model_independent.joblib')
    imputer_b = joblib.load('../data/processed/imputer_independent.joblib')
    print("✅ Model B (Independent) loaded")
    
    # Create SHAP explainers
    explainer_a = shap.TreeExplainer(model_a)
    explainer_b = shap.TreeExplainer(model_b)
    print("✅ SHAP explainers created")
    
except Exception as e:
    print(f"❌ Error loading models: {e}")
    model_a = model_b = None

# ============================================================================
# FEATURE DEFINITIONS (Must match training)
# ============================================================================

MODEL_A_FEATURES = [
    'age', 'gender', 'systolic_bp', 'diastolic_bp', 'pulse_pressure', 
    'mean_arterial_pressure', 'bmi', 'waist_cm', 'waist_height_ratio',
    'hba1c', 'fasting_glucose', 'triglycerides', 'log_triglycerides',
    'hdl_cholesterol', 'ldl_cholesterol', 'total_cholesterol',
    'tg_hdl_ratio', 'total_hdl_ratio', 'non_hdl',
    'serum_creatinine', 'egfr', 'bun', 'bun_cr_ratio',
    'uric_acid', 'log_uric_acid', 'sodium', 'potassium',
    'hscrp', 'log_hscrp', 'neutrophil_lymphocyte_ratio',
    'hemoglobin', 'hematocrit', 'rdw', 'mets_score',
    'cardiometabolic_index', 'vasc_metabolic_load', 'metabolic_renal_stress'
]

MODEL_B_FEATURES = [
    'age', 'gender', 'triglycerides', 'log_triglycerides',
    'hdl_cholesterol', 'ldl_cholesterol', 'total_cholesterol',
    'tg_hdl_ratio', 'total_hdl_ratio', 'non_hdl',
    'bmi', 'waist_cm', 'waist_height_ratio',
    'hscrp', 'log_hscrp', 'neutrophil_lymphocyte_ratio',
    'hemoglobin', 'hematocrit', 'rdw',
    'sodium', 'potassium', 'ferritin', 'serum_iron',
    'uric_acid', 'log_uric_acid', 'cardiometabolic_index'
]

# ============================================================================
# ROUTES
# ============================================================================

@app.route("/")
def dashboard():
    """Landing page"""
    return render_template("dashboard.html")


@app.route("/screening-tool")
def screening_tool():
    """Screening tool interface"""
    return render_template("screening_tool.html")


@app.route("/predict", methods=["POST"])
def predict():
    """Handle prediction requests"""
    try:
        data = request.json
        model_choice = data.get('model', 'B')  # Default to Model B (Independent)
        
        # Extract and engineer features
        features = engineer_features(data)
        
        # Select model and features
        if model_choice == 'A':
            model = model_a
            imputer = imputer_a
            explainer = explainer_a
            feature_list = MODEL_A_FEATURES
        else:
            model = model_b
            imputer = imputer_b
            explainer = explainer_b
            feature_list = MODEL_B_FEATURES
        
        # Create feature dataframe
        X = pd.DataFrame([features])
        X = X.reindex(columns=feature_list, fill_value=np.nan)
        
        # Impute missing values
        X_imputed = pd.DataFrame(
            imputer.transform(X),
            columns=feature_list
        )
        
        # Make prediction
        risk_proba = model.predict_proba(X_imputed)[0, 1]
        risk_class = "High Risk" if risk_proba > 0.5 else "Low Risk"
        
        # Generate SHAP explanation
        shap_values = explainer(X_imputed)
        shap_data = generate_shap_plot(shap_values, X_imputed, risk_proba)
        
        # Get top contributing features
        shap_importance = get_top_features(shap_values, X_imputed, top_n=5)
        
        return jsonify({
            'success': True,
            'risk_score': float(risk_proba),
            'risk_class': risk_class,
            'model_used': f"Model {'A (Upper Bound)' if model_choice == 'A' else 'B (Independent)'}",
            'shap_plot': shap_data,
            'top_features': shap_importance
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def engineer_features(raw_data):
    """Engineer features from raw input data"""
    features = {}
    
    # Demographics
    features['age'] = float(raw_data.get('age', 50))
    features['gender'] = int(raw_data.get('gender', 1))  # 1=M, 2=F
    
    # Blood Pressure
    sbp = float(raw_data.get('systolic_bp', 120))
    dbp = float(raw_data.get('diastolic_bp', 80))
    features['systolic_bp'] = sbp
    features['diastolic_bp'] = dbp
    features['pulse_pressure'] = sbp - dbp
    features['mean_arterial_pressure'] = dbp + (features['pulse_pressure'] / 3)
    
    # Anthropometrics
    waist = float(raw_data.get('waist_cm', 90))
    height = float(raw_data.get('height_cm', 170))
    features['bmi'] = float(raw_data.get('bmi', 25))
    features['waist_cm'] = waist
    features['height_cm'] = height
    features['waist_height_ratio'] = waist / (height + 0.01)
    
    # Glucose
    hba1c = float(raw_data.get('hba1c', 5.5))
    features['hba1c'] = hba1c
    features['fasting_glucose'] = float(raw_data.get('fasting_glucose', 90))
    
    # Lipids
    tg = float(raw_data.get('triglycerides', 150))
    hdl = float(raw_data.get('hdl_cholesterol', 50))
    ldl = float(raw_data.get('ldl_cholesterol', 100))
    total_chol = float(raw_data.get('total_cholesterol', 200))
    
    features['triglycerides'] = tg
    features['log_triglycerides'] = np.log1p(tg)
    features['hdl_cholesterol'] = hdl
    features['ldl_cholesterol'] = ldl
    features['total_cholesterol'] = total_chol
    features['tg_hdl_ratio'] = tg / (hdl + 0.01)
    features['total_hdl_ratio'] = total_chol / (hdl + 0.01)
    features['non_hdl'] = total_chol - hdl
    
    # Renal
    cr = float(raw_data.get('serum_creatinine', 1.0))
    features['serum_creatinine'] = cr
    features['egfr'] = calculate_egfr(features['age'], features['gender'], cr)
    features['bun'] = float(raw_data.get('bun', 15))
    features['bun_cr_ratio'] = features['bun'] / (cr + 0.01)
    
    # Other
    uric = float(raw_data.get('uric_acid', 5.5))
    features['uric_acid'] = uric
    features['log_uric_acid'] = np.log1p(uric)
    features['sodium'] = float(raw_data.get('sodium', 140))
    features['potassium'] = float(raw_data.get('potassium', 4.0))
    
    # Inflammatory
    hscrp = float(raw_data.get('hscrp', 2.0))
    features['hscrp'] = hscrp
    features['log_hscrp'] = np.log1p(hscrp)
    
    neutrophil = float(raw_data.get('neutrophil_pct', 60))
    lymphocyte = float(raw_data.get('lymphocyte_pct', 30))
    features['neutrophil_lymphocyte_ratio'] = neutrophil / (lymphocyte + 0.01)
    
    # Hematology
    features['hemoglobin'] = float(raw_data.get('hemoglobin', 14))
    features['hematocrit'] = float(raw_data.get('hematocrit', 42))
    features['rdw'] = float(raw_data.get('rdw', 13))
    
    # Iron (Model B only)
    features['ferritin'] = float(raw_data.get('ferritin', 100))
    features['serum_iron'] = float(raw_data.get('serum_iron', 80))
    
    # Composite scores
    features['cardiometabolic_index'] = features['tg_hdl_ratio'] * features['waist_height_ratio']
    features['mets_score'] = calculate_mets_score(features)
    
    # CASCADE INTERACTIONS
    features['vasc_metabolic_load'] = sbp * hba1c
    features['metabolic_renal_stress'] = hba1c * (1 / (features['egfr'] + 1))
    
    return features


def calculate_egfr(age, gender, creatinine):
    """Calculate eGFR using CKD-EPI equation"""
    is_female = (gender == 2)
    kappa = 0.7 if is_female else 0.9
    alpha = -0.329 if is_female else -0.411
    female_factor = 1.018 if is_female else 1.0
    
    min_ratio = min(creatinine / kappa, 1.0)
    max_ratio = max(creatinine / kappa, 1.0)
    
    egfr = 141 * (min_ratio ** alpha) * (max_ratio ** -1.209) * (0.993 ** age) * female_factor
    return egfr


def calculate_mets_score(features):
    """Calculate metabolic syndrome score (0-5)"""
    score = 0
    
    # Waist
    if features['gender'] == 1 and features['waist_cm'] > 102:
        score += 1
    elif features['gender'] == 2 and features['waist_cm'] > 88:
        score += 1
    
    # Triglycerides
    if features['triglycerides'] >= 150:
        score += 1
    
    # HDL
    if features['gender'] == 1 and features['hdl_cholesterol'] < 40:
        score += 1
    elif features['gender'] == 2 and features['hdl_cholesterol'] < 50:
        score += 1
    
    # Blood Pressure
    if features['systolic_bp'] >= 130 or features['diastolic_bp'] >= 85:
        score += 1
    
    # Glucose
    if features['hba1c'] >= 5.7:
        score += 1
    
    return score


def generate_shap_plot(shap_values, X, risk_score):
    """Generate SHAP waterfall plot as base64 image"""
    try:
        plt.figure(figsize=(10, 6))
        shap.plots.waterfall(shap_values[0, :, 1], show=False)
        plt.title(f'Risk Explanation (Score: {risk_score:.1%})', 
                 fontsize=14, fontweight='bold', pad=20)
        plt.tight_layout()
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', 
                   facecolor='#0f172a', edgecolor='none')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        return f"data:image/png;base64,{image_base64}"
    except Exception as e:
        print(f"Error generating SHAP plot: {e}")
        return None


def get_top_features(shap_values, X, top_n=5):
    """Get top contributing features"""
    shap_vals = shap_values[0, :, 1].values
    feature_names = X.columns
    
    # Get absolute SHAP values and sort
    abs_shap = np.abs(shap_vals)
    top_indices = np.argsort(abs_shap)[-top_n:][::-1]
    
    top_features = []
    for idx in top_indices:
        top_features.append({
            'feature': feature_names[idx].replace('_', ' ').title(),
            'shap_value': float(shap_vals[idx]),
            'feature_value': float(X.iloc[0, idx]),
            'impact': 'Increases Risk' if shap_vals[idx] > 0 else 'Decreases Risk'
        })
    
    return top_features


# ============================================================================
# RUN APP
# ============================================================================

if __name__ == "__main__":
    app.run(debug=True, port=5000)