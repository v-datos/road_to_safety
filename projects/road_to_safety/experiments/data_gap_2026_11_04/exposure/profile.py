"""Full-snapshot exposure data audit, separate from frozen NCDB experiments."""
from pathlib import Path
import json,re,hashlib,collections
import pandas as pd
ROOT=Path(__file__).resolve().parents[3];RAW=ROOT/'data/raw/data_gap_2026_11_04/exposure';OUT=Path(__file__).resolve().parent
f=json.loads((RAW/'mtq_traffic.geojson').read_text());features=f['features'];df=pd.DataFrame([x['properties'] for x in features])
missing=lambda s:int((s.isna()|s.astype(str).str.strip().eq('')).sum())
fields=[{'field':c,'dtype':str(df[c].dtype),'missing':missing(df[c]),'missing_fraction':missing(df[c])/len(df),'distinct_including_blank':int(df[c].nunique(dropna=False))} for c in df]
pd.DataFrame(fields).to_csv(OUT/'mtq_field_profile.csv',index=False)
rows=[]
for i in range(1,11):
 yr='djma_annee_'+str(i);val='val_djma_annee_'+str(i)
 for year,sub in df.groupby(yr,dropna=False):
  raw=sub[val].astype(str).str.strip();num=pd.to_numeric(raw,errors='coerce')
  invalid=raw[num.isna()&raw.ne('')]
  rows.append({'year':year,'features':len(sub),'known_djma':int(num.notna().sum()),'blank_djma':int(raw.eq('').sum()),'nonnumeric_djma':int(len(invalid)),'zero_djma':int(num.eq(0).sum()),'negative_djma':int(num.lt(0).sum()),'minimum_djma':float(num.min()) if num.notna().any() else None,'maximum_djma':float(num.max()) if num.notna().any() else None,'invalid_examples':' | '.join(invalid.unique()[:8])})
pd.DataFrame(rows).to_csv(OUT/'mtq_annual_aadt_profile.csv',index=False)
coords=[]
def walk(v):
 if isinstance(v,list) and len(v)>=2 and isinstance(v[0],(int,float)):
  coords.append(v[:2])
 elif isinstance(v,list):
  for x in v:walk(x)
for x in features:
 if x.get('geometry'):walk(x['geometry']['coordinates'])
summary={'input_sha256':hashlib.sha256((RAW/'mtq_traffic.geojson').read_bytes()).hexdigest(),'features':len(df),'fields':len(df.columns),'numberMatched':f.get('numberMatched'),'feature_id_unique':len(set(str(x.get('id')) for x in features)),'traffic_section_id_unique':int(df.ide_sectn_trafc.nunique()),'traffic_section_duplicate_extra':int(df.duplicated('ide_sectn_trafc').sum()),'traffic_number_unique':int(df.num_sectn_trafc.nunique()),'traffic_number_duplicate_extra':int(df.duplicated('num_sectn_trafc').sum()),'geometry_types':dict(collections.Counter(x.get('geometry',{}).get('type') for x in features)),'missing_geometry':sum(x.get('geometry') is None for x in features),'coordinate_pairs':len(coords),'bbox_actual':[min(x[0] for x in coords),min(x[1] for x in coords),max(x[0] for x in coords),max(x[1] for x in coords)],'bbox_metadata':f.get('bbox'),'same_rtss_start_end':int(df.rtss_debut.eq(df.rtss_fin).sum()),'missing_rtss_start':missing(df.rtss_debut),'missing_rtss_end':missing(df.rtss_fin),'section_start_min':str(df.dat_debut_sectn_trafc.min()),'section_start_max':str(df.dat_debut_sectn_trafc.max()),'all_geometry_pairs_valid_lonlat':all(-180<=x[0]<=180 and -90<=x[1]<=90 for x in coords),'profiled_all_features':True}
(OUT/'mtq_profile.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2));print(pd.DataFrame(rows).to_string(index=False))
# Toronto short-term count summary: each count is a location-time study, not annual traffic exposure.
p=RAW/'toronto_svc_summary.csv';td=pd.read_csv(p,dtype=str)
start=pd.to_datetime(td.count_date_start,errors='coerce');end=pd.to_datetime(td.count_date_end,errors='coerce')
duration=pd.to_numeric(td.count_duration,errors='coerce');volume=pd.to_numeric(td.avg_daily_vol,errors='coerce')
lat=pd.to_numeric(td.latitude,errors='coerce');lon=pd.to_numeric(td.longitude,errors='coerce')
tp={'input_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rows':len(td),'fields':len(td.columns),'count_id_distinct':int(td.count_id.nunique()),'count_id_duplicate_extra':int(td.duplicated('count_id').sum()),'id_duplicate_extra':int(td.duplicated('_id').sum()),'unique_centreline_ids':int(td.centreline_id.nunique()),'missing_centreline_id':missing(td.centreline_id),'missing_lat':int(lat.isna().sum()),'missing_lon':int(lon.isna().sum()),'valid_lonlat':int((lat.between(-90,90)&lon.between(-180,180)).sum()),'date_start_min':str(start.min().date()),'date_start_max':str(start.max().date()),'date_end_min':str(end.min().date()),'date_end_max':str(end.max().date()),'invalid_start':int(start.isna().sum()),'invalid_end':int(end.isna().sum()),'end_before_start':int((end<start).sum()),'missing_duration':int(duration.isna().sum()),'nonpositive_duration':int(duration.le(0).sum()),'duration_min_hours':float(duration.min()),'duration_max_hours':float(duration.max()),'duration_outside_24_168_hours':int((duration.lt(24)|duration.gt(168)).sum()),'missing_avg_daily_vol':int(volume.isna().sum()),'zero_avg_daily_vol':int(volume.eq(0).sum()),'negative_avg_daily_vol':int(volume.lt(0).sum()),'min_avg_daily_vol':float(volume.min()),'max_avg_daily_vol':float(volume.max()),'post_2021_count_studies':int(start.dt.year.gt(2021).sum()),'geometry_context':'point coordinate per count; dictionary centreline_id references current Toronto Centreline; no directional completeness indicator in this summary'}
tp.update(over_14_days_studies=int(duration.gt(336).sum()),maximum_duration_count_id=str(td.loc[duration.idxmax(),'count_id']),missing_avg_speed=missing(td.avg_speed),missing_heavy_pct=missing(td.avg_heavy_pct))
(OUT/'toronto_profile.json').write_text(json.dumps(tp,indent=2)+'\n')
td[duration.lt(24)|duration.gt(168)][['count_id','count_type','count_date_start','count_date_end','count_duration','centreline_id','avg_daily_vol']].to_csv(OUT/'toronto_nonstandard_duration_studies.csv',index=False)
pd.DataFrame([{'field':c,'missing':missing(td[c]),'missing_fraction':missing(td[c])/len(td),'distinct_including_blank':int(td[c].nunique(dropna=False))} for c in td]).to_csv(OUT/'toronto_field_profile.csv',index=False)
yr=td.assign(start_year=start.dt.year)
yr.groupby('start_year').agg(count_studies=('count_id','size'),unique_centreline_ids=('centreline_id','nunique')).reset_index().to_csv(OUT/'toronto_annual_profile.csv',index=False)
# An actual exact-key pilot is legitimate for traffic counts -> road geometry, not collisions -> counts.
tcl_path=ROOT/'data/raw/data_gap_2026_11_04/geography/toronto_centreline_4326.csv'
if tcl_path.exists():
 tcl=pd.read_csv(tcl_path,dtype=str,keep_default_na=False)
 expected=td.centreline_id.str.strip(); keys=tcl.CENTRELINE_ID.str.strip()
 unique=not keys.duplicated().any()
 matches=expected.isin(set(keys))
 j=td.merge(tcl[['CENTRELINE_ID','FEATURE_CODE_DESC']],left_on='centreline_id',right_on='CENTRELINE_ID',how='left',validate='many_to_one')
 jp={'left_input_sha256':tp['input_sha256'],'right_input_sha256':hashlib.sha256(tcl_path.read_bytes()).hexdigest(),'join':'toronto traffic count centreline_id = current TCL CENTRELINE_ID','left_rows':len(td),'right_rows':len(tcl),'right_keys_unique':unique,'left_matched_rows':int(matches.sum()),'left_unmatched_rows':int((~matches).sum()),'left_matched_unique_ids':int(td.loc[matches,'centreline_id'].nunique()),'left_unmatched_unique_ids':int(td.loc[~matches,'centreline_id'].nunique()),'output_rows':len(j),'row_expansion':len(j)-len(td),'matched_feature_types':j.loc[matches,'FEATURE_CODE_DESC'].value_counts().to_dict(),'caveat':'Exact current-road identifier join only; historical ID validity, geometry/version, road type and the collision spatial/time link are not validated.'}
 (OUT/'toronto_count_to_tcl_join.json').write_text(json.dumps(jp,indent=2)+'\n')
 counts=td.assign(matched_current_tcl=matches,start_year=start.dt.year).groupby('start_year').matched_current_tcl.agg(['size','sum']).reset_index().rename(columns={'size':'count_studies','sum':'matched_current_tcl'})
 counts.to_csv(OUT/'toronto_count_to_tcl_join_by_year.csv',index=False)
print(json.dumps(tp,indent=2))
if tcl_path.exists():print(json.dumps(jp,indent=2))
