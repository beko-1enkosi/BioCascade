
import pytest

from app.app import engineer_all_features


def test_pulse_pressure():
    features = engineer_all_features({
        "systolic_bp": 130,
        "diastolic_bp": 85
    })

    assert features["pulse_pressure"] == 45


def test_mean_arterial_pressure():
    features = engineer_all_features({
        "systolic_bp": 130,
        "diastolic_bp": 85
    })

    assert features["mean_arterial_pressure"] == pytest.approx(100)


def test_vascular_metabolic_load():
    features = engineer_all_features({
        "systolic_bp": 130,
        "hba1c": 6.2
    })

    assert features["vasc_metabolic_load"] == pytest.approx(806)


def test_waist_height_ratio():
    features = engineer_all_features({
        "waist_cm": 95,
        "height_cm": 170
    })

    assert features["waist_height_ratio"] == pytest.approx(
        95 / 170.01
    )


def test_non_hdl_cholesterol():
    features = engineer_all_features({
        "total_cholesterol": 210,
        "hdl_cholesterol": 42
    })

    assert features["non_hdl"] == 168


def test_metabolic_renal_stress():
    features = engineer_all_features({
        "age": 55,
        "gender": 1,
        "serum_creatinine": 1.1,
        "hba1c": 6.2
    })

    expected = 6.2 / (features["egfr"] + 1)

    assert features["metabolic_renal_stress"] == pytest.approx(expected)
