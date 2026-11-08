"""Reproduce public aggregate captures and HTML-table extracts (stdlib only).
Run from the project: python -m road_to_safety.acquire_aggregates
Existing original captures are never overwritten; use --offline to verify/reparse.
"""
from pathlib import Path
from html.parser import HTMLParser
from urllib.request import build_opener, HTTPCookieProcessor
from urllib.parse import urlencode
from http.cookiejar import CookieJar
import csv
import datetime
import hashlib
import json
import argparse
import re

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'data/raw/aggregates'
REGISTRY = ROOT / 'data/reference/aggregate_sources.json'

class Form(HTMLParser):
    def __init__(self):
        super().__init__(); self.fields = []; self.options = []; self.select = None
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == 'input' and 'name' in d and 'disabled' not in d:
            if d.get('type') == 'hidden' or (d.get('type') in ('checkbox', 'radio') and 'checked' in d):
                self.fields.append((d['name'], d.get('value', '')))
        if tag == 'select': self.select = d.get('name')
        if tag == 'option' and self.select and 'selected' in d:
            self.fields.append((self.select, d.get('value', '')))
    def handle_endtag(self, tag):
        if tag == 'select': self.select = None

class Tables(HTMLParser):
    def __init__(self):
        super().__init__(); self.tables=[]; self.table=None; self.row=None; self.cell=None; self.caption=None; self.skip=False
    def handle_starttag(self, tag, attrs):
        if tag == 'table': self.table={'caption':'','rows':[]}
        if self.table is not None:
            if tag == 'caption': self.caption=[]
            if tag == 'tr': self.row=[]
            if tag in ('td','th'): self.cell=[]
            if tag == 'sup': self.skip=True
    def handle_data(self, data):
        if self.caption is not None:self.caption.append(data)
        if self.cell is not None and not self.skip:self.cell.append(data)
    def handle_endtag(self, tag):
        if tag == 'sup':self.skip=False
        if tag == 'caption' and self.caption is not None:
            self.table['caption']=' '.join(''.join(self.caption).split());self.caption=None
        if tag in ('td','th') and self.cell is not None:
            self.row.append(' '.join(''.join(self.cell).split()));self.cell=None
        if tag == 'tr' and self.row is not None:
            self.table['rows'].append(self.row);self.row=None
        if tag == 'table' and self.table is not None:
            self.tables.append(self.table);self.table=None

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    if REGISTRY.exists():raise FileExistsError(f'{REGISTRY} already exists; use --offline to preserve this acquisition')
    RAW.mkdir(parents=True,exist_ok=True)
    records=[];opener=build_opener(HTTPCookieProcessor(CookieJar()))
    def capture(name,url,fields=None):
        path=RAW/(name+'.html')
        if path.exists():raise FileExistsError(f'{path} already exists; use --offline to preserve the acquisition')
        with opener.open(url, None if fields is None else urlencode(fields).encode(),timeout=90) as response:
            body=response.read(); headers=dict(response.headers); final=response.url
        path.write_bytes(body)
        records.append(dict(id=name,source_url=url,final_url=final,acquired_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),path=str(path.relative_to(ROOT)),bytes=len(body),sha256=digest(path),http_headers=headers,acquisition_type='original_http_response',request_method='GET' if fields is None else 'POST',request_fields=fields))
        REGISTRY.write_text(json.dumps({'sources':records},indent=2))
        return body.decode('utf-8-sig')
    base='https://tc.canada.ca/en/road-transportation/statistics-data'
    pages={'tc_statistics_index':base,'tc_casualties_dashboard':base+'/2025/motor-vehicle-casualties-dashboard','tc_dashboard_guide':base+'/motor-vehicle-casualties-dashboard-user-guide','tc_statistics_2024':base+'/canadian-motor-vehicle-traffic-collision-statistics/2024/canadian-motor-vehicle-traffic-collision-statistics-2024'}
    ncdb='https://wwwapps2.tc.gc.ca/Saf-Sec-Sur/7/NCDB-BNDC/p.aspx?l=en'
    for name,url in pages.items(): capture(name,url)
    for name,code in [('ncdb_online_landing','100-0-0'),('ncdb_online_faq','100-5-0'),('ncdb_online_help','100-4-0-0-23-101'),('ncdb_year_details','100-3-0-0-0')]:capture(name,ncdb+'&c='+code)
    html=capture('ncdb_online_query',ncdb+'&c=100-1-0')
    for name,button,value in [('ncdb_online_items','WD_C_100_2_0','Next step'),('ncdb_online_years','WD_C_100_2_1_1','Year'),('ncdb_online_layout','WD_C_3_21','Next step'),('ncdb_online_annual','WD_C_3_8','Next step')]:
        form=Form();form.feed(html)
        html=capture(name,ncdb,form.fields+[(button,value)])
        if '<title>Error -' in html:
            records[-1]['status']='source_application_error'
            REGISTRY.write_text(json.dumps({'sources':records},indent=2))
            break
    extract()

def extract():
    """Save auditable cells without interpreting spans or fabricating joint records."""
    extracts=[]
    for name in ['tc_casualties_dashboard','tc_statistics_2024','ncdb_online_annual']:
        path=RAW/(name+'.html')
        if not path.exists() or '<title>Error -' in path.read_text():continue
        parser=Tables();parser.feed(path.read_text())
        out=ROOT/'data/reference'/('aggregate_'+name+'_cells.csv')
        with out.open('w',newline='') as stream:
            writer=csv.writer(stream);writer.writerow(['source_id','table_index','caption','row_index','cell_index','value'])
            for ti,table in enumerate(parser.tables):
                for ri,row in enumerate(table['rows']):
                    for ci,value in enumerate(row):writer.writerow([name,ti,table['caption'],ri,ci,value])
        extracts.append(dict(path=str(out.relative_to(ROOT)),sha256=digest(out),derived_from=str(path.relative_to(ROOT)),source_sha256=digest(path),type='extracted_html_table_cells',tables=len(parser.tables)))
    def table_source(name):
        parser=Tables();parser.feed((RAW/(name+'.html')).read_text());return parser.tables
    def write(name,header,rows,source):
        out=ROOT/'data/reference'/name
        with out.open('w',newline='') as stream:
            writer=csv.writer(stream);writer.writerow(header);writer.writerows(rows)
        extracts.append(dict(path=str(out.relative_to(ROOT)),sha256=digest(out),derived_from='data/raw/aggregates/'+source+'.html',source_sha256=digest(RAW/(source+'.html')),type='normalized_html_table_extract',rows=len(rows)))
    pub=table_source('tc_statistics_2024')
    annual=[[int(v.replace(',','')) for v in row] for row in pub[0]['rows'][1:] if len(row)==6 and row[0].isdigit()]
    assert len(annual)==20 and [r[0] for r in annual]==list(range(2005,2025))
    write('aggregate_national_annual_2024_vintage.csv',['year','fatal_collisions','injury_collisions','fatalities','serious_injuries','total_injuries'],annual,'tc_statistics_2024')
    geography=[[2024,row[0]]+[float(v) for v in row[1:]] for row in pub[4]['rows'][2:] if len(row)==7]
    assert len(geography)==14 and len({row[1] for row in geography})==14
    write('aggregate_jurisdiction_rates_2024.csv',['year','location','fatalities_per_100k_population','injuries_per_100k_population','fatalities_per_billion_vkm','injuries_per_billion_vkm','fatalities_per_100k_licensed_drivers','injuries_per_100k_licensed_drivers'],geography,'tc_statistics_2024')
    dashboard=table_source('tc_casualties_dashboard');margins=[];sums={}
    for table in dashboard:
        dimension,measure=table['rows'][0]
        for category,value in table['rows'][1:]:margins.append([2014,2023,dimension,category,measure,int(value.replace(',',''))])
        sums[(dimension,measure)]=sum(int(r[1].replace(',','')) for r in table['rows'][1:])
    mismatches=[{'dimension':d,'measure':m,'partition_sum':v,'year_sum':sums[('Year',m)],'difference':v-sums[('Year',m)]} for (d,m),v in sums.items() if v!=sums[('Year',m)]]
    write('aggregate_dashboard_margins_2014_2023.csv',['period_start','period_end','dimension','category','measure','count'],margins,'tc_casualties_dashboard')
    registry=json.loads(REGISTRY.read_text());registry['extracts']=extracts
    registry['checks']={'national_annual_years':list(range(2005,2025)),'jurisdiction_rows_including_canada':14,'dashboard_partition_mismatches':mismatches,'dashboard_partition_sums':[{ 'dimension':d,'measure':m,'sum':v} for (d,m),v in sums.items()],'dashboard_vs_2024_publication_injuries_2016':{'dashboard':160246,'publication':160248,'resolution':'retain separate vintages'}}
    for source in registry['sources']:
        text=(ROOT/source['path']).read_text()
        source['status']='source_application_error' if '<title>Error -' in text else 'captured'
        source['publication_vintage']={'tc_statistics_2024':'2024 reference year; linked index publication 2026-10-15','tc_casualties_dashboard':'2014–2023 text tables; page modified 2025-12-11','tc_statistics_index':'index links to 2024 publication dated 2026-10-15; footer 2023-04-13'}.get(source['id'],'see original page metadata; acquisition date is not publication date')
    for source in registry['sources']:
        if 'request_fields' in source or any(k.lower()=='set-cookie' for k in source.get('http_headers',{})):
            provenance=RAW/(source['id']+'.provenance.json')
            if provenance.exists():raise FileExistsError(str(provenance))
            provenance.write_text(json.dumps({'request_fields':source.pop('request_fields',None),'http_headers':source.get('http_headers',{})},indent=2))
            source['http_headers']={k:v for k,v in source.get('http_headers',{}).items() if k.lower() in ('content-type','content-length','last-modified','etag','date')}
            source['provenance_path']=str(provenance.relative_to(ROOT));source['provenance_sha256']=digest(provenance)
        source['query_scope']={'years':'1999–2023' if source['id'].startswith('ncdb_') else 'see publication_vintage','road_users':'all; no road-user filter applied','measure':'Number of collisions only' if source['id']=='ncdb_retry_single_measure' else 'all five default measures where applicable'}
    REGISTRY.write_text(json.dumps(registry,indent=2))

def verify():
    registry=json.loads(REGISTRY.read_text())
    for item in registry['sources']+registry['extracts']:
        path=ROOT/item['path']
        assert digest(path)==item['sha256'],str(path)
        if 'derived_from' in item:
            assert digest(ROOT/item['derived_from'])==item['source_sha256'],item['derived_from']
        if 'provenance_path' in item:
            assert digest(ROOT/item['provenance_path'])==item['provenance_sha256'],item['provenance_path']
    print(f"Verified {len(registry['sources'])} original captures and {len(registry['extracts'])} extracts")

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline',action='store_true',help='Verify existing capture hashes and regenerate extracts, without networking')
    args=parser.parse_args()
    if args.offline:
        verify();extract();verify()
    else:
        main();verify()
