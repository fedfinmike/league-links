// v0.27: distinguish opposition teams from the actual players faced.
(function(){
  const priorApply=window.applyV25Copy;
  window.applyV25Copy=function(){
    if(typeof priorApply==='function')priorApply();
    const ver=document.querySelector('.sidefoot span:first-child');if(ver)ver.textContent='v0.27';
  };

  window.renderOpponents=async function(id){
    const m=playerMeta(id);
    $('#playerSub').innerHTML='<div class="card empty"><strong>Loading opponents…</strong></div>';
    const ok=await ensureOpponents();
    if(state.selectedPlayer!==String(id)||state.ledgerTab!=='opponents')return;
    if(!ok){$('#playerSub').innerHTML='<div class="card empty"><strong>Opponent history is unavailable right now.</strong>Try again shortly.</div>';return}

    const teamBase=opponentRowsForPlayer(id),playerBase=playerOpponentRowsForPlayer(id);
    const allYears=[...teamBase.map(r=>r.year),...playerBase.map(r=>r.year)];
    const start=allYears.length?Math.min(...allYears):(m.span?.first||2000);
    const end=allYears.length?Math.max(...allYears):(m.span?.last||2026);
    const compOptions=['All',...orderedCompetitionIds([...teamBase.map(r=>r.competition),...playerBase.map(r=>r.competition)])];
    let mode='players';

    $('#playerSub').innerHTML=`
      <div class="subtabs opponent-scope">
        <button class="subtab" id="oppPlayers">Players</button>
        <button class="subtab" id="oppTeams">Teams</button>
      </div>
      <div class="toolbar">
        <div class="field"><label id="oppFindLabel">Find an opponent player</label><input id="oppFilter" placeholder="Type a player name…"></div>
        <div class="field"><label>Competition</label><select id="oppComp">${compOptions.map(x=>`<option>${esc(x)}</option>`).join('')}</select></div>
        <div class="field"><label>From</label><select id="oppFrom">${yearOptions(start,end,start)}</select></div>
        <div class="field"><label>To</label><select id="oppTo">${yearOptions(start,end,end)}</select></div>
        <button class="ghost" id="resetOpp">Reset</button>
      </div>
      <div id="opponentTable"></div>`;

    const setModeButtons=()=>{
      $('#oppPlayers').classList.toggle('active',mode==='players');
      $('#oppTeams').classList.toggle('active',mode==='teams');
      $('#oppFindLabel').textContent=mode==='players'?'Find an opponent player':'Find an opponent team';
      $('#oppFilter').placeholder=mode==='players'?'Type a player name…':'Type a team…';
    };

    const redraw=()=>{
      const q=$('#oppFilter').value.toLowerCase(),from=Number($('#oppFrom').value)||0,to=Number($('#oppTo').value)||9999,comp=$('#oppComp').value;
      if(mode==='teams'){
        const agg=new Map();
        for(const r of teamBase){
          if(r.year<from||r.year>to||(comp!=='All'&&r.competition!==comp))continue;
          const k=r.opponent,v=agg.get(k)||{opponent:k,games:0,years:new Set(),competitions:new Set()};
          v.games+=r.games;v.years.add(r.year);v.competitions.add(r.competition);agg.set(k,v);
        }
        const rows=[...agg.values()].filter(r=>r.opponent.toLowerCase().includes(q)).sort((a,b)=>b.games-a.games||a.opponent.localeCompare(b.opponent));
        $('#opponentTable').innerHTML=`<div class="tablewrap"><table><thead><tr><th>#</th><th>Opponent team</th><th>Games against</th><th>Years</th><th>Competitions</th></tr></thead><tbody>${rows.map((r,i)=>{const ys=[...r.years],cs=orderedCompetitionIds([...r.competitions]).map(competitionShort);return`<tr><td>${i+1}</td><td><strong>${esc(r.opponent)}</strong></td><td class="games">${r.games}</td><td class="yearspan">${ys.length?`${Math.min(...ys)}–${Math.max(...ys)}`:'—'}</td><td class="yearspan">${esc(cs.join(', ')||'—')}</td></tr>`}).join('')}</tbody></table></div>${rows.length?'':'<div class="card empty"><strong>No opponent teams found for those filters.</strong></div>'}`;
        return;
      }

      const agg=new Map();
      for(const r of playerBase){
        if(r.year<from||r.year>to||(comp!=='All'&&r.competition!==comp))continue;
        const k=r.opponentId,v=agg.get(k)||{id:k,games:0,years:new Set(),competitions:new Set(),teams:new Set()};
        v.games+=r.games;v.years.add(r.year);v.competitions.add(r.competition);if(r.opponentTeam)v.teams.add(r.opponentTeam);agg.set(k,v);
      }
      const rows=[...agg.values()].map(r=>({...r,name:playerMeta(r.id).name})).filter(r=>r.name.toLowerCase().includes(q)).sort((a,b)=>b.games-a.games||a.name.localeCompare(b.name));
      $('#opponentTable').innerHTML=`<div class="tablewrap"><table><thead><tr><th>#</th><th>Opponent player</th><th>Games against</th><th>Years</th><th>Teams faced</th><th>Competitions</th></tr></thead><tbody>${rows.map((r,i)=>{const ys=[...r.years],cs=orderedCompetitionIds([...r.competitions]).map(competitionShort),teams=[...r.teams].sort();return`<tr><td>${i+1}</td><td><button class="playerlink" data-opp-player="${esc(r.id)}">${esc(r.name)}</button></td><td class="games">${r.games}</td><td class="yearspan">${ys.length?`${Math.min(...ys)}–${Math.max(...ys)}`:'—'}</td><td class="yearspan">${esc(teams.join(', ')||'—')}</td><td class="yearspan">${esc(cs.join(', ')||'—')}</td></tr>`}).join('')}</tbody></table></div>${rows.length?'':'<div class="card empty"><strong>No opponent players found for those filters.</strong></div>'}`;
      $$('[data-opp-player]').forEach(b=>b.onclick=()=>openPlayer(b.dataset.oppPlayer));
    };

    $('#oppPlayers').onclick=()=>{mode='players';$('#oppFilter').value='';setModeButtons();redraw()};
    $('#oppTeams').onclick=()=>{mode='teams';$('#oppFilter').value='';setModeButtons();redraw()};
    $('#oppFilter').oninput=redraw;$('#oppComp').onchange=redraw;$('#oppFrom').onchange=redraw;$('#oppTo').onchange=redraw;
    $('#resetOpp').onclick=()=>{$('#oppFilter').value='';$('#oppComp').value='All';$('#oppFrom').value=start;$('#oppTo').value=end;redraw()};
    setModeButtons();redraw();
  };
})();
