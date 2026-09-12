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
