#!/usr/bin/env python3
import re,urllib.request
URLS=[
 'https://www.rugbyleagueproject.org/seasons/senior-international-matches-2025/australia/Round-1',
 'https://www.rugbyleagueproject.org/seasons/senior-international-matches-2025/australia/summary.html',
 'https://www.rugbyleagueproject.org/seasons/senior-international-matches-2025/australia/detail.html',
 'https://www.rugbyleagueproject.org/competitions/senior-international-matches-2025/australia/detail.html',
 'https://www.rugbyleagueproject.org/teams/australia/results-senior-international-matches.html',
 'https://www.rugbyleagueproject.org/teams/australia/players-senior-international-matches.html'
]
for url in URLS:
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 LeagueLinks/0.27'})
  with urllib.request.urlopen(req,timeout=25) as r:
   html=r.read().decode('utf-8','replace')
  match_ids=re.findall(r'/matches/(\d+)',html)
  player_ids=re.findall(r'/players/(\d+)',html)
  hrefs=re.findall(r'href=["\']([^"\']+)["\']',html,re.I)
  print('\nURL',url,'status OK bytes',len(html),'match links',len(set(match_ids)),'player links',len(set(player_ids)))
  print('title',re.search(r'<title>(.*?)</title>',html,re.I|re.S).group(1)[:160] if re.search(r'<title>(.*?)</title>',html,re.I|re.S) else 'none')
  print('sample match hrefs',[x for x in hrefs if '/matches/' in x][:6])
  print('sample player hrefs',[x for x in hrefs if '/players/' in x][:6])
 except Exception as e: print('\nURL',url,'ERROR',repr(e))
