
import pytest

from app.app import app, REQUIRED_FIELDS


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
        "serum_iron": 80,
        "sodium": 140,
        "potassium": 4.0
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


# Test the raw input contract independently of the backend constants.
# These include the inputs used only for derived features.
COMMON_INPUTS = {
    "age", "gender", "bmi", "waist_cm", "height_cm",
    "hdl_cholesterol", "total_cholesterol", "uric_acid", "hscrp",
    "neutrophil_pct", "lymphocyte_pct", "hemoglobin", "hematocrit",
    "rdw", "sodium", "potassium",
}
EXPECTED_INPUTS = {
    "A": COMMON_INPUTS | {
        "systolic_bp", "diastolic_bp", "hba1c", "triglycerides",
        "serum_creatinine", "bun",
    },
    "B": COMMON_INPUTS | {"ferritin", "serum_iron"},
}


def test_required_field_contract():
    assert REQUIRED_FIELDS == EXPECTED_INPUTS


def model_payload(profile, model):
    return {"model": model, **{key: profile[key] for key in EXPECTED_INPUTS[model]}}


@pytest.mark.parametrize("model", ["A", "B"])
def test_exact_model_payload_succeeds(client, demo_profile, model):
    response = client.post("/predict", json=model_payload(demo_profile, model))
    assert response.status_code == 200
    assert response.get_json()["success"] is True


@pytest.mark.parametrize("model, field", [
    (model, field)
    for model, fields in EXPECTED_INPUTS.items()
    for field in sorted(fields)
])
def test_every_required_field_is_enforced(client, demo_profile, model, field):
    payload = model_payload(demo_profile, model)
    del payload[field]
    response = client.post("/predict", json=payload)
    assert response.status_code == 400
    result = response.get_json()
    assert result["success"] is False
    assert field in result["error"]
    assert "risk_score" not in result


@pytest.mark.parametrize("model", ["A", "B"])
def test_model_only_is_rejected(client, model):
    response = client.post("/predict", json={"model": model})
    assert response.status_code == 400
    assert "Missing required biomarkers" in response.get_json()["error"]


@pytest.mark.parametrize("bad_value", [" ", [], {}, "Infinity", 1e100])
def test_malformed_biomarker_rejected(client, demo_profile, bad_value):
    payload = model_payload(demo_profile, "B")
    payload["age"] = bad_value
    response = client.post("/predict", json=payload)
    assert response.status_code == 400
    assert response.get_json()["success"] is False


def test_numeric_string_gender_normalized(client, demo_profile):
    payload = model_payload(demo_profile, "B")
    payload["gender"] = "1.0"
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    assert response.get_json()["success"] is True


def test_unknown_biomarker_rejected(client, demo_profile):
    payload = model_payload(demo_profile, "A")
    payload["made_up_biomarker"] = 12
    response = client.post("/predict", json=payload)
    assert response.status_code == 400
    assert "Unrecognized biomarker" in response.get_json()["error"]


def test_inverted_blood_pressure_rejected(client, demo_profile):
    payload = model_payload(demo_profile, "A")
    payload.update(systolic_bp=80, diastolic_bp=120)
    response = client.post("/predict", json=payload)
    assert response.status_code == 400
    assert "Systolic pressure" in response.get_json()["error"]


def test_malformed_json_rejected(client):
    response = client.post("/predict", data="{", content_type="application/json")
    assert response.status_code == 400
    assert response.get_json()["success"] is False


def test_non_object_json_rejected(client):
    response = client.post("/predict", json=["A", 55])
    assert response.status_code == 400
    assert response.get_json()["success"] is False


def test_inactive_biomarkers_do_not_affect_model_b(client, demo_profile):
    payload = model_payload(demo_profile, "B")
    baseline = client.post("/predict", json=payload)
    # Known inactive inputs are ignored, even if malformed.
    payload.update(systolic_bp="not a number", serum_creatinine=None,
                   hba1c=-10, triglycerides=999)
    modified = client.post("/predict", json=payload)
    assert baseline.status_code == modified.status_code == 200
    assert baseline.get_json()["risk_score"] == pytest.approx(
        modified.get_json()["risk_score"]
    )
