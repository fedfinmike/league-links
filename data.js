const SOURCE_BASE='https://raw.githubusercontent.com/uselessnrlstats/uselessnrlstats/main/data/nrl';
const CACHE_VERSION='ll-v22-2026-09-11';
const YEARS=Array.from({length:19},(_,i)=>2008+i);
const state={
 players:new Map(),edges:new Map(),adj:new Map(),historyByPair:new Map(),
 rosters:new Map(),career:new Map(),appearances:new Map(),teams:new Set(),
 playerYears:new Map(),selectedPlayer:null,ledgerLimit:50,ledgerTab:'ledger',
 connectA:null,connectB:null,loaded:false
};

const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const fmt=n=>Number(n||0).toLocaleString('en-AU');
const pairKey=(a,b)=>Number(a)<Number(b)?`${a}|${b}`:`${b}|${a}`;
const initials=name=>(name||'?').split(/\s+/).filter(Boolean).slice(0,2).map(x=>x[0]).join('').toUpperCase();

function titleCase(s){
 return (s||'').toLowerCase().replace(/(^|[\s\-'])\p{L}/gu,m=>m.toUpperCase())
   .replace(/\bMc([a-z])/g,(_,c)=>'Mc'+c.toUpperCase());
}
function playerNameFromComma(raw){
 if(!raw)return 'Unknown player';
 const i=raw.indexOf(',');
 if(i<0)return titleCase(raw);
 const last=raw.slice(0,i).trim(), first=raw.slice(i+1).trim();
 return `${titleCase(first)} ${titleCase(last)}`.trim();
}
function canonicalTeam(raw){
 const s=(raw||'').replace(/\r/g,' ').replace(/\n/g,' ').replace(/\s+/g,' ').trim();
 const u=s.toUpperCase();
 const rules=[
  ['CANBERRA','Canberra Raiders'],['BRISBANE','Brisbane Broncos'],['CANTERBURY','Canterbury-Bankstown Bulldogs'],
  ['CRONULLA','Cronulla-Sutherland Sharks'],['GOLD COAST','Gold Coast Titans'],['MANLY','Manly Warringah Sea Eagles'],
  ['MELBOURNE','Melbourne Storm'],['NEWCASTLE','Newcastle Knights'],['NORTH QUEENSLAND','North Queensland Cowboys'],
  ['PARRAMATTA','Parramatta Eels'],['PENRITH','Penrith Panthers'],['SOUTH SYDNEY','South Sydney Rabbitohs'],
  ['ST GEORGE','St George Illawarra Dragons'],['SYDNEY ROOSTERS','Sydney Roosters'],['ROOSTERS','Sydney Roosters'],
  ['WESTS','Wests Tigers'],['NEW ZEALAND','New Zealand Warriors'],['WARRIORS','New Zealand Warriors'],
  ['DOLPHINS','Dolphins']
 ];
 for(const [needle,name] of rules)if(u.includes(needle))return name;
 return titleCase(s);
}
function parseCSV(text){
 const rows=[]; let row=[],field='',q=false;
 for(let i=0;i<text.length;i++){
  const c=text[i];
  if(q){
   if(c==='"'){if(text[i+1]==='"'){field+='"';i++;}else q=false;}
   else field+=c;
  }else{
   if(c==='"')q=true;
   else if(c===','){row.push(field);field='';}
   else if(c==='\n'){row.push(field);rows.push(row);row=[];field='';}
   else if(c!=='\r')field+=c;
  }
 }
 if(field.length||row.length){row.push(field);rows.push(row);}
 return rows;
}
function headers(rows){
 const h={}; (rows[0]||[]).forEach((v,i)=>h[v.trim()]=i); return h;
}
function setProgress(p,msg){$('#progressBar').style.width=`${Math.max(4,Math.min(100,p))}%`;$('#loadStatus').textContent=msg;}
function toast(msg){const t=$('#toast');t.textContent=msg;t.classList.add('show');clearTimeout(toast._t);toast._t=setTimeout(()=>t.classList.remove('show'),1800);}

async function fetchText(url){
 const r=await fetch(url,{cache:'force-cache'});
 if(!r.ok)throw new Error(`${r.status} ${url}`);
 return r.text();
}
async function openDB(){
 return new Promise((res,rej)=>{
  const q=indexedDB.open('league-links',1);
  q.onupgradeneeded=()=>q.result.createObjectStore('cache');
  q.onsuccess=()=>res(q.result);q.onerror=()=>rej(q.error);
 });
}
async function cacheGet(){
 try{const db=await openDB();return await new Promise((res,rej)=>{const tx=db.transaction('cache','readonly');const q=tx.objectStore('cache').get(CACHE_VERSION);q.onsuccess=()=>res(q.result||null);q.onerror=()=>rej(q.error);});}catch{return null;}
}
async function cachePut(payload){
 try{const db=await openDB();await new Promise((res,rej)=>{const tx=db.transaction('cache','readwrite');tx.objectStore('cache').put(payload,CACHE_VERSION);tx.oncomplete=res;tx.onerror=()=>rej(tx.error);});}catch(e){console.warn('cache write',e);}
}
async function clearCache(){
 try{const db=await openDB();await new Promise((res,rej)=>{const tx=db.transaction('cache','readwrite');tx.objectStore('cache').clear();tx.oncomplete=res;tx.onerror=()=>rej(tx.error);});}catch{}
}

function addCareer(pid,year,team,n=1){
 if(!state.career.has(pid))state.career.set(pid,new Map());
 const ym=state.career.get(pid);if(!ym.has(year))ym.set(year,new Map());
 ym.get(year).set(team,(ym.get(year).get(team)||0)+n);
 const span=state.playerYears.get(pid)||{first:year,last:year};span.first=Math.min(span.first,year);span.last=Math.max(span.last,year);state.playerYears.set(pid,span);
}
function processSeason(rows,year){
 const h=headers(rows);const groups=new Map();
 for(let i=1;i<rows.length;i++){
  const r=rows[i], pid=(r[h.player_id]||'').trim(), match=(r[h.match_id]||'').trim();
  if(!pid||!match)continue;
  const team=canonicalTeam(r[h.team]);
  const key=`${match}|${team}`;
  if(!groups.has(key))groups.set(key,{team,players:new Set()});
  groups.get(key).players.add(pid); state.teams.add(team);
 }
 for(const g of groups.values()){
  const ids=[...g.players];
  const rk=`${year}|${g.team}`; if(!state.rosters.has(rk))state.rosters.set(rk,new Map());
  const rm=state.rosters.get(rk);
  for(const pid of ids){
   rm.set(pid,(rm.get(pid)||0)+1); state.appearances.set(pid,(state.appearances.get(pid)||0)+1); addCareer(pid,year,g.team,1);
  }
  for(let a=0;a<ids.length;a++)for(let b=a+1;b<ids.length;b++){
   const x=ids[a],y=ids[b],pk=pairKey(x,y); let e=state.edges.get(pk);
   if(!e)e={a:Number(x)<Number(y)?x:y,b:Number(x)<Number(y)?y:x,games:0,first:year,last:year};
   e.games++;e.first=Math.min(e.first,year);e.last=Math.max(e.last,year);state.edges.set(pk,e);
   if(!state.historyByPair.has(pk))state.historyByPair.set(pk,new Map());
   const hm=state.historyByPair.get(pk), hk=`${year}|${g.team}`, hv=hm.get(hk)||{year,team:g.team,games:0};
   hv.games++;hm.set(hk,hv);
  }
 }
}
function buildAdj(){
 state.adj.clear();
 for(const e of state.edges.values()){
  if(!state.adj.has(e.a))state.adj.set(e.a,[]);if(!state.adj.has(e.b))state.adj.set(e.b,[]);
  state.adj.get(e.a).push({id:e.b,games:e.games,first:e.first,last:e.last});
  state.adj.get(e.b).push({id:e.a,games:e.games,first:e.first,last:e.last});
 }
 for(const arr of state.adj.values())arr.sort((a,b)=>b.games-a.games);
}
function snapshot(){
 const career=[];for(const [id,ym] of state.career)for(const [year,tm] of ym)for(const [team,games] of tm)career.push([id,year,team,games]);
 const rosters=[];for(const [key,rm] of state.rosters){const [year,...rest]=key.split('|'),team=rest.join('|');for(const [id,games] of rm)rosters.push([year,team,id,games]);}
 const histories=[];for(const [pk,hm] of state.historyByPair)for(const hv of hm.values())histories.push([pk,hv.year,hv.team,hv.games]);
 return {players:[...state.players.values()],edges:[...state.edges.values()],career,rosters,histories,appearances:[...state.appearances],savedAt:Date.now()};
}
function restore(s){
 state.players=new Map((s.players||[]).map(p=>[String(p.id),p]));state.edges=new Map();
 for(const e of s.edges||[])state.edges.set(pairKey(e.a,e.b),e);
 state.career=new Map();state.playerYears=new Map();state.teams=new Set();
 for(const [id,year,team,games] of s.career||[]){addCareer(String(id),Number(year),team,Number(games));state.teams.add(team);}
 state.rosters=new Map();for(const [year,team,id,games] of s.rosters||[]){const k=`${year}|${team}`;if(!state.rosters.has(k))state.rosters.set(k,new Map());state.rosters.get(k).set(String(id),Number(games));}
 state.historyByPair=new Map();for(const [pk,year,team,games] of s.histories||[]){if(!state.historyByPair.has(pk))state.historyByPair.set(pk,new Map());state.historyByPair.get(pk).set(`${year}|${team}`,{year:Number(year),team,games:Number(games)});}
 state.appearances=new Map((s.appearances||[]).map(([id,n])=>[String(id),Number(n)]));buildAdj();
}
async function loadData(){
 setProgress(6,'Checking local League Links cache…');
 const cached=await cacheGet();
 if(cached){restore(cached);setProgress(100,'Loaded cached network');return;}
 setProgress(10,'Loading player identities…');
 const ps=parseCSV(await fetchText(`${SOURCE_BASE}/player_summary_data.csv`)), ph=headers(ps);
 for(let i=1;i<ps.length;i++){
  const r=ps[i],id=(r[ph.player_id]||'').trim();if(!id)continue;
  state.players.set(id,{id,name:playerNameFromComma(r[ph.player_name_comma]),birthday:(r[ph.player_birthday]||'').trim()});
 }
 let completed=0;
 const tasks=YEARS.map(async year=>{
  const idx=year-1907;
  const txt=await fetchText(`${SOURCE_BASE}/player_match_data/player_match_data_${idx}.csv`);
  processSeason(parseCSV(txt),year);
  completed++;setProgress(12+(completed/YEARS.length)*75,`Loading exact NRL appearances · ${completed} of ${YEARS.length} seasons`);
 });
 await Promise.all(tasks);buildAdj();
 setProgress(90,'Saving a faster local snapshot…');await cachePut(snapshot());setProgress(100,'Network ready');
}
function playerMeta(id){
 const p=state.players.get(String(id))||{id:String(id),name:`Player ${id}`,birthday:''};
 const span=state.playerYears.get(String(id));
 const cm=state.career.get(String(id));let latestTeam='NRL player';
 if(cm&&span&&cm.get(span.last)){latestTeam=[...cm.get(span.last).entries()].sort((a,b)=>b[1]-a[1])[0]?.[0]||latestTeam;}
 return {...p,span,latestTeam,appearances:state.appearances.get(String(id))||0,teammates:(state.adj.get(String(id))||[]).length,teams:cm?[...new Set([...cm.values()].flatMap(m=>[...m.keys()]))].length:0};
}
function findPlayers(q,limit=9){
 q=(q||'').trim().toLowerCase();if(!q)return[];
 const starts=[],includes=[];
 for(const p of state.players.values()){
  if(!(state.appearances.get(String(p.id))>0))continue;
  const n=p.name.toLowerCase();if(n.startsWith(q))starts.push(p);else if(n.includes(q))includes.push(p);
 }
 const rank=p=>state.appearances.get(String(p.id))||0;starts.sort((a,b)=>rank(b)-rank(a));includes.sort((a,b)=>rank(b)-rank(a));
 return starts.concat(includes).slice(0,limit);
}
