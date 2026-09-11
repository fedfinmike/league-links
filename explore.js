function shortestPath(start,end){
 start=String(start);end=String(end);if(start===end)return[start];
 const q=[start],prev=new Map([[start,null]]);
 for(let head=0;head<q.length;head++){
  const cur=q[head],neighbors=(state.adj.get(cur)||[]).slice().sort((a,b)=>b.games-a.games);
  for(const e of neighbors){if(prev.has(e.id))continue;prev.set(e.id,cur);if(e.id===end){const p=[end];let x=cur;while(x){p.push(x);x=prev.get(x)}return p.reverse();}q.push(e.id);}
 }
 return null;
}
function renderConnection(){
 if(!state.connectA||!state.connectB){$('#connectionResult').innerHTML='<div class="empty"><strong>Choose two players.</strong>We’ll show the shortest confirmed teammate chain between them.</div>';return;}
 const p=shortestPath(state.connectA,state.connectB);
 if(!p){$('#connectionResult').innerHTML='<div class="empty"><strong>No exact path found.</strong>The loaded NRL graph does not connect these two players.</div>';return;}
 let html='<div class="pathline">';
 p.forEach((id,i)=>{html+=`<button class="nodebtn" data-path-player="${id}">${esc(playerMeta(id).name)}</button>`;if(i<p.length-1){const e=state.edges.get(pairKey(id,p[i+1])),hs=histories(id,p[i+1]);html+=`<span class="edge"><b>${e?.games||0} games</b>${hs.length?`${hs[0].year}–${hs[hs.length-1].year}`:''}</span>`;}});
 html+=`</div><div class="pathsummary"><span class="badge"><b>${p.length-1}</b> connection${p.length-1===1?'':'s'}</span><span class="badge"><b>${p.length}</b> players in path</span><span class="badge">Shortest match-confirmed route</span></div>`;
 $('#connectionResult').innerHTML=html;$$('[data-path-player]').forEach(b=>b.onclick=()=>openPlayer(b.dataset.pathPlayer));
}
$('#connectGo').onclick=()=>{if(state.connectA&&state.connectB){route('connect',{a:state.connectA,b:state.connectB});}else toast('Choose both players first');};

function fillYears(){const y=$('#clubYear');y.innerHTML=[...YEARS].reverse().map(x=>`<option value="${x}" ${x===2026?'selected':''}>${x}${x===2026?' · current':''}</option>`).join('');fillTeams(y.value)}
function fillTeams(year,selected){
 const teams=[...state.teams].filter(t=>state.rosters.has(`${year}|${t}`)).sort();$('#clubTeam').innerHTML=teams.map(t=>`<option ${t===selected?'selected':''}>${esc(t)}</option>`).join('');
}
$('#clubYear').onchange=()=>fillTeams($('#clubYear').value);$('#clubGo').onclick=renderRoster;
function renderRoster(){
 const y=$('#clubYear').value,t=$('#clubTeam').value,rm=state.rosters.get(`${y}|${t}`);
 if(!rm){$('#clubMeta').innerHTML='';$('#clubRoster').innerHTML='<div class="card empty" style="grid-column:1/-1">No confirmed appearances for that selection.</div>';return;}
 const rows=[...rm.entries()].map(([id,games])=>({id,games,name:playerMeta(id).name})).sort((a,b)=>b.games-a.games||a.name.localeCompare(b.name));
 $('#clubMeta').innerHTML=`<div class="sectionhead" style="margin-top:26px"><div><h2>${esc(t)} · ${y}</h2><p>${rows.length} players with confirmed NRL appearances</p></div></div>`;
 $('#clubRoster').innerHTML=rows.map(r=>`<button class="rostercard" data-roster-player="${r.id}"><strong>${esc(r.name)}</strong><small>${r.games} appearance${r.games===1?'':'s'} · ${y}</small></button>`).join('');
 $$('[data-roster-player]').forEach(b=>b.onclick=()=>openPlayer(b.dataset.rosterPlayer));
}
function renderCoverage(){
 const appTotal=[...state.appearances.values()].reduce((a,b)=>a+b,0),histTotal=[...state.historyByPair.values()].reduce((n,m)=>n+m.size,0);
 $('#cPlayers').textContent=fmt(state.players.size);$('#cEdges').textContent=fmt(state.edges.size);$('#cApps').textContent=fmt(appTotal);$('#cHist').textContent=fmt(histTotal);
 $('#coverageYears').innerHTML=YEARS.map(y=>`<div class="yearcell ${y===2026?'current':''}">${y}${y===2026?'<br><small>current</small>':''}</div>`).join('');
}
$('#refreshData').onclick=async()=>{await clearCache();toast('Source cache cleared · reloading');setTimeout(()=>location.reload(),500)};

function initUI(){
 const appTotal=[...state.appearances.values()].reduce((a,b)=>a+b,0);
 $('#sPlayers').textContent=fmt(state.players.size);$('#sEdges').textContent=fmt(state.edges.size);$('#sApps').textContent=fmt(appTotal);
 $('#dataStatus').textContent='Exact NRL network ready';$('#dataStatus').classList.add('ready');
 renderHomePeople();fillYears();renderRoster();renderCoverage();
 setupAutocomplete($('#homeSearch'),$('#homeSuggestions'),id=>openPlayer(id));
 setupAutocomplete($('#ledgerSearch'),$('#ledgerSuggestions'),id=>openPlayer(id));
 setupAutocomplete($('#connectA'),$('#connectASuggestions'),id=>{state.connectA=id;});
 setupAutocomplete($('#connectB'),$('#connectBSuggestions'),id=>{state.connectB=id;});
 $$('[data-route]').forEach(b=>b.onclick=()=>route(b.dataset.route));
 $('#startExplore').onclick=()=>{$('#homeSearch').focus();$('#homeSearch').scrollIntoView({behavior:'smooth',block:'center'});};
 $('#globalSearchBtn').onclick=()=>{route('players');setTimeout(()=>$('#ledgerSearch').focus(),80);};
 applyRoute();
}
(async()=>{
 try{
  await loadData();state.loaded=true;initUI();$('#loader').style.display='none';
 }catch(err){
  console.error(err);$('#loadStatus').innerHTML=`Could not load the NRL source data. <button class="ghost" onclick="location.reload()" style="margin-left:8px">Try again</button>`;$('#progressBar').style.width='100%';$('#progressBar').style.background='var(--red)';
 }
})();
