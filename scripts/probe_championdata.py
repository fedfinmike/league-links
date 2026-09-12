#!/usr/bin/env python3
import json,re,urllib.request

def text(url):
 req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 LeagueLinks/0.27','Accept':'application/json, text/plain, */*'})
 with urllib.request.urlopen(req,timeout=30) as r:return r.status,r.read().decode('utf-8','replace')

print('CHAMPION DATA COMPETITIONS')
_,body=text('https://mc.championdata.com/data/competitions.json');data=json.loads(body)
for r in ((data.get('competitionDetails') or {}).get('competition') or []):
 name=str(r.get('name',''))
 if re.search(r'NRL|Origin|World Cup|Pacific Cup',name,re.I):print(json.dumps(r,sort_keys=True))

print('\n2026 NRL FIXTURE')
status,body=text('https://mc.championdata.com/data/12999/fixture.json');fixture=json.loads(body)
matches=(fixture.get('fixture') or {}).get('match') or []
print('status',status,'matches',len(matches),'completed',sum(str(m.get('matchStatus','')).lower()=='complete' for m in matches))
for m in matches[-16:]:print(json.dumps(m,sort_keys=True)[:2500])

for mid in [129992608,129992707]:
 status,body=text(f'https://mc.championdata.com/data/12999/{mid}.json');d=json.loads(body);ms=d.get('matchStats') or {}
 info={int(x['playerId']):x for x in ((ms.get('playerInfo') or {}).get('player') or [])}
 stats=(ms.get('playerStats') or {}).get('player') or []
 print('\nEELS MATCH',mid,'player stats',len(stats))
 for s in stats:
  x=info.get(int(s.get('playerId',0)),{}); name=((x.get('firstname') or '')+' '+(x.get('surname') or '')).strip()
  if name in ('Mitchell Moses','Harrison Edwards') or int(s.get('squadId',0))==328:
   print(json.dumps({'name':name,'championPlayerId':s.get('playerId'),'squadId':s.get('squadId'),'jumperNumber':s.get('jumperNumber'),'position':s.get('position')},ensure_ascii=False))
