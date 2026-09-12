#!/usr/bin/env python3
import gzip,json,os
from collections import defaultdict
from itertools import combinations
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
GRAPH=os.path.join(ROOT,'data','league-links.json.gz')
INTL=os.path.join(ROOT,'data','international-exact.json')
META=os.path.join(ROOT,'data','build-meta.json')

def pair_key(a,b):
 a,b=str(a),str(b);return f'{a}|{b}' if int(a)<int(b) else f'{b}|{a}'

def main():
 if not os.path.exists(INTL):
  print('No international exact file');return
 with gzip.open(GRAPH,'rb') as f:p=json.loads(f.read())
 with open(INTL,encoding='utf-8') as f:l=json.load(f)
 try:
  with open(META,encoding='utf-8') as f:old_meta=json.load(f)
 except Exception:old_meta={}
 players={str(x['id']):x for x in p.get('players',[])}
 for x in l.get('players',[]):
  pid=str(x['id']);players.setdefault(pid,{'id':pid,'name':x.get('name') or f'Player {pid}','birthday':''})
 apps=defaultdict(int,{str(k):int(v) for k,v in p.get('appearances',[])})
 career=defaultdict(int)
 for pid,y,c,t,g in p.get('career',[]):career[(str(pid),int(y),c,t)]+=int(g)
 rosters=defaultdict(int)
 for c,y,t,pid,g in p.get('rosters',[]):rosters[(c,int(y),t,str(pid))]+=int(g)
 edges={pair_key(e['a'],e['b']):{'a':str(e['a']),'b':str(e['b']),'games':int(e['games']),'first':int(e['first']),'last':int(e['last'])} for e in p.get('edges',[])}
 histories=defaultdict(int)
 for pk,y,c,t,g in p.get('histories',[]):histories[(pk,int(y),c,t)]+=int(g)
 groups=defaultdict(set)
 for pid,mid,y,c,t,opp in l.get('appearances',[]):groups[(mid,int(y),c,t)].add(str(pid))
 for (mid,y,c,t),ids in groups.items():
  ids=sorted(ids,key=int)
  for pid in ids:
   apps[pid]+=1;career[(pid,y,c,t)]+=1;rosters[(c,y,t,pid)]+=1
  for a,b in combinations(ids,2):
   pk=pair_key(a,b);e=edges.get(pk)
   if not e:e={'a':a if int(a)<int(b) else b,'b':b if int(a)<int(b) else a,'games':0,'first':y,'last':y}
   e['games']+=1;e['first']=min(e['first'],y);e['last']=max(e['last'],y);edges[pk]=e
   histories[(pk,y,c,t)]+=1
 comps=set(p.get('competitionsLoaded',[]));comps.add('International')
 used=set(apps)
 p['players']=[players[pid] for pid in sorted(used,key=int) if pid in players]
 p['appearances']=[[pid,n] for pid,n in apps.items()]
 p['career']=[[pid,y,c,t,g] for (pid,y,c,t),g in career.items()]
 p['rosters']=[[c,y,t,pid,g] for (c,y,t,pid),g in rosters.items()]
 p['edges']=list(edges.values())
 p['histories']=[[pk,y,c,t,g] for (pk,y,c,t),g in histories.items()]
 p['competitionsLoaded']=sorted(comps)
 p['version']=24
 raw=json.dumps(p,separators=(',',':'),ensure_ascii=False).encode()
 with gzip.open(GRAPH,'wb',compresslevel=9) as f:f.write(raw)
 meta=dict(old_meta)
 meta.update({
  'version':28,
  'players':len(p['players']),
  'links':len(p['edges']),
  'playerAppearances':sum(apps.values()),
  'competitions':sorted(comps),
  'internationalMatchesExact':int(l.get('matches',0)),
  'internationalAppearancesExact':len(l.get('appearances',[])),
  'internationalYears':l.get('years',[]),
  'internationalMatchesByYear':l.get('matchesByYear',{}),
  'internationalParseGaps':len(l.get('errors',[])),
  'internationalIdentity':l.get('identity',{}),
  'compressedBytes':os.path.getsize(GRAPH)
 })
 with open(META,'w',encoding='utf-8') as f:json.dump(meta,f,indent=2)
 print(json.dumps({'internationalMatchGroups':len(groups),'internationalAppearances':len(l.get('appearances',[])),**{k:meta[k] for k in ['players','links','playerAppearances','internationalMatchesExact','internationalParseGaps']}},indent=2))

if __name__=='__main__':main()
