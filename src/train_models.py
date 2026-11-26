"""Train candidate BioCascade models without overwriting deployed artifacts.
Run from the repository root: python src/train_portfolio_models.py
"""
from pathlib import Path
import json

import duckdb
import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (roc_auc_score, average_precision_score,
                             classification_report)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
OUT = ROOT / ".venv" / "candidate_models"


def engineer_features(df_labeled):
    """Reproduce the original notebook's feature calculations."""
    df = df_labeled.copy()

    df['tg_hdl_ratio'] = df['triglycerides'] / (df['hdl_cholesterol'] + 0.01)
    df['total_hdl_ratio'] = df['total_cholesterol'] / (df['hdl_cholesterol'] + 0.01)
    df['non_hdl'] = df['total_cholesterol'] - df['hdl_cholesterol']
    df['waist_height_ratio'] = df['waist_cm'] / (df['height_cm'] + 0.01)
    df['cardiometabolic_index'] = df['tg_hdl_ratio'] * df['waist_height_ratio']

    def calculate_egfr(row):
        cr = row['serum_creatinine']
        age = row['age']
        is_female = (row['gender'] == 2)
        if pd.isna(cr) or pd.isna(age):
            return np.nan
        kappa = 0.7 if is_female else 0.9
        alpha = -0.329 if is_female else -0.411
        female_factor = 1.018 if is_female else 1.0
        min_ratio = min(cr / kappa, 1.0)
        max_ratio = max(cr / kappa, 1.0)
        egfr = 141 * (min_ratio ** alpha) * (max_ratio ** -1.209) * (0.993 ** age) * female_factor
        return egfr

    df['egfr'] = df.apply(calculate_egfr, axis=1)
    df['bun_cr_ratio'] = df['bun'] / (df['serum_creatinine'] + 0.01)

    df['pulse_pressure'] = df['systolic_bp'] - df['diastolic_bp']
    df['mean_arterial_pressure'] = df['diastolic_bp'] + (df['pulse_pressure'] / 3)

    df['neutrophil_lymphocyte_ratio'] = df['neutrophil_pct'] / (df['lymphocyte_pct'] + 0.01)
    df['log_hscrp'] = np.log1p(df['hscrp'])

    df['vasc_metabolic_load'] = df['systolic_bp'] * df['hba1c']
    df['metabolic_renal_stress'] = df['hba1c'] * (1 / (df['egfr'] + 1))

    df['log_triglycerides'] = np.log1p(df['triglycerides'])
    df['log_uric_acid'] = np.log1p(df['uric_acid'])

    # Metabolic syndrome score
    def calculate_mets_score(row):
        score = 0
        if row['gender'] == 1 and row['waist_cm'] > 102: score += 1
        elif row['gender'] == 2 and row['waist_cm'] > 88: score += 1
        if row['triglycerides'] >= 150: score += 1
        if row['gender'] == 1 and row['hdl_cholesterol'] < 40: score += 1
        elif row['gender'] == 2 and row['hdl_cholesterol'] < 50: score += 1
        if row['systolic_bp'] >= 130 or row['diastolic_bp'] >= 85: score += 1
        if row['hba1c'] >= 5.7: score += 1
        return score

    df['mets_score'] = df.apply(calculate_mets_score, axis=1)

    return df


MODELS = {"A": ("upper_bound", 15), "B": ("independent", 12)}


def split(df):
    return train_test_split(np.arange(len(df)), test_size=0.2,
                            random_state=42, stratify=df["is_high_risk"])


def main():
    con = duckdb.connect(str(DATA / "biocascade.db"), read_only=True)
    try:
        raw = con.execute("SELECT * FROM labeled_patients").df()
    finally:
        con.close()
    df = engineer_features(raw)
    train, test = split(df)
    saved = {key: pd.read_csv(DATA / f"X_test_{suffix}.csv")
             for key, (suffix, _) in MODELS.items()}
    matches = {}
    for key, frame in saved.items():
        reconstructed = df.iloc[test][frame.columns]
        matches[key] = (reconstructed.shape == frame.shape and
                        np.allclose(reconstructed.to_numpy(dtype=float),
                                    frame.to_numpy(dtype=float),
                                    rtol=1e-7, atol=1e-9, equal_nan=True))
        print(f"Model {key}: historical test matrix matches: {matches[key]}")

    historical = all(matches.values())
    if not historical:
        # New documented split; not a claim of reproducing the old test set.
        if "SEQN" not in df or not df["SEQN"].is_unique or df["SEQN"].isna().any():
            raise ValueError("Cannot create deterministic split: expected unique SEQN")
        df = df.sort_values("SEQN").reset_index(drop=True)
        train, test = split(df)
        print("Using a new deterministic holdout; historical metrics are not directly comparable.")
    y = df["is_high_risk"]
    if set(y.unique()) != {0, 1}:
        raise ValueError("Expected binary proxy labels 0 and 1")
    OUT.mkdir(parents=True, exist_ok=True)
    metrics = {"scikit_learn": sklearn.__version__,
               "historical_test_matrix_matches": matches,
               "split": "reconstructed" if historical else "new_SEQN_sorted",
               "seed": 42, "train_size": len(train), "test_size": len(test),
               "models": {}}
    baseline_path = ROOT / ".venv" / "prediction_baseline.csv"
    baseline = pd.read_csv(baseline_path) if historical and baseline_path.exists() else None
    if baseline is not None and len(baseline) != len(test):
        raise ValueError("Baseline row count differs from reconstructed test split")
    if "SEQN" in df:
        pd.DataFrame({"SEQN": df["SEQN"], "split": "train"}).assign(
            split=np.where(np.isin(np.arange(len(df)), test), "test", "train")
        ).to_csv(OUT / "split_manifest.csv", index=False)
    for key, (suffix, depth) in MODELS.items():
        columns = saved[key].columns.tolist()
        X_train, X_test = df.iloc[train][columns], df.iloc[test][columns]
        y_train, y_test = y.iloc[train], y.iloc[test]
        imputer = SimpleImputer(strategy="median")
        train_imp = pd.DataFrame(imputer.fit_transform(X_train), columns=columns)
        test_imp = pd.DataFrame(imputer.transform(X_test), columns=columns)
        rf = RandomForestClassifier(n_estimators=200, max_depth=depth,
                                    min_samples_split=20, random_state=42,
                                    class_weight="balanced", n_jobs=-1)
        # Keep B's current runtime interface: a one-step pipeline named 'rf'.
        model = rf if key == "A" else Pipeline([("rf", rf)])
        model.fit(train_imp, y_train)
        scores = model.predict_proba(test_imp)[:, 1]
        predicted = model.predict(test_imp)
        report = classification_report(y_test, predicted, output_dict=True, zero_division=0)
        result = {"roc_auc": roc_auc_score(y_test, scores),
                  "average_precision": average_precision_score(y_test, scores),
                  "classification_report": report}
        if baseline is not None:
            old = baseline[f"model_{key}_probability"].to_numpy()
            result.update({"old_roc_auc": roc_auc_score(y_test, old),
                           "old_average_precision": average_precision_score(y_test, old),
                           "mean_absolute_score_difference": float(np.mean(np.abs(scores-old)))})
        metrics["models"][key] = result
        joblib.dump(model, OUT / f"biocascade_model_{suffix}.joblib")
        joblib.dump(imputer, OUT / f"imputer_{suffix}.joblib")
        X_test.to_csv(OUT / f"X_test_{suffix}.csv", index=False)
        pd.DataFrame({"label": y_test.to_numpy(), "score": scores,
                      "prediction": predicted}).to_csv(OUT / f"evaluation_{suffix}.csv", index=False)
        print(f"\nModel {key} — ROC-AUC: {result['roc_auc']:.4f}, AP: {result['average_precision']:.4f}")
        print(classification_report(y_test, predicted, zero_division=0))
        if baseline is not None:
            print(f"Old ROC-AUC: {result['old_roc_auc']:.4f}")
            print(f"Mean absolute score difference: {result['mean_absolute_score_difference']:.6f}")
    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=2))
    print(f"\nCandidates saved in {OUT}; original models unchanged.")


if __name__ == "__main__":
    main()
