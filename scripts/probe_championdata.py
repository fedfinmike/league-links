#!/usr/bin/env python3
import json,re,urllib.request
BASE='https://mc.championdata.com/data'

def get(url):
 req=urllib.request.Request(url,headers={'User-Agent':'LeagueLinksProbe/0.26'})
 with urllib.request.urlopen(req,timeout=20) as r:return json.load(r)

data=get(f'{BASE}/competitions.json')
rows=((data.get('competitionDetails') or {}).get('competition') or []) if isinstance(data,dict) else []
print('MATCHING COMPETITIONS',len(rows))
for r in rows:
 txt=' '.join(str(v) for v in r.values() if isinstance(v,(str,int,float)))
 if re.search(r'NRL|Origin|Cup|Flegg|Ball|Matthews|Meninga|Connell|Colts|Queensland|NSW|Knock|Hostplus',txt,re.I):
  print(json.dumps(r,sort_keys=True))
