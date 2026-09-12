#!/usr/bin/env python3
import csv, gzip, io, json, os, re, urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from html.parser import HTMLParser

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
OUT=os.path.join(ROOT,'data')
NRL='https://raw.githubusercontent.com/uselessnrlstats/uselessnrlstats/main/data/nrl'
RLP='https://www.rugbyleagueproject.org/seasons'
VERSION=26

CONFIG=[
 ('NSW Cup',range(2014,2027),['nsw-cup-{year}']),
 ('Queensland Cup',range(2014,2027),['qld-cup-{year}']),
 ('NYC / Jersey Flegg',range(2018,2027),['jersey-flegg-cup-{year}','jersey-flegg-{year}']),
 ('SG Ball',range(2018,2027),['sg-ball-cup-{year}','sg-ball-{year}']),
 ('Harold Matthews',range(2018,2027),['harold-matthews-cup-{year}','harold-matthews-{year}']),
 ('Mal Meninga',range(2018,2027),['mal-meninga-cup-{year}','mal-meninga-{year}']),
 ('Cyril Connell',range(2024,2027),['cyril-connell-cup-{year}','cyril-connell-{year}']),
 ('Queensland Colts',range(2018,2024),['hastings-deering-colts-{year}','qld-colts-{year}','queensland-colts-{year}'])
]

TEAM_NAMES={
 'canberra-raiders':'Canberra Raiders','canterbury-bankstown-bulldogs':'Canterbury-Bankstown Bulldogs','cronulla-sutherland-sharks':'Cronulla-Sutherland Sharks','manly-warringah-sea-eagles':'Manly Warringah Sea Eagles','melbourne-storm':'Melbourne Storm','newcastle-knights':'Newcastle Knights','new-zealand-warriors':'New Zealand Warriors','newtown-jets':'Newtown Jets','north-sydney-bears':'North Sydney Bears','parramatta-eels':'Parramatta Eels','penrith-panthers':'Penrith Panthers','south-sydney-rabbitohs':'South Sydney Rabbitohs','st-george-illawarra-dragons':'St George Illawarra Dragons','sydney-roosters':'Sydney Roosters','western-suburbs-magpies':'Western Suburbs Magpies','wests-tigers':'Wests Tigers','blacktown-workers-sea-eagles':'Blacktown Workers Sea Eagles',
 'brisbane-tigers':'Brisbane Tigers','burleigh-bears':'Burleigh Bears','central-queensland-capras':'Central Queensland Capras','ipswich-jets':'Ipswich Jets','mackay-cutters':'Mackay Cutters','northern-pride':'Northern Pride','norths-devils':'Norths Devils','papua-new-guinea-hunters':'Papua New Guinea Hunters','redcliffe-dolphins':'Redcliffe Dolphins','souths-logan-magpies':'Souths Logan Magpies','sunshine-coast-falcons':'Sunshine Coast Falcons','townsville-blackhawks':'Townsville Blackhawks','tweed-seagulls':'Tweed Seagulls','western-clydesdales':'Western Clydesdales','wynnum-manly-seagulls':'Wynnum Manly Seagulls',
 'balmain-tigers':'Balmain Tigers','central-coast-roosters':'Central Coast Roosters','illawarra-steelers':'Illawarra Steelers','st-george-dragons':'St George Dragons','kaiviti-silktails':'Kaiviti Silktails'
}

class TableParser(HTMLParser):
    def __init__(self):
        super().__init__();self.rows=[];self.row=None;self.cell=None;self.link=None
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='tr':self.row=[]
        elif tag in ('td','th') and self.row is not None:self.cell={'text':[],'links':[]}
        elif tag=='a' and self.cell is not None:
            self.link={'href':attrs.get('href',''),'text':[]};self.cell['links'].append(self.link)
    def handle_data(self,data):
        if self.cell is not None:self.cell['text'].append(data)
        if self.link is not None:self.link['text'].append(data)
    def handle_endtag(self,tag):
        if tag=='a':self.link=None
        elif tag in ('td','th') and self.cell is not None and self.row is not None:
            self.cell['text']=' '.join(''.join(self.cell['text']).split())
            for l in self.cell['links']:l['text']=' '.join(''.join(l['text']).split())
            self.row.append(self.cell);self.cell=None
        elif tag=='tr' and self.row is not None:
            if self.row:self.rows.append(self.row)
            self.row=None

def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'LeagueLinksCatalogueBuilder/0.26'})
    with urllib.request.urlopen(req,timeout=35) as r:return r.read().decode('utf-8','replace')

def get_csv(url):return list(csv.DictReader(io.StringIO(get(url))))

def norm(s):return re.sub(r'[^a-z0-9]','',(s or '').lower())
def clean_name(s):
    s=' '.join((s or '').split())
    if ',' in s:
        last,first=s.split(',',1);return f'{first.strip().title()} {last.strip().title()}'.strip()
    return s.title()
def intish(s):
    m=re.search(r'\d+',s or '');return int(m.group()) if m else 0

def team_from_link(link):
    href=link.get('href','')
    m=re.search(r'/teams/([^/]+)/',href)
    if not m:return None
    slug=m.group(1).lower();return TEAM_NAMES.get(slug,slug.replace('-',' ').title())

def parse_players(html):
    p=TableParser();p.feed(html);out=[]
    for row in p.rows:
        pidx=None;plink=None
        for i,c in enumerate(row):
            for l in c.get('links',[]):
                if '/players/' in l.get('href',''):
                    pidx=i;plink=l;break
            if pidx is not None:break
        if pidx is None:continue
        name=clean_name(row[pidx].get('text') or plink.get('text'))
        if not name or name.lower() in ('player','players'):continue
        team_cell=None;team_names=[];team_idx=None
        for j in range(pidx+1,len(row)):
            ts=[team_from_link(l) for l in row[j].get('links',[])]
            ts=[t for t in ts if t]
            if ts:team_cell=row[j];team_names=ts;team_idx=j;break
        if not team_names:
            # RLP season tables normally place Team(s) two columns after Player.
            j=min(pidx+2,len(row)-1);team_idx=j
            txt=row[j].get('text','').strip()
            if txt and not txt.isdigit():team_names=[txt]
        if not team_names:continue
        apps=0
        for j in range((team_idx or pidx)+1,min(len(row),(team_idx or pidx)+4)):
            v=intish(row[j].get('text',''))
            if v or row[j].get('text','').strip() in ('0','-'):
                apps=v;break
        slug=''
        m=re.search(r'/players/([^/]+)/',plink.get('href',''))
        if m:slug=m.group(1)
        out.append({'name':name,'slug':slug,'teams':list(dict.fromkeys(team_names)),'appearances':apps})
    return out

def build():
    name_ids=defaultdict(list)
    for r in get_csv(f'{NRL}/player_summary_data.csv'):
        pid=(r.get('player_id') or '').strip();raw=(r.get('player_name_comma') or '').strip()
        if not pid or not raw:continue
        name=clean_name(raw);name_ids[norm(name)].append(pid)
    rows=[];coverage=[]
    for competition,years,patterns in CONFIG:
        for year in years:
            found=[];source=''
            for pat in patterns:
                url=f'{RLP}/{pat.format(year=year)}/players.html'
                try:
                    html=get(url);parsed=parse_players(html)
                    if len(parsed)>=5:
                        found=parsed;source=url;break
                except Exception:pass
            if not found:continue
            team_count=set()
            for p in found:
                ids=name_ids.get(norm(p['name']),[]);pid=ids[0] if len(ids)==1 else None
                for team in p['teams']:
                    team_count.add(team);rows.append([competition,year,team,pid,p['name'],p['appearances'],p['slug']])
            coverage.append([competition,year,len(found),len(team_count),source])
            print(competition,year,'players',len(found),'teams',len(team_count))
    payload={'version':VERSION,'builtAt':int(datetime.now(timezone.utc).timestamp()*1000),'rows':rows,'coverage':coverage}
    os.makedirs(OUT,exist_ok=True)
    raw=json.dumps(payload,separators=(',',':'),ensure_ascii=False).encode('utf-8')
    path=os.path.join(OUT,'season-catalogues.json.gz')
    with gzip.open(path,'wb',compresslevel=9) as f:f.write(raw)
    meta={'version':VERSION,'rows':len(rows),'competitionSeasons':len(coverage),'competitions':sorted({r[0] for r in coverage}),'compressedBytes':os.path.getsize(path)}
    with open(os.path.join(OUT,'season-catalogues-meta.json'),'w',encoding='utf-8') as f:json.dump(meta,f,indent=2)
    print(json.dumps(meta,indent=2))

if __name__=='__main__':build()
