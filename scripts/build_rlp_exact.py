#!/usr/bin/env python3
import csv, io, json, os, re, urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from html.parser import HTMLParser

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
OUT=os.path.join(ROOT,'data','lower-grade-exact.json')
NRL='https://raw.githubusercontent.com/uselessnrlstats/uselessnrlstats/main/data/nrl'
RLP='https://www.rugbyleagueproject.org/seasons'
YEARS=range(2024,2027)
COMPS=[('NSW Cup','nsw-cup'),('Queensland Cup','qld-cup')]

TEAM_MAP={
 'brisbane-tigers':'Brisbane Tigers','burleigh-bears':'Burleigh Bears','central-queensland-capras':'Central Queensland Capras','ipswich-jets':'Ipswich Jets','mackay-cutters':'Mackay Cutters','northern-pride':'Northern Pride','norths-devils':'Norths Devils','papua-new-guinea-hunters':'Papua New Guinea Hunters','redcliffe-dolphins':'Redcliffe Dolphins','souths-logan-magpies':'Souths Logan Magpies','sunshine-coast-falcons':'Sunshine Coast Falcons','townsville-blackhawks':'Townsville Blackhawks','tweed-seagulls':'Tweed Seagulls','western-clydesdales':'Western Clydesdales','wynnum-manly-seagulls':'Wynnum Manly Seagulls',
 'canberra-raiders':'Canberra Raiders','canterbury-bankstown-bulldogs':'Canterbury-Bankstown Bulldogs','cronulla-sutherland-sharks':'Cronulla-Sutherland Sharks','manly-warringah-sea-eagles':'Manly Warringah Sea Eagles','new-zealand-warriors':'New Zealand Warriors','newtown-jets':'Newtown Jets','newcastle-knights':'Newcastle Knights','north-sydney-bears':'North Sydney Bears','parramatta-eels':'Parramatta Eels','penrith-panthers':'Penrith Panthers','south-sydney-rabbitohs':'South Sydney Rabbitohs','st-george-illawarra-dragons':'St George Illawarra Dragons','sydney-roosters':'Sydney Roosters','western-suburbs-magpies':'Western Suburbs Magpies','blacktown-workers-sea-eagles':'Blacktown Workers Sea Eagles'
}
SHORT_TEAM={
 'Brisbane':'Brisbane Tigers','Burleigh':'Burleigh Bears','Central QLD':'Central Queensland Capras','Ipswich':'Ipswich Jets','Mackay':'Mackay Cutters','Northern':'Northern Pride','Norths':'Norths Devils','PNG':'Papua New Guinea Hunters','Redcliffe':'Redcliffe Dolphins','Souths Logan':'Souths Logan Magpies','Sunshine Coast':'Sunshine Coast Falcons','Townsville':'Townsville Blackhawks','Tweed':'Tweed Seagulls','Western':'Western Clydesdales','Wynnum-Manly':'Wynnum Manly Seagulls',
 'Canberra':'Canberra Raiders','Canterbury':'Canterbury-Bankstown Bulldogs','Cronulla':'Cronulla-Sutherland Sharks','Manly':'Manly Warringah Sea Eagles','Warriors':'New Zealand Warriors','New Zealand':'New Zealand Warriors','Newtown':'Newtown Jets','Newcastle':'Newcastle Knights','North Sydney':'North Sydney Bears','Parramatta':'Parramatta Eels','Penrith':'Penrith Panthers','South Sydney':'South Sydney Rabbitohs','St George Illawarra':'St George Illawarra Dragons','Sydney Roosters':'Sydney Roosters','Western Suburbs':'Western Suburbs Magpies','Blacktown Workers':'Blacktown Workers Sea Eagles'
}

def get(url):
 req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 LeagueLinks/0.26'})
 with urllib.request.urlopen(req,timeout=30) as r:return r.read().decode('utf-8','replace')

def read_csv(url):return list(csv.DictReader(io.StringIO(get(url))))
def norm(s):return re.sub(r'[^a-z0-9]','',(s or '').lower())
def display_name(s):
 s=' '.join((s or '').split())
 if ',' in s:
  last,first=s.split(',',1);return f'{first.strip().title()} {last.strip().title()}'.strip()
 parts=s.split();return ' '.join(p[:1].upper()+p[1:].lower() if not p.isupper() or len(p)<=2 else p.title() for p in parts)
def team_name(slug):return TEAM_MAP.get(slug,slug.replace('-',' ').title())
def opponent_name(s):return SHORT_TEAM.get(' '.join((s or '').split()),' '.join((s or '').split()))

class SeasonLinks(HTMLParser):
 def __init__(self,prefix):super().__init__();self.prefix=prefix;self.teams=set()
 def handle_starttag(self,tag,attrs):
  if tag!='a':return
  href=dict(attrs).get('href','')
  m=re.match(rf'^/seasons/{re.escape(self.prefix)}/([^/]+)/(?:summary\.html|Round-1)$',href)
  if m:self.teams.add(m.group(1))

class TableParser(HTMLParser):
 def __init__(self):super().__init__();self.tables=[];self.table=None;self.row=None;self.cell=None;self.link=None
 def handle_starttag(self,tag,attrs):
  attrs=dict(attrs)
  if tag=='table':self.table=[]
  elif tag=='tr' and self.table is not None:self.row=[]
  elif tag in ('td','th') and self.row is not None:self.cell={'text':[],'links':[],'attrs':attrs}
  elif tag=='a' and self.cell is not None:
   self.link={'href':attrs.get('href',''),'text':[]};self.cell['links'].append(self.link)
 def handle_data(self,d):
  if self.cell is not None:self.cell['text'].append(d)
  if self.link is not None:self.link['text'].append(d)
 def handle_endtag(self,tag):
  if tag=='a':self.link=None
  elif tag in ('td','th') and self.cell is not None and self.row is not None:
   self.cell['text']=' '.join(''.join(self.cell['text']).split())
   for l in self.cell['links']:l['text']=' '.join(''.join(l['text']).split())
   self.row.append(self.cell);self.cell=None
  elif tag=='tr' and self.row is not None:
   if self.row:self.table.append(self.row)
   self.row=None
  elif tag=='table' and self.table is not None:
   self.tables.append(self.table);self.table=None

def nrl_names():
 idx=defaultdict(list)
 for r in read_csv(f'{NRL}/player_summary_data.csv'):
  pid=(r.get('player_id') or '').strip();raw=(r.get('player_name_comma') or '').strip()
  if not pid or not raw:continue
  idx[norm(display_name(raw))].append(pid)
 return idx

def synthetic_id(rlp_id):return str(9000000+int(rlp_id))

def parse_team_page(html,competition,season,team,canonical_names):
 p=TableParser();p.feed(html)
 matrix=None;matches=None
 for t in p.tables:
  if t and t[0] and t[0][0]['text']=='Player' and any(re.search(r'/matches/\d+',l.get('href','')) for c in t[0][1:] for l in c['links']):matrix=t
  if len(t)>1 and any(c['text']=='Opposition' for c in t[1] if isinstance(c,dict)):matches=t
 if not matrix:return [],{}
 header=matrix[0];match_cols=[]
 for i,c in enumerate(header[1:],1):
  mid=None
  for l in c['links']:
   m=re.search(r'/matches/(\d+)',l.get('href',''))
   if m:mid=m.group(1);break
  if mid:match_cols.append((i,mid))
 opponents={}
 if matches:
  for row in matches[2:]:
   mid=None
   for c in row:
    for l in c['links']:
     m=re.search(r'/matches/(\d+)',l.get('href',''))
     if m:mid=m.group(1)
   if mid and len(row)>2:opponents[mid]=opponent_name(row[2]['text'])
 out=[];players={}
 for row in matrix[1:]:
  if not row:continue
  plink=next((l for l in row[0]['links'] if re.search(r'/players/\d+',l.get('href',''))),None)
  if not plink:continue
  m=re.search(r'/players/(\d+)',plink['href']);rlp_id=m.group(1) if m else None
  name=display_name(row[0]['text'] or plink.get('text'))
  ids=canonical_names.get(norm(name),[]);pid=ids[0] if len(ids)==1 else synthetic_id(rlp_id)
  players[pid]={'id':pid,'name':name,'rlpId':rlp_id}
  for ci,mid in match_cols:
   if ci<len(row) and row[ci]['text'].strip():
    out.append([pid,f'RLP-{competition.replace(" ","-")}-{season}-{mid}',season,competition,team,opponents.get(mid,'')])
 return out,players

def build():
 canonical=nrl_names();appearances=[];players={};coverage=[]
 for competition,slug in COMPS:
  for season in YEARS:
   prefix=f'{slug}-{season}';url=f'{RLP}/{prefix}/players.html'
   try:html=get(url)
   except Exception as e:print('season unavailable',competition,season,e);continue
   lp=SeasonLinks(prefix);lp.feed(html);teams=sorted(lp.teams)
   print(competition,season,'teams found',len(teams),teams)
   season_apps=0;season_players=set();loaded_teams=0
   for team_slug in teams:
    try:page=get(f'{RLP}/{prefix}/{team_slug}/Round-1')
    except Exception as e:print(' team unavailable',team_slug,e);continue
    rows,ps=parse_team_page(page,competition,season,team_name(team_slug),canonical)
    if not rows:continue
    loaded_teams+=1;appearances.extend(rows);players.update(ps);season_apps+=len(rows);season_players.update(r[0] for r in rows)
   coverage.append([competition,season,loaded_teams,len(season_players),season_apps])
   print(' loaded',loaded_teams,'teams',len(season_players),'players',season_apps,'appearances')
 # exact dedupe
 appearances=list({tuple(r):r for r in appearances}.values())
 used={r[0] for r in appearances};players=[players[p] for p in sorted(used,key=int) if p in players]
 payload={'version':26,'builtAt':int(datetime.now(timezone.utc).timestamp()*1000),'players':players,'appearances':appearances,'coverage':coverage}
 os.makedirs(os.path.dirname(OUT),exist_ok=True)
 with open(OUT,'w',encoding='utf-8') as f:json.dump(payload,f,separators=(',',':'),ensure_ascii=False)
 print(json.dumps({'players':len(players),'appearances':len(appearances),'coverage':coverage},indent=2))

if __name__=='__main__':build()
