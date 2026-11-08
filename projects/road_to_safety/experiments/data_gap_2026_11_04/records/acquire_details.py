"""Acquire current dictionary/latest released originals and bounded Online query evidence."""
from pathlib import Path
import sys,json,urllib.request,urllib.error,urllib.parse,hashlib
from datetime import datetime,timezone
from http.cookiejar import CookieJar
sys.path.insert(0,str(Path(__file__).resolve().parent))
from acquire_snapshot import ROOT,OUT,capture
from road_to_safety.acquire_aggregates import Form
catalog=json.loads((OUT/'ncdb_catalog.json').read_text())['result']
urls={
'ncdb_online_help.html':'https://wwwapps2.tc.gc.ca/Saf-Sec-Sur/7/NCDB-BNDC/p.aspx?l=en&c=100-4-0-0-23-101',
'ncdb_online_faq.html':'https://wwwapps2.tc.gc.ca/Saf-Sec-Sur/7/NCDB-BNDC/p.aspx?l=en&c=100-5-0',
'ncdb_online_year_details.html':'https://wwwapps2.tc.gc.ca/Saf-Sec-Sur/7/NCDB-BNDC/p.aspx?l=en&c=100-3-0-0-0',
'publication_2024.html':'https://tc.canada.ca/en/road-transportation/statistics-data/canadian-motor-vehicle-traffic-collision-statistics/2024/canadian-motor-vehicle-traffic-collision-statistics-2024',
'dashboard_guide.html':'https://tc.canada.ca/en/road-transportation/statistics-data/motor-vehicle-casualties-dashboard-user-guide',
}
for r in catalog['resources']:
 if r['id']=='21eb7966-38da-4814-a80e-521bce6c4c27':urls['dictionary_current.pdf']=r['url']
 if r['id']=='f964d00f-6bba-44be-ae79-85f574d04a31':urls['records_2021_fr_current.csv']=r['url']
 if r['id']=='2164b2a7-a580-4708-bdac-8ab0c1304bc2':urls['records_2020_en_current.csv']=r['url']
results=[]
for name,url in urls.items():
 try:r=capture(name,url);results.append(r);print(name,r['http_status'],r['size_bytes'],flush=True)
 except Exception as e:results.append({'requested_url':url,'status':'request_failed','error':str(e)});print(name,e,flush=True)
( ROOT/'experiments/data_gap_2026_11_04/records/detail_inventory.json').write_text(json.dumps(results,indent=2)+'\n')
# Stateful Online form: every response is a query-interface capture, never assumed numeric data.
opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
base='https://wwwapps2.tc.gc.ca/Saf-Sec-Sur/7/NCDB-BNDC/p.aspx?l=en'
query=[]
def query_capture(name,url,fields=None):
 p=OUT/name; side=p.with_suffix(p.suffix+'.provenance.json')
 if p.exists():
  record=json.loads(side.read_text());assert hashlib.sha256(p.read_bytes()).hexdigest()==record['sha256'];query.append(record);return p.read_text()
 request=urllib.request.Request(url,data=None if fields is None else urllib.parse.urlencode(fields).encode(),headers={'User-Agent':'RoadToSafetyResearch/1.0'})
 started=datetime.now(timezone.utc).isoformat()
 try:response=opener.open(request,timeout=90)
 except urllib.error.HTTPError as e:response=e
 body=response.read();p.write_bytes(body)
 final=urllib.parse.urlsplit(response.url)
 record={'requested_url':url,'request_method':'GET' if fields is None else 'POST','action_fields':None if fields is None else [list(f) for f in fields if not f[0].startswith('__')], 'acquired_at_utc':started,'http_status':response.status,'headers':{k:v for k,v in response.headers.items() if k.lower() in ['content-type','content-length','last-modified','etag','date']},'final_url_without_query':urllib.parse.urlunsplit((final.scheme,final.netloc,final.path,'','')),'size_bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),'local_path':str(p.relative_to(ROOT))}
 text=body.decode('utf-8-sig');record['source_application_error']='<title>Error -' in text or 'Server Error in' in text
 side.write_text(json.dumps(record,indent=2)+'\n');query.append(record);print(name,record['http_status'],'applicationerror',record['source_application_error'],flush=True);return text
try:
 html=query_capture('ncdb_query_start.html',base+'&c=100-1-0')
 for name,button,value in [('ncdb_query_items.html','WD_C_100_2_0','Next step'),('ncdb_query_years.html','WD_C_100_2_1_1','Year'),('ncdb_query_layout.html','WD_C_3_21','Next step'),('ncdb_query_result_attempt.html','WD_C_3_8','Next step')]:
  form=Form();form.feed(html);html=query_capture(name,base,form.fields+[(button,value)])
  if query[-1]['source_application_error']:break
except Exception as e:query.append({'status':'request_failed','error':str(e)})
(ROOT/'experiments/data_gap_2026_11_04/records/online_query_inventory.json').write_text(json.dumps(query,indent=2)+'\n')
