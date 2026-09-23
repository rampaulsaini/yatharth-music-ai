const $=id=>document.getElementById(id);
const KEY="yatharth_creative_projects";
let projects=JSON.parse(localStorage.getItem(KEY)||"[]");
function selectedStyles(){return [...document.querySelectorAll("#styles button.on")].map(x=>x.textContent)}
function esc(s){return String(s).replace(/[&<>'"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[c]))}
function render(){
 const el=$("projectsList");
 if(!projects.length){el.innerHTML='<div class="empty">No saved production projects yet.</div>';return}
 el.innerHTML=projects.slice(0,12).map(p=>'<div class="project"><b>'+esc(p.title)+'</b><small>'+esc(p.format)+' • '+esc(p.language)+'</small><small>'+p.styles.map(esc).join(" • ")+'</small></div>').join("");
}
function localPlan(idea,styles){
 const scenes=Math.max(4,Math.min(30,Math.ceil(idea.length/45)));
 return {status:"REVIEW_REQUIRED",title:idea.split(/[.!?।]/)[0].slice(0,64)||"Untitled Production",counts:{scenes,characters:styles.includes("Kids & Family")?3:2,shots:scenes*4,music:1},agents:[],review_required:true,render_available:false};
}
async function buildPlan(){
 const idea=$("idea").value.trim();
 if(!idea){$("planStatus").textContent="पहले creative idea लिखें.";return}
 const styles=selectedStyles();
 const payload={idea,language:$("lang").value,format:$("format").value,styles};
 $("planStatus").textContent="Automission agents production graph तैयार कर रहे हैं…";
 $("projectState").textContent="ORCHESTRATING";
 try{
   const response=await fetch("/api/studio/plan",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
   if(!response.ok) throw new Error("studio API unavailable");
   const data=await response.json();
   applyPlan(data,idea,styles);
 }catch(error){
   const data=localPlan(idea,styles);
   applyPlan(data,idea,styles);
   $("planStatus").textContent="Local planning mode सक्रिय है — backend उपलब्ध होने पर वही production contract sync होगा.";
 }
}
function applyPlan(data,idea,styles){
 const p={id:data.plan_id||crypto.randomUUID(),title:data.title,idea,language:$("lang").value,format:$("format").value,styles,created:Date.now(),status:data.status};
 projects=[p,...projects.filter(x=>x.title!==p.title)].slice(0,20);
 localStorage.setItem(KEY,JSON.stringify(projects));
 $("projectState").textContent=data.status==="REVIEW_REQUIRED"?"REVIEW REQUIRED":"ORCHESTRATED";
 $("stageTitle").textContent=data.title;
 $("canvasState").textContent=data.status;
 $("canvasTitle").textContent=data.title;
 $("canvasText").textContent="Production graph prepared: story → characters → storyboard → music → animation → editing → QC.";
 $("sceneCount").textContent=data.counts.scenes;
 $("charCount").textContent=data.counts.characters;
 $("shotCount").textContent=data.counts.shots;
 $("musicCount").textContent=data.counts.music;
 $("planStatus").textContent=data.render_available
   ?"Production plan तैयार है — configured music engine integration उपलब्ध है; animation rendering adapters अलग से connect होंगे."
   :"Production plan तैयार है — rendering उपलब्ध नहीं है; approved model/engine adapters जोड़ने के बाद generation शुरू की जा सकती है.";
 render();
}
document.querySelectorAll("#styles button").forEach(b=>b.onclick=()=>b.classList.toggle("on"));
$("plan").onclick=buildPlan;
$("newProject").onclick=()=>{$("idea").focus();window.scrollTo({top:$("idea").getBoundingClientRect().top+scrollY-90,behavior:"smooth"})};
$("clearProjects").onclick=()=>{projects=[];localStorage.removeItem(KEY);render()};
render();