#!/usr/bin/env python3
import re,urllib.request
URLS=['https://www.nrl.com/news/2026/08/25/nrl-team-lists-round-26/','https://www.nrl.com/news/2026/09/01/nrl-team-lists-round-27/']
for url in URLS:
 print('\nURL',url)
 req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 LeagueLinks/0.27'})
 try:
  html=urllib.request.urlopen(req,timeout=60).read().decode('utf-8','replace')
 except Exception as e:
  print('FETCH ERROR',repr(e));continue
 print('bytes',len(html),'Harrison',html.lower().find('harrison edwards'),'Mitchell Moses',html.lower().find('mitchell moses'))
 for needle in ['Harrison Edwards','Mitchell Moses','Eels v Sharks','Dragons v Eels','Team Lists']:
  i=html.lower().find(needle.lower())
  if i>=0:
   s=max(0,i-1000);e=min(len(html),i+1800)
   print('\n---',needle,'---\n',re.sub(r'\s+',' ',html[s:e]))
