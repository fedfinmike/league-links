function setupAutocomplete(input,box,onPick){
 let selected=-1;
 input.addEventListener('input',()=>{selected=-1;render();});
 input.addEventListener('focus',render);
 input.addEventListener('keydown',e=>{
  const items=[...box.querySelectorAll('.suggestion')];if(!items.length)return;
  if(e.key==='ArrowDown'){e.preventDefault();selected=Math.min(items.length-1,selected+1);}
  else if(e.key==='ArrowUp'){e.preventDefault();selected=Math.max(0,selected-1);}
  else if(e.key==='Enter'&&selected>=0){e.preventDefault();items[selected].click();return;}
  else if(e.key==='Escape'){box.classList.remove('show');return;}
  items.forEach((x,i)=>x.classList.toggle('selected',i===selected));
 });
 function render(){
  const rs=findPlayers(input.value);box.innerHTML='';
  if(!rs.length){box.classList.remove('show');return;}
  for(const p of rs){
   const m=playerMeta(p.id),b=document.createElement('button');b.className='suggestion';
   b.innerHTML=`<span>${esc(m.name)}</span><small>${esc(m.latestTeam)}${m.span?` · ${m.span.first}–${m.span.last}`:''}${m.birthday&&m.birthday!=='-'?` · DOB ${esc(m.birthday)}`:''}</small>`;
   b.onclick=()=>{input.value=m.name;box.classList.remove('show');onPick(String(m.id));};box.appendChild(b);
  }box.classList.add('show');
 }
 document.addEventListener('click',e=>{if(e.target!==input&&!box.contains(e.target))box.classList.remove('show');});
}
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function route(name,params={},push=true){
 let h=name;if(name==='player'&&params.id)h=`player/${params.id}`;if(name==='connect'&&params.a&&params.b)h=`connect/${params.a}/${params.b}`;if(name==='clubs'&&params.year&&params.team)h=`clubs/${params.year}/${encodeURIComponent(params.team)}`;
 if(push)location.hash=h;else applyRoute(h);
}
function currentRoute(){return (location.hash||'#home').slice(1);}
function applyRoute(raw=currentRoute()){
 const bits=raw.split('/'),name=bits[0]||'home';
 const viewName=name==='player'?'players':name;
 $$('.view').forEach(v=>v.classList.toggle('active',v.id===`view-${viewName}`));
 $$('[data-route]').forEach(b=>b.classList.toggle('active',b.dataset.route===viewName||(viewName==='players'&&b.dataset.route==='players')));
 $('#pageTitle').textContent={home:'Player connection intelligence',players:'Player ledger',player:'Player ledger',connect:'Connection finder',clubs:'Club & season explorer',coverage:'Data coverage'}[name]||'League Links';
 if(name==='player'&&bits[1])openPlayer(bits[1],false);
 if(name==='connect'){if(bits[1]&&bits[2]){state.connectA=bits[1];state.connectB=bits[2];$('#connectA').value=playerMeta(bits[1]).name;$('#connectB').value=playerMeta(bits[2]).name;renderConnection();}}
 if(name==='clubs'&&bits[1]){const y=bits[1],t=decodeURIComponent(bits.slice(2).join('/'));$('#clubYear').value=y;fillTeams(y,t);renderRoster();}
 window.scrollTo({top:0,behavior:'smooth'});
}
window.addEventListener('hashchange',()=>applyRoute());

function recentIds(){try{return JSON.parse(localStorage.getItem('ll-recent')||'[]')}catch{return[]}}
function favIds(){try{return JSON.parse(localStorage.getItem('ll-favs')||'[]')}catch{return[]}}
function remember(id){let a=recentIds().filter(x=>x!==String(id));a.unshift(String(id));localStorage.setItem('ll-recent',JSON.stringify(a.slice(0,10)));renderHomePeople();}
function toggleFav(id){let a=favIds(),s=String(id);a=a.includes(s)?a.filter(x=>x!==s):[s,...a];localStorage.setItem('ll-favs',JSON.stringify(a));renderHomePeople();if(state.selectedPlayer===s)renderPlayerHeaderOnly();toast(a.includes(s)?'Saved to favourites':'Removed from favourites');}
function personCard(id){
 const m=playerMeta(id);return `<button class="person" data-player="${esc(id)}"><span class="star ${favIds().includes(String(id))?'on':''}">★</span><span class="initials">${initials(m.name)}</span><strong>${esc(m.name)}</strong><small>${esc(m.latestTeam)}</small></button>`;
}
function renderHomePeople(){
 const r=recentIds().filter(id=>state.players.has(String(id))).slice(0,5),f=favIds().filter(id=>state.players.has(String(id))).slice(0,5);
 $('#recentPeople').innerHTML=r.map(personCard).join('')||`<div class="card empty" style="grid-column:1/-1"><strong>No recent players yet.</strong>Open a ledger and your history will appear here.</div>`;
 $('#favPeople').innerHTML=f.map(personCard).join('')||`<div class="card empty" style="grid-column:1/-1"><strong>No favourites yet.</strong>Use the star on a player page to save one.</div>`;
 $$('[data-player]').forEach(b=>b.onclick=()=>route('player',{id:b.dataset.player}));
}
$('#clearRecent').onclick=()=>{localStorage.removeItem('ll-recent');renderHomePeople();};

function histories(a,b){
 const hm=state.historyByPair.get(pairKey(String(a),String(b)));return hm?[...hm.values()].sort((x,y)=>x.year-y.year):[];
}
function filteredEdgeGames(a,b,from,to){
 const hs=histories(a,b);return hs.filter(h=>(!from||h.year>=from)&&(!to||h.year<=to)).reduce((s,h)=>s+h.games,0);
}
function renderPlayerHeaderOnly(){renderPlayer(state.selectedPlayer);}
function openPlayer(id,push=true){id=String(id);if(!state.players.has(id))return;state.selectedPlayer=id;state.ledgerLimit=50;remember(id);if(push){route('player',{id});return;}renderPlayer(id);}
function renderPlayer(id){
 id=String(id);const m=playerMeta(id),adj=state.adj.get(id)||[];
 $('#ledgerHeading').textContent=m.name;$('#ledgerIntro').textContent=`${m.latestTeam}${m.span?` · exact NRL appearance history ${m.span.first}–${m.span.last}`:''}`;
 const fav=favIds().includes(id);
 $('#playerContent').innerHTML=`
 <div class="card playerhero">
  <div class="playerrow">
   <div class="playerid"><div class="avatar">${initials(m.name)}</div><div><h2>${esc(m.name)}</h2><p>${esc(m.latestTeam)}${m.birthday&&m.birthday!=='-'?` · DOB ${esc(m.birthday)}`:''}</p></div></div>
   <div class="playeractions"><button class="ghost" id="copyPlayer">Copy link</button><button class="iconbtn" id="favPlayer" title="Favourite">${fav?'★':'☆'}</button></div>
  </div>
  <div class="metrics"><div class="metric"><strong>${fmt(m.appearances)}</strong><span>NRL appearances loaded</span></div><div class="metric"><strong>${fmt(m.teammates)}</strong><span>Exact teammates</span></div><div class="metric"><strong>${m.span?m.span.last-m.span.first+1:0}</strong><span>Season span</span></div><div class="metric"><strong>${fmt(m.teams)}</strong><span>NRL clubs loaded</span></div></div>
 </div>
 <div class="subtabs"><button class="subtab ${state.ledgerTab==='ledger'?'active':''}" data-subtab="ledger">Teammate ledger</button><button class="subtab ${state.ledgerTab==='career'?'active':''}" data-subtab="career">Career timeline</button></div>
 <div id="playerSub"></div>`;
 $('#copyPlayer').onclick=()=>navigator.clipboard.writeText(location.href).then(()=>toast('Player link copied'));
 $('#favPlayer').onclick=()=>toggleFav(id);
 $$('[data-subtab]').forEach(b=>b.onclick=()=>{state.ledgerTab=b.dataset.subtab;renderPlayer(id);});
 if(state.ledgerTab==='career')renderCareer(id);else renderLedger(id,adj);
}
function renderLedger(id,adj){
 const m=playerMeta(id),start=m.span?.first||2008,end=m.span?.last||2026;
 $('#playerSub').innerHTML=`
 <div class="toolbar">
  <div class="field"><label>Filter teammates</label><input id="mateFilter" placeholder="Type a teammate name…"></div>
  <div class="field"><label>From season</label><select id="mateFrom">${yearOptions(start,end,start,true)}</select></div>
  <div class="field"><label>To season</label><select id="mateTo">${yearOptions(start,end,end,true)}</select></div>
  <button class="ghost" id="resetLedger">Reset</button>
 </div><div id="ledgerTable"></div>`;
 const redraw=()=>{
  const q=$('#mateFilter').value.toLowerCase(),from=Number($('#mateFrom').value)||0,to=Number($('#mateTo').value)||9999;
  let rows=adj.map(e=>({...e,name:playerMeta(e.id).name,g:filteredEdgeGames(id,e.id,from,to)})).filter(e=>e.g>0&&e.name.toLowerCase().includes(q)).sort((a,b)=>b.g-a.g||a.name.localeCompare(b.name));
  const shown=rows.slice(0,state.ledgerLimit);
  $('#ledgerTable').innerHTML=`<div class="tablewrap"><table><thead><tr><th>#</th><th>Teammate</th><th>Games together</th><th>Shared seasons</th><th>Playing history</th></tr></thead><tbody>${shown.map((e,i)=>{const hs=histories(id,e.id).filter(h=>h.year>=from&&h.year<=to),ys=[...new Set(hs.map(h=>h.year))];return `<tr><td>${i+1}</td><td><button class="playerlink" data-open="${e.id}">${esc(e.name)}</button></td><td class="games">${e.g}</td><td class="yearspan">${ys.length?`${Math.min(...ys)}–${Math.max(...ys)} · ${ys.length} season${ys.length===1?'':'s'}`:'—'}</td><td><button class="historybtn" data-history="${e.id}">Shared history</button></td></tr>`}).join('')}</tbody></table></div>${rows.length>shown.length?`<div class="loadmore"><button class="ghost" id="moreLedger">Show more · ${rows.length-shown.length} remaining</button></div>`:''}`;
  $$('[data-open]').forEach(b=>b.onclick=()=>openPlayer(b.dataset.open));
  $$('[data-history]').forEach(b=>b.onclick=()=>openHistory(id,b.dataset.history));
  if($('#moreLedger'))$('#moreLedger').onclick=()=>{state.ledgerLimit+=50;redraw();};
 };
 $('#mateFilter').oninput=redraw;$('#mateFrom').onchange=redraw;$('#mateTo').onchange=redraw;
 $('#resetLedger').onclick=()=>{state.ledgerLimit=50;$('#mateFilter').value='';$('#mateFrom').value=start;$('#mateTo').value=end;redraw();};redraw();
}
function yearOptions(start,end,sel,includeAll=false){
 let out=includeAll?`<option value="${sel}">${sel}</option>`:'';for(let y=start;y<=end;y++)if(y!==sel)out+=`<option value="${y}">${y}</option>`;return out;
}
function renderCareer(id){
 const ym=state.career.get(id);if(!ym){$('#playerSub').innerHTML='<div class="card empty">No loaded career appearances.</div>';return;}
 const rows=[];for(const [year,tm] of [...ym.entries()].sort((a,b)=>b[0]-a[0]))for(const [team,games] of [...tm.entries()].sort((a,b)=>b[1]-a[1]))rows.push({year,team,games});
 $('#playerSub').innerHTML=`<div class="timeline">${rows.map(r=>`<div class="seasonrow"><div class="year">${r.year}</div><div class="club">${esc(r.team)}<small>NRL · match-confirmed appearances</small></div><div class="count">${r.games} game${r.games===1?'':'s'}</div></div>`).join('')}</div>`;
}
function openHistory(a,b){
 const A=playerMeta(a),B=playerMeta(b),hs=histories(a,b);if(!hs.length)return;
 const total=hs.reduce((s,h)=>s+h.games,0),years=[...new Set(hs.map(h=>h.year))],max=Math.max(...hs.map(h=>h.games));
 $('#drawer').innerHTML=`
 <div class="drawerhead"><div><p class="eyebrow">SHARED PLAYING HISTORY</p><h2>${esc(A.name)} × ${esc(B.name)}</h2><p>Only confirmed same-match appearances are counted.</p></div><button class="iconbtn" id="closeDrawer">×</button></div>
 <div class="sharedstats"><div class="sharedstat"><strong>${total}</strong><span>Games together</span></div><div class="sharedstat"><strong>${years.length}</strong><span>Shared seasons</span></div><div class="sharedstat"><strong>${Math.min(...years)}–${Math.max(...years)}</strong><span>Shared span</span></div></div>
 <div class="bars">${[...hs].sort((x,y)=>y.year-x.year).map(h=>`<div class="barrow"><div class="yr">${h.year}</div><div class="bar"><i style="width:${Math.max(6,h.games/max*100)}%"></i></div><div class="n">${h.games}</div><div class="barclub">${esc(h.team)} · NRL</div></div>`).join('')}</div>
 <div class="heroactions" style="margin-top:22px"><button class="ghost" data-drawer-player="${a}">Open ${esc(A.name)}</button><button class="primary" data-drawer-player="${b}">Open ${esc(B.name)}</button></div>`;
 $('#drawerBack').classList.add('show');$('#closeDrawer').onclick=closeDrawer;$$('[data-drawer-player]').forEach(x=>x.onclick=()=>{closeDrawer();openPlayer(x.dataset.drawerPlayer);});
}
function closeDrawer(){$('#drawerBack').classList.remove('show')}
$('#drawerBack').onclick=e=>{if(e.target===$('#drawerBack'))closeDrawer()};document.addEventListener('keydown',e=>{if(e.key==='Escape')closeDrawer()});
