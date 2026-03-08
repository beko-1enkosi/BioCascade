document.getElementById('predict-btn').addEventListener('click', async () => {
    
    // Collect all input values
    const data = {
        model: document.getElementById('model-select').value,
        age: document.getElementById('age').value,
        gender: document.getElementById('gender').value,
        systolic_bp: document.getElementById('systolic_bp').value,
        diastolic_bp: document.getElementById('diastolic_bp').value,
        bmi: document.getElementById('bmi').value,
        waist_cm: document.getElementById('waist_cm').value,
        height_cm: document.getElementById('height_cm').value,
        hba1c: document.getElementById('hba1c').value,
        fasting_glucose: document.getElementById('fasting_glucose').value,
        triglycerides: document.getElementById('triglycerides').value,
        hdl_cholesterol: document.getElementById('hdl_cholesterol').value,
        ldl_cholesterol: document.getElementById('ldl_cholesterol').value,
        total_cholesterol: document.getElementById('total_cholesterol').value,
        serum_creatinine: document.getElementById('serum_creatinine').value,
        bun: document.getElementById('bun').value,
        uric_acid: document.getElementById('uric_acid').value,
        hscrp: document.getElementById('hscrp').value,
        neutrophil_pct: document.getElementById('neutrophil_pct').value,
        lymphocyte_pct: document.getElementById('lymphocyte_pct').value,
        hemoglobin: document.getElementById('hemoglobin').value,
        hematocrit: document.getElementById('hematocrit').value,
        rdw: document.getElementById('rdw').value
    };
    
    // Show loading state
    document.getElementById('predict-btn').innerHTML = '<i class="bi bi-hourglass-split"></i> Calculating...';
    
    try {
        const response = await fetch('/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayResults(result);
        } else {
            alert('Error: ' + result.error);
        }
        
    } catch (error) {
        alert('Request failed: ' + error.message);
    }
    
    // Reset button
    document.getElementById('predict-btn').innerHTML = '<i class="bi bi-cpu-fill"></i> Calculate Risk Score';
});

function displayResults(result) {
    // Hide waiting state, show results
    document.getElementById('waiting-state').style.display = 'none';
    document.getElementById('results-content').style.display = 'block';
    
    // Update risk score
    const riskPercent = (result.risk_score * 100).toFixed(1);
    document.getElementById('risk-value').textContent = riskPercent + '%';
    document.getElementById('risk-label').textContent = result.risk_class;
    document.getElementById('model-used').textContent = result.model_used;
    
    // Update SHAP plot
    if (result.shap_plot) {
        document.getElementById('shap-plot').src = result.shap_plot;
    }
    
    // Update top features
    const featuresList = document.getElementById('features-list');
    featuresList.innerHTML = '';
    
    result.top_features.forEach(feat => {
        const div = document.createElement('div');
        div.className = `feature-item ${feat.shap_value > 0 ? 'positive' : 'negative'}`;
        div.innerHTML = `
            <div>
                <div class="feature-name">${feat.feature}</div>
                <div class="feature-impact">${feat.impact}</div>
            </div>
            <div style="font-weight:700; color:${feat.shap_value > 0 ? '#ef4444' : '#10b981'}">
                ${feat.shap_value > 0 ? '+' : ''}${feat.shap_value.toFixed(3)}
            </div>
        `;
        featuresList.appendChild(div);
    });
    
    // Smooth scroll to results
    document.getElementById('results-panel').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}