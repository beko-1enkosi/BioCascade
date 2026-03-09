// ==========================================================================
// BIOCASCADE SCREENING TOOL - FRONTEND LOGIC
// ==========================================================================

document.getElementById('predict-btn').addEventListener('click', async () => {
    
    // Collect all input values
    const data = collectFormData();
    
    // Show loading state
    setLoadingState(true);
    
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
            await displayResults(result);
        } else {
            showError(result.error);
        }
        
    } catch (error) {
        showError('Request failed: ' + error.message);
    } finally {
        setLoadingState(false);
    }
});

// ==========================================================================
// HELPER FUNCTIONS
// ==========================================================================

function collectFormData() {
    return {
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
        rdw: document.getElementById('rdw').value,
        ferritin: 100,  // Default value
        serum_iron: 80,  // Default value
        sodium: 140,     // Default value
        potassium: 4.0   // Default value
    };
}

function setLoadingState(isLoading) {
    const btn = document.getElementById('predict-btn');
    
    if (isLoading) {
        btn.classList.add('loading');
        btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Analyzing Biomarkers...';
    } else {
        btn.classList.remove('loading');
        btn.innerHTML = '<i class="bi bi-cpu-fill"></i> Calculate Risk Score';
    }
}

async function displayResults(result) {
    // Hide waiting state, show results
    document.getElementById('waiting-state').style.display = 'none';
    document.getElementById('results-content').style.display = 'block';
    
    // Animate gauge
    await animateGauge(result.risk_score);
    
    // Show risk classification
    await delay(800);
    showRiskClassification(result.risk_class, result.risk_score);
    
    // Show model badge
    document.getElementById('model-used').textContent = result.model_used;
    
    // Show SHAP plot
    await delay(400);
    showShapPlot(result.shap_plot);
    
    // Show top features
    await delay(200);
    showTopFeatures(result.top_features);
    
    // Smooth scroll to results
    document.getElementById('results-panel').scrollIntoView({ 
        behavior: 'smooth', 
        block: 'nearest' 
    });
}

function animateGauge(riskScore) {
    return new Promise((resolve) => {
        const percentage = (riskScore * 100).toFixed(1);
        const gaugeElement = document.querySelector('.gauge-fill');
        const percentageElement = document.getElementById('risk-percentage');
        
        // Calculate circle parameters
        const radius = 130;
        const circumference = 2 * Math.PI * radius;
        
        // Set initial state
        gaugeElement.style.strokeDasharray = circumference;
        gaugeElement.style.strokeDashoffset = circumference;
        
        // Determine risk level and color
        let riskLevel, gaugeClass;
        if (riskScore < 0.3) {
            riskLevel = 'Low';
            gaugeClass = 'low-risk';
        } else if (riskScore < 0.7) {
            riskLevel = 'Medium';
            gaugeClass = 'medium-risk';
        } else {
            riskLevel = 'High';
            gaugeClass = 'high-risk';
        }
        
        gaugeElement.className = `gauge-fill ${gaugeClass}`;
        
        // Animate the gauge fill
        setTimeout(() => {
            const offset = circumference - (riskScore * circumference);
            gaugeElement.style.strokeDashoffset = offset;
        }, 100);
        
        // Animate the percentage number
        setTimeout(() => {
            percentageElement.textContent = percentage + '%';
            percentageElement.classList.add('show');
            
        }, 300);
        
        // Counter animation
        animateCounter(0, parseFloat(percentage), 1500, (val) => {
            percentageElement.textContent = val.toFixed(1) + '%';
        });
        
        setTimeout(resolve, 2000);
    });
}

function animateCounter(start, end, duration, callback) {
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Ease out cubic
        const easeProgress = 1 - Math.pow(1 - progress, 3);
        const current = start + (end - start) * easeProgress;
        
        callback(current);
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

function showRiskClassification(riskClass, riskScore) {
    const classElement = document.getElementById('risk-classification');
    
    let className = 'low';
    if (riskScore >= 0.7) className = 'high';
    else if (riskScore >= 0.3) className = 'medium';
    
    classElement.className = `risk-classification ${className}`;
    classElement.textContent = riskClass;
    
    setTimeout(() => {
        classElement.classList.add('show');
    }, 100);
}

function showShapPlot(plotData) {
    const shapSection = document.querySelector('.shap-explanation');
    const plotImg = document.getElementById('shap-plot');
    
    if (plotData) {
        plotImg.src = plotData;
        setTimeout(() => {
            shapSection.classList.add('show');
        }, 100);
    }
}

function showTopFeatures(features) {
    const featuresList = document.getElementById('features-list');
    const topSection = document.querySelector('.top-features');
    
    featuresList.innerHTML = '';
    
    features.forEach((feat, index) => {
        const div = document.createElement('div');
        div.className = `feature-item ${feat.shap_value > 0 ? 'positive' : 'negative'}`;
        
        const impactColor = feat.shap_value > 0 ? '#ef4444' : '#10b981';
        const impactText = feat.shap_value > 0 ? 'Risk Factor' : 'Protective';
        
        div.innerHTML = `
            <div>
                <div class="feature-name">${feat.feature}</div>
                <div class="feature-value">Value: ${feat.feature_value.toFixed(2)}</div>
            </div>
            <div class="feature-impact">
                <div class="shap-value" style="color: ${impactColor}">
                    ${feat.shap_value > 0 ? '+' : ''}${feat.shap_value.toFixed(3)}
                </div>
                <div class="impact-label" style="color: ${impactColor}">
                    ${impactText}
                </div>
            </div>
        `;
        
        featuresList.appendChild(div);
        
        // Stagger animation
        setTimeout(() => {
            div.classList.add('show');
        }, index * 100);
    });
    
    setTimeout(() => {
        topSection.classList.add('show');
    }, 100);
}

function showError(message) {
    alert('❌ Error: ' + message);
}

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}