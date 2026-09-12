const OPPONENTS_URL='data/opponents.json.gz?v=27';
state.opponents=new Map();
state.playerOpponents=new Map();
let opponentsLoaded=false;
let opponentsPromise=null;

async function ensureOpponents(){
 if(opponentsLoaded)return true;
 if(opponentsPromise)return opponentsPromise;
 opponentsPromise=(async()=>{
  try{
   const r=await fetch(OPPONENTS_URL,{cache:'no-cache'});
   if(!r.ok||!('DecompressionStream'in window))return false;
   const stream=r.body.pipeThrough(new DecompressionStream('gzip'));
   const payload=JSON.parse(await new Response(stream).text());
   if(!payload||payload.version!==27)return false;
   const teams=new Map(),players=new Map();
   for(const [pid,year,competition,opponent,games] of payload.rows||[]){
    const id=String(pid);if(!teams.has(id))teams.set(id,[]);
    teams.get(id).push({year:Number(year),competition,opponent,games:Number(games)});
   }
   for(const [pid,opponentId,year,competition,opponentTeam,games] of payload.playerRows||[]){
    const id=String(pid);if(!players.has(id))players.set(id,[]);
    players.get(id).push({opponentId:String(opponentId),year:Number(year),competition,opponentTeam,games:Number(games)});
   }
   state.opponents=teams;state.playerOpponents=players;opponentsLoaded=true;return true;
  }catch(e){console.warn('Opponent history unavailable',e);return false}
 })();
 return opponentsPromise;
}

function opponentRowsForPlayer(id){return(state.opponents.get(String(id))||[]).slice()}
function playerOpponentRowsForPlayer(id){return(state.playerOpponents.get(String(id))||[]).slice()}
