"""Acquire pinned official regional evidence without touching prior project assets."""
import datetime
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT=Path(__file__).resolve().parents[3]
RAW=ROOT/'data/raw/data_gap_2026_11_04/geography'
OUT=Path(__file__).resolve().parent
ASSETS={
 'quebec_2022.csv':'https://dq-prd-bucket1.s3.ca-central-1.amazonaws.com/saaq/Rapport_Accident_2022.csv',
 'quebec_dictionary.pdf':'https://www.donneesquebec.ca/recherche/dataset/8dd0ab9b-d45d-4526-9256-c598fbc4ff3a/resource/86cd3bcb-fe10-4ca5-992e-5bb80e5c534a/download/rapports-accident-documentation.pdf',
 'toronto_ksi_4326.csv':'https://ckan0.cf.opendata.inter.prod-toronto.ca/dataset/73a8e475-9683-42e1-ac06-b8690dcba062/resource/b95f5270-4eb0-40c2-917d-37fb494328a1/download/motor-vehicle-collisions-with-ksi-data-4326.csv',
 'toronto_ksi_dictionary.json':'https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/datastore_search?resource_id=9c9a9b60-95c1-4541-ad44-15c4a643aff9&limit=0',
 'toronto_centreline_4326.csv':'https://ckan0.cf.opendata.inter.prod-toronto.ca/dataset/1d079757-377b-4564-82df-eb5638583bfb/resource/4dec5884-a5cf-49e7-b562-f835150dc0b1/download/centreline-version-2-4326.csv',
 'toronto_centreline_dictionary.json':'https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/datastore_search?resource_id=ad296ebf-fca6-4e67-b3ce-48040a20e6cd&limit=0'
}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def run():
 RAW.mkdir(parents=True,exist_ok=True)
 path=OUT/'sources.json'
 records=json.loads(path.read_text()) if path.exists() else json.loads((RAW/'metadata_retrieval.json').read_text())
 byname={row['name']:row for row in records}
 for filename,url in ASSETS.items():
  dest=RAW/filename
  if dest.exists():
   assert filename in byname and sha(dest)==byname[filename]['sha256'],filename
   print('Verified',filename,flush=True);continue
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'RoadToSafety-source-audit/1.0'}),timeout=90) as response:
    body=response.read(100_000_001)
    assert len(body)<=100_000_000,'Resource exceeds scoped100MB'
    headers=dict(response.headers);final=response.url;status=response.status
   dest.write_bytes(body)
   record={'name':filename,'url':url,'final_url':final,'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'http_status':status,'headers':headers,'path':str(dest.relative_to(ROOT)),'bytes':len(body),'sha256':sha(dest)}
   records.append(record);byname[filename]=record
   path.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
   print('Acquired',filename,len(body),flush=True)
  except Exception as e:
   print('Unavailable',filename,type(e).__name__,str(e),flush=True)
   (OUT/'acquisition_errors.jsonl').open('a').write(json.dumps({'name':filename,'url':url,'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'error':str(e)})+'\n')
 return records
if __name__=='__main__':run()
