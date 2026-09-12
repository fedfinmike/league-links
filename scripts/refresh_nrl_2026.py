#!/usr/bin/env python3
import gzip
import json
import os
import re
import unicodedata
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from itertools import combinations

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
GRAPH=os.path.join(ROOT,'data','league-links.json.gz')
GRAPH_META=os.path.join(ROOT,'data','build-meta.json')
OPP=os.path.join(ROOT,'data','opponents.json.gz')
OPP_META=os.path.join(ROOT,'data','opponents-meta.json')
SEASON=2026
COMPETITION='NRL'
COMPETITION_ID=12999
MC='https://mc.championdata.com/data'

TEAM_NAME={
 321:'New Zealand Warriors',322:'Brisbane Broncos',323:'Canberra Raiders',324:'Melbourne Storm',
 325:'Newcastle Knights',326:'North Queensland Cowboys',328:'Parramatta Eels',329:'Penrith Panthers',
 330:'St George Illawarra Dragons',331:'Sydney Roosters',332:'Canterbury-Bankstown Bulldogs',
 333:'Cronulla-Sutherland Sharks',334:'Wests Tigers',335:'South Sydney Rabbitohs',
 336:'Manly Warringah Sea Eagles',337:'Gold Coast Titans',9538:'Dolphins'
}
NAME_ALIASES={
 'sosefifita':'jojofifita','selumielahalasima':'lekahalasima','fetalaigapauga':'juniorpauga',
 'tolutaukoula':'tolutaukoula','nicholastsougranis':'nicktsougranis',
}
IGNORE_ACTIVITY={'playerId','squadId','jumperNumber'}

def get_json(url):
 req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 LeagueLinks/0.27','Accept':'application/json, text/plain, */*'})
 with urllib.request.urlopen(req,timeout=30) as r:return json.loads(r.read().decode('utf-8','replace'))

def norm_name(s):
 s=unicodedata.normalize('NFKD',str(s or '')).encode('ascii','ignore').decode('ascii').lower()
 s=re.sub(r'[^a-z0-9]+','',s)
 return NAME_ALIASES.get(s,s)

def pair_key(a,b):
 a,b=str(a),str(b);return f'{a}|{b}' if int(a)<int(b) else f'{b}|{a}'

def full_name(x):return ' '.join(v for v in [str(x.get('firstname') or '').strip(),str(x.get('surname') or '').strip()] if v).strip()

def did_play(stat):
 # Match Centre can name up to 19 players. A starter is identified by an on-field position.
 # Bench/reserve players are labelled Interchange, so they count only when official match
 # statistics record actual activity. This excludes unused reserves but keeps any activated
 # replacement who genuinely participates, including exceptional matches with 18 or 19 players.
 if str(stat.get('position') or '').strip().lower()!='interchange':return True
 for k,v in stat.items():
  if k in IGNORE_ACTIVITY or k=='position':continue
  if isinstance(v,(int,float)) and v!=0:return True
 return False

def load_base_graph():
 with gzip.open(GRAPH,'rb') as f:return json.loads(f.read())

def build_name_resolver(graph):
 players={str(x['id']):x for x in graph.get('players',[])};by_norm=defaultdict(list)
 for pid,p in players.items():by_norm[norm_name(p.get('name'))].append(pid)
 current_same=defaultdict(set);current_any=set()
 for pid,y,c,t,g in graph.get('career',[]):
  if int(y)==SEASON and c==COMPETITION and int(g)>0:current_same[(str(pid),t)].add(int(g));current_any.add(str(pid))
 synthetic={}
 def resolve(name,champ_id,team):
  key=norm_name(name);cands=by_norm.get(key,[])
  if len(cands)==1:return cands[0]
  if len(cands)>1:
   same=[p for p in cands if (p,team) in current_same]
   if len(same)==1:return same[0]
   curr=[p for p in cands if p in current_any]
   if len(curr)==1:return curr[0]
   raise RuntimeError(f'Ambiguous current NRL identity: {name!r} -> {cands}')
  sid=str(9_000_000_000_000+int(champ_id));synthetic[sid]={'id':sid,'name':name,'birthday':''};by_norm[key].append(sid);return sid
 return players,resolve,synthetic

def fetch_current_rows(graph):
 fixture=get_json(f'{MC}/{COMPETITION_ID}/fixture.json');matches=(fixture.get('fixture') or {}).get('match') or []
 completed=[m for m in matches if str(m.get('matchStatus','')).lower()=='complete']
 if len(completed)<204 or max((int(m.get('roundNumber') or 0) for m in completed),default=0)<27:raise RuntimeError(f'Official 2026 NRL feed is unexpectedly incomplete: {len(completed)} completed matches')
 players,resolve,synthetic=build_name_resolver(graph);raw_rows=[];unmapped=set()
 def fetch_match(m):
  mid=int(m['matchId']);ms=(get_json(f'{MC}/{COMPETITION_ID}/{mid}.json').get('matchStats') or {})
  info={int(x['playerId']):x for x in ((ms.get('playerInfo') or {}).get('player') or [])};stats=(ms.get('playerStats') or {}).get('player') or []
  home=int(m.get('homeSquadId') or 0);away=int(m.get('awaySquadId') or 0);out=[]
  for s in stats:
   if not did_play(s):continue
   squad=int(s.get('squadId') or 0);team=TEAM_NAME.get(squad)
   if not team:out.append(('__UNMAPPED__',squad,mid));continue
   opponent_id=away if squad==home else home if squad==away else 0;opponent=TEAM_NAME.get(opponent_id,'')
   x=info.get(int(s.get('playerId') or 0),{});name=full_name(x)
   if not name:raise RuntimeError(f'Missing player name in official match {mid} for {s.get("playerId")}')
   out.append((name,int(s.get('playerId')),str(mid),team,opponent))
  return out
 with ThreadPoolExecutor(max_workers=10) as ex:
  futs=[ex.submit(fetch_match,m) for m in completed]
  for fut in as_completed(futs):raw_rows.extend(fut.result())
 rows=[]
 for item in raw_rows:
  if item[0]=='__UNMAPPED__':unmapped.add(item[1]);continue
  name,champ_id,mid,team,opponent=item;rows.append([resolve(name,champ_id,team),mid,SEASON,COMPETITION,team,opponent])
 if unmapped:raise RuntimeError(f'Unmapped official NRL squad IDs: {sorted(unmapped)}')
 rows=list({tuple(r):r for r in rows}.values());groups=defaultdict(set)
 for pid,mid,y,c,t,o in rows:groups[(mid,t)].add(pid)
 # Official match activity is decisive. 17 is standard, but exceptional replacement cases
 # can produce 18 or 19 genuine participants. A named reserve with zero activity is filtered out above.
 bad=[(k,len(v)) for k,v in groups.items() if not (13<=len(v)<=19)]
 if bad:raise RuntimeError(f'Unexpected participant counts in official feed: {bad[:10]}')
 print('Official 2026 NRL:',len(completed),'completed matches',len(groups),'team-match groups',len(rows),'player appearances')
 print('Synthetic late-debut identities:',len(synthetic))
 return rows,players,synthetic,len(completed),max(int(m.get('roundNumber') or 0) for m in completed)

def rebuild_edges(histories):
 agg={}
 for pk,y,c,t,g in histories:
  e=agg.get(pk)
  if not e:
   a,b=pk.split('|',1);e={'a':a,'b':b,'games':0,'first':int(y),'last':int(y)}
  e['games']+=int(g);e['first']=min(e['first'],int(y));e['last']=max(e['last'],int(y));agg[pk]=e
 return list(agg.values())

def refresh_graph(graph,rows,players,synthetic,completed_matches,max_round):
 players.update(synthetic);apps=defaultdict(int,{str(k):int(v) for k,v in graph.get('appearances',[])});career=[]
 for pid,y,c,t,g in graph.get('career',[]):
  if int(y)==SEASON and c==COMPETITION:apps[str(pid)]-=int(g)
  else:career.append([str(pid),int(y),c,t,int(g)])
 rosters=[[c,int(y),t,str(pid),int(g)] for c,y,t,pid,g in graph.get('rosters',[]) if not (int(y)==SEASON and c==COMPETITION)]
 histories=[[pk,int(y),c,t,int(g)] for pk,y,c,t,g in graph.get('histories',[]) if not (int(y)==SEASON and c==COMPETITION)]
 groups=defaultdict(set)
 for pid,mid,y,c,t,opp in rows:groups[(mid,int(y),c,t)].add(str(pid))
 career_counts=defaultdict(int,{(pid,y,c,t):g for pid,y,c,t,g in career});roster_counts=defaultdict(int,{(c,y,t,pid):g for c,y,t,pid,g in rosters});history_counts=defaultdict(int,{(pk,y,c,t):g for pk,y,c,t,g in histories})
 for (mid,y,c,t),ids in groups.items():
  ids=sorted(ids,key=int)
  for pid in ids:apps[pid]+=1;career_counts[(pid,y,c,t)]+=1;roster_counts[(c,y,t,pid)]+=1
  for a,b in combinations(ids,2):history_counts[(pair_key(a,b),y,c,t)]+=1
 apps={pid:n for pid,n in apps.items() if n>0};histories=[[pk,y,c,t,g] for (pk,y,c,t),g in history_counts.items()]
 graph['career']=[[pid,y,c,t,g] for (pid,y,c,t),g in career_counts.items()];graph['rosters']=[[c,y,t,pid,g] for (c,y,t,pid),g in roster_counts.items()];graph['histories']=histories;graph['edges']=rebuild_edges(histories);graph['appearances']=[[pid,n] for pid,n in apps.items()];graph['players']=[players[pid] for pid in sorted(apps,key=int) if pid in players];graph['builtAt']=int(datetime.now(timezone.utc).timestamp()*1000)
 comps=set(graph.get('competitionsLoaded',[]));comps.add(COMPETITION);graph['competitionsLoaded']=sorted(comps)
 with gzip.open(GRAPH,'wb',compresslevel=9) as f:f.write(json.dumps(graph,separators=(',',':'),ensure_ascii=False).encode())
 try:
  with open(GRAPH_META,encoding='utf-8') as f:meta=json.load(f)
 except Exception:meta={}
 meta.update({'builtAt':graph['builtAt'],'players':len(graph['players']),'links':len(graph['edges']),'playerAppearances':sum(apps.values()),'compressedBytes':os.path.getsize(GRAPH),'currentNRLSource':'NRL Match Centre / Champion Data','currentNRLCompetitionId':COMPETITION_ID,'currentNRLSeason':SEASON,'currentNRLCompletedMatches':completed_matches,'currentNRLMaxRound':max_round,'currentNRLPlayerAppearances':len(rows),'currentNRLMatchTeamGroups':len(groups)})
 with open(GRAPH_META,'w',encoding='utf-8') as f:json.dump(meta,f,indent=2)

def refresh_opponents(rows,completed_matches,max_round):
 with gzip.open(OPP,'rb') as f:p=json.loads(f.read())
 counts=defaultdict(int)
 for pid,y,c,o,g in p.get('rows',[]):
  if int(y)==SEASON and c==COMPETITION:continue
  counts[(str(pid),int(y),c,o)]+=int(g)
 for pid,mid,y,c,t,o in rows:
  if o:counts[(str(pid),int(y),c,o)]+=1
 out=[[pid,y,c,o,g] for (pid,y,c,o),g in counts.items()];p={'version':26,'builtAt':int(datetime.now(timezone.utc).timestamp()*1000),'rows':out}
 with gzip.open(OPP,'wb',compresslevel=9) as f:f.write(json.dumps(p,separators=(',',':'),ensure_ascii=False).encode())
 meta={'version':26,'players':len({r[0] for r in out}),'rows':len(out),'games':sum(r[4] for r in out),'compressedBytes':os.path.getsize(OPP),'currentNRLSource':'NRL Match Centre / Champion Data','currentNRLSeason':SEASON,'currentNRLCompletedMatches':completed_matches,'currentNRLMaxRound':max_round}
 with open(OPP_META,'w',encoding='utf-8') as f:json.dump(meta,f,indent=2)

def main():
 graph=load_base_graph();rows,players,synthetic,completed,max_round=fetch_current_rows(graph);refresh_graph(graph,rows,players,synthetic,completed,max_round);refresh_opponents(rows,completed,max_round)
if __name__=='__main__':main()
