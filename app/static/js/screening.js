// BioCascade research demo
const form = document.getElementById('biomarker-form');
const picker = document.querySelector('.model-picker');
const message = document.getElementById('form-message');
const predictButton = document.getElementById('predict-btn');
const profiles = {
 one:{age:55,gender:1,systolic_bp:130,diastolic_bp:85,bmi:28.5,waist_cm:95,height_cm:170,hba1c:6.2,triglycerides:180,hdl_cholesterol:42,total_cholesterol:210,serum_creatinine:1.1,bun:18,uric_acid:6.5,hscrp:3.5,neutrophil_pct:65,lymphocyte_pct:25,hemoglobin:13.5,hematocrit:40,rdw:13.5,ferritin:100,serum_iron:80,sodium:140,potassium:4},
 two:{age:72,gender:2,systolic_bp:165,diastolic_bp:95,bmi:34,waist_cm:110,height_cm:160,hba1c:8.1,triglycerides:250,hdl_cholesterol:32,total_cholesterol:245,serum_creatinine:1.8,bun:30,uric_acid:8,hscrp:8,neutrophil_pct:72,lymphocyte_pct:18,hemoglobin:11.5,hematocrit:35,rdw:16,ferritin:220,serum_iron:55,sodium:138,potassium:4.6}
};
let busy = false;
function selectedModel(){return picker.querySelector('input:checked').value;}
function status(text='',error=false){message.textContent=text;message.classList.toggle('error',error);}
function clearResults(){
 document.getElementById('results-content').style.display='none';
 document.getElementById('waiting-state').style.display='';
 document.getElementById('shap-plot').removeAttribute('src');
 document.getElementById('features-list').replaceChildren();
}
function updateFields(){
 const model=selectedModel();
 form.querySelectorAll('[data-model]').forEach(group=>{
  const active=group.dataset.model==='both'||group.dataset.model===model;
  group.hidden=!active;
  group.querySelectorAll('input,select').forEach(input=>{input.disabled=!active;input.required=active;});
 });
 form.querySelectorAll('.form-section').forEach(section=>{
  const groups=[...section.querySelectorAll('[data-model]')];
  section.hidden=groups.length>0&&groups.every(group=>group.hidden);
 });
 clearResults();status();
}
const requested=new URLSearchParams(location.search).get('model');
if(requested==='A'||requested==='B')picker.querySelector('input[value="'+requested+'"]').checked=true;
picker.addEventListener('change',updateFields);
updateFields();
document.getElementById('load-demo').addEventListener('click',()=>{
 const profile=profiles[document.getElementById('demo-select').value];
 Object.entries(profile).forEach(([id,value])=>{const input=document.getElementById(id);if(input)input.value=value;});
 clearResults();status('Synthetic example loaded. Edit the values or switch models.');
});
document.getElementById('reset-form').addEventListener('click',()=>{form.reset();clearResults();status('Inputs cleared.');});
form.addEventListener('input',event=>{if(event.target.matches('[data-model] input,[data-model] select')){clearResults();status();}});
function setBusy(value){
 busy=value;predictButton.disabled=value;predictButton.classList.toggle('loading',value);
 predictButton.innerHTML=value?'<i class="bi bi-hourglass-split"></i> Analyzing biomarkers…':'<i class="bi bi-cpu-fill"></i> Calculate model score';
 picker.disabled=value;
 form.querySelectorAll('input,select,button[type="button"]').forEach(input=>{const group=input.closest('[data-model]');input.disabled=value||Boolean(group&&group.hidden);});
}
form.addEventListener('submit',async event=>{
 event.preventDefault();if(busy||!form.reportValidity())return;
 const data={model:selectedModel()};
 form.querySelectorAll('[data-model]:not([hidden]) input,[data-model]:not([hidden]) select').forEach(input=>{data[input.id]=Number(input.value);});
 if(data.model==='A'&&data.systolic_bp<data.diastolic_bp){status('Systolic pressure must not be lower than diastolic pressure.',true);return;}
 clearResults();setBusy(true);status('Calculating the research proxy score…');
 try{
  const response=await fetch('/predict',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  const result=await response.json();
  if(!response.ok||!result.success)throw new Error(result.error||'Prediction failed.');
  displayResults(result);status('Prediction complete.');
 }catch(error){status('Prediction failed: '+error.message,true);}finally{setBusy(false);}
});
function displayResults(result){
 document.getElementById('waiting-state').style.display='none';
 document.getElementById('results-content').style.display='block';
 const high=result.risk_class==='High Risk';
 const gauge=document.querySelector('.gauge-fill'),circumference=2*Math.PI*130;
 gauge.setAttribute('class','gauge-fill '+(high?'high-risk':'low-risk'));
 gauge.style.strokeDasharray=circumference;gauge.style.strokeDashoffset=circumference*(1-result.risk_score);
 const percentage=document.getElementById('risk-percentage');
 percentage.textContent=(result.risk_score*100).toFixed(1)+'%';percentage.classList.add('show');
 const classification=document.getElementById('risk-classification');
 classification.className='risk-classification show '+(high?'high':'low');classification.textContent=high?'High proxy risk':'Low proxy risk';
 document.getElementById('model-used').textContent=result.model_used;
 const shapSection=document.querySelector('.shap-explanation');shapSection.classList.add('show');shapSection.hidden=!result.shap_plot;
 if(result.shap_plot)document.getElementById('shap-plot').src=result.shap_plot;
 const list=document.getElementById('features-list');list.replaceChildren();
 for(const feat of result.top_features||[]){
  const positive=feat.shap_value>0,item=document.createElement('div');item.className='feature-item show '+(positive?'positive':'negative');
  const name=document.createElement('div'),title=document.createElement('div'),value=document.createElement('div');
  title.className='feature-name';title.textContent=feat.feature;value.className='feature-value';value.textContent='Value: '+Number(feat.feature_value).toFixed(2);name.append(title,value);
  const impact=document.createElement('div'),score=document.createElement('div'),label=document.createElement('div');
  impact.className='feature-impact';score.className='shap-value';score.textContent=(positive?'+':'')+Number(feat.shap_value).toFixed(3);score.style.color=positive?'#f87171':'#34d399';
  label.className='impact-label';label.textContent=positive?'Raises model score':feat.shap_value<0?'Lowers model score':'No score change';impact.append(score,label);item.append(name,impact);list.append(item);
 }
 document.querySelector('.top-features').classList.add('show');
 if(matchMedia('(max-width:950px)').matches)document.getElementById('results-panel').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'auto':'smooth',block:'start'});
}
