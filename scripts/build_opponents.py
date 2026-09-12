#!/usr/bin/env python3
import csv, gzip, io, json, os, re, urllib.request
from collections import defaultdict
from datetime import datetime, timezone

NRL='https://raw.githubusercontent.com/uselessnrlstats/uselessnrlstats/main/data/nrl'
ORIGIN='https://raw.githubusercontent.com/uselessnrlstats/uselessnrlstats/main/cleaned_data/origin'
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
OUT=os.path.join(ROOT,'data')
SUPP=os.path.join(ROOT,'sources','confirmed_appearances.csv')
START=2000
END=2026
VERSION=27

def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'LeagueLinksOpponentBuilder/0.27'})
    with urllib.request.urlopen(req,timeout=60) as r:
        return r.read().decode('utf-8','replace')

def read_csv(url):
    return list(csv.DictReader(io.StringIO(get(url))))

def title_case(s):
    return ' '.join(x[:1].upper()+x[1:].lower() if x else x for x in re.split(r'(\s+)',s or ''))

def canonical_team(raw):
    s=re.sub(r'\s+',' ',(raw or '').replace('\r',' ').replace('\n',' ')).strip();u=s.upper()
    rules=[('CANBERRA','Canberra Raiders'),('BRISBANE','Brisbane Broncos'),('CANTERBURY','Canterbury-Bankstown Bulldogs'),('CRONULLA','Cronulla-Sutherland Sharks'),('GOLD COAST','Gold Coast Titans'),('MANLY','Manly Warringah Sea Eagles'),('MELBOURNE','Melbourne Storm'),('NEWCASTLE','Newcastle Knights'),('NORTH QUEENSLAND','North Queensland Cowboys'),('PARRAMATTA','Parramatta Eels'),('PENRITH','Penrith Panthers'),('SOUTH SYDNEY','South Sydney Rabbitohs'),('ST GEORGE','St George Illawarra Dragons'),('SYDNEY ROOSTERS','Sydney Roosters'),('ROOSTERS','Sydney Roosters'),('WESTS','Wests Tigers'),('NEW ZEALAND','New Zealand Warriors'),('WARRIORS','New Zealand Warriors'),('DOLPHINS','Dolphins')]
    for needle,name in rules:
        if needle in u:return name
    return title_case(s)

def origin_team(raw):
    u=(raw or '').strip().upper()
    if 'MAROON' in u or u=='QUEENSLAND': return 'Queensland'
    if 'BLUE' in u or 'NEW SOUTH WALES' in u or u=='NSW': return 'New South Wales'
    return title_case(raw)

team_counts=defaultdict(int)
player_counts=defaultdict(int)

def add_team(pid,year,competition,opponent,n=1):
    if pid and opponent:
        team_counts[(str(pid),int(year),competition,opponent)]+=n

def add_player(pid,opponent_pid,year,competition,opponent_team,n=1):
    if pid and opponent_pid and str(pid)!=str(opponent_pid):
        player_counts[(str(pid),str(opponent_pid),int(year),competition,opponent_team or '')]+=n

def cross_opponents(rosters,opponents,year,competition):
    for (mid,team),ids in rosters.items():
        opponent=opponents.get((mid,team),'')
        if not opponent:continue
        other=rosters.get((mid,opponent))
        if not other:continue
        for pid in ids:
            for opp_pid in other:
                add_player(pid,opp_pid,year,competition,opponent)

def build():
    for year in range(START,END+1):
        idx=year-1907
        print('NRL opponents',year)
        rows=read_csv(f'{NRL}/player_match_data/player_match_data_{idx}.csv')
        rosters=defaultdict(set);opponents={}
        for r in rows:
            pid=(r.get('player_id') or '').strip();mid=(r.get('match_id') or '').strip()
            team=canonical_team(r.get('team') or '')
            opponent=canonical_team(r.get('opposition_team') or r.get('opposition') or '')
            if pid and opponent:add_team(pid,year,'NRL',opponent)
            if pid and mid and team:
                rosters[(mid,team)].add(pid)
                if opponent:opponents[(mid,team)]=opponent
        cross_opponents(rosters,opponents,year,'NRL')

    print('Origin opponents')
    matches={}
    for r in read_csv(f'{ORIGIN}/match_data.csv'):
        mid=(r.get('match_id') or '').strip(); y=(r.get('year') or '').strip()
        if not mid or not y.isdigit() or int(y)<START:continue
        matches[mid]=(int(y),origin_team(r.get('home_team')),origin_team(r.get('away_team')))
    origin_rosters=defaultdict(set);origin_opponents={}
    for r in read_csv(f'{ORIGIN}/player_match_data.csv'):
        pid=(r.get('player_id') or '').strip();mid=(r.get('match_id') or '').strip();m=matches.get(mid)
        if not pid or not m:continue
        year,home,away=m;team=origin_team(r.get('team'))
        opponent=away if team==home else home if team==away else ''
        if opponent:add_team(pid,year,'State of Origin',opponent)
        if team and opponent:
            origin_rosters[(mid,year,team)].add(pid)
            origin_opponents[(mid,year,team)]=opponent
    for (mid,year,team),ids in origin_rosters.items():
        opponent=origin_opponents.get((mid,year,team),'')
        other=origin_rosters.get((mid,year,opponent))
        if not other:continue
        for pid in ids:
            for opp_pid in other:add_player(pid,opp_pid,year,'State of Origin',opponent)

    # Supplemental exact match rows may also provide lower-grade/representative opponents.
    if os.path.exists(SUPP):
        supp=[]
        with open(SUPP,newline='',encoding='utf-8-sig') as f:
            for r in csv.DictReader(f):
                pid=(r.get('league_links_id') or '').strip();year=(r.get('year') or '').strip()
                comp=(r.get('competition') or '').strip();opp=(r.get('opponent_team') or '').strip()
                mid=(r.get('match_id') or '').strip();team=(r.get('team') or '').strip()
                if pid and year.isdigit() and comp and opp:
                    add_team(pid,int(year),comp,opp)
                    supp.append((pid,mid,int(year),comp,team,opp))
        groups=defaultdict(set);opp_map={}
        for pid,mid,year,comp,team,opp in supp:
            if mid and team:
                groups[(mid,year,comp,team)].add(pid);opp_map[(mid,year,comp,team)]=opp
        for key,ids in groups.items():
            mid,year,comp,team=key;opp=opp_map.get(key,'');other=groups.get((mid,year,comp,opp))
            if not other:continue
            for pid in ids:
                for opp_pid in other:add_player(pid,opp_pid,year,comp,opp)

    rows=[[pid,year,comp,opp,games] for (pid,year,comp,opp),games in sorted(team_counts.items(),key=lambda x:(x[0][0],x[0][1],x[0][2],x[0][3]))]
    player_rows=[[pid,opp_pid,year,comp,opp_team,games] for (pid,opp_pid,year,comp,opp_team),games in sorted(player_counts.items(),key=lambda x:(x[0][0],x[0][1],x[0][2],x[0][3],x[0][4]))]
    payload={'version':VERSION,'builtAt':int(datetime.now(timezone.utc).timestamp()*1000),'rows':rows,'playerRows':player_rows}
    os.makedirs(OUT,exist_ok=True)
    raw=json.dumps(payload,separators=(',',':'),ensure_ascii=False).encode('utf-8')
    path=os.path.join(OUT,'opponents.json.gz')
    with gzip.open(path,'wb',compresslevel=9) as f:f.write(raw)
    meta={'version':VERSION,'players':len({r[0] for r in rows}),'teamRows':len(rows),'teamGames':sum(r[4] for r in rows),'playerOpponentRows':len(player_rows),'playerOpponentGames':sum(r[5] for r in player_rows),'compressedBytes':os.path.getsize(path)}
    with open(os.path.join(OUT,'opponents-meta.json'),'w',encoding='utf-8') as f:json.dump(meta,f,indent=2)
    print(json.dumps(meta,indent=2))

if __name__=='__main__':build()
