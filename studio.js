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
let activeRunId=null;
const stageLabels={story:"Story",characters:"Characters",storyboard:"Storyboard",music:"Music",animation:"Animation",editing:"Editing",qc:"Quality Control"};
function stageClass(status){return String(status||"PLANNED").toLowerCase().replace(/[^a-z_]/g,"-")}
function renderRun(data){
  activeRunId=data.run_id||activeRunId;
  $("runId").textContent=activeRunId||"—"; $("runBadge").textContent=data.status||"READY";
  $("runMode").textContent=data.render_available?"RENDER ADAPTER AVAILABLE":"PLANNING / ADAPTERS REQUIRED";
  const stages=data.stages||[], ready=stages.filter(s=>["READY","COMPLETED","DONE"].includes(s.status)).length;
  $("runProgressText").textContent=ready+" / "+stages.length+" stages";
  $("runProgressBar").style.width=(stages.length?Math.round(ready/stages.length*100):0)+"%";
  $("stageList").innerHTML=stages.map((s,i)=>'<div class="run-stage"><span class="stage-num">'+String(i+1).padStart(2,"0")+'</span><div><b>'+esc(stageLabels[s.stage]||s.stage)+'</b><small>'+esc(s.agent||"agent")+'</small></div><i class="state-'+stageClass(s.status)+'">'+esc(s.status)+'</i>'+((s.status==="PLANNED")?'<button class="ghost stage-execute" data-stage="'+esc(s.stage)+'">Execute</button>':'')+((s.stage==="music"&&["READY","COMPLETED","DONE"].includes(s.status))?'<button class="ghost music-generate">Generate Music</button>':'')+'</div>').join("");
  $("artifactList").innerHTML=(data.artifacts||[]).map(a=>'<div class="artifact"><div><b>'+esc(a.name)+'</b><small>'+esc(a.type||"structured artifact")+'</small></div><div class="artifact-actions"><span>'+esc(a.status||"PLANNED")+'</span><button class="ghost artifact-open" data-artifact="'+encodeURIComponent(a.name)+'">View</button><button class="ghost artifact-download" data-artifact="'+encodeURIComponent(a.name)+'">JSON</button></div></div>').join("")||'<div class="empty">No run artifacts yet.</div>';
  document.querySelectorAll(".artifact-open").forEach(b=>b.onclick=()=>viewArtifact(decodeURIComponent(b.dataset.artifact)));
  document.querySelectorAll(".artifact-download").forEach(b=>b.onclick=()=>downloadArtifact(decodeURIComponent(b.dataset.artifact))); document.querySelectorAll(".stage-execute").forEach(b=>b.onclick=()=>executeStage(b.dataset.stage)); document.querySelectorAll(".music-generate").forEach(b=>b.onclick=generateStudioMusic);
  $("downloadManifest").disabled=!activeRunId; $("reviewGate").classList.toggle("attention",!!data.review_required);
}
async function startProduction(){
  const idea=$("idea").value.trim();
  if(!idea){$("planStatus").textContent="पहले creative idea लिखें."; $("idea").focus(); return}
  const styles=selectedStyles(), payload={idea,language:$("lang").value,format:$("format").value,styles};
  $("runProduction").disabled=true; $("runProduction").textContent="⏳ Starting Automission…";
  try{
    const r=await fetch("/api/studio/run",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
    if(!r.ok) throw new Error("run API unavailable");
    const data=await r.json(); renderRun(data);
    $("productionRun").scrollIntoView({behavior:"smooth",block:"start"});
    $("planStatus").textContent="Automission production run created. Planning artifacts are registered; execution adapters remain explicit.";
    $("projectState").textContent=data.status||"RUN CREATED";
  }catch(e){
    $("runBadge").textContent="LOCAL FALLBACK"; $("runMode").textContent="NO BACKEND";
    $("planStatus").textContent="Backend unavailable — local plan remains available; no fabricated production run was created.";
  }finally{$("runProduction").disabled=false; $("runProduction").textContent="🚀 Start Automission Production"}
}
async function generateStudioMusic(){
  if(!activeRunId)return;
  try{
    const r=await fetch("/api/studio/runs/"+encodeURIComponent(activeRunId)+"/music-task",{method:"POST"});
    const data=await r.json();
    if(!r.ok)throw new Error(data.detail||"music hand-off failed");
    $("planStatus").textContent=data.demo?"Music task connected — DEMO audio is ready. Connect ACE-Step for real generation.":"Music task connected — generation is running through the configured music engine.";
    const rr=await fetch("/api/studio/runs/"+encodeURIComponent(activeRunId));
    if(rr.ok)renderRun(await rr.json());
  }catch(e){$("planStatus").textContent="Music hand-off blocked: "+e.message}
}
async function executeStage(stage){
  if(!activeRunId)return;
  try{
    const r=await fetch("/api/studio/runs/"+encodeURIComponent(activeRunId)+"/stages/"+encodeURIComponent(stage)+"/execute",{method:"POST"});
    const data=await r.json();
    if(!r.ok)throw new Error(data.detail||"stage execution failed");
    renderRun(data);
    $("planStatus").textContent=(stageLabels[stage]||stage)+" stage executed: structured hand-off updated.";
  }catch(e){$("planStatus").textContent="Stage execution blocked: "+e.message}
}
async function refreshRun(){
  if(!activeRunId)return;
  try{
    const r=await fetch("/api/studio/runs/"+encodeURIComponent(activeRunId));
    if(r.ok)renderRun(await r.json());
  }catch(e){}
}
async function fetchArtifact(name){
  if(!activeRunId)return null;
  const r=await fetch("/api/studio/runs/"+encodeURIComponent(activeRunId)+"/artifacts/"+encodeURIComponent(name));
  if(!r.ok)throw new Error("artifact unavailable");
  return r.json();
}
async function viewArtifact(name){
  try{
    const data=await fetchArtifact(name);
    const pretty=JSON.stringify(data.data||data,null,2);
    $("planStatus").textContent=name+" loaded — structured planning artifact ready for review/export.";
    $("canvasTitle").textContent=data.project?.title||name;
    $("canvasText").textContent=pretty.slice(0,500)+(pretty.length>500?"…":"");
  }catch(e){$("planStatus").textContent="Artifact could not be loaded from the current run."}
}
async function downloadArtifact(name){
  try{
    const data=await fetchArtifact(name);
    const blob=new Blob([JSON.stringify(data,null,2)],{type:"application/json"});
    const url=URL.createObjectURL(blob),a=document.createElement("a"); a.href=url; a.download="yatharth-"+name; a.click(); URL.revokeObjectURL(url);
  }catch(e){$("planStatus").textContent="Artifact download unavailable."}
}
async function exportManifest(){
  if(!activeRunId)return;
  const r=await fetch("/api/studio/runs/"+encodeURIComponent(activeRunId)+"/manifest"); if(!r.ok)return;
  const blob=new Blob([JSON.stringify(await r.json(),null,2)],{type:"application/json"});
  const url=URL.createObjectURL(blob),a=document.createElement("a"); a.href=url; a.download="yatharth-production-"+activeRunId+".json"; a.click(); URL.revokeObjectURL(url);
}
$("runProduction").onclick=startProduction; $("downloadManifest").onclick=exportManifest; setInterval(refreshRun,15000);
