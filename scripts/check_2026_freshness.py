#!/usr/bin/env python3
import gzip,json,os,sys
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
GRAPH=os.path.join(ROOT,'data','league-links.json.gz')

def pair_key(a,b):
 a,b=str(a),str(b)
 return f'{a}|{b}' if int(a)<int(b) else f'{b}|{a}'

with gzip.open(GRAPH,'rb') as f:p=json.loads(f.read())
by_name={x.get('name'):str(x.get('id')) for x in p.get('players',[])}
moses=by_name.get('Mitchell Moses')
edwards=by_name.get('Harrison Edwards')
if not moses or not edwards:
 raise SystemExit('Missing Mitchell Moses or Harrison Edwards')
pk=pair_key(moses,edwards)
shared=sum(int(g) for pair,y,c,t,g in p.get('histories',[]) if pair==pk and int(y)==2026 and c=='NRL' and t=='Parramatta Eels')
apps={str(pid):int(n) for pid,n in p.get('appearances',[])}
career={(str(pid),int(y),c,t):int(g) for pid,y,c,t,g in p.get('career',[])}
moses_2026=career.get((moses,2026,'NRL','Parramatta Eels'),0)
edwards_2026=career.get((edwards,2026,'NRL','Parramatta Eels'),0)
print(json.dumps({'Mitchell Moses 2026 Eels appearances':moses_2026,'Harrison Edwards 2026 Eels appearances':edwards_2026,'Moses-Edwards games together':shared},indent=2))
if shared < 7:
 raise SystemExit(f'Stale 2026 NRL data: Moses and Edwards only show {shared} games together; expected at least 7')
if moses_2026 < 19:
 raise SystemExit(f'Stale 2026 NRL data: Mitchell Moses shows {moses_2026} Eels appearances; expected at least 19')
if edwards_2026 < 12:
 raise SystemExit(f'Stale 2026 NRL data: Harrison Edwards shows {edwards_2026} Eels appearances; expected at least 12')
print('2026 NRL freshness check passed')
