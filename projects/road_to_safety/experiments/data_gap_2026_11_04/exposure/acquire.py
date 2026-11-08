"""Acquire a separate official exposure reference snapshot; never changes prior inputs."""
from pathlib import Path
from datetime import datetime,timezone
import urllib.request,json,hashlib
ROOT=Path(__file__).resolve().parents[3]
RAW=ROOT/'data/raw/data_gap_2026_11_04/exposure';RAW.mkdir(parents=True,exist_ok=True)
SOURCES={
 'toronto_svc_summary.csv':'https://ckan0.cf.opendata.inter.prod-toronto.ca/dataset/7a0ac637-43da-4e42-a79c-6d8279e21d85/resource/af1ccce4-d978-4a6d-9dc3-3fb33b1cc349/download/svc_summary_data.csv',
 'toronto_svc_dictionary.xlsx':'https://ckan0.cf.opendata.inter.prod-toronto.ca/dataset/7a0ac637-43da-4e42-a79c-6d8279e21d85/resource/bed17b1a-a425-4130-a49c-67174dcf0e50/download/svc_data_dictionary_dec2025_update.xlsx',
 'toronto_volume_metadata.json':'https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/package_show?id=traffic-volumes-midblock-vehicle-speed-volume-and-classification-counts',
 'mtq_metadata.json':'https://www.donneesquebec.ca/recherche/api/3/action/package_show?id=c77c495a-2a4c-447e-9184-25722289007f',
 'mtq_traffic.geojson':'https://ws.mapserver.transports.gouv.qc.ca/swtq?service=wfs&version=2.0.0&request=getfeature&typename=ms:circulation_routier&outfile=DebitCirculation&srsname=EPSG:4326&outputformat=geojson',
 'mtq_dictionary.pdf':'https://www.donneesquebec.ca/recherche/dataset/c77c495a-2a4c-447e-9184-25722289007f/resource/782087a6-3f53-4591-b9e2-07af432a1379/download/debit_circulation_dictionnaire.pdf',
 'tc_s6_2024.pdf':'https://tdih-cdit.tc.canada.ca/sites/default/files/addendum-tables/2024/S6-en.pdf',
 'statcan_cvs_discontinued.html':'https://www150.statcan.gc.ca/n1/daily-quotidien/100707/dq100707b-eng.htm'
}
old_path=ROOT/'experiments/data_gap_2026_11_04/exposure/acquisition.json'
old={x['name']:x for x in json.loads(old_path.read_text())} if old_path.exists() else {}
rows=[]
for name,url in SOURCES.items():
 path=RAW/name
 if path.exists() and name in old and 'sha256' in old[name]:
  assert hashlib.sha256(path.read_bytes()).hexdigest()==old[name]['sha256'],name
  rows.append(old[name]);print(name,'verified existing',flush=True);continue
 record={'name':name,'url':url,'retrieved_utc':datetime.now(timezone.utc).isoformat(),'path':str(path.relative_to(ROOT))}
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Road-to-Safety-Research/1.0 (public-data feasibility)'})
  with urllib.request.urlopen(req,timeout=90) as response:
   data=response.read();record.update(status=response.status,final_url=response.url,headers=dict(response.headers))
  path.write_bytes(data);record.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
  print(name,record['status'],len(data),flush=True)
 except Exception as error:
  record.update(error=str(error));print(name,'ERROR',str(error),flush=True)
 rows.append(record)
(ROOT/'experiments/data_gap_2026_11_04/exposure/acquisition.json').write_text(json.dumps(rows,indent=2)+'\n')
