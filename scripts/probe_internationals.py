#!/usr/bin/env python3
import re,urllib.request

def fetch(url):
 req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 LeagueLinks/0.27'})
 with urllib.request.urlopen(req,timeout=25) as r:return r.read().decode('utf-8','replace')

URLS=[
 'https://www.rugbyleagueproject.org/seasons/senior-international-matches-2025/australia/Round-1',
 'https://www.rugbyleagueproject.org/teams/australia/results-senior-international-matches.html',
 'https://www.rugbyleagueproject.org/teams/australia/players-senior-international-matches.html'
]
for url in URLS:
 try:
  html=fetch(url);match_ids=re.findall(r'/matches/(\d+)',html);player_ids=re.findall(r'/players/(\d+)',html);hrefs=re.findall(r'href=["\']([^"\']+)["\']',html,re.I)
  print('\nURL',url,'bytes',len(html),'match links',len(set(match_ids)),'player links',len(set(player_ids)))
  print('sample match hrefs',[x for x in hrefs if '/matches/' in x][:8])
 except Exception as e:print('ERROR',url,repr(e))

for mid in ('120375','103083'):
 try:
  html=fetch(f'https://www.rugbyleagueproject.org/matches/{mid}')
  title=re.search(r'<title>(.*?)</title>',html,re.I|re.S)
  links=re.findall(r'<a[^>]+href=["\']([^"\']*/players/\d+)["\'][^>]*>(.*?)</a>',html,re.I|re.S)
  print('\nMATCH',mid,'bytes',len(html),'title',re.sub('<.*?>','',title.group(1)).strip() if title else 'none','unique players',len({x[0] for x in links}))
  print('first player links',[(h,re.sub('<.*?>','',t).strip()) for h,t in links[:12]])
  for needle in ('Home Team','Away Team','Team Lists','Australia','New Zealand','Tonga','Samoa'):
   pos=html.find(needle)
   if pos>=0:print('AROUND',needle,re.sub(r'\s+',' ',re.sub('<.*?>',' ',html[max(0,pos-250):pos+500]))[:800])
 except Exception as e:print('MATCH ERROR',mid,repr(e))
