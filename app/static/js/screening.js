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
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));

function animateScore(gauge, percentage, circumference, target, duration) {
 if (!duration) {
  gauge.style.strokeDashoffset = circumference * (1 - target);
  percentage.textContent = (target * 100).toFixed(1) + '%';
  return Promise.resolve();
 }
 return new Promise(resolve => {
  let start;
  function frame(now) {
   if (start === undefined) start = now;
   const progress = Math.min((now - start) / duration, 1);
   const eased = 1 - Math.pow(1 - progress, 3);
   const value = target * eased;
   gauge.style.strokeDashoffset = circumference * (1 - value);
   percentage.textContent = (value * 100).toFixed(1) + '%';
   if (progress < 1 && !reducedMotion.matches) {
    requestAnimationFrame(frame);
   } else {
    gauge.style.strokeDashoffset = circumference * (1 - target);
    percentage.textContent = (target * 100).toFixed(1) + '%';
    resolve();
   }
  }
  requestAnimationFrame(frame);
 });
}
function selectedModel(){return picker.querySelector('input:checked').value;}
function status(text='',error=false){message.textContent=text;message.classList.toggle('error',error);}
function clearResults(){
 document.getElementById('results-content').style.display='none';
 document.getElementById('waiting-state').style.display='';
 document.getElementById('shap-plot').removeAttribute('src');
 document.getElementById('features-list').replaceChildren();
 document.getElementById('results-panel').removeAttribute('aria-busy');
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
 const started = performance.now();
 document.getElementById('results-panel').setAttribute('aria-busy','true');
 try{
  const response=await fetch('/predict',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  const result=await response.json();
  if(!response.ok||!result.success)throw new Error(result.error||'Prediction failed.');
  if (!reducedMotion.matches) await wait(Math.max(0, 600 - (performance.now() - started)));
  status('Revealing model result…');
  await displayResults(result);
  status('Prediction complete.');
 }catch(error){clearResults();status('Prediction failed: '+error.message,true);}finally{document.getElementById('results-panel').removeAttribute('aria-busy');setBusy(false);}
});
async function displayResults(result){
 const panel = document.getElementById('results-panel');
 const content = document.getElementById('results-content');
 const target = Number(result.risk_score);
 if (!Number.isFinite(target) || target < 0 || target > 1) throw new Error('Invalid model score.');
 const high = result.risk_class === 'High Risk';
 const gauge = document.querySelector('.gauge-fill');
 const circumference = 2 * Math.PI * Number(gauge.getAttribute('r'));
 const percentage = document.getElementById('risk-percentage');
 const classification = document.getElementById('risk-classification');
 const model = document.getElementById('model-used');
 const note = content.querySelector('.risk-score-display .form-note');
 const shapSection = content.querySelector('.shap-explanation');
 const topSection = content.querySelector('.top-features');
 const plot = document.getElementById('shap-plot');
 const list = document.getElementById('features-list');
 const pause = ms => reducedMotion.matches ? Promise.resolve() : wait(ms);

 // Reset every result, including repeated predictions with the same score.
 gauge.setAttribute('class','gauge-fill ' + (high ? 'high-risk' : 'low-risk'));
 gauge.style.strokeDasharray = circumference;
 gauge.style.strokeDashoffset = circumference;
 percentage.textContent = '0.0%';
 percentage.classList.add('show');
 classification.className = 'risk-classification ' + (high ? 'high' : 'low');
 classification.textContent = high ? 'High proxy risk' : 'Low proxy risk';
 model.textContent = result.model_used;
 for (const element of [classification, model, note, shapSection, topSection]) {
  element.hidden = true;
  element.classList.remove('show', 'result-reveal');
 }
 list.replaceChildren();
 if (result.shap_plot) plot.src = result.shap_plot;
 document.getElementById('waiting-state').style.display = 'none';
 content.style.display = 'block';
 if (matchMedia('(max-width:950px)').matches) {
  panel.scrollIntoView({behavior:reducedMotion.matches?'auto':'smooth',block:'start'});
 }

 await animateScore(gauge, percentage, circumference, target, reducedMotion.matches ? 0 : 1400);

 function reveal(element) {
  element.hidden = false;
  element.classList.add('show', 'result-reveal');
 }
 reveal(classification);
 reveal(model);
 reveal(note);
 await pause(200);
 if (result.shap_plot) {
  reveal(shapSection);
  await pause(400);
 }
 for(const feat of result.top_features||[]){
  const positive=feat.shap_value>0,item=document.createElement('div');item.className='feature-item '+(positive?'positive':'negative');
  const name=document.createElement('div'),title=document.createElement('div'),value=document.createElement('div');
  title.className='feature-name';title.textContent=feat.feature;value.className='feature-value';value.textContent='Value: '+Number(feat.feature_value).toFixed(2);name.append(title,value);
  const impact=document.createElement('div'),score=document.createElement('div'),label=document.createElement('div');
  impact.className='feature-impact';score.className='shap-value';score.textContent=(positive?'+':'')+Number(feat.shap_value).toFixed(3);score.style.color=positive?'#f87171':'#34d399';
  label.className='impact-label';label.textContent=positive?'Raises model score':feat.shap_value<0?'Lowers model score':'No score change';impact.append(score,label);item.append(name,impact);list.append(item);
 }
 if (list.children.length) {
  reveal(topSection);
  for (const item of list.children) {
   item.classList.add('show', 'result-reveal');
   await pause(100);
  }
 }
}
