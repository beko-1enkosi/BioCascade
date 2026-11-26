
import json
import hashlib

import joblib
import numpy as np
import pandas as pd
import pytest

from src import train_models


@pytest.fixture
def sample_data():
    return pd.DataFrame({
        "age": [55],
        "gender": [1],
        "systolic_bp": [130],
        "diastolic_bp": [85],
        "triglycerides": [180],
        "hdl_cholesterol": [42],
        "total_cholesterol": [210],
        "waist_cm": [95],
        "height_cm": [170],
        "serum_creatinine": [1.1],
        "bun": [18],
        "hba1c": [6.2],
        "neutrophil_pct": [65],
        "lymphocyte_pct": [25],
        "hscrp": [3.5],
        "uric_acid": [6.5]
    })


def test_training_feature_engineering(sample_data):
    features = train_models.engineer_features(sample_data)

    assert features["pulse_pressure"].iloc[0] == 45

    assert features["vasc_metabolic_load"].iloc[0] == pytest.approx(806)

    assert features["non_hdl"].iloc[0] == 168

    assert features["mets_score"].iloc[0] == 3


def test_feature_engineering_preserves_input(sample_data):
    original = sample_data.copy(deep=True)

    train_models.engineer_features(sample_data)

    pd.testing.assert_frame_equal(sample_data, original)


def test_missing_creatinine(sample_data):
    sample_data.loc[0, "serum_creatinine"] = np.nan

    features = train_models.engineer_features(sample_data)

    assert pd.isna(features["egfr"].iloc[0])
    assert pd.isna(features["metabolic_renal_stress"].iloc[0])


@pytest.fixture
def labeled_data():
    return pd.DataFrame({
        "is_high_risk": [0] * 90 + [1] * 10
    })


def test_split_is_reproducible(labeled_data):
    train_a, test_a = train_models.split(labeled_data)
    train_b, test_b = train_models.split(labeled_data)

    np.testing.assert_array_equal(train_a, train_b)
    np.testing.assert_array_equal(test_a, test_b)


def test_split_has_no_overlap(labeled_data):
    train, test = train_models.split(labeled_data)

    assert len(train) == 80
    assert len(test) == 20
    assert set(train).isdisjoint(test)
    assert set(train) | set(test) == set(range(100))


def test_split_preserves_class_distribution(labeled_data):
    train, test = train_models.split(labeled_data)

    assert labeled_data.iloc[train]["is_high_risk"].mean() == pytest.approx(0.1)

    assert labeled_data.iloc[test]["is_high_risk"].mean() == pytest.approx(0.1)


def test_training_pipeline(tmp_path, monkeypatch):
    artifact_names = [
        "biocascade_model_upper_bound.joblib",
        "biocascade_model_independent.joblib",
        "imputer_upper_bound.joblib",
        "imputer_independent.joblib"
    ]

    def checksum(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    original_hashes = {
        name: checksum(train_models.DATA / name)
        for name in artifact_names
    }

    monkeypatch.setattr(train_models, "OUT", tmp_path)
    monkeypatch.setattr(train_models, "ROOT", tmp_path)

    train_models.main()

    for name in artifact_names:
        assert (tmp_path / name).exists()

        assert checksum(
            train_models.DATA / name
        ) == original_hashes[name]

    metrics = json.loads(
        (tmp_path / "metrics.json").read_text()
    )

    assert metrics["train_size"] == 3658
    assert metrics["test_size"] == 915

    assert all(
        metrics["historical_test_matrix_matches"].values()
    )

    for name in ["A", "B"]:
        assert 0 <= metrics["models"][name]["roc_auc"] <= 1
        assert 0 <= metrics["models"][name]["average_precision"] <= 1

    model_a = joblib.load(
        tmp_path / "biocascade_model_upper_bound.joblib"
    )

    model_b = joblib.load(
        tmp_path / "biocascade_model_independent.joblib"
    )

    assert len(model_a.feature_names_in_) == 31
    assert len(model_b.feature_names_in_) == 21
    assert "rf" in model_b.named_steps
