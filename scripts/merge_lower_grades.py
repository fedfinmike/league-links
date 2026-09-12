#!/usr/bin/env python3
import gzip,json,os
from collections import defaultdict
from itertools import combinations
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
GRAPH=os.path.join(ROOT,'data','league-links.json.gz')
LOWER=os.path.join(ROOT,'data','lower-grade-exact.json')

def pair_key(a,b):
 a,b=str(a),str(b);return f'{a}|{b}' if int(a)<int(b) else f'{b}|{a}'

def main():
 if not os.path.exists(LOWER):
  print('No lower-grade exact file');return
 with gzip.open(GRAPH,'rb') as f:p=json.loads(f.read())
 with open(LOWER,encoding='utf-8') as f:l=json.load(f)
 players={str(x['id']):x for x in p.get('players',[])}
 for x in l.get('players',[]):players.setdefault(str(x['id']),{'id':str(x['id']),'name':x.get('name') or f"Player {x['id']}",'birthday':''})
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
 comps=set(p.get('competitionsLoaded',[]));comps.update(x[3] for x in l.get('appearances',[]))
 used=set(apps)
 p['players']=[players[pid] for pid in sorted(used,key=int) if pid in players]
 p['appearances']=[[pid,n] for pid,n in apps.items()]
 p['career']=[[pid,y,c,t,g] for (pid,y,c,t),g in career.items()]
 p['rosters']=[[c,y,t,pid,g] for (c,y,t,pid),g in rosters.items()]
 p['edges']=list(edges.values())
 p['histories']=[[pk,y,c,t,g] for (pk,y,c,t),g in histories.items()]
 p['competitionsLoaded']=sorted(comps)
 p['version']=26
 raw=json.dumps(p,separators=(',',':'),ensure_ascii=False).encode()
 with gzip.open(GRAPH,'wb',compresslevel=9) as f:f.write(raw)
 print(json.dumps({'lowerGradeMatchGroups':len(groups),'lowerGradeAppearances':sum(len(x) for x in groups.values()),'players':len(p['players']),'links':len(p['edges']),'competitions':p['competitionsLoaded']},indent=2))

if __name__=='__main__':main()
