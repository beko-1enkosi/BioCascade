
from app.app import (
    model_a,
    model_b,
    imputer_a,
    imputer_b,
    MODEL_A_FEATURES,
    MODEL_B_FEATURES
)


def test_model_a_loaded():
    assert model_a is not None


def test_model_b_loaded():
    assert model_b is not None


def test_model_a_feature_count():
    assert len(MODEL_A_FEATURES) == 31


def test_model_b_feature_count():
    assert len(MODEL_B_FEATURES) == 21


def test_model_a_feature_alignment():
    assert list(model_a.feature_names_in_) == list(
        imputer_a.feature_names_in_
    )


def test_model_b_feature_alignment():
    assert list(model_b.feature_names_in_) == list(
        imputer_b.feature_names_in_
    )


def test_model_b_excludes_label_ingredients():
    excluded_features = {
        "systolic_bp",
        "diastolic_bp",
        "pulse_pressure",
        "mean_arterial_pressure",
        "hba1c",
        "fasting_glucose",
        "serum_creatinine",
        "egfr",
        "bun",
        "bun_cr_ratio",
        "mets_score",
        "vasc_metabolic_load",
        "metabolic_renal_stress"
    }

    assert excluded_features.isdisjoint(MODEL_B_FEATURES)
