"""Offline audit of the new official national-source snapshot and native export."""
from pathlib import Path
import csv,json,hashlib,re
from datetime import datetime,timezone
import pandas as pd
import duckdb
from road_to_safety.acquire_aggregates import Tables
from road_to_safety.audit_data import COLUMNS,FRENCH
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'experiments/data_gap_2026_11_04/records';RAW=ROOT/'data/raw/data_gap_2026_11_04/records'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,rows):
 rows=list(rows);p=OUT/name
 if not rows:p.write_text('');return
 with p.open('w',newline='') as stream:
  w=csv.DictWriter(stream,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def tables(name):
 p=Tables();p.feed((RAW/name).read_text());return p.tables
assets=[]
for side in sorted(RAW.glob('*.provenance.json')):
 item=json.loads(side.read_text());p=ROOT/item['local_path'];assert sha(p)==item['sha256'],p
 assets.append({'path':item['local_path'],'source_url':item['requested_url'],'method':item.get('request_method','GET'),'http_status':item['http_status'],'bytes':p.stat().st_size,'sha256':sha(p),'metadata_path':str(side.relative_to(ROOT)),'metadata_sha256':sha(side),'content_type':item.get('headers',{}).get('Content-Type',item.get('headers',{}).get('content-type',''))})
write('asset_inventory.csv',assets)
current=json.loads((RAW/'ncdb_catalog.json').read_text())['result']
previous=json.loads((ROOT/'data/raw/source_metadata/ncdb_catalog.json').read_text())['result']
old={x['id']:x for x in previous['resources']};new={x['id']:x for x in current['resources']}
fields=['name','format','url','last_modified','metadata_modified','date_published','size','language']
changes=[]
for resource in current['resources']:
 for field in fields:
  if resource['id'] not in old or resource.get(field)!=old[resource['id']].get(field):changes.append({'resource_id':resource['id'],'field':field,'previous':json.dumps(old.get(resource['id'],{}).get(field),ensure_ascii=False),'current':json.dumps(resource.get(field),ensure_ascii=False)})
resources=[]
for x in current['resources']:
 years=[int(y) for y in re.findall(r'(?:19|20)\d{2}',x['name'])]
 resources.append({'resource_id':x['id'],'name':x['name'],'format':x['format'],'language':','.join(x.get('language',[])),'url':x['url'],'nominal_year':max(years) if years else None,'data_last_modified':x.get('last_modified'),'metadata_modified':x.get('metadata_modified'),'date_published':x.get('date_published'),'catalog_size_bytes':x.get('size'),'url_present':bool(x['url'])})
write('current_ncdb_resource_inventory.csv',resources)
(OUT/'catalog_resource_changes.json').write_text(json.dumps({'added_ids':sorted(new.keys()-old.keys()),'removed_ids':sorted(old.keys()-new.keys()),'changed_fields':changes},indent=2,ensure_ascii=False)+'\n')
# Native download is an original CSV; the earlier CSV-named response was an HTML prompt.
body=(RAW/'native_online_collision_counts_actual.csv').read_text(encoding='utf-8-sig')
assert '<html' not in body.lower()
rows=[row for row in csv.reader(body.splitlines()) if row]
assert rows[0][0]=='Year' and rows[2][0]=='Number of collisions'
labels=rows[0][1:];values=list(map(int,rows[2][1:]));assert len(labels)==len(values)==26
native=dict(zip(labels,values));assert native['Total']==sum(v for k,v in native.items() if k!='Total')
annual_native=[{'year':int(k),'fatal_plus_injury_collisions':v,'source_sha256':sha(RAW/'native_online_collision_counts_actual.csv')} for k,v in native.items() if k!='Total']
write('native_online_annual_counts.csv',annual_native)
pub=tables('publication_2024.html')
annual_pub=[]
for row in pub[0]['rows']:
 if len(row)==6 and row[0].isdigit():
  values=[int(value.replace(',','')) for value in row]
  annual_pub.append(dict(zip(['year','fatal_collisions','injury_collisions','fatalities','serious_injuries','total_injuries'],values)))
assert len(annual_pub)==20 and [r['year'] for r in annual_pub]==list(range(2005,2025))
write('publication_2024_annual_counts.csv',annual_pub)
geographic=[]
for row in pub[4]['rows'][2:]:
 if len(row)==7:
  try:values=[float(x) for x in row[1:]]
  except ValueError:continue
  geographic.append(dict(zip(['year','jurisdiction','fatalities_per_100k_population','injuries_per_100k_population','fatalities_per_billion_vkm','injuries_per_billion_vkm','fatalities_per_100k_licensed_drivers','injuries_per_100k_licensed_drivers'],[2024,row[0]]+values)))
assert len(geographic)==14
write('publication_2024_jurisdiction_rates.csv',geographic)
benchmark={int(r['C_YEAR']):int(r['collisions']) for r in csv.DictReader((ROOT/'reports/tables/validation_annual.csv').open())}
pubyears={r['year']:r for r in annual_pub}
comparisons=[]
for row in annual_native:
 y=row['year'];n=row['fatal_plus_injury_collisions'];p=pubyears.get(y)
 comparisons.append({'year':y,'online_collision_count':n,'prepared_record_collision_count':benchmark.get(y),'online_minus_prepared':n-benchmark[y] if y in benchmark else None,'publication_fatal_plus_injury_collisions':p['fatal_collisions']+p['injury_collisions'] if p else None,'online_minus_publication':n-(p['fatal_collisions']+p['injury_collisions']) if p else None})
write('source_vintage_comparison.csv',comparisons)
# Fresh latest annual originals: verify bytes and independently scan key/target/feature structure.
selected={x['resource_id']:x for x in json.loads((ROOT/'data/sources.json').read_text())['resources']}
ids={'dictionary_current.pdf':'21eb7966-38da-4814-a80e-521bce6c4c27','records_2020_en_current.csv':'2164b2a7-a580-4708-bdac-8ab0c1304bc2','records_2021_fr_current.csv':'f964d00f-6bba-44be-ae79-85f574d04a31'}
revision=[]
for name,resource in ids.items():revision.append({'current_path':str((RAW/name).relative_to(ROOT)),'resource_id':resource,'current_sha256':sha(RAW/name),'frozen_sha256':selected[resource]['sha256'],'byte_identical':sha(RAW/name)==selected[resource]['sha256']})
write('latest_original_revision_check.csv',revision)
features=json.loads((ROOT/'data/reference/modeling_contract.json').read_text())['features'];domains=json.loads((ROOT/'data/reference/modeling_contract.json').read_text())['categorical_domains']
profiles=[];missingness=[]
for year,enc,name in [(2020,'utf-8','records_2020_en_current.csv'),(2021,'cp1252','records_2021_fr_current.csv')]:
 frame=pd.read_csv(RAW/name,encoding=enc,dtype=str,keep_default_na=False)
 if year==2021:
  assert list(frame.columns)==FRENCH;frame=frame.rename(columns=dict(zip(FRENCH,COLUMNS)))
 assert list(frame.columns)==COLUMNS
 for field in ['C_YEAR','C_CASE','C_SEV']+features:
  frame[field]=frame[field].map(lambda s:str(int(s)) if re.fullmatch(r'\d+',s.strip()) else s.strip())
 con=duckdb.connect();con.register('raw',frame)
 selections=['C_YEAR','C_CASE','count(*) source_rows','min(C_SEV) C_SEV','count(distinct C_SEV) target_values']
 selections += [f'min({f}) {f},count(distinct {f}) {f}_values' for f in features]
 event=con.execute('SELECT '+','.join(selections)+' FROM raw GROUP BY C_YEAR,C_CASE').df()
 badkeys=con.execute('SELECT count(*) FROM raw WHERE try_cast(C_CASE as bigint) IS NULL OR try_cast(C_CASE as bigint)<=0 OR C_YEAR<>?',[str(year)]).fetchone()[0]
 feature_conflicts=sum(int((event[f+'_values']!=1).sum()) for f in features)
 domain_errors=sum(int((~event[f].isin(domains[f])).sum()) for f in features)
 profiles.append({'year':year,'raw_rows':len(frame),'columns':len(frame.columns),'candidate_collisions':len(event),'fatal_collisions':int(event.C_SEV.eq('1').sum()),'injury_collisions':int(event.C_SEV.eq('2').sum()),'target_conflicts':int(event.target_values.ne(1).sum()),'invalid_or_unexpected_year_key_rows':badkeys,'feature_conflicting_collision_values':feature_conflicts,'feature_out_of_domain_collision_values':domain_errors,'has_province_field':False,'has_coordinates':False,'has_full_date':False,'source_sha256':sha(RAW/name)})
 for f in features:
  for value,count in event[f].value_counts(dropna=False).items():
   cls='unknown' if set(str(value))=={'U'} else 'other' if set(str(value))=={'Q'} else 'unavailable' if set(str(value))=={'X'} else 'stated'
   missingness.append({'year':year,'field':f,'value':value,'value_class':cls,'collisions':int(count),'denominator':len(event),'share':count/len(event)})
 con.close()
write('latest_original_collision_profile.csv',profiles);write('latest_original_feature_values.csv',missingness)
searches=[]
for name in ['catalog_search_exact.json','catalog_search_tc_collision.json','catalog_search_ncdb.json','catalog_search_collision2022.json']:
 v=json.loads((RAW/name).read_text())['result'];searches.append({'capture':name,'reported_matches':v['count'],'captured_matches':len(v['results']),'complete_result_page':v['count']<=len(v['results'])})
write('catalog_search_coverage.csv',searches)
checks={'original_asset_hashes_verified':len(assets),'catalog_resource_count':len(resources),'catalog_metadata_modified':current['metadata_modified'],'catalog_added_resources':len(new.keys()-old.keys()),'catalog_removed_resources':len(old.keys()-new.keys()),'catalog_changed_resource_fields':len(changes),'post2021_named_resources':sum((r['nominal_year'] or 0)>2021 for r in resources),'latest_named_record_year':max(r['nominal_year'] or 0 for r in resources),'latest_originals_identical_to_frozen':all(r['byte_identical'] for r in revision),'native_export_year_min':min(r['year'] for r in annual_native),'native_export_year_max':max(r['year'] for r in annual_native),'native_export_total':native['Total'],'native_export_total_reconciles':True,'native_online_vs_prepared_mismatch_years':sum(r['online_minus_prepared'] not in [None,0] for r in comparisons),'native_online_vs_publication_mismatch_years':sum(r['online_minus_publication'] not in [None,0] for r in comparisons),'publication_year_min':2005,'publication_year_max':2024,'jurisdiction_rows_including_canada':len(geographic),'new_post2021_national_microdata_acquired':False,'assessment':'No post-2021 national collision record release located in audited official catalog and Transport Canada routes. Native Online count CSV successfully acquired but cannot extend record-level validation.'}
(OUT/'assessment.json').write_text(json.dumps(checks,indent=2)+'\n')
print(json.dumps(checks,indent=2));print(profiles)
