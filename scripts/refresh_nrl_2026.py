#!/usr/bin/env python3
import gzip, json, os
from collections import defaultdict
from datetime import datetime, timezone
from itertools import combinations

import build_rlp_exact as rlp

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
GRAPH=os.path.join(ROOT,'data','league-links.json.gz')
GRAPH_META=os.path.join(ROOT,'data','build-meta.json')
OPP=os.path.join(ROOT,'data','opponents.json.gz')
OPP_META=os.path.join(ROOT,'data','opponents-meta.json')
SEASON=2026
COMPETITION='NRL'
RLP_PREFIX='nrl-2026'

TEAM_CANDIDATES=[
 ('brisbane-broncos','Brisbane Broncos'),
 ('canberra-raiders','Canberra Raiders'),
 ('canterbury-bankstown-bulldogs','Canterbury-Bankstown Bulldogs'),
 ('cronulla-sutherland-sharks','Cronulla-Sutherland Sharks'),
 ('cronulla-sharks','Cronulla-Sutherland Sharks'),
 ('dolphins','Dolphins'),
 ('gold-coast-titans','Gold Coast Titans'),
 ('manly-warringah-sea-eagles','Manly Warringah Sea Eagles'),
 ('melbourne-storm','Melbourne Storm'),
 ('newcastle-knights','Newcastle Knights'),
 ('new-zealand-warriors','New Zealand Warriors'),
 ('north-queensland-cowboys','North Queensland Cowboys'),
 ('parramatta-eels','Parramatta Eels'),
 ('penrith-panthers','Penrith Panthers'),
 ('south-sydney-rabbitohs','South Sydney Rabbitohs'),
 ('st-george-illawarra-dragons','St George Illawarra Dragons'),
 ('sydney-roosters','Sydney Roosters'),
 ('wests-tigers','Wests Tigers'),
]
TEAM_NAMES={name for _,name in TEAM_CANDIDATES}
OPPONENT_MAP={
 'Brisbane':'Brisbane Broncos','Brisbane Tigers':'Brisbane Broncos',
 'Canberra':'Canberra Raiders','Canberra Raiders':'Canberra Raiders',
 'Canterbury':'Canterbury-Bankstown Bulldogs','Canterbury-Bankstown Bulldogs':'Canterbury-Bankstown Bulldogs',
 'Cronulla':'Cronulla-Sutherland Sharks','Cronulla-Sutherland Sharks':'Cronulla-Sutherland Sharks',
 'Dolphins':'Dolphins',
 'Gold Coast':'Gold Coast Titans','Gold Coast Titans':'Gold Coast Titans',
 'Manly':'Manly Warringah Sea Eagles','Manly Warringah Sea Eagles':'Manly Warringah Sea Eagles',
 'Melbourne':'Melbourne Storm','Melbourne Storm':'Melbourne Storm',
 'Newcastle':'Newcastle Knights','Newcastle Knights':'Newcastle Knights',
 'Warriors':'New Zealand Warriors','New Zealand':'New Zealand Warriors','New Zealand Warriors':'New Zealand Warriors',
 'North Qld':'North Queensland Cowboys','North Queensland':'North Queensland Cowboys','North Queensland Cowboys':'North Queensland Cowboys',
 'Parramatta':'Parramatta Eels','Parramatta Eels':'Parramatta Eels',
 'Penrith':'Penrith Panthers','Penrith Panthers':'Penrith Panthers',
 'South Sydney':'South Sydney Rabbitohs','Souths':'South Sydney Rabbitohs','South Sydney Rabbitohs':'South Sydney Rabbitohs',
 'St Geo Illa':'St George Illawarra Dragons','St George Illawarra':'St George Illawarra Dragons','St George Illawarra Dragons':'St George Illawarra Dragons',
 'Sydney':'Sydney Roosters','Sydney Roosters':'Sydney Roosters',
 'Wests':'Wests Tigers','Wests Tigers':'Wests Tigers',
}

def pair_key(a,b):
 a,b=str(a),str(b)
 return f'{a}|{b}' if int(a)<int(b) else f'{b}|{a}'

def canonical_opponent(raw):
 return OPPONENT_MAP.get((raw or '').strip(),(raw or '').strip())

def current_rows():
 canonical=rlp.nrl_names(); rows=[]; players={}; loaded=set()
 for slug,team in TEAM_CANDIDATES:
  if team in loaded: continue
  try:
   html=rlp.get(f'{rlp.RLP}/{RLP_PREFIX}/{slug}/Round-1')
   parsed,ps=rlp.parse_team_page(html,COMPETITION,SEASON,team,canonical)
  except Exception as e:
   print('NRL 2026 unavailable',team,slug,e); continue
  clean=[]
  for pid,mid,year,comp,t,opp in parsed:
   opp=canonical_opponent(opp)
   # Excludes Brisbane's World Club Challenge and any other non-NRL match embedded on a team page.
   if opp and opp not in TEAM_NAMES: continue
   clean.append([str(pid),mid,int(year),COMPETITION,team,opp])
  if not clean: continue
  loaded.add(team); rows.extend(clean); players.update(ps)
  print('NRL 2026',team,len({r[1] for r in clean}),'matches',len(clean),'player appearances')
 rows=list({tuple(r):r for r in rows}.values())
 if len(loaded)<17:
  missing=sorted(TEAM_NAMES-loaded)
  raise RuntimeError(f'Only {len(loaded)} NRL teams loaded; missing {missing}')
 return rows,players

def rebuild_edges(histories):
 agg={}
 for pk,y,c,t,g in histories:
  e=agg.get(pk)
  if not e:
   a,b=pk.split('|',1);e={'a':a,'b':b,'games':0,'first':int(y),'last':int(y)}
  e['games']+=int(g);e['first']=min(e['first'],int(y));e['last']=max(e['last'],int(y));agg[pk]=e
 return list(agg.values())

def refresh_graph(rows,new_players):
 with gzip.open(GRAPH,'rb') as f:p=json.loads(f.read())
 players={str(x['id']):x for x in p.get('players',[])}
 for pid,x in new_players.items():
  players.setdefault(str(pid),{'id':str(pid),'name':x.get('name') or f'Player {pid}','birthday':''})
 apps=defaultdict(int,{str(k):int(v) for k,v in p.get('appearances',[])})
 career=[]
 for pid,y,c,t,g in p.get('career',[]):
  if int(y)==SEASON and c==COMPETITION:
   apps[str(pid)]-=int(g)
  else: career.append([str(pid),int(y),c,t,int(g)])
 rosters=[[c,int(y),t,str(pid),int(g)] for c,y,t,pid,g in p.get('rosters',[]) if not (int(y)==SEASON and c==COMPETITION)]
 histories=[[pk,int(y),c,t,int(g)] for pk,y,c,t,g in p.get('histories',[]) if not (int(y)==SEASON and c==COMPETITION)]
 groups=defaultdict(set)
 for pid,mid,y,c,t,opp in rows: groups[(mid,int(y),c,t)].add(str(pid))
 career_counts=defaultdict(int,{(pid,y,c,t):g for pid,y,c,t,g in career})
 roster_counts=defaultdict(int,{(c,y,t,pid):g for c,y,t,pid,g in rosters})
 history_counts=defaultdict(int,{(pk,y,c,t):g for pk,y,c,t,g in histories})
 for (mid,y,c,t),ids in groups.items():
  ids=sorted(ids,key=int)
  for pid in ids:
   apps[pid]+=1;career_counts[(pid,y,c,t)]+=1;roster_counts[(c,y,t,pid)]+=1
  for a,b in combinations(ids,2): history_counts[(pair_key(a,b),y,c,t)]+=1
 apps={pid:n for pid,n in apps.items() if n>0}
 histories=[[pk,y,c,t,g] for (pk,y,c,t),g in history_counts.items()]
 p['career']=[[pid,y,c,t,g] for (pid,y,c,t),g in career_counts.items()]
 p['rosters']=[[c,y,t,pid,g] for (c,y,t,pid),g in roster_counts.items()]
 p['histories']=histories
 p['edges']=rebuild_edges(histories)
 p['appearances']=[[pid,n] for pid,n in apps.items()]
 p['players']=[players[pid] for pid in sorted(apps,key=int) if pid in players]
 p['builtAt']=int(datetime.now(timezone.utc).timestamp()*1000)
 comps=set(p.get('competitionsLoaded',[]));comps.add(COMPETITION);p['competitionsLoaded']=sorted(comps)
 raw=json.dumps(p,separators=(',',':'),ensure_ascii=False).encode()
 with gzip.open(GRAPH,'wb',compresslevel=9) as f:f.write(raw)
 try:
  with open(GRAPH_META,encoding='utf-8') as f:meta=json.load(f)
 except Exception:meta={}
 meta.update({'builtAt':p['builtAt'],'players':len(p['players']),'links':len(p['edges']),'playerAppearances':sum(apps.values()),'compressedBytes':os.path.getsize(GRAPH),'currentNRLSource':'Rugby League Project match matrices','currentNRLSeason':SEASON,'currentNRLPlayerAppearances':len(rows),'currentNRLMatchTeamGroups':len(groups)})
 with open(GRAPH_META,'w',encoding='utf-8') as f:json.dump(meta,f,indent=2)

def refresh_opponents(rows):
 with gzip.open(OPP,'rb') as f:p=json.loads(f.read())
 counts=defaultdict(int)
 for pid,y,c,o,g in p.get('rows',[]):
  if int(y)==SEASON and c==COMPETITION: continue
  counts[(str(pid),int(y),c,o)]+=int(g)
 for pid,mid,y,c,t,o in rows:
  if o: counts[(str(pid),int(y),c,o)]+=1
 out=[[pid,y,c,o,g] for (pid,y,c,o),g in counts.items()]
 p={'version':26,'builtAt':int(datetime.now(timezone.utc).timestamp()*1000),'rows':out}
 raw=json.dumps(p,separators=(',',':'),ensure_ascii=False).encode()
 with gzip.open(OPP,'wb',compresslevel=9) as f:f.write(raw)
 meta={'version':26,'players':len({r[0] for r in out}),'rows':len(out),'games':sum(r[4] for r in out),'compressedBytes':os.path.getsize(OPP),'currentNRLSource':'Rugby League Project match matrices','currentNRLSeason':SEASON}
 with open(OPP_META,'w',encoding='utf-8') as f:json.dump(meta,f,indent=2)

def main():
 rows,players=current_rows()
 print('Fresh NRL 2026:',len(players),'players',len(rows),'player appearances')
 refresh_graph(rows,players)
 refresh_opponents(rows)

if __name__=='__main__':main()
