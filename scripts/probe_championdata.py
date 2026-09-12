#!/usr/bin/env python3
import difflib,gzip,json,os,re,unicodedata
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
GRAPH=os.path.join(ROOT,'data','league-links.json.gz')
TARGETS=['Apa Twidle','Braden Uele','Clint Gutherson','Cooper Toy','Dayne Jennings','Hayden Watson','Jacob Webster','Jai Bowden','Jared Haywood','Jethro Rinakama','Jett Cleary','Jezaiah Funa-Iuta','Joe Roddy','Jojo Fifita','Josese Lanyon','Josh Coric','Josh Patston','Kalani Leuluai-Going','Lachlan Crouch','Makaia Tafua','Malachi Smith','Mat Feagai','Matt Timoko','Matthew Lodge','Michael Gabrael','Rex Bassingthwaite','Riley Pollard','Ryda Talagi','Sam Hughes','Solomone Saukuru','Toby Winter','Tom Hazelton','Tuki Simpkins','Vaka Aho','Vena Patuki-Case']

def norm(s):
 s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
 return re.sub(r'[^a-z0-9]+','',s)
with gzip.open(GRAPH,'rb') as f:p=json.loads(f.read())
base=[x.get('name','') for x in p.get('players',[]) if int(x.get('id') or 0)<9_000_000_000_000]
nb={norm(x):x for x in base}
keys=list(nb)
for t in TARGETS:
 k=norm(t);close=difflib.get_close_matches(k,keys,n=5,cutoff=.55)
 scored=sorted(((difflib.SequenceMatcher(None,k,x).ratio(),nb[x]) for x in close),reverse=True)
 print(t,'=>',scored)
