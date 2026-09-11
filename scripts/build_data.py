#!/usr/bin/env python3
import csv, gzip, io, json, os, re, urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from itertools import combinations

NRL='https://raw.githubusercontent.com/uselessnrlstats/uselessnrlstats/main/data/nrl'
ORIGIN='https://raw.githubusercontent.com/uselessnrlstats/uselessnrlstats/main/cleaned_data/origin'
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
OUT=os.path.join(ROOT,'data')
SUPP_PLAYERS=os.path.join(ROOT,'sources','players.csv')
SUPP_APPEARANCES=os.path.join(ROOT,'sources','confirmed_appearances.csv')

def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'LeagueLinksDataBuilder/0.23'})
    with urllib.request.urlopen(req,timeout=60) as r:
        return r.read().decode('utf-8')

def read_csv(url):
    return list(csv.DictReader(io.StringIO(get(url))))

def title_case(s):
    return ' '.join(x[:1].upper()+x[1:].lower() if x else x for x in re.split(r'(\s+)',s or ''))

def player_name(raw):
    if not raw:return 'Unknown player'
    if ',' not in raw:return title_case(raw)
    last,first=raw.split(',',1)
    return f'{title_case(first.strip())} {title_case(last.strip())}'.strip()

def canonical_team(raw):
    s=re.sub(r'\s+',' ',(raw or '').replace('\r',' ').replace('\n',' ')).strip();u=s.upper()
    rules=[('CANBERRA','Canberra Raiders'),('BRISBANE','Brisbane Broncos'),('CANTERBURY','Canterbury-Bankstown Bulldogs'),('CRONULLA','Cronulla-Sutherland Sharks'),('GOLD COAST','Gold Coast Titans'),('MANLY','Manly Warringah Sea Eagles'),('MELBOURNE','Melbourne Storm'),('NEWCASTLE','Newcastle Knights'),('NORTH QUEENSLAND','North Queensland Cowboys'),('PARRAMATTA','Parramatta Eels'),('PENRITH','Penrith Panthers'),('SOUTH SYDNEY','South Sydney Rabbitohs'),('ST GEORGE','St George Illawarra Dragons'),('SYDNEY ROOSTERS','Sydney Roosters'),('ROOSTERS','Sydney Roosters'),('WESTS','Wests Tigers'),('NEW ZEALAND','New Zealand Warriors'),('WARRIORS','New Zealand Warriors'),('DOLPHINS','Dolphins')]
    for needle,name in rules:
        if needle in u:return name
    return title_case(s)

def pair_key(a,b):
    a,b=str(a),str(b)
    return f'{a}|{b}' if int(a)<int(b) else f'{b}|{a}'

players={}
appearances=defaultdict(int)
career=defaultdict(int)
rosters=defaultdict(int)
edges={}
histories=defaultdict(int)
competitions=set()

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

def build():
    print('Loading player names')
    for r in read_csv(f'{NRL}/player_summary_data.csv'):
        pid=(r.get('player_id') or '').strip()
        if pid: players[pid]={'id':pid,'name':player_name(r.get('player_name_comma','')),'birthday':(r.get('player_birthday') or '').strip()}
    for year in range(2008,2027):
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
        if not pid or not mid or not year or year < 2008:continue
        team=title_case((r.get('team') or '').strip())
        groups[(mid,year,team)].add(pid)
    for (_,year,team),ids in groups.items():add_group(year,'State of Origin',team,ids)

    # Optional League Links-owned match appearances for state cups, youth and other representative football.
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

    used=set(appearances)
    payload={
      'version':23,
      'builtAt':int(datetime.now(timezone.utc).timestamp()*1000),
      'players':[players.get(pid,{'id':pid,'name':f'Player {pid}','birthday':''}) for pid in sorted(used,key=int)],
      'edges':list(edges.values()),
      'career':[[pid,y,c,t,g] for (pid,y,c,t),g in career.items()],
      'rosters':[[c,y,t,pid,g] for (c,y,t,pid),g in rosters.items()],
      'histories':[[pk,y,c,t,g] for (pk,y,c,t),g in histories.items()],
      'appearances':[[pid,n] for pid,n in appearances.items()],
      'competitionsLoaded':sorted(competitions)
    }
    os.makedirs(OUT,exist_ok=True)
    raw=json.dumps(payload,separators=(',',':'),ensure_ascii=False).encode('utf-8')
    with gzip.open(os.path.join(OUT,'league-links.json.gz'),'wb',compresslevel=9) as f:f.write(raw)
    meta={'version':23,'builtAt':payload['builtAt'],'players':len(payload['players']),'links':len(payload['edges']),'gamesRecorded':sum(appearances.values()),'competitions':payload['competitionsLoaded'],'compressedBytes':os.path.getsize(os.path.join(OUT,'league-links.json.gz'))}
    with open(os.path.join(OUT,'build-meta.json'),'w',encoding='utf-8') as f:json.dump(meta,f,indent=2)
    print(json.dumps(meta,indent=2))
if __name__=='__main__':build()
