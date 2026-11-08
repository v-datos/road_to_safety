"""Preserve current official NCDB discovery responses without touching old inputs."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,urllib.request,urllib.error
from urllib.parse import urlsplit,urlunsplit,quote
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'data/raw/data_gap_2026_11_04/records'
OUT.mkdir(parents=True,exist_ok=True)
CATALOG='https://open.canada.ca/data/api/action/package_show?id=1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a'
URLS={
'ncdb_catalog.json':CATALOG,
'ncdb_catalog_page.html':'https://open.canada.ca/data/en/dataset/1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a',
'ncdb_online.html':'https://wwwapps2.tc.gc.ca/Saf-Sec-Sur/7/NCDB-BNDC/p.aspx?c=100-0-0&l=en',
'dashboard.html':'https://tc.canada.ca/en/road-transportation/statistics-data/2025/motor-vehicle-casualties-dashboard',
'statistics_index.html':'https://tc.canada.ca/en/road-transportation/statistics-data',
'catalog_search_ncdb.json':'https://open.canada.ca/data/api/action/package_search?q='+quote('National Collision Database')+'&rows=100',
'catalog_search_collision2022.json':'https://open.canada.ca/data/api/action/package_search?q='+quote('collision 2022')+'&rows=100',
}
def capture(name,url):
 p=OUT/name;s=p.with_suffix(p.suffix+'.provenance.json')
 if p.exists() and s.exists():
  item=json.loads(s.read_text());assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'];return item
 if p.exists():raise ValueError('Orphaned existing capture '+str(p))
 started=datetime.now(timezone.utc).isoformat()
 request=urllib.request.Request(url,headers={'User-Agent':'RoadToSafetyResearch/1.0 (public-data acquisition)'})
 try:response=urllib.request.urlopen(request,timeout=90)
 except urllib.error.HTTPError as error:response=error
 body=response.read();headers={k:v for k,v in response.headers.items() if k.lower() in ['content-type','content-length','last-modified','etag','date','cache-control','location']}
 final=urlsplit(response.url);final_url=urlunsplit((final.scheme,final.netloc,final.path,'',''))
 item={'requested_url':url,'final_url_without_query':final_url,'redirect_query_redacted':bool(final.query),'acquired_at_utc':started,'completed_at_utc':datetime.now(timezone.utc).isoformat(),'http_status':response.status,'headers':headers,'size_bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),'local_path':str(p.relative_to(ROOT))}
 p.write_bytes(body);s.write_text(json.dumps(item,indent=2)+'\n');return item
if __name__=='__main__':
 results=[]
 for name,url in URLS.items():
  try:item=capture(name,url);results.append(item);print(name,item['http_status'],item['size_bytes'],flush=True)
  except Exception as error:results.append({'requested_url':url,'local_path':str((OUT/name).relative_to(ROOT)),'status':'request_failed','error':str(error)});print(name,str(error),flush=True)
 (ROOT/'experiments/data_gap_2026_11_04/records/http_inventory.json').write_text(json.dumps(results,indent=2)+'\n')
