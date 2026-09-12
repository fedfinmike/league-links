#!/usr/bin/env python3
import re,urllib.request
from html.parser import HTMLParser

def fetch(url):
 req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 LeagueLinks/0.27'})
 with urllib.request.urlopen(req,timeout=25) as r:return r.read().decode('utf-8','replace')

class P(HTMLParser):
 def __init__(self):super().__init__();self.tables=[];self.t=None;self.r=None;self.c=None;self.a=None
 def handle_starttag(self,tag,attrs):
  attrs=dict(attrs)
  if tag=='table':self.t=[]
  elif tag=='tr' and self.t is not None:self.r=[]
  elif tag in ('td','th') and self.r is not None:self.c={'text':[],'links':[]}
  elif tag=='a' and self.c is not None:self.a={'href':attrs.get('href',''),'text':[]};self.c['links'].append(self.a)
 def handle_data(self,d):
  if self.c is not None:self.c['text'].append(d)
  if self.a is not None:self.a['text'].append(d)
 def handle_endtag(self,tag):
  if tag=='a':self.a=None
  elif tag in ('td','th') and self.c is not None:
   self.c['text']=' '.join(''.join(self.c['text']).split());self.r.append(self.c);self.c=None
  elif tag=='tr' and self.r is not None:
   if self.r:self.t.append(self.r)
   self.r=None
  elif tag=='table' and self.t is not None:self.tables.append(self.t);self.t=None

html=fetch('https://www.rugbyleagueproject.org/matches/103083')
p=P();p.feed(html)
print('tables',len(p.tables))
for ti,t in enumerate(p.tables):
 pc=sum(1 for row in t for c in row for l in c['links'] if re.search(r'/players/\d+',l['href']))
 if not pc:continue
 print('\nTABLE',ti,'rows',len(t),'player-links',pc)
 for row in t[:25]:
  vals=[]
  for c in row:
   pls=[l for l in c['links'] if re.search(r'/players/\d+',l['href'])]
   vals.append(c['text']+(' ['+','.join(l['href'] for l in pls)+']' if pls else ''))
  print(' | '.join(vals))
