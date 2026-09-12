#!/usr/bin/env python3
import gzip,json,os
from collections import defaultdict
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
OPP=os.path.join(ROOT,'data','opponents.json.gz')
LOWER=os.path.join(ROOT,'data','lower-grade-exact.json')
META=os.path.join(ROOT,'data','opponents-meta.json')

def main():
 if not os.path.exists(LOWER):return
 with gzip.open(OPP,'rb') as f:p=json.loads(f.read())
 with open(LOWER,encoding='utf-8') as f:l=json.load(f)
 counts=defaultdict(int)
 for pid,y,c,o,g in p.get('rows',[]):counts[(str(pid),int(y),c,o)]+=int(g)
 for pid,mid,y,c,t,o in l.get('appearances',[]):
  if o:counts[(str(pid),int(y),c,o)]+=1
 rows=[[pid,y,c,o,g] for (pid,y,c,o),g in counts.items()]
 p={'version':26,'builtAt':p.get('builtAt'),'rows':rows}
 raw=json.dumps(p,separators=(',',':'),ensure_ascii=False).encode()
 with gzip.open(OPP,'wb',compresslevel=9) as f:f.write(raw)
 meta={'version':26,'players':len({r[0] for r in rows}),'rows':len(rows),'games':sum(r[4] for r in rows),'compressedBytes':os.path.getsize(OPP)}
 with open(META,'w',encoding='utf-8') as f:json.dump(meta,f,indent=2)
 print(json.dumps(meta,indent=2))
if __name__=='__main__':main()
