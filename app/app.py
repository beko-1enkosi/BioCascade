from flask import Flask, render_template, request, jsonify
import joblib
import pandas as pd
import numpy as np
import shap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import os

app = Flask(__name__)

# ============================================================================
# PATH RESOLUTION
# ============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data', 'processed')

# ============================================================================
# LOAD MODELS
# ============================================================================
print("🔄 Loading BioCascade models...")

try:
    model_a = joblib.load(os.path.join(DATA_DIR, 'biocascade_model_upper_bound.joblib'))
    imputer_a = joblib.load(os.path.join(DATA_DIR, 'imputer_upper_bound.joblib'))
    explainer_a = shap.TreeExplainer(model_a)
    
    model_b = joblib.load(os.path.join(DATA_DIR, 'biocascade_model_independent.joblib'))
    imputer_b = joblib.load(os.path.join(DATA_DIR, 'imputer_independent.joblib'))
    explainer_b = shap.TreeExplainer(model_b)
    
    # GET ACTUAL FEATURE NAMES FROM MODELS
    MODEL_A_FEATURES = list(imputer_a.feature_names_in_)
    MODEL_B_FEATURES = list(imputer_b.feature_names_in_)
    
    print("✅ Model A loaded")
    print(f"   Features ({len(MODEL_A_FEATURES)}): {MODEL_A_FEATURES[:5]}...")
    print("✅ Model B loaded")
    print(f"   Features ({len(MODEL_B_FEATURES)}): {MODEL_B_FEATURES[:5]}...")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    model_a = model_b = None
    MODEL_A_FEATURES = MODEL_B_FEATURES = []

# ============================================================================
# ROUTES
# ============================================================================
@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/screening-tool")
def screening_tool():
    return render_template("screening_tool.html")

@app.route("/predict", methods=["POST"])
def predict():
    if model_a is None or model_b is None:
        return jsonify({'success': False, 'error': 'Models not loaded'}), 500
    
    try:
        data = request.json
        model_choice = data.get('model', 'B')
        
        print(f"\n{'='*70}")
        print(f"🔍 PREDICTION REQUEST (Model {model_choice})")
        print(f"{'='*70}")
        
        # Select model
        if model_choice == 'A':
            model, imputer, explainer = model_a, imputer_a, explainer_a
            feature_list = MODEL_A_FEATURES
        else:
            model, imputer, explainer = model_b, imputer_b, explainer_b
            feature_list = MODEL_B_FEATURES
        
        print(f"Expected features: {len(feature_list)}")
        
        # Engineer ALL features (comprehensive)
        features = engineer_all_features(data)
        print(f"Engineered features: {len(features)}")
        
        # Create DataFrame with ONLY the features the model expects
        X = pd.DataFrame([features])
        X = X.reindex(columns=feature_list, fill_value=np.nan)
        
        print(f"Final feature matrix shape: {X.shape}")
        print(f"Missing values: {X.isnull().sum().sum()}")
        
        # Impute
        X_imputed = pd.DataFrame(
            imputer.transform(X),
            columns=feature_list
        )
        
        # Predict
        risk_proba = model.predict_proba(X_imputed)[0, 1]
        risk_class = "High Risk" if risk_proba > 0.5 else "Low Risk"
        
        print(f"✅ Prediction: {risk_proba:.1%} ({risk_class})")
        
        # SHAP
        shap_values = explainer(X_imputed)
        shap_plot = generate_shap_plot(shap_values, risk_proba)
        top_features = get_top_features(shap_values, X_imputed)
        
        return jsonify({
            'success': True,
            'risk_score': float(risk_proba),
            'risk_class': risk_class,
            'model_used': f"Model {'A (Upper Bound)' if model_choice == 'A' else 'B (Independent)'}",
            'shap_plot': shap_plot,
            'top_features': top_features
        })
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 400

# ============================================================================
# FEATURE ENGINEERING (COMPREHENSIVE)
# ============================================================================
def engineer_all_features(raw):
    """Engineer ALL possible features that might be needed"""
    f = {}
    
    # ===== DEMOGRAPHICS =====
    f['age'] = float(raw.get('age', 50))
    f['gender'] = int(raw.get('gender', 1))
    
    # ===== BLOOD PRESSURE =====
    sbp = float(raw.get('systolic_bp', 120))
    dbp = float(raw.get('diastolic_bp', 80))
    f['systolic_bp'] = sbp
    f['diastolic_bp'] = dbp
    f['pulse_pressure'] = sbp - dbp
    f['mean_arterial_pressure'] = dbp + (f['pulse_pressure'] / 3)
    
    # ===== ANTHROPOMETRICS =====
    waist = float(raw.get('waist_cm', 90))
    height = float(raw.get('height_cm', 170))
    f['bmi'] = float(raw.get('bmi', 25))
    f['waist_cm'] = waist
    f['height_cm'] = height
    f['waist_height_ratio'] = waist / (height + 0.01)
    
    # ===== GLUCOSE =====
    hba1c = float(raw.get('hba1c', 5.5))
    f['hba1c'] = hba1c
    f['fasting_glucose'] = float(raw.get('fasting_glucose', 90))
    
    # ===== LIPIDS =====
    tg = float(raw.get('triglycerides', 150))
    hdl = float(raw.get('hdl_cholesterol', 50))
    ldl = float(raw.get('ldl_cholesterol', 100))
    total = float(raw.get('total_cholesterol', 200))
    
    f['triglycerides'] = tg
    f['log_triglycerides'] = np.log1p(tg)
    f['hdl_cholesterol'] = hdl
    f['ldl_cholesterol'] = ldl
    f['total_cholesterol'] = total
    f['tg_hdl_ratio'] = tg / (hdl + 0.01)
    f['total_hdl_ratio'] = total / (hdl + 0.01)
    f['non_hdl'] = total - hdl
    
    # ===== RENAL =====
    cr = float(raw.get('serum_creatinine', 1.0))
    f['serum_creatinine'] = cr
    f['egfr'] = calculate_egfr(f['age'], f['gender'], cr)
    f['bun'] = float(raw.get('bun', 15))
    f['bun_cr_ratio'] = f['bun'] / (cr + 0.01)
    
    # ===== URIC ACID =====
    uric = float(raw.get('uric_acid', 5.5))
    f['uric_acid'] = uric
    f['log_uric_acid'] = np.log1p(uric)
    
    # ===== ELECTROLYTES =====
    f['sodium'] = float(raw.get('sodium', 140))
    f['potassium'] = float(raw.get('potassium', 4.0))
    
    # ===== INFLAMMATION =====
    hscrp = float(raw.get('hscrp', 2.0))
    f['hscrp'] = hscrp
    f['log_hscrp'] = np.log1p(hscrp)
    
    neutrophil = float(raw.get('neutrophil_pct', 60))
    lymphocyte = float(raw.get('lymphocyte_pct', 30))
    f['neutrophil_pct'] = neutrophil
    f['lymphocyte_pct'] = lymphocyte
    f['neutrophil_lymphocyte_ratio'] = neutrophil / (lymphocyte + 0.01)
    
    # ===== HEMATOLOGY =====
    f['hemoglobin'] = float(raw.get('hemoglobin', 14))
    f['hematocrit'] = float(raw.get('hematocrit', 42))
    f['rdw'] = float(raw.get('rdw', 13))
    f['wbc_count'] = float(raw.get('wbc_count', 7.0))
    
    # ===== IRON =====
    f['ferritin'] = float(raw.get('ferritin', 100))
    f['serum_iron'] = float(raw.get('serum_iron', 80))
    
    # ===== COMPOSITE SCORES =====
    f['cardiometabolic_index'] = f['tg_hdl_ratio'] * f['waist_height_ratio']
    f['mets_score'] = calculate_mets_score(f, hba1c)
    
    # ===== CASCADE FEATURES =====
    f['vasc_metabolic_load'] = sbp * hba1c
    f['metabolic_renal_stress'] = hba1c * (1 / (f['egfr'] + 1))
    
    return f

def calculate_egfr(age, gender, cr):
    """CKD-EPI equation"""
    k = 0.7 if gender == 2 else 0.9
    a = -0.329 if gender == 2 else -0.411
    return 141 * (min(cr/k, 1)**a) * (max(cr/k, 1)**-1.209) * (0.993**age) * (1.018 if gender == 2 else 1.0)

def calculate_mets_score(f, hba1c):
    """Metabolic syndrome score"""
    s = 0
    if (f['gender'] == 1 and f['waist_cm'] > 102) or (f['gender'] == 2 and f['waist_cm'] > 88): s += 1
    if f['triglycerides'] >= 150: s += 1
    if (f['gender'] == 1 and f['hdl_cholesterol'] < 40) or (f['gender'] == 2 and f['hdl_cholesterol'] < 50): s += 1
    if f['systolic_bp'] >= 130 or f['diastolic_bp'] >= 85: s += 1
    if hba1c >= 5.7: s += 1
    return s

def generate_shap_plot(shap_values, risk_score):
    """Generate SHAP waterfall plot"""
    try:
        plt.style.use('dark_background')
        fig = plt.figure(figsize=(10, 6))
        fig.patch.set_facecolor('#0f172a')
        
        shap.plots.waterfall(shap_values[0, :, 1], show=False)
        plt.title(f'Feature Contribution Analysis (Risk: {risk_score:.1%})', 
                 color='#00E5FF', fontsize=14, fontweight='bold', pad=20)
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=120, facecolor='#0f172a', edgecolor='none')
        plt.close()
        buf.seek(0)
        return f"data:image/png;base64,{base64.b64encode(buf.read()).decode()}"
    except Exception as e:
        print(f"SHAP plot error: {e}")
        return None

def get_top_features(shap_values, X, top_n=5):
    """Get top contributing features"""
    vals = shap_values[0, :, 1].values
    indices = np.argsort(np.abs(vals))[-top_n:][::-1]
    
    return [{
        'feature': X.columns[i].replace('_', ' ').title(),
        'shap_value': float(vals[i]),
        'feature_value': float(X.iloc[0, i]),
        'impact': 'Increases Risk' if vals[i] > 0 else 'Decreases Risk'
    } for i in indices]

if __name__ == "__main__":
    app.run(debug=True, port=5000)