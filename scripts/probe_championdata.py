#!/usr/bin/env python3
import json,re,urllib.request
from html.parser import HTMLParser

def text(url):
 req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 LeagueLinks/0.27','Accept':'application/json, text/plain, */*'})
 with urllib.request.urlopen(req,timeout=30) as r:return r.status,r.read().decode('utf-8','replace')

class P(HTMLParser):
 def __init__(self):super().__init__();self.tables=[];self.table=None;self.row=None;self.cell=None
 def handle_starttag(self,tag,attrs):
  attrs=dict(attrs)
  if tag=='table':self.table=[]
  elif tag=='tr' and self.table is not None:self.row=[]
  elif tag in ('td','th') and self.row is not None:self.cell={'text':[],'links':[],'attrs':attrs}
  elif tag=='a' and self.cell is not None:self.cell['links'].append({'href':attrs.get('href',''),'text':''})
 def handle_data(self,d):
  if self.cell is not None:self.cell['text'].append(d)
  if self.cell is not None and self.cell['links']:self.cell['links'][-1]['text']+=d
 def handle_endtag(self,tag):
  if tag in ('td','th') and self.cell is not None:
   self.cell['text']=' '.join(''.join(self.cell['text']).split());self.row.append(self.cell);self.cell=None
  elif tag=='tr' and self.row is not None:
   if self.row:self.table.append(self.row)
   self.row=None
  elif tag=='table' and self.table is not None:self.tables.append(self.table);self.table=None

print('CHAMPION DATA COMPETITIONS')
_,body=text('https://mc.championdata.com/data/competitions.json');data=json.loads(body)
for r in ((data.get('competitionDetails') or {}).get('competition') or []):
 name=str(r.get('name',''))
 if re.search(r'NRL|Origin|World Cup|Pacific Cup',name,re.I):print(json.dumps(r,sort_keys=True))

print('\n2026 NRL FIXTURE')
status,body=text('https://mc.championdata.com/data/12999/fixture.json');fixture=json.loads(body)
matches=(fixture.get('fixture') or {}).get('match') or []
print('status',status,'matches',len(matches))
for m in matches[-20:]:print(json.dumps(m,sort_keys=True)[:2500])
completed=[m for m in matches if str(m.get('matchStatus','')).lower()=='complete']
if completed:
 m=completed[-1];mid=m['matchId'];print('\nLATEST COMPLETED MATCH',mid)
 status,body=text(f'https://mc.championdata.com/data/12999/{mid}.json');d=json.loads(body);ms=d.get('matchStats') or {}
 print('status',status,'keys',sorted(ms.keys()))
 for key in ['matchInfo','teamInfo','playerInfo','playerStats']:
  obj=ms.get(key);print('\n',key, json.dumps(obj,ensure_ascii=False)[:12000])

for url in ['https://www.rugbyleagueproject.org/seasons/qld-cup-2025/players.html','https://www.rugbyleagueproject.org/seasons/qld-cup-2025/brisbane-tigers/Round-1','https://www.rugbyleagueproject.org/seasons/nsw-cup-2025/players.html']:
 status,html=text(url);p=P();p.feed(html)
 print('RLP',url,'status',status,'bytes',len(html),'tables',len(p.tables))
 for ti,t in enumerate(p.tables[:2]):
  print('TABLE',ti,'rows',len(t))
  for row in t[:5]:print(json.dumps(row,ensure_ascii=False)[:3000])
