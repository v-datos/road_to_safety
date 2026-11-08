"""One corrected native count-query attempt with full successful form fields."""
from pathlib import Path
import sys,json,hashlib,urllib.request,urllib.error,urllib.parse,re
from datetime import datetime,timezone
from http.cookiejar import CookieJar
from html.parser import HTMLParser
sys.path.insert(0,str(Path(__file__).resolve().parent))
from acquire_snapshot import ROOT,OUT,capture
class Form(HTMLParser):
 def __init__(self):super().__init__();self.fields=[];self.select=None
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if tag=='input' and 'name' in d and 'disabled' not in d:
   kind=d.get('type','text')
   if kind in ['hidden','text','number'] or (kind in ['checkbox','radio'] and 'checked' in d):self.fields.append((d['name'],d.get('value','')))
  if tag=='select':self.select=d.get('name')
  if tag=='option' and self.select and 'selected' in d:self.fields.append((self.select,d.get('value','')))
 def handle_endtag(self,tag):
  if tag=='select':self.select=None
opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
base='https://wwwapps2.tc.gc.ca/Saf-Sec-Sur/7/NCDB-BNDC/p.aspx?l=en';records=[]
def request(name,url,fields=None):
 path=OUT/name
 if path.exists():raise FileExistsError('Corrected workflow preserves capture '+str(path))
 req=urllib.request.Request(url,data=None if fields is None else urllib.parse.urlencode(fields).encode(),headers={'User-Agent':'RoadToSafetyResearch/1.0'})
 acquired=datetime.now(timezone.utc).isoformat()
 try:resp=opener.open(req,timeout=90)
 except urllib.error.HTTPError as e:resp=e
 body=resp.read();path.write_bytes(body);text=body.decode('utf-8-sig')
 record={'requested_url':url,'request_method':'GET' if fields is None else 'POST','request_scope':'Number of collisions only; all selected years, no other filters','acquired_at_utc':acquired,'http_status':resp.status,'headers':{k:v for k,v in resp.headers.items() if k.lower() in ['content-type','content-length','last-modified','etag','date']},'size_bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),'local_path':str(path.relative_to(ROOT)),'html_title':re.search(r'<title>(.*?)</title>',text,re.S).group(1),'source_application_error':'<title>Error -' in text or 'Server Error in' in text,'client_validation_error':'The number of rows must be' in text}
 path.with_suffix('.html.provenance.json').write_text(json.dumps(record,indent=2)+'\n');records.append(record);print(name,record['html_title'],flush=True);return text
try:
 text=request('corrected_query_start.html',base+'&c=100-1-0')
 for name,key,value in [('corrected_query_measures.html','WD_C_100_2_0','Next step'),('corrected_query_years.html','WD_C_100_2_1_1','Year'),('corrected_query_layout.html','WD_C_3_21','Next step'),('corrected_query_result.html','WD_C_3_8','Next step')]:
  f=Form();f.feed(text);fields=f.fields
  # Keep only collision measure when leaving measure-selection page.
  if name=='corrected_query_years.html':fields=[(k,v) for k,v in fields if k!='WD_Value' or v=='0']
  text=request(name,base,fields+[(key,value)])
  if records[-1]['source_application_error']:break
except Exception as e:records.append({'status':'request_failed','error':str(e)});print(e,flush=True)
(ROOT/'experiments/data_gap_2026_11_04/records/corrected_query_inventory.json').write_text(json.dumps(records,indent=2)+'\n')
# Restrict follow-up catalog queries to exact phrase / responsible publisher, avoiding broad OR results.
for name,q in [('catalog_search_exact.json','"National Collision Database"'),('catalog_search_tc_collision.json','collision')]:
 url='https://open.canada.ca/data/api/action/package_search?q='+urllib.parse.quote(q)+'&rows=100'
 if 'tc_collision' in name:url+='&fq=organization:tc'
 item=capture(name,url);print(name,item['http_status'],item['size_bytes'],flush=True)
