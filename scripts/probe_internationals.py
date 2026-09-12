#!/usr/bin/env python3
import re,urllib.request

def fetch(url):
 req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 LeagueLinks/0.27'})
 with urllib.request.urlopen(req,timeout=25) as r:return r.read().decode('utf-8','replace')

html=fetch('https://www.rugbyleagueproject.org/matches/103083')
for needle in ('/players/23815','/players/20851','/players/22807'):
 pos=html.find(needle)
 print('\nNEEDLE',needle,'pos',pos)
 if pos>=0:
  chunk=html[max(0,pos-1200):pos+1800]
  print(chunk.replace('\n',' ')[:3000])

# show likely section/class markers near player list
for pat in (r'class="([^"]*(?:team|player|lineup|squad)[^"]*)"',r'id="([^"]*(?:team|player|lineup|squad)[^"]*)"'):
 vals=[]
 for x in re.findall(pat,html,re.I):
  if x not in vals:vals.append(x)
 print('\nMARKERS',vals[:80])
