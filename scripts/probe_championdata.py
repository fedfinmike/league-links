#!/usr/bin/env python3
import json,re,urllib.request

def text(url):
 req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 LeagueLinks/0.27','Accept':'application/json, text/plain, */*'})
 with urllib.request.urlopen(req,timeout=30) as r:return r.status,r.read().decode('utf-8','replace')

_,body=text('https://mc.championdata.com/data/12999/fixture.json');fixture=json.loads(body)
matches=(fixture.get('fixture') or {}).get('match') or []
print('2026 NRL matches',len(matches),'completed',sum(str(m.get('matchStatus','')).lower()=='complete' for m in matches),'last round',max(int(m.get('roundNumber') or 0) for m in matches))
for mid in [129992608,129992707]:
 _,body=text(f'https://mc.championdata.com/data/12999/{mid}.json');ms=(json.loads(body).get('matchStats') or {})
 info={int(x['playerId']):x for x in ((ms.get('playerInfo') or {}).get('player') or [])}
 stats=(ms.get('playerStats') or {}).get('player') or []
 subs=(ms.get('playerSubs') or {}).get('player') or (ms.get('playerSubs') or {}).get('sub') or (ms.get('playerSubs') or {}).get('substitution') or []
 print('\nMATCH',mid,'stats',len(stats),'playerSubs type',type(ms.get('playerSubs')).__name__,'playerSubs',json.dumps(ms.get('playerSubs'),ensure_ascii=False)[:15000])
 for s in stats:
  if int(s.get('squadId',0))!=328:continue
  x=info.get(int(s.get('playerId',0)),{});name=((x.get('firstname') or '')+' '+(x.get('surname') or '')).strip()
  nonzero={k:v for k,v in s.items() if k not in ('playerId','squadId','jumperNumber','position') and isinstance(v,(int,float)) and v!=0}
  print(json.dumps({'name':name,'playerId':s.get('playerId'),'jumper':s.get('jumperNumber'),'position':s.get('position'),'nonzeroCount':len(nonzero),'nonzero':nonzero},ensure_ascii=False))
