#!/usr/bin/env python3
import json,re,urllib.request
BASE='https://mc.championdata.com/data'

def get(url):
 req=urllib.request.Request(url,headers={'User-Agent':'LeagueLinksProbe/0.26'})
 with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)

def flatten(x):
 if isinstance(x,dict):
  for k,v in x.items():
   if isinstance(v,(dict,list)):yield from flatten(v)
 elif isinstance(x,list):
  for v in x:
   if isinstance(v,dict):yield v;yield from flatten(v)

data=get(f'{BASE}/competitions.json')
rows=[]
for r in flatten(data):
 txt=' '.join(str(v) for v in r.values() if isinstance(v,(str,int,float)))
 if re.search(r'NRL|Origin|Cup|Flegg|Ball|Matthews|Meninga|Connell|Colts|Queensland|NSW|Knock|Hostplus',txt,re.I):
  if any(k in r for k in ('id','competitionId','name','displayName','shortName','year','season')):rows.append(r)
seen=set()
print('MATCHING COMPETITIONS')
for r in rows:
 s=json.dumps(r,sort_keys=True)
 if s in seen:continue
 seen.add(s);print(s)
 # probe fixtures for numeric ids
 cid=r.get('id') or r.get('competitionId')
 if str(cid).isdigit():
  try:
   fx=get(f'{BASE}/{cid}/fixture.json')
   matches=((fx.get('fixture') or {}).get('match') or []) if isinstance(fx,dict) else []
   print('  fixtures',len(matches),'sample',json.dumps(matches[:1])[:1200])
  except Exception as e:print('  fixture error',type(e).__name__,str(e)[:160])
