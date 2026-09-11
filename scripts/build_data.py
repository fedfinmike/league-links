#!/usr/bin/env python3
import csv, gzip, io, json, os, re, urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from itertools import combinations

NRL='https://raw.githubusercontent.com/uselessnrlstats/uselessnrlstats/main/data/nrl'
ORIGIN='https://raw.githubusercontent.com/uselessnrlstats/uselessnrlstats/main/cleaned_data/origin'
RLP='https://www.rugbyleagueproject.org/teams'
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
OUT=os.path.join(ROOT,'data')
SUPP_PLAYERS=os.path.join(ROOT,'sources','players.csv')
SUPP_APPEARANCES=os.path.join(ROOT,'sources','confirmed_appearances.csv')
INTERNATIONAL_TEAMS_FILE=os.path.join(ROOT,'sources','international_teams.json')
HISTORY_START=2000
HISTORY_END=2026
VERSION=24

class RowParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.rows=[]; self.row=None; self.cell=None
    def handle_starttag(self,tag,attrs):
        if tag=='tr': self.row=[]
        elif tag in ('td','th') and self.row is not None: self.cell=[]
    def handle_data(self,data):
        if self.cell is not None: self.cell.append(data)
    def handle_endtag(self,tag):
        if tag in ('td','th') and self.cell is not None and self.row is not None:
            self.row.append(re.sub(r'\s+',' ',' '.join(self.cell)).strip()); self.cell=None
        elif tag=='tr' and self.row is not None:
            if self.row: self.rows.append(self.row)
            self.row=None; self.cell=None

def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'LeagueLinksDataBuilder/0.24 (+public rugby league history project)'})
    with urllib.request.urlopen(req,timeout=60) as r:
        return r.read().decode('utf-8','replace')

def read_csv(url):
    return list(csv.DictReader(io.StringIO(get(url))))

def title_case(s):
    return ' '.join(x[:1].upper()+x[1:].lower() if x else x for x in re.split(r'(\s+)',s or ''))

def player_name(raw):
    if not raw:return 'Unknown player'
    if ',' not in raw:return title_case(raw)
    last,first=raw.split(',',1)
    return f'{title_case(first.strip())} {title_case(last.strip())}'.strip()

def norm_name(s):
    return re.sub(r'[^a-z0-9]','',(s or '').lower())

def canonical_team(raw):
    s=re.sub(r'\s+',' ',(raw or '').replace('\r',' ').replace('\n',' ')).strip();u=s.upper()
    rules=[('CANBERRA','Canberra Raiders'),('BRISBANE','Brisbane Broncos'),('CANTERBURY','Canterbury-Bankstown Bulldogs'),('CRONULLA','Cronulla-Sutherland Sharks'),('GOLD COAST','Gold Coast Titans'),('MANLY','Manly Warringah Sea Eagles'),('MELBOURNE','Melbourne Storm'),('NEWCASTLE','Newcastle Knights'),('NORTH QUEENSLAND','North Queensland Cowboys'),('PARRAMATTA','Parramatta Eels'),('PENRITH','Penrith Panthers'),('SOUTH SYDNEY','South Sydney Rabbitohs'),('ST GEORGE','St George Illawarra Dragons'),('SYDNEY ROOSTERS','Sydney Roosters'),('ROOSTERS','Sydney Roosters'),('WESTS','Wests Tigers'),('NEW ZEALAND','New Zealand Warriors'),('WARRIORS','New Zealand Warriors'),('DOLPHINS','Dolphins')]
    for needle,name in rules:
        if needle in u:return name
    return title_case(s)

def pair_key(a,b):
    a,b=str(a),str(b)
    return f'{a}|{b}' if int(a)<int(b) else f'{b}|{a}'

def year_from_text(s):
    m=re.search(r'(19|20)\d{2}',s or '')
    return int(m.group()) if m else None

def int_or_none(s):
    s=re.sub(r'[^0-9]','',s or '')
    return int(s) if s else None

players={}
appearances=defaultdict(int)
career=defaultdict(int)
rosters=defaultdict(int)
edges={}
histories=defaultdict(int)
competitions=set()
team_catalogues={}

def add_group(year,competition,team,ids):
    ids=sorted(set(str(x) for x in ids if x),key=int)
    competitions.add(competition)
    for pid in ids:
        appearances[pid]+=1
        career[(pid,int(year),competition,team)]+=1
        rosters[(competition,int(year),team,pid)]+=1
    for a,b in combinations(ids,2):
        pk=pair_key(a,b)
        e=edges.setdefault(pk,{'a':a,'b':b,'games':0,'first':int(year),'last':int(year)})
        e['games']+=1;e['first']=min(e['first'],int(year));e['last']=max(e['last'],int(year))
        histories[(pk,int(year),competition,team)]+=1

def player_index():
    out=defaultdict(list)
    for pid,p in players.items(): out[norm_name(p.get('name'))].append(pid)
    return out

def resolve_existing_player(name,dob,index):
    ids=index.get(norm_name(name),[])
    if len(ids)==1:return ids[0]
    if dob:
        exact=[pid for pid in ids if (players.get(pid,{}).get('birthday') or '')==dob]
        if len(exact)==1:return exact[0]
    return None

def load_international_catalogues():
    try:
        with open(INTERNATIONAL_TEAMS_FILE,encoding='utf-8') as f: teams=json.load(f)
    except Exception as e:
        print('International team catalogue not loaded:',e); return
    index=player_index()
    for info in teams:
        name=info.get('name'); slug=info.get('slug')
        if not name or not slug:continue
        url=f'{RLP}/{slug}/players-senior-international-matches.html'
        try:
            html=get(url); parser=RowParser(); parser.feed(html); entries=[]
            for cells in parser.rows:
                if len(cells)<8:continue
                raw_name=(cells[0] or '').strip(); dob=(cells[1] or '').strip()
                if ',' not in raw_name:continue
                last_year=year_from_text(cells[4] if len(cells)>4 else '')
                first_year=year_from_text(cells[3] if len(cells)>3 else '')
                if last_year and last_year < HISTORY_START:continue
                display=player_name(raw_name)
                apps=int_or_none(cells[6] if len(cells)>6 else '')
                if apps is None:apps=int_or_none(cells[7] if len(cells)>7 else '')
                if apps is None:apps=int_or_none(cells[5] if len(cells)>5 else '')
                pid=resolve_existing_player(display,dob,index)
                entries.append({'id':pid,'name':display,'birthday':dob,'first':first_year,'last':last_year,'appearances':apps or 0})
            entries.sort(key=lambda x:(-(x.get('appearances') or 0),x.get('name') or ''))
            team_catalogues[name]={'source':url,'players':entries}
            print('International',name,len(entries))
        except Exception as e:
            print('International catalogue unavailable for',name,':',e)
            team_catalogues[name]={'source':url,'players':[]}

def build():
    print('Loading player names')
    for r in read_csv(f'{NRL}/player_summary_data.csv'):
        pid=(r.get('player_id') or '').strip()
        if pid: players[pid]={'id':pid,'name':player_name(r.get('player_name_comma','')),'birthday':(r.get('player_birthday') or '').strip()}
    for year in range(HISTORY_START,HISTORY_END+1):
        idx=year-1907;print('NRL',year)
        rows=read_csv(f'{NRL}/player_match_data/player_match_data_{idx}.csv')
        groups=defaultdict(set)
        for r in rows:
            pid=(r.get('player_id') or '').strip();mid=(r.get('match_id') or '').strip()
            if not pid or not mid:continue
            team=canonical_team(r.get('team'))
            groups[(mid,team)].add(pid)
        for (_,team),ids in groups.items():add_group(year,'NRL',team,ids)
    print('State of Origin')
    match_rows=read_csv(f'{ORIGIN}/match_data.csv');years={(r.get('match_id') or '').strip():int(r['year']) for r in match_rows if (r.get('match_id') or '').strip() and (r.get('year') or '').isdigit()}
    groups=defaultdict(set)
    for r in read_csv(f'{ORIGIN}/player_match_data.csv'):
        pid=(r.get('player_id') or '').strip();mid=(r.get('match_id') or '').strip();year=years.get(mid)
        if not pid or not mid or not year or year < HISTORY_START:continue
        team=title_case((r.get('team') or '').strip())
        groups[(mid,year,team)].add(pid)
    for (_,year,team),ids in groups.items():add_group(year,'State of Origin',team,ids)

    # League Links-owned match appearances for state cups, youth and representative football.
    # Only rows with an explicit match_id are promoted into teammate counts.
    if os.path.exists(SUPP_PLAYERS):
        with open(SUPP_PLAYERS,newline='',encoding='utf-8-sig') as f:
            for r in csv.DictReader(f):
                pid=(r.get('league_links_id') or '').strip()
                if pid and pid.isdigit():
                    players[pid]={'id':pid,'name':(r.get('name') or f'Player {pid}').strip(),'birthday':(r.get('birthday') or '').strip()}
    if os.path.exists(SUPP_APPEARANCES):
        local_groups=defaultdict(set)
        with open(SUPP_APPEARANCES,newline='',encoding='utf-8-sig') as f:
            for r in csv.DictReader(f):
                pid=(r.get('league_links_id') or '').strip();mid=(r.get('match_id') or '').strip()
                year=(r.get('year') or '').strip();competition=(r.get('competition') or '').strip();team=(r.get('team') or '').strip()
                if not (pid.isdigit() and mid and year.isdigit() and competition and team):continue
                local_groups[(mid,int(year),competition,team)].add(pid)
        for (_,year,competition,team),ids in local_groups.items():add_group(year,competition,team,ids)

    # International player lists are useful for team browsing, but do not create teammate links.
    # Exact international links will only come from match-confirmed rows in confirmed_appearances.csv.
    load_international_catalogues()

    used=set(appearances)
    payload={
      'version':VERSION,
      'builtAt':int(datetime.now(timezone.utc).timestamp()*1000),
      'historyStart':HISTORY_START,
      'historyEnd':HISTORY_END,
      'players':[players.get(pid,{'id':pid,'name':f'Player {pid}','birthday':''}) for pid in sorted(used,key=int)],
      'edges':list(edges.values()),
      'career':[[pid,y,c,t,g] for (pid,y,c,t),g in career.items()],
      'rosters':[[c,y,t,pid,g] for (c,y,t,pid),g in rosters.items()],
      'histories':[[pk,y,c,t,g] for (pk,y,c,t),g in histories.items()],
      'appearances':[[pid,n] for pid,n in appearances.items()],
      'competitionsLoaded':sorted(competitions),
      'teamCatalogues':[[team,data] for team,data in sorted(team_catalogues.items())]
    }
    os.makedirs(OUT,exist_ok=True)
    raw=json.dumps(payload,separators=(',',':'),ensure_ascii=False).encode('utf-8')
    with gzip.open(os.path.join(OUT,'league-links.json.gz'),'wb',compresslevel=9) as f:f.write(raw)
    meta={'version':VERSION,'builtAt':payload['builtAt'],'historyStart':HISTORY_START,'historyEnd':HISTORY_END,'players':len(payload['players']),'links':len(payload['edges']),'playerAppearances':sum(appearances.values()),'competitions':payload['competitionsLoaded'],'internationalTeams':len(team_catalogues),'compressedBytes':os.path.getsize(os.path.join(OUT,'league-links.json.gz'))}
    with open(os.path.join(OUT,'build-meta.json'),'w',encoding='utf-8') as f:json.dump(meta,f,indent=2)
    print(json.dumps(meta,indent=2))
if __name__=='__main__':build()
