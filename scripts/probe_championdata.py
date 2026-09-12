#!/usr/bin/env python3
import json,re,urllib.request

def text(url):
 req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 LeagueLinks/0.26'})
 with urllib.request.urlopen(req,timeout=20) as r:
  body=r.read().decode('utf-8','replace')
  return r.status,body

print('CHAMPION DATA COMPETITIONS')
status,body=text('https://mc.championdata.com/data/competitions.json')
data=json.loads(body)
rows=((data.get('competitionDetails') or {}).get('competition') or [])
for r in rows:
 name=str(r.get('name',''))
 if re.search(r'NRL|Origin|World Cup|Pacific Cup',name,re.I):print(json.dumps(r,sort_keys=True))

for url in [
 'https://www.rugbyleagueproject.org/seasons/qld-cup-2025/players.html',
 'https://www.rugbyleagueproject.org/seasons/qld-cup-2025/brisbane-tigers/Round-1',
 'https://www.rugbyleagueproject.org/seasons/nsw-cup-2025/players.html'
]:
 try:
  status,html=text(url)
  print('RLP',url,'status',status,'bytes',len(html),'tables',html.lower().count('<table'),'player-links',html.lower().count('/players/'))
  print(re.sub(r'\s+',' ',html[:1200]))
 except Exception as e:print('RLP ERROR',url,type(e).__name__,str(e))
