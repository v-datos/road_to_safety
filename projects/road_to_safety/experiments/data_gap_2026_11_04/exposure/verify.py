"""Verify acquired exposure snapshot and exact count-to-road key pilot."""
from pathlib import Path
import hashlib,json,re
import pandas as pd
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent;RAW=ROOT/'data/raw/data_gap_2026_11_04/exposure'
checks=[]
def require(name,condition):
 if not condition: raise ValueError(name)
 checks.append(name)
acq=json.loads((OUT/'acquisition.json').read_text())
for x in acq:
 require('original SHA256: '+x['name'],hashlib.sha256((ROOT/x['path']).read_bytes()).hexdigest()==x['sha256'])
mtq=json.loads((OUT/'mtq_profile.json').read_text());annual=pd.read_csv(OUT/'mtq_annual_aadt_profile.csv')
require('MTQ complete WFS response and unique section IDs',mtq['features']==mtq['numberMatched']==mtq['traffic_section_id_unique'])
require('MTQ all geometry and WGS84 coordinate domains',mtq['missing_geometry']==0 and mtq['all_geometry_pairs_valid_lonlat'])
require('MTQ year/value accounting',((annual.known_djma+annual.blank_djma+annual.nonnumeric_djma)==annual.features).all())
require('MTQ annual year slots complete',set(annual.year)==set(range(2016,2026)))
tr=json.loads((OUT/'toronto_profile.json').read_text());byyear=pd.read_csv(OUT/'toronto_annual_profile.csv')
require('Toronto count ID uniqueness',tr['rows']==tr['count_id_distinct'] and tr['count_id_duplicate_extra']==0)
require('Toronto dates/coordinate shape',tr['invalid_start']==tr['invalid_end']==tr['end_before_start']==0 and tr['valid_lonlat']==tr['rows'])
require('Toronto annual partition conservation',int(byyear.count_studies.sum())==tr['rows'])
require('Toronto newer year partition conservation',int(byyear.loc[byyear.start_year>2021,'count_studies'].sum())==tr['post_2021_count_studies'])
j=json.loads((OUT/'toronto_count_to_tcl_join.json').read_text())
require('Current-TCL exact join no expansion',j['right_keys_unique'] and j['output_rows']==j['left_rows'] and j['row_expansion']==0 and j['left_matched_rows']+j['left_unmatched_rows']==j['left_rows'])
require('PDF dictionary actual PDF', (RAW/'mtq_dictionary.pdf').read_bytes().startswith(b'%PDF'))
require('Excel dictionary actual XLSX',(RAW/'toronto_svc_dictionary.xlsx').read_bytes().startswith(b'PK'))
# Extract an explicitly older-vintage aggregate context table, preserving units and preliminary marker.
rows=[]
for line in (OUT/'tc_s6_2024.txt').read_text().splitlines():
 match=re.match(r'^(20\d{2})(P)?\s+([0-9,.\s]+)$',line.strip())
 if match:
  vals=re.split(r'\s+',match[3].strip())
  if len(vals)==9:
   rows.append(dict(zip(['year','preliminary','casualty_collisions','fatalities','injuries','motor_vehicle_registrations_thousands','vehicle_km_millions','fatality_per_10000_mvr','injury_per_10000_mvr','fatality_per_billion_vkm','injury_per_billion_vkm'],[int(match[1]),bool(match[2]),*[float(v.replace(',','')) for v in vals]])))
require('TC S6 context table ten annual rows only',len(rows)==10 and [r['year'] for r in rows]==list(range(2014,2024)))
pd.DataFrame(rows).to_csv(OUT/'tc_s6_2024_values.csv',index=False)
inputs=[ROOT/x['path'] for x in acq]+[ROOT/'data/raw/data_gap_2026_11_04/geography/toronto_centreline_4326.csv']
result={'status':'passed','checks_passed':checks,'failures':[],'scope':'Exposure source integrity, full-file profile conservation and traffic-count-to-current-road exact ID join; no collision-to-exposure join or occurrence model validated.','input_fingerprints':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},'code_fingerprints':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [OUT/'acquire.py',OUT/'profile.py',Path(__file__)]}}
(OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
print('passed',len(checks),'checks')
