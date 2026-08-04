# 🫀 BioCascade — Metabolic Cascade Risk Prediction

Predicting cardiometabolic risk from routine bloodwork, with a clinical hypothesis at its core and a leakage-controlled model to test it honestly.

---

## 🧠 The Idea

Vascular, metabolic, and renal dysfunction rarely happen in isolation. In practice they cascade: elevated blood pressure strains the kidneys, poor glucose control damages blood vessels, and each system's decline accelerates the others. BioCascade tests this "metabolic cascade" hypothesis using NHANES 2017-2018 data, defining a clinical proxy for systemic risk based on three thresholds:

- **Vascular:** Systolic BP > 140 mmHg
- **Metabolic:** HbA1c ≥ 6.5%
- **Renal:** Sex-aware serum creatinine (Male > 1.3, Female > 1.1 mg/dL)

A patient flagged on two or more of these triads is labeled **high risk**, the target the models are trained to predict from the surrounding clinical picture.

---

## 🔬 Dual-Model Validation

A single model trained on all available features risks leaking the label's own ingredients back into its predictors. BioCascade addresses this by training two models side by side:

- **Model A (Upper Bound):** Uses the full feature set, including BP, HbA1c, and renal markers, to establish a ceiling on achievable performance.
- **Model B (Independent):** Deliberately excludes BP, glucose, creatinine, and any derived interaction terms, relying only on lipids, anthropometrics, inflammatory markers, hematology, and iron studies. This measures how much signal exists in features that are genuinely independent of the label definition.

Comparing the two exposes how much of the model's apparent skill is circular versus how well cardiometabolic risk can be inferred from indirect markers alone.

---

## 🧾 Explainability

Every prediction is paired with SHAP (TreeExplainer) output:

- A global summary plot showing which features drive risk across the population
- A per-patient waterfall plot breaking down exactly which values pushed an individual's score up or down

This keeps the model auditable rather than a black box, which matters for anything touching clinical decision-making, even in a research context.

---

## 🖥️ Interactive Dashboard

A Flask app (`app/app.py`) serves a screening tool where you can input a patient's values and get:

- A risk score and classification (High Risk / Low Risk) from either model
- A live SHAP waterfall plot explaining the prediction
- The top contributing features and their direction of impact

---

## 🏗️ Pipeline

```
NHANES CSVs (Demographics, Examination, Laboratory)
        ↓
DuckDB ingestion + integrity checks (preprocess.py)
        ↓
Clinical proxy labeling via SQL (labeling.py, label_definition.sql)
        ↓
Feature engineering: ratios, composite scores, cascade interactions
        ↓
Dual RandomForest training (model.py, model_independent.py)
        ↓
SHAP explainability (explain.py)
        ↓
Flask dashboard for interactive screening
```

---

## 🧰 Tech Stack

| Layer | Tools |
|---|---|
| Data storage & querying | DuckDB, SQL |
| Data processing | pandas, NumPy, PyArrow |
| Modeling | scikit-learn (RandomForest), XGBoost |
| Explainability | SHAP |
| Visualization | matplotlib, seaborn |
| App | Flask |
| Deployment | Docker, Terraform (Coder workspace) |

---

## 📁 Project Structure

```
BioCascade/
├── app/
│   ├── app.py                  # Flask dashboard + prediction API
│   ├── templates/              # Dashboard & screening tool UI
│   └── static/plots/           # Generated SHAP & ROC plots
├── data/
│   ├── raw/                    # NHANES source CSVs
│   └── processed/               # DuckDB database, trained models
├── sql/
│   ├── schema.sql               # Raw patient table schema
│   └── label_definition.sql     # Clinical proxy labeling logic
├── src/
│   ├── preprocess.py            # ETL: CSV to DuckDB
│   ├── labeling.py              # Applies clinical risk labels
│   ├── features.py              # Feature engineering
│   ├── model.py                 # Full-feature model (upper bound)
│   ├── model_independent.py     # Leakage-controlled model
│   └── explain.py               # SHAP global & local explanations
├── BioCascade_Complete_Analysis.ipynb   # End-to-end notebook walkthrough
├── Dockerfile
├── main.tf
└── requirements.txt
```

---

## ⚙️ Getting Started

**1. Clone the repo**

```bash
git clone https://github.com/beko-1enkosi/BioCascade.git
cd BioCascade
```

**2. Create a virtual environment**

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/MacOS
venv\Scripts\activate     # Windows
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Run the pipeline**

```bash
python src/preprocess.py
python src/labeling.py
python src/model.py
python src/model_independent.py
python src/explain.py
```

**5. Launch the dashboard**

```bash
python app/app.py
```

Or build and run with Docker:

```bash
docker build -t biocascade .
docker run -p 5000:5000 biocascade
```

---

## ⚠️ Disclaimer

This project uses a research-defined clinical proxy, not a validated diagnostic criterion. It is built for educational and analytical purposes and is not intended for clinical use, diagnosis, or treatment decisions.

---

## 👩‍💻 Author

Built by **Thobeka Nkosi**
WeThinkCode_ Software Engineering Student | Life Sciences background (Biochemistry & Physiology)