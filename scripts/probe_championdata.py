#!/usr/bin/env python3
import json,urllib.request

def get(url):
 req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 LeagueLinks/0.27','Accept':'application/json'})
 with urllib.request.urlopen(req,timeout=30) as r:return json.loads(r.read().decode())
mid=129991401
ms=(get(f'https://mc.championdata.com/data/12999/{mid}.json').get('matchStats') or {})
info={int(x['playerId']):x for x in ((ms.get('playerInfo') or {}).get('player') or [])}
stats=(ms.get('playerStats') or {}).get('player') or []
print('match',mid,'rows',len(stats))
for s in stats:
 if int(s.get('squadId',0))!=335:continue
 x=info.get(int(s.get('playerId',0)),{});name=((x.get('firstname') or '')+' '+(x.get('surname') or '')).strip()
 nonzero={k:v for k,v in s.items() if k not in ('playerId','squadId','jumperNumber','position') and isinstance(v,(int,float)) and v!=0}
 print(json.dumps({'name':name,'jumper':s.get('jumperNumber'),'position':s.get('position'),'nonzero':nonzero},ensure_ascii=False))
