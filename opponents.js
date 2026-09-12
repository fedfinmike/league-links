const OPPONENTS_URL='data/opponents.json.gz?v=26';
state.opponents=new Map();
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
   if(!payload||payload.version!==26)return false;
   const map=new Map();
   for(const [pid,year,competition,opponent,games] of payload.rows||[]){
    const id=String(pid);if(!map.has(id))map.set(id,[]);
    map.get(id).push({year:Number(year),competition,opponent,games:Number(games)});
   }
   state.opponents=map;opponentsLoaded=true;return true;
  }catch(e){console.warn('Opponent history unavailable',e);return false}
 })();
 return opponentsPromise;
}

function opponentRowsForPlayer(id){return(state.opponents.get(String(id))||[]).slice()}
