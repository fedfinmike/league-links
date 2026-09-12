const SEASON_CATALOGUES_URL='data/season-catalogues.json.gz?v=26';
state.seasonCatalogues=new Map();
state.catalogueCoverage=[];
let seasonCataloguesLoaded=false;
let seasonCataloguesPromise=null;

async function ensureSeasonCatalogues(){
 if(seasonCataloguesLoaded)return true;
 if(seasonCataloguesPromise)return seasonCataloguesPromise;
 seasonCataloguesPromise=(async()=>{
  try{
   const r=await fetch(SEASON_CATALOGUES_URL,{cache:'no-cache'});
   if(!r.ok||!('DecompressionStream'in window))return false;
   const stream=r.body.pipeThrough(new DecompressionStream('gzip'));
   const payload=JSON.parse(await new Response(stream).text());
   if(!payload||payload.version!==26)return false;
   const map=new Map();
   for(const [competition,year,team,id,name,appearances,slug] of payload.rows||[]){
    const key=`${competition}|${year}|${team}`;
    if(!map.has(key))map.set(key,[]);
    map.get(key).push({id:id==null?null:String(id),name,appearances:Number(appearances||0),slug:slug||''});
   }
   for(const rows of map.values())rows.sort((a,b)=>b.appearances-a.appearances||a.name.localeCompare(b.name));
   state.seasonCatalogues=map;
   state.catalogueCoverage=payload.coverage||[];
   seasonCataloguesLoaded=true;return true;
  }catch(e){console.warn('Season catalogues unavailable',e);return false}
 })();
 return seasonCataloguesPromise;
}

function catalogueKeysForCompetition(comp){return[...state.seasonCatalogues.keys()].filter(k=>k.startsWith(`${comp}|`))}

// Cleaner public UI without changing player-history logic.
window.addEventListener('DOMContentLoaded',()=>{
 const style=document.createElement('style');
 style.textContent=`
  .topactions{display:none!important}
  .topcopy small{display:none}
  .competition-card{min-height:118px;padding:18px}
  .competition-card h3{margin:0;font-size:18px}
  .competition-card .meta{margin-top:auto;padding-top:18px}
  .competition-ad{margin-top:18px}
  .coverage-rule{margin:12px 2px 0;color:#6f8195;font-size:11px}
  @media(max-width:760px){
   .topcopy small{display:block;font-size:8px;letter-spacing:1px;color:#66778c;margin-bottom:1px}
   .competition-grid{grid-template-columns:1fr 1fr}
  }
  @media(max-width:520px){.competition-grid{grid-template-columns:1fr}}
 `;
 document.head.appendChild(style);

 const compHead=document.querySelector('#view-competitions .sectionhead');
 if(compHead){
  const eyebrow=compHead.querySelector('.eyebrow');
  const h=compHead.querySelector('h1');
  const p=compHead.querySelector('p');
  if(eyebrow)eyebrow.remove();
  if(h)h.textContent='Coverage';
  if(p)p.textContent='What is live now, and what is being added.';
 }

 document.querySelectorAll('#view-competitions .simple-note').forEach(x=>x.remove());
 const grid=document.querySelector('#competitionGrid');
 if(grid&&!document.querySelector('#competitionAd')){
  grid.insertAdjacentHTML('afterend',`<aside class="ad-slot ad-wide competition-ad" id="competitionAd" aria-label="Advertisement"><span>Advertisement</span><div><strong>Partner space</strong><small>Reserved for a future sponsor.</small></div></aside><div class="coverage-rule">Player links only count confirmed appearances in the same team and match.</div>`);
 }

 function actualYears(comp){
  const years=[...state.rosters.keys()].filter(k=>k.startsWith(`${comp}|`)).map(k=>Number(k.split('|')[1])).filter(Number.isFinite);
  return [...new Set(years)].sort((a,b)=>a-b);
 }
 function coverageLabel(c){
  if(c.id==='NRL'||c.id==='State of Origin')return'2000–2026';
  const years=actualYears(c.id);
  if(years.length)return years.length===1?`${years[0]} · partial`:`${years[0]}–${years[years.length-1]} · partial`;
  return String(c.years||'').replace(/ target$/,'');
 }
 function statusLabel(c){
  if(c.id==='NRL'||c.id==='State of Origin')return['Live','live'];
  if(actualYears(c.id).length)return['Matches loaded','live'];
  if(c.id==='International'||(TEAM_DIRECTORY[c.id]?.teams||[]).length)return['Teams mapped','building'];
  return['Building','building'];
 }
 renderCompetitions=function(){
  const target=document.querySelector('#competitionGrid');if(!target)return;
  target.innerHTML=COMPETITIONS.map(c=>{const [label,cls]=statusLabel(c);return`<article class="competition-card card"><h3>${esc(c.name)}</h3><div class="meta"><span>${esc(coverageLabel(c))}</span><span class="comp-status ${cls}">${label}</span></div></article>`}).join('');
 };

 const baseApplyRoute=applyRoute;
 applyRoute=function(raw=currentRoute()){
  baseApplyRoute(raw);
  const name=(raw||currentRoute()).split('/')[0]||'home';
  const title={home:'Home',players:'Players',player:'Players',connect:'Connect',teams:'Teams',competitions:'Competitions'}[name]||'League Links';
  const page=document.querySelector('#pageTitle');if(page)page.textContent=title;
 };

 const brandSmall=document.querySelector('.topcopy small');
 if(brandSmall)brandSmall.textContent='LEAGUE LINKS';
 if(state.loaded)renderCompetitions();
});

// v0.27 loads after the deferred application scripts so it can safely extend the opponent view.
window.addEventListener('DOMContentLoaded',()=>{
 const s=document.createElement('script');
 s.src='v27.js';
 s.async=false;
 document.body.appendChild(s);
});
