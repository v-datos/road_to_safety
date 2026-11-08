"""Full-file regional-grain, quality and join-feasibility audit; no model fitting."""
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
RAW=ROOT/'data/raw/data_gap_2026_11_04/geography'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def run():
 sources=json.loads((OUT/'sources.json').read_text())
 for row in sources:
  if 'sha256' in row:assert sha(ROOT/row['path'])==row['sha256'],row['name']
 q=pd.read_csv(RAW/'quebec_2022.csv',dtype=str,keep_default_na=False)
 headers={c:c.strip().strip('"').strip() for c in q.columns}
 q=q.rename(columns=headers).apply(lambda s:s.str.strip())
 t=pd.read_csv(RAW/'toronto_ksi_4326.csv',dtype=str,keep_default_na=False)
 roads=pd.read_csv(RAW/'toronto_centreline_4326.csv',dtype=str,keep_default_na=False)
 dictionary=json.loads((RAW/'toronto_ksi_dictionary.json').read_text())['result']['fields']
 event_fields=[row['id'] for row in dictionary if row.get('info',{}).get('notes','').startswith('Event-level')]
 conflicts={f:int((t.groupby('collision_id')[f].nunique(dropna=False)>1).sum()) for f in event_fields}
 assert not any(conflicts.values()),'Event-level conflicts require resolution before descriptive collapse'
 e=t.drop_duplicates('collision_id')[['collision_id']+event_fields].copy()
 date=pd.to_datetime(e.accdate,errors='coerce')
 assert date.notna().all()
 e['year']=date.dt.year
 t['year']=pd.to_datetime(t.accdate).dt.year
 annual=[]
 for year,rows in e.groupby('year'):
  people=t[t.year.eq(year)]
  annual.append({'source':'toronto_ksi','year':int(year),'person_rows':len(people),'candidate_collisions':len(rows),
   'fatal_class':int(rows.acclass.eq('Fatal Injury').sum()),'nonfatal_injury_class':int(rows.acclass.eq('Non-Fatal Injury').sum()),
   'property_damage_class':int(rows.acclass.eq('Property Damage Only').sum()),'unknown_or_blank_class':int(rows.acclass.isin(['','Unknown']).sum()),
   'blank_coordinates':int((rows.longitude.eq('')|rows.latitude.eq('')).sum()),
   'min_date':rows.accdate.min(),'max_date':rows.accdate.max()})
 pd.DataFrame(annual).to_csv(OUT/'annual_records.csv',index=False)
 missing=[]
 for source,frame in [('quebec_2022_collision',q),('toronto_ksi_person',t.drop(columns='year')),('toronto_ksi_collision',e.drop(columns='year')),('toronto_centreline',roads)]:
  for column in frame:
   missing.append({'source':source,'field':column,'n':len(frame),'blank':int(frame[column].eq('').sum()),'blank_share':float(frame[column].eq('').mean()),'distinct_including_blank':int(frame[column].nunique(dropna=False))})
 pd.DataFrame(missing).to_csv(OUT/'missingness.csv',index=False)
 value_rows=[]
 qfields=['AN','MS_ACCDN','HR_ACCDN','JR_SEMN_ACCDN','GRAVITE','REG_ADM','CD_ETAT_SURFC','CD_ASPCT_ROUTE','CD_LOCLN_ACCDN','CD_CONFG_ROUTE','CD_COND_METEO']
 tfields=['acclass','accloc','traffictl','visible','rdsfcond','road_class']
 for source,frame,fields in [('quebec_2022',q,qfields),('toronto_ksi_collision',e,tfields)]:
  for f in fields:
   for value,n in frame[f].value_counts(dropna=False).items():value_rows.append({'source':source,'field':f,'value':value,'n':int(n)})
 pd.DataFrame(value_rows).to_csv(OUT/'categorical_values.csv',index=False)
 # Coordinates describe released points; numerical precision does not prove positional accuracy.
 longitude=pd.to_numeric(e.longitude,errors='coerce');latitude=pd.to_numeric(e.latitude,errors='coerce')
 valid=longitude.between(-180,180)&latitude.between(-90,90)
 toronto_extent=longitude.between(-79.7,-79.0)&latitude.between(43.5,43.95)
 geometry=t.geometry.map(json.loads)
 pcounts=t.groupby('collision_id').agg(rows=('per_no','size'),declared=('per_inv','first'))
 pcounts['difference']=pcounts.rows-pd.to_numeric(pcounts.declared)
 # All observed people have different documented per_no within a collision except one unresolved blank ID.
 assert not t.duplicated(['collision_id','per_no']).any()
 people_ksi=t.groupby('collision_id').injury.apply(lambda x:x.isin(['Major','Fatal']).any())
 # A same-name road candidate check is not a valid collision/road join.
 road_names=roads.LINEAR_NAME_FULL.str.upper().str.strip().value_counts()
 candidates=e.stname1.str.upper().str.strip().map(road_names).fillna(0).astype(int)
 name_profiles=[]
 for population,mask in [('all',pd.Series(True,index=e.index)),('post_2021',e.year.gt(2021))]:
  values=candidates[mask]
  name_profiles.append({'population':population,'collisions':len(values),'no_exact_name_candidates':int(values.eq(0).sum()),
   'one_name_candidate':int(values.eq(1).sum()),'multiple_name_candidates':int(values.gt(1).sum()),
   'maximum_candidates':int(values.max()),'total_candidate_pairs':int(values.sum()),
   'interpretation':'Exact uppercase/trimmed street-name equality only; not a spatial match and not validated join coverage.'})
 pd.DataFrame(name_profiles).to_csv(OUT/'road_name_candidate_cardinality.csv',index=False)
 # The Centreline contains roads and many non-road line types, not a pure road inventory.
 roads.FEATURE_CODE_DESC.value_counts().rename_axis('feature_class').reset_index(name='segments').to_csv(OUT/'centreline_feature_classes.csv',index=False)
 receipt={
  'status':'passed_with_material_use_limitations','method':'Full-file pandas profiles; source-dictionary grain checks; no fitting, target imputation or incident linkage.',
  'quebec':{'rows':len(q),'columns':len(q.columns),'years':sorted(q.AN.unique().tolist()),
   'unique_collision_keys':q.NO_SEQ_COLL.nunique(),'duplicate_collision_keys':int(q.NO_SEQ_COLL.duplicated().sum()),'exact_duplicate_rows':int(q.duplicated().sum()),
   'header_normalization':{k:v for k,v in headers.items() if k!=v},'target_values':q.GRAVITE.value_counts().to_dict(),
   'mortality_target_recoverable':False,'why':'Mortel ou grave combines fatal and serious injuries; four-hour bands, workweek/weekend and region-only geography after privacy revision.',
   'available_geographic_fields':['REG_ADM'],'no_full_date_coordinates_or_road_id':True},
  'toronto':{'person_rows':len(t),'columns':len(t.columns)-1,'candidate_collisions':len(e),
   'post_2021_person_rows':int(t.year.gt(2021).sum()),'post_2021_candidate_collisions':int(e.year.gt(2021).sum()),
   'date_min':e.accdate.min(),'date_max':e.accdate.max(),'year_id_prefix_mismatches':int((e.collision_id.str[:4]!=e.year.astype(str)).sum()),
   'duplicate_row_ids':int(t._id.duplicated().sum()),'duplicate_collision_person_keys':int(t.duplicated(['collision_id','per_no']).sum()),'blank_person_id_rows':int(t.per_no.eq('').sum()),
   'exact_duplicate_rows':int(t.drop(columns='year').duplicated().sum()),'event_field_conflicts':conflicts,
   'event_outcomes':e.acclass.value_counts().to_dict(),'post_2021_event_outcomes':e.loc[e.year.gt(2021),'acclass'].value_counts().to_dict(),
   'every_event_has_released_major_or_fatal_person':bool(people_ksi.all()),
   'declared_person_count_disagreement_events':int(pcounts.difference.ne(0).sum()),'person_count_difference_distribution':{str(k):int(v) for k,v in pcounts.difference.value_counts().items()},
   'valid_coordinate_events':int(valid.sum()),'missing_coordinate_events':int((~valid).sum()),'valid_post_2021_coordinate_events':int((valid&e.year.gt(2021)).sum()),
   'invalid_nonblank_coordinate_events':int(((e.longitude.ne('')|e.latitude.ne(''))&~valid).sum()),
   'broad_toronto_extent_outside_nonmissing':int((valid&~toronto_extent).sum()),
   'longitude_range':[float(longitude.min()),float(longitude.max())],'latitude_range':[float(latitude.min()),float(latitude.max())],
   'geometry_types':geometry.map(lambda x:x.get('type','missing') if x else 'missing').value_counts().to_dict(),
   'road_alignment_field_present':False,'exact_centreline_id_field_present':False,
   'outcome_scope':'KSI-selected collisions; Non-Fatal Injury here is not all nonfatal injury collisions. Eight PDO, one unknown and one blank event class despite major/fatal person presence are unresolved source inconsistencies.'},
  'centreline':{'rows':len(roads),'columns':len(roads.columns),'unique_centreline_id':roads.CENTRELINE_ID.nunique(),
   'duplicate_centreline_id':int(roads.CENTRELINE_ID.duplicated().sum()),'blank_centreline_id':int(roads.CENTRELINE_ID.eq('').sum()),
   'source_snapshot':'2026-11-04 current network; not automatically historical collision-year geometry.',
   'crs':'EPSG:4326 selected official export; metric matching would require documented projection, e.g. official EPSG:2952 alternative.',
   'contains_nonroad_features':True,'collision_exact_key_join_available':False},
  'join_findings':name_profiles,
  'input_fingerprints':{row['path']:row['sha256'] for row in sources if 'sha256' in row},
  'producer_sha256':sha(Path(__file__))}
 assert len(q)==q.NO_SEQ_COLL.nunique() and q.GRAVITE.value_counts().sum()==len(q)
 assert sum(row['candidate_collisions'] for row in annual)==len(e)
 assert sum(row['person_rows'] for row in annual)==len(t)
 assert roads.CENTRELINE_ID.nunique()==len(roads)
 assert int(e.year.gt(2021).sum())==1393
 (OUT/'quality_assessment.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
 return receipt
if __name__=='__main__':
 result=run()
 print(json.dumps({k:result[k] for k in ['status','quebec','toronto','centreline']},ensure_ascii=False,indent=2))
