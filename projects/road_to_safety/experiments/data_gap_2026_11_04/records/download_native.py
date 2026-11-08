"""Follow the verified public native-download prompt; preserve actual response bytes."""
from pathlib import Path
import sys,json,hashlib,urllib.request,urllib.parse,urllib.error
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parent))
from acquire_snapshot import ROOT,OUT
from road_to_safety.acquire_aggregates import Form
p=OUT/'native_online_collision_counts_actual.csv';side=p.with_suffix('.csv.provenance.json')
if p.exists():raise FileExistsError(str(p))
f=Form();f.feed((OUT/'native_online_collision_counts.csv').read_text())
url='https://wwwapps2.tc.gc.ca/Saf-Sec-Sur/7/NCDB-BNDC/p.aspx?l=en'
request=urllib.request.Request(url,data=urllib.parse.urlencode(f.fields+[('WD_C_1_13','Download')]).encode(),headers={'User-Agent':'RoadToSafetyResearch/1.0'})
start=datetime.now(timezone.utc).isoformat()
try:response=urllib.request.urlopen(request,timeout=90)
except urllib.error.HTTPError as e:response=e
body=response.read();p.write_bytes(body)
record={'requested_url':url,'request_method':'POST','action':'WD_C_1_13=Download','derived_request_from':str((OUT/'native_online_collision_counts.csv').relative_to(ROOT)),'query_scope':'Number of collisions, year1999–2023 and all-years total; no other filters','acquired_at_utc':start,'http_status':response.status,'headers':{k:v for k,v in response.headers.items() if k.lower() in ['content-type','content-length','content-disposition','date']},'size_bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),'local_path':str(p.relative_to(ROOT)),'looks_like_html':b'<html' in body.lower()}
side.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2));print(body[:600].decode('utf-8-sig',errors='replace'))
