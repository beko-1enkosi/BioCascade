# 🧬 BioCascade

[![BioCascade CI](https://github.com/beko-1enkosi/BioCascade/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/beko-1enkosi/BioCascade/actions/workflows/ci.yml)
![Python 3.13](https://img.shields.io/badge/Python-3.13-3776AB) ![scikit-learn 1.9.1](https://img.shields.io/badge/scikit--learn-1.9.1-F7931E)

**Interpretable machine learning for multi-system cardiometabolic dysfunction**

BioCascade is a research-oriented, full-stack machine learning application inspired by heart failure with preserved ejection fraction (HFpEF). It combines biological domain knowledge, data engineering, statistical analysis, and explainable AI to investigate whether routine biomarkers can distinguish a research-defined vascular, metabolic and renal dysfunction phenotype.

> **Research only:** BioCascade does not diagnose HFpEF, predict future heart failure, or provide medical advice. Its target is a constructed proxy, not a clinically confirmed disease outcome.

**Explore:** [Research notebook](notebooks/BioCascade_Complete_Analysis.ipynb) · [Application source](app/) · [Data and ML pipeline](src/)

**Live demo:** [Launch BioCascade](https://biocascade.onrender.com/) · [Screening terminal](https://biocascade.onrender.com/screening-tool)

Hosted on Render using Docker and Gunicorn. The free instance sleeps when inactive, so the first visit may take 50 seconds or longer. Use the built-in synthetic demo profiles only.

## 1. Scientific motivation

Cardiometabolic dysfunction involves interconnected biological systems. BioCascade explores a *cascade hypothesis*: joint patterns of vascular stress, glucose dysregulation and impaired renal function may carry useful predictive information. The project uses engineered interaction features to investigate this idea, while distinguishing prediction of a constructed label from evidence of biological causation.

Two models address different questions:

- **Model A — Upper Bound:** How well can a model reconstruct the phenotype when given its defining biomarkers and derived features?
- **Model B — Independent:** How much predictive signal remains when direct label ingredients and their derivatives are excluded?

## 2. Dataset and data engineering

The analysis uses the NHANES 2017–2018 survey (CDC/NCHS), combining demographic, laboratory and examination data. DuckDB and SQL support ingestion, querying and phenotype construction; pandas and NumPy support transformation and feature engineering.

| Cohort characteristic | Recorded value |
|---|---:|
| Original adult participants | 5,533 |
| Raw dataset columns | 30 |
| Age range | 18–80 years |
| Mean age ± SD | 49.8 ± 18.6 years |
| Male participants | 2,672 (48.3%) |
| Female participants | 2,861 (51.7%) |
| Participants with phenotype labels | 4,573 |

The notebook reads `raw_patient_data` and `labeled_patients` from `data/processed/biocascade.db`.

### Data quality and missingness

![Missing data patterns and missingness by feature](app/static/plots/01_missing_data.png)

**Figure 1.** Missingness was present in 26 raw columns. Fasting glucose, triglycerides and LDL cholesterol each had more than 50% missingness. This motivates feature availability filtering and imputation; it also limits what can be inferred from the observed sample.

![Clinical biomarker distributions](app/static/plots/01_biomarker_distributions.png)

**Figure 2.** Distributions of blood pressure, HbA1c, triglycerides, creatinine and BMI reveal differences in spread and skewness. These visual checks help identify variables needing transformation or further quality assessment; they do not establish that every observation is clinically valid.

## 3. Research phenotype definition

The SQL label definition (`sql/label_definition.sql`) constructs a binary target based on at least two of the following three indicators:

| System | Research indicator |
|---|---|
| Vascular | Systolic blood pressure > 140 mmHg |
| Metabolic | HbA1c ≥ 6.5% |
| Renal | Serum creatinine > 1.3 mg/dL (male) or > 1.1 mg/dL (female) |

The SQL excludes records missing any of the three label-defining measurements. The historical notebook's prose differs at the systolic BP boundary; the table above follows the actual SQL implementation.

| Proxy class | Count | Share | Mean age |
|---|---:|---:|---:|
| Low | 4,235 | 92.6% | 48.3 years |
| High | 338 | 7.4% | 67.8 years |
| Total | 4,573 | 100% | — |

The 7.4% figure is the frequency of the constructed label in the analyzed cohort, not HFpEF prevalence. The marked imbalance makes minority-class metrics particularly important.

## 4. Feature engineering and cascade interactions

The notebook reports approximately 16 engineered features and 51 total columns after transformation (not 51 model inputs).

| Feature family | Examples |
|---|---|
| Metabolic | TG/HDL ratio, non-HDL cholesterol, waist-to-height ratio, cardiometabolic index, metabolic syndrome score |
| Renal | Estimated glomerular filtration rate (eGFR), BUN/creatinine ratio |
| Vascular | Pulse pressure, mean arterial pressure |
| Inflammatory | Neutrophil-to-lymphocyte ratio, log-transformed hsCRP |
| Additional transformations | `log1p` of triglycerides and uric acid |

The two central interaction features are:

- **Vascular-metabolic load:** `systolic_bp × hba1c`
- **Metabolic-renal stress:** `hba1c / (egfr + 1)` (the implemented denominator includes a stabilizing offset).

![Distributions of cascade interaction features](app/static/plots/02_cascade_features.png)

**Figure 3.** Both engineered interaction features show right-skewed distributions. They encode joint biomarker patterns; their importance in a classifier does not by itself demonstrate physiological synergy or an improvement over individual components.

## 5. Dual-model methodology

| Property | Model A — Upper Bound | Model B — Independent |
|---|---|---|
| Model inputs | 31 | 21 |
| Algorithm | Random Forest | Random Forest |
| Direct label ingredients | Included | Excluded by design |
| Purpose | Label reconstruction benchmark | Evaluate indirect predictive signal |
| Main limitation | Circularity from label-related inputs | Modest minority-class detection and no external validation |

The recorded experiment used a stratified 80/20 split (3,658 training and 915 testing observations), random seed 42, median imputation fitted on training data, and balanced class weights. Candidate features with at most 50% observed values were filtered out. Model B excludes direct BP, glucose and creatinine inputs and label-derived interactions by design. Both historical test matrices were reconstructed and matched during retraining. The imputer is fitted on training data only.

## 6. Model evaluation

### Current released model artifacts

Both models were retrained under scikit-learn 1.9.1 using the reconstructed historical holdout (seed 42). Evaluation results are recorded in [docs/model_metrics.json](docs/model_metrics.json).

| Metric | Model A — Upper Bound | Model B — Independent |
|---|---:|---:|
| ROC-AUC | 0.9984 | 0.8293 |
| Average precision | 0.9803 | 0.2869 |
| Accuracy | 0.9880 | 0.8699 |
| Positive-class precision | 0.8904 | 0.2960 |
| Positive-class recall | 0.9559 | 0.5441 |
| Positive-class F1 | 0.9220 | 0.3834 |

The holdout contains 915 records, including 68 positive proxy cases. Model A's near-perfect discrimination reflects access to target-defining features; Model B's modest precision and recall underscore the limitations of indirect prediction. Neither model has been validated as a clinical screening tool. The scores are not calibrated probabilities of HFpEF.

### Historical notebook results

| Metric | Model A | Model B |
|---|---:|---:|
| ROC-AUC | 0.9985 | 0.8221 |
| Accuracy (rounded) | 0.99 | 0.90 |
| High-class precision | 0.92 | 0.34 |
| High-class recall | 0.90 | 0.31 |
| High-class F1 | 0.91 | 0.33 |
| Average precision | — | 0.2733 |
| Reported mean cross-validation ROC-AUC | — | 0.8572 |

The test set contained 847 low-class and 68 high-class observations. These are historical notebook outputs, distinct from the retrained artifacts reported above. The figures in the following sections remain historical research figures rather than regenerated plots for the current models. Cross-validation preprocessing still needs to be audited.

![ROC curves comparing the two models](app/static/plots/03_roc_comparison.png)

**Figure 4.** Model A nearly separates the constructed classes, as expected given its access to label-defining variables. Model B shows useful discrimination without those direct inputs, but ROC-AUC is not accuracy or a measure of probability calibration.

![Precision-recall curve for Model B](app/static/plots/03_pr_curve_model_b.png)

**Figure 5.** Model B's average precision (0.2733, calculated using `average_precision_score`) provides additional context for the rare positive class. At the recorded classification operating point, recall was only 0.31 and precision 0.34. This is an important limitation despite the ROC-AUC of approximately 0.82.

![Random Forest feature importance comparison](app/static/plots/03_feature_importance.png)

**Figure 6.** In the recorded impurity-based importance results, vascular-metabolic load (0.1847) and metabolic-renal stress (0.1633) were the two leading Model A features. Age (0.2713) led Model B. These importance scores are not causal effect estimates.

## 7. Explainable AI with SHAP

SHAP (SHapley Additive exPlanations) attributes a model output to its input features relative to a baseline. BioCascade provides population-level summary plots and individual waterfall explanations.

### Model A — Global explanations

![Model A SHAP summary](app/static/plots/04_shap_summary_model_a.png)

**Figure 7.** The recorded mean absolute SHAP values rank systolic BP (0.0898), HbA1c (0.0886), vascular-metabolic load (0.0806) and metabolic-renal stress (0.0778) as the top four features. This is a separate ranking from Random Forest impurity importance. The notebook's later rank-printing cell is inconsistent with these values and should be corrected before rerunning the analysis.

### Model B — Global explanations

![Model B SHAP summary](app/static/plots/04_shap_summary_model_b.png)

**Figure 8.** Age dominates the recorded mean absolute SHAP ranking (0.1489), followed by uric acid, log uric acid and waist-to-height ratio. These are model associations, not evidence that changing a feature changes disease risk.

### Individual explanations

| Model A — historical example | Model B — historical example |
|---|---|
| ![Model A waterfall](app/static/plots/04_patient_example_model_a.png) | ![Model B waterfall](app/static/plots/04_patient_example_model_b.png) |

**Figure 9.** The notebook selected separate high-score observations with outputs of 96.7% and 79.5%, respectively. Waterfall plots show how features shift each output from its baseline. These are not necessarily the same individual or calibrated probabilities of disease.

## 8. Interactive web application

The Flask application serves a dashboard and interactive screening demonstration built using vanilla HTML, CSS and JavaScript. It accepts biomarker inputs, engineers features, selects the appropriate model feature set, applies the saved imputer, generates a model score and returns a SHAP waterfall and contributing features.

The dashboard retains the original scroll-driven DNA animation. The responsive screening terminal includes:

- Selectable Model A and Model B cards with their current ROC-AUC values and research purpose.
- Model-specific biomarker fields, empty inputs with example placeholders, two synthetic demo profiles and reset functionality.
- A staged circular score animation followed by classification, SHAP waterfall and individual feature contributions.
- Explicit research-only wording and reduced-motion support.

Both models and SHAP outputs were smoke-tested locally. The saved Model B is a scikit-learn pipeline; the app uses its underlying `rf` estimator for TreeExplainer while retaining the pipeline for prediction.

Both the browser and Flask API enforce the selected model's required raw biomarkers: 22 for Model A and 18 for Model B, including dependencies of engineered features. Missing, blank, nonnumeric, nonfinite and invalid required values return HTTP 400 before inference. Unrecognized fields are rejected; known inactive biomarkers are ignored for compatibility with earlier clients. No missing required biomarker is silently defaulted. Use synthetic profiles only; do not submit personal or clinical data.

| Route | Purpose |
|---|---|
| `GET /` | Research dashboard |
| `GET /screening-tool` | Interactive model demonstration |
| `POST /predict` | Return a research proxy score, classification and SHAP explanation |

## 9. System architecture

```mermaid
flowchart TD
    A[NHANES source data] --> B[DuckDB ingestion and SQL labeling]
    B --> C[Feature engineering]
    C --> D[Model A training]
    C --> E[Model B training]
    D --> F[Saved models and imputers]
    E --> F
    G[HTML CSS JavaScript interface] --> H[Flask prediction API]
    H --> I[Input feature engineering and imputation]
    I --> F
    F --> J[Prediction and SHAP explanation]
    J --> G
```

## 10. Technology stack

| Layer | Technologies |
|---|---|
| Data engineering | Python, DuckDB, SQL, pandas, NumPy, PyArrow |
| Machine learning | scikit-learn, Random Forest, joblib |
| Explainability and visualization | SHAP, matplotlib, seaborn |
| Backend | Flask, Gunicorn (production WSGI) |
| Frontend | HTML, CSS, vanilla JavaScript |
| Research | Jupyter Notebook |
| Packaging and version control | Docker, Git, GitHub |
| Testing and CI | pytest, GitHub Actions |

## 11. Repository structure

```text
BioCascade/
├── app/
│   ├── app.py
│   ├── templates/
│   └── static/
│       ├── css/
│       ├── js/
│       └── plots/
├── data/
│   ├── raw/
│   └── processed/
├── notebooks/
│   └── BioCascade_Complete_Analysis.ipynb
├── sql/
├── src/
│   └── train_models.py
├── docs/
│   └── model_metrics.json
├── tests/
├── .github/workflows/ci.yml
├── Dockerfile
├── .dockerignore
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

## 12. Run, test and deploy

### Local development

Use Python 3.13 and the pinned dependencies. The four current model and imputer artifacts were serialized using scikit-learn 1.9.1. Only load trusted artifacts.

```bash
git clone https://github.com/beko-1enkosi/BioCascade.git
cd BioCascade
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m flask --app app.app run --port 5002
```

Open `http://127.0.0.1:5002` and select Try Demo. On Windows, activate with `.venv\Scripts\activate` instead.

### Automated tests

```bash
python -m pip check
python -m pytest -q -W error::sklearn.exceptions.InconsistentVersionWarning
```

The expanded local test suite passed all **96 tests with zero warnings**, including direct API tests for every required-field omission, valid model-specific payloads, malformed inputs and inactive biomarker isolation, alongside feature engineering, inference, SHAP and training coverage. GitHub Actions runs the Python suite on Ubuntu with Python 3.13. The CI badge above tracks the main branch.

### Docker and production server

```bash
docker build -t biocascade:latest .
docker run --rm --name biocascade -p 5001:5000 biocascade:latest
```

Open `http://127.0.0.1:5001`. The container runs Gunicorn with one worker and one thread, as a non-root user, and includes the Flask application and four required model/imputer artifacts. It accepts the hosting provider's `PORT` environment variable (default 5000). Research data, notebooks and training code are not copied into the runtime image.

To simulate a small hosting instance locally:

```bash
docker run --rm --name biocascade-limited \
  --memory=512m --memory-swap=512m --cpus=1 \
  -p 5001:5000 biocascade:latest
```

The local constrained run loaded both models and served Model B predictions successfully; an observed memory snapshot was 185.5 MiB out of 512 MiB, not a measured peak or a guarantee of cloud performance. One worker timeout occurred and recovered. The Render deployment succeeded on 26 November 2026; dashboard health checks and a live Model B prediction with SHAP were confirmed. Continue monitoring cold starts, peak memory and repeated requests; verify both models on the hosted instance.

### Reproduce training

The application does not require retraining. For research reproduction, run from the repository root with the included processed database and historical test matrices:

```bash
python src/train_models.py
```

The script reconstructs the holdout, fits training-only median imputers, trains both Random Forest models and writes candidate artifacts and metrics to `.venv/candidate_models/`, leaving the current deployed artifacts unchanged. The historical test matrices matched for both models during the revamp. The research notebook is preserved; full execution and relative paths after relocation have not yet been reverified.

## 13. Findings, limitations and future work

The recorded experiment demonstrates that engineered interaction features are prominent in Model A and that indirect biomarkers provide discriminatory signal in Model B. It does not establish incremental benefit of interaction terms, causality, clinical utility or prospective disease prediction.

Key limitations include:

- **Target circularity:** Model A uses label ingredients and derivatives; it is a benchmark, not independent validation.
- **Proxy outcome:** NHANES does not supply confirmed HFpEF diagnoses for this analysis.
- **Cross-sectional design:** Temporal progression and future outcomes cannot be established.
- **Single survey cohort:** External validation and consideration of survey design and sampling weights are needed.
- **Missingness and class imbalance:** Feature availability and minority-class precision/recall constrain interpretation.
- **Calibration and thresholds:** Class weighting and a default classification threshold do not establish calibrated clinical probabilities.
- **Reproducibility:** The current artifacts and dependencies are aligned; training-serving parity, historical plot provenance, notebook execution and cross-validation preprocessing still warrant further verification.

Future work includes a controlled feature-ablation study, leakage-safe evaluation, calibration and threshold analysis, and external validation with appropriate confirmed outcomes. Longitudinal datasets, imaging and other modalities could be explored if available and scientifically justified.

## 14. Author and acknowledgments

**Thobeka Nkosi** — BSc Life Sciences (Biochemistry & Physiology) | Software Engineering

BioCascade began as a personal research and engineering project in March 2026, inspired by cardiovascular pathophysiology coursework.

Data: NHANES 2017–2018, CDC/NCHS. Research and application built with Python, DuckDB, scikit-learn, SHAP and Flask.

---

**Educational research prototype — not a medical device or clinical decision-support tool.**
