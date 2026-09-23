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
function buildPlan(){
 const idea=$("idea").value.trim();
 if(!idea){$("planStatus").textContent="पहले creative idea लिखें.";return}
 const styles=selectedStyles();
 const title=idea.split(/[.!?।]/)[0].slice(0,48)||"Untitled Film";
 const p={id:crypto.randomUUID(),title,idea,language:$("lang").value,format:$("format").value,styles,created:Date.now()};
 projects=[p,...projects.filter(x=>x.title!==title)].slice(0,20);
 localStorage.setItem(KEY,JSON.stringify(projects));
 const scenes=Math.max(4,Math.min(24,Math.ceil(idea.length/35)));
 const chars=styles.includes("Kids & Family")?3:2;
 $("projectState").textContent="ORCHESTRATED";$("stageTitle").textContent=title;
 $("canvasState").textContent="PLAN READY";$("canvasTitle").textContent=title;
 $("canvasText").textContent="Production graph prepared: story → characters → storyboard → music → animation → QC.";
 $("sceneCount").textContent=scenes;$("charCount").textContent=chars;$("shotCount").textContent=scenes*4;$("musicCount").textContent=1;
 $("planStatus").textContent="Production plan तैयार है — वास्तविक AI rendering के लिए configured model/engine adapters जोड़ें.";
 render();
}
document.querySelectorAll("#styles button").forEach(b=>b.onclick=()=>b.classList.toggle("on"));
$("plan").onclick=buildPlan;
$("newProject").onclick=()=>{$("idea").focus();window.scrollTo({top:$("idea").getBoundingClientRect().top+scrollY-90,behavior:"smooth"})};
$("clearProjects").onclick=()=>{projects=[];localStorage.removeItem(KEY);render()};
render();