
import pytest

from app.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


@pytest.fixture
def demo_profile():
    return {
        "age": 55,
        "gender": 1,
        "systolic_bp": 130,
        "diastolic_bp": 85,
        "bmi": 28.5,
        "waist_cm": 95,
        "height_cm": 170,
        "hba1c": 6.2,
        "fasting_glucose": 105,
        "triglycerides": 180,
        "hdl_cholesterol": 42,
        "ldl_cholesterol": 130,
        "total_cholesterol": 210,
        "serum_creatinine": 1.1,
        "bun": 18,
        "uric_acid": 6.5,
        "hscrp": 3.5,
        "neutrophil_pct": 65,
        "lymphocyte_pct": 25,
        "hemoglobin": 13.5,
        "hematocrit": 40,
        "rdw": 13.5,
        "ferritin": 100,
        "serum_iron": 80
    }


def test_dashboard(client):
    response = client.get("/")
    assert response.status_code == 200


def test_screening_page(client):
    response = client.get("/screening-tool")
    assert response.status_code == 200


@pytest.mark.parametrize("model", ["A", "B"])
def test_prediction(client, demo_profile, model):
    payload = {**demo_profile, "model": model}

    response = client.post("/predict", json=payload)

    assert response.status_code == 200

    result = response.get_json()

    assert result["success"] is True
    assert 0 <= result["risk_score"] <= 1
    assert result["risk_class"] in ["High Risk", "Low Risk"]
    assert result["model_used"].startswith(f"Model {model}")


@pytest.mark.parametrize("model", ["A", "B"])
def test_shap_explanation(client, demo_profile, model):
    payload = {**demo_profile, "model": model}

    response = client.post("/predict", json=payload)

    assert response.status_code == 200

    result = response.get_json()

    assert result["success"] is True
    assert result["shap_plot"] is not None
    assert result["shap_plot"].startswith("data:image/png;base64,")
    assert len(result["top_features"]) > 0


def test_model_b_ignores_direct_label_inputs(client, demo_profile):
    original = {**demo_profile, "model": "B"}

    modified = {
        **original,
        "systolic_bp": 165,
        "diastolic_bp": 100,
        "hba1c": 8.5,
        "serum_creatinine": 2.0
    }

    first = client.post("/predict", json=original)
    second = client.post("/predict", json=modified)

    assert first.status_code == 200
    assert second.status_code == 200

    assert first.get_json()["risk_score"] == pytest.approx(
        second.get_json()["risk_score"]
    )



@pytest.mark.parametrize("invalid_input", [
    {"model": "C"},
    {"age": -25},
    {"age": "abc"},
    {"age": ""},
    {"age": None},
    {"age": True},
    {"age": "NaN"},
    {"gender": 5},
    {"height_cm": 0},
    {"serum_creatinine": -1},
    {"hdl_cholesterol": 0},
    {"lymphocyte_pct": 120},
])
def test_invalid_input(client, demo_profile, invalid_input):
    payload = {
        **demo_profile,
        "model": "A",
        **invalid_input
    }

    response = client.post("/predict", json=payload)

    assert response.status_code == 400
    assert response.get_json()["success"] is False


def test_empty_payload(client):
    response = client.post("/predict", json={})

    assert response.status_code == 400
    assert response.get_json()["success"] is False
