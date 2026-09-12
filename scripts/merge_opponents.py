#!/usr/bin/env python3
import gzip,json,os
from collections import defaultdict
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
OPP=os.path.join(ROOT,'data','opponents.json.gz')
SOURCES=[os.path.join(ROOT,'data','lower-grade-exact.json'),os.path.join(ROOT,'data','international-exact.json')]
META=os.path.join(ROOT,'data','opponents-meta.json')
VERSION=28

def merge_source(path,team_counts,player_counts):
 if not os.path.exists(path):return {'path':os.path.basename(path),'appearances':0}
 with open(path,encoding='utf-8') as f:l=json.load(f)
 appearances=l.get('appearances',[])
 groups=defaultdict(set);opp_map={}
 for pid,mid,y,c,t,o in appearances:
  pid=str(pid);y=int(y)
  if o:team_counts[(pid,y,c,o)]+=1
  if mid and t:
   groups[(mid,y,c,t)].add(pid)
   if o:opp_map[(mid,y,c,t)]=o
 for (mid,y,c,t),ids in groups.items():
  opp=opp_map.get((mid,y,c,t),'')
  other=groups.get((mid,y,c,opp)) if opp else None
  if not other:continue
  for pid in ids:
   for opp_pid in other:
    if pid!=opp_pid:player_counts[(pid,opp_pid,y,c,opp)]+=1
 return {'path':os.path.basename(path),'appearances':len(appearances),'groups':len(groups)}

def main():
 with gzip.open(OPP,'rb') as f:p=json.loads(f.read())
 team_counts=defaultdict(int)
 player_counts=defaultdict(int)
 for pid,y,c,o,g in p.get('rows',[]):team_counts[(str(pid),int(y),c,o)]+=int(g)
 for pid,opp_pid,y,c,opp_team,g in p.get('playerRows',[]):player_counts[(str(pid),str(opp_pid),int(y),c,opp_team)]+=int(g)
 merged=[]
 for path in SOURCES:merged.append(merge_source(path,team_counts,player_counts))
 rows=[[pid,y,c,o,g] for (pid,y,c,o),g in team_counts.items()]
 player_rows=[[pid,opp_pid,y,c,opp_team,g] for (pid,opp_pid,y,c,opp_team),g in player_counts.items()]
 payload={'version':VERSION,'builtAt':p.get('builtAt'),'rows':rows,'playerRows':player_rows}
 raw=json.dumps(payload,separators=(',',':'),ensure_ascii=False).encode()
 with gzip.open(OPP,'wb',compresslevel=9) as f:f.write(raw)
 meta={'version':VERSION,'players':len({r[0] for r in rows}),'teamRows':len(rows),'teamGames':sum(r[4] for r in rows),'playerOpponentRows':len(player_rows),'playerOpponentGames':sum(r[5] for r in player_rows),'mergedSources':merged,'compressedBytes':os.path.getsize(OPP)}
 with open(META,'w',encoding='utf-8') as f:json.dump(meta,f,indent=2)
 print(json.dumps(meta,indent=2))
if __name__=='__main__':main()
