#!/usr/bin/env python3
import csv, html as htmllib, io
import json, os, re, time, urllib.error, urllib.request
from collections import Counter, defaultdict

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
OUT=os.path.join(ROOT,'data','international-exact.json')
BASE='https://www.rugbyleagueproject.org'
NRL='https://raw.githubusercontent.com/uselessnrlstats/uselessnrlstats/main/data/nrl'
DEFAULT_YEARS=range(2000,2027)
UA='Mozilla/5.0 LeagueLinks/0.28 (+historical research)'
_LAST_RLP_REQUEST=0.0
MIN_RLP_INTERVAL=0.9


def get(url,tries=5,timeout=25):
 global _LAST_RLP_REQUEST
 last=None
 for attempt in range(tries):
  try:
   if url.startswith(BASE):
    wait=MIN_RLP_INTERVAL-(time.monotonic()-_LAST_RLP_REQUEST)
    if wait>0:time.sleep(wait)
    _LAST_RLP_REQUEST=time.monotonic()
   req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html,application/xhtml+xml'})
   with urllib.request.urlopen(req,timeout=timeout) as r:return r.read().decode('utf-8','replace')
  except urllib.error.HTTPError as e:
   last=e
   if e.code==429:
    retry=e.headers.get('Retry-After') if e.headers else None
    try:delay=max(4.0,float(retry)) if retry else min(45.0,5.0*(attempt+1))
    except Exception:delay=min(45.0,5.0*(attempt+1))
    print('RLP rate limit; waiting',delay,'seconds for',url,flush=True);time.sleep(delay);continue
   if 500<=e.code<600:
    time.sleep(min(15.0,2.0*(attempt+1)));continue
   raise
  except Exception as e:
   last=e;time.sleep(min(10.0,1.5*(attempt+1)))
 raise last


def clean_text(s):return ' '.join(htmllib.unescape(re.sub(r'<[^>]+>',' ',s or '')).split())
def norm(s):return re.sub(r'[^a-z0-9]','',(s or '').lower())
def display_name(raw):
 raw=' '.join((raw or '').split())
 if ',' in raw:
  last,first=raw.split(',',1);return f'{first.strip().title()} {last.strip().title()}'.strip()
 return ' '.join(p[:1].upper()+p[1:].lower() if p else p for p in raw.split())
def synthetic_id(rlp_id):return str(9000000+int(rlp_id))


def canonical_names():
 idx=defaultdict(list)
 text=get(f'{NRL}/player_summary_data.csv',tries=3,timeout=30)
 for r in csv.DictReader(io.StringIO(text)):
  pid=(r.get('player_id') or '').strip();raw=(r.get('player_name_comma') or '').strip()
  if pid and raw:idx[norm(display_name(raw))].append(pid)
 return idx


def years_to_build():
 raw=os.environ.get('LL_INT_YEARS','').strip()
 if not raw:return list(DEFAULT_YEARS)
 out=[]
 for part in raw.split(','):
  part=part.strip()
  if '-' in part:
   a,b=part.split('-',1);out.extend(range(int(a),int(b)+1))
  elif part:out.append(int(part))
 return sorted(set(out))


def discover_matches(years):
 wanted=set(years);target=min(wanted);found={};pages=[];seen=set();earliest=None
 for page_no in range(9,0,-1):
  url=f'{BASE}/competitions/senior-international-matches/results.html?page={page_no}'
  try:page=get(url,tries=5,timeout=25)
  except Exception as e:
   print('International discovery page',page_no,'failed',repr(e),flush=True);continue
  page_ids=set(re.findall(r'/matches/(\d+)',page))
  if not page_ids:continue
  seen.update(page_ids);pages.append(page_no)
  page_years=[]
  for row in re.findall(r'<tr[^>]*>(.*?)</tr>',page,re.I|re.S):
   mids=re.findall(r'/matches/(\d+)',row)
   if not mids:continue
   txt=clean_text(row)
   ys=[int(x) for x in re.findall(r'\b(20\d{2})\b',txt)]
   if not ys:continue
   year=ys[0];page_years.append(year)
   if year in wanted:
    for mid in mids:found.setdefault(mid,year)
  if page_years:
   pmin=min(page_years);earliest=pmin if earliest is None else min(earliest,pmin)
   print('International archive page',page_no,'years',min(page_years),'-',max(page_years),'wanted matches so far',len(found),flush=True)
   if pmin<=target:break
 print('International discovery pages',sorted(pages),'archive matches scanned',len(seen),'requested matches',len(found),flush=True)
 return found,{'archivePages':sorted(pages),'archiveMatchesScanned':len(seen),'requestedMatches':len(found),'earliestScannedYear':earliest}


def player_from_cell(cell,canonical):
 m=re.search(r'<a[^>]+href=["\']/players/(\d+)["\'][^>]*>(.*?)</a>',cell,re.I|re.S)
 if not m:return None
 rlp_id=m.group(1);name=display_name(clean_text(m.group(2)))
 ids=canonical.get(norm(name),[])
 pid=ids[0] if len(ids)==1 else synthetic_id(rlp_id)
 return {'id':pid,'name':name,'rlpId':rlp_id,'mapped':len(ids)==1}


def parse_match(mid,year,canonical):
 page=get(f'{BASE}/matches/{mid}',tries=5,timeout=25)
 m=re.search(
  r'<tr>\s*<th[^>]*align=["\']right["\'][^>]*>(.*?)</th>\s*'
  r'<th[^>]*data-section=["\']match_teams["\'][^>]*>\s*Teams\s*</th>\s*'
  r'<th[^>]*align=["\']left["\'][^>]*>(.*?)</th>\s*</tr>\s*'
  r'<tbody[^>]*id=["\']match_teams["\'][^>]*>(.*?)</tbody>',page,re.I|re.S)
 if not m:return {'match':str(mid),'year':year,'error':'no match_teams block'}
 left_team,right_team=clean_text(m.group(1)),clean_text(m.group(2));body=m.group(3)
 left=[];right=[];players={}
 for row in re.findall(r'<tr[^>]*>(.*?)</tr>',body,re.I|re.S):
  cells=re.findall(r'<td[^>]*>(.*?)</td>',row,re.I|re.S)
  if not cells:continue
  lp=player_from_cell(cells[0],canonical);rp=player_from_cell(cells[-1],canonical)
  if lp:left.append(lp['id']);players[lp['id']]=lp
  if rp:right.append(rp['id']);players[rp['id']]=rp
 left=list(dict.fromkeys(left));right=list(dict.fromkeys(right))
 if len(left)<13 or len(right)<13:return {'match':str(mid),'year':year,'error':f'short lineup {left_team}={len(left)} {right_team}={len(right)}'}
 if len(left)>19 or len(right)>19:return {'match':str(mid),'year':year,'error':f'oversize lineup {left_team}={len(left)} {right_team}={len(right)}'}
 return {'match':str(mid),'year':year,'leftTeam':left_team,'rightTeam':right_team,'left':left,'right':right,'players':players}


def main():
 years=years_to_build();canonical=canonical_names();match_year,discovery=discover_matches(years)
 print('Unique match pages',len(match_year),flush=True)
 results=[]
 for i,(mid,year) in enumerate(sorted(match_year.items(),key=lambda x:(x[1],int(x[0]))),1):
  try:results.append(parse_match(mid,year,canonical))
  except Exception as e:results.append({'match':str(mid),'year':year,'error':repr(e)})
  if i%10==0 or i==len(match_year):print('Parsed',i,'of',len(match_year),flush=True)
 errors=[r for r in results if r.get('error')];good=[r for r in results if not r.get('error')]
 appearances=[];players={};team_counter=Counter();year_counter=Counter();mapped=set();synthetic=set()
 for r in good:
  mid=str(r['match']);year=int(r['year']);lt=r['leftTeam'];rt=r['rightTeam'];players.update(r['players'])
  for p in r['players'].values():(mapped if p.get('mapped') else synthetic).add(p['id'])
  for pid in r['left']:appearances.append([pid,f'RLP-INT-{mid}',year,'International',lt,rt]);team_counter[lt]+=1
  for pid in r['right']:appearances.append([pid,f'RLP-INT-{mid}',year,'International',rt,lt]);team_counter[rt]+=1
  year_counter[year]+=1
 payload={'version':4,'years':years,'players':list(players.values()),'appearances':appearances,'matches':len(good),'errors':errors,'matchesByYear':dict(sorted(year_counter.items())),'teams':sorted(team_counter),'discovery':discovery,'identity':{'canonical':len(mapped),'synthetic':len(synthetic)}}
 os.makedirs(os.path.dirname(OUT),exist_ok=True)
 with open(OUT,'w',encoding='utf-8') as f:json.dump(payload,f,separators=(',',':'),ensure_ascii=False)
 print(json.dumps({'years':years,'discovered':len(match_year),'matches':len(good),'errors':len(errors),'players':len(players),'canonicalMapped':len(mapped),'synthetic':len(synthetic),'appearances':len(appearances),'teams':len(team_counter),'matchesByYear':dict(sorted(year_counter.items())),'discovery':discovery},indent=2),flush=True)
 if errors:print('Sample parse gaps:',json.dumps(errors[:12],indent=2),flush=True)
 if not good:raise SystemExit('No exact international matches parsed')
 # Missing source line-ups remain explicit gaps. A build succeeds when the source yielded
 # a material exact layer, never by converting missing records into zero appearances.
 if len(good)<max(2,len(match_year)//10):raise SystemExit(f'Too few exact international lineups: {len(good)}/{len(match_year)}')

if __name__=='__main__':main()
