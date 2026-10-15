"""Describe recorded harm in road-tractor events; run after build_casualties.

PYTHONPATH=src .venv/bin/python -m truck_collisions.analyze_casualties
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb

GROUPS = {
    'tractor_occupant': 'Tractor occupants',
    'other_motor_vehicle_occupant': 'Other motor vehicle occupants',
    'pedestrian': 'Pedestrians',
    'cyclist': 'Cyclists',
    'motorcyclist': 'Motorcyclists',
    'other_or_unknown': 'Other / unknown road users',
    'ambiguous': 'Conflicting road-user group',
}
PERIODS = [(2012,2021),(2012,2019),(2016,2021),(2016,2019),(2019,2020),(2020,2021),(2019,2021)]
SCENARIOS = ['low','high']
MEASURES = ['deaths','injuries']


def read_csv(path):
    with path.open(newline='', encoding='utf-8') as stream:
        return [{key: (int(value) if key not in ('subset','road_user_group') else value) for key,value in row.items()} for row in csv.DictReader(stream)]


def write_csv(path, rows):
    with path.open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def sha256(path):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            digest.update(block)
    return digest.hexdigest()


def ratio(numerator,denominator):
    return 100*numerator/denominator if denominator else None


def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(str,row))+' |' for row in rows])


def make_figures(output,annual,grouped):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import StrMethodFormatter
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','savefig.dpi':180})
    colors=['#175b80','#b66d15','#65853b','#8b5d95','#c24638','#667079','#a89975']
    observed=[r for r in annual if r['subset']=='observed']
    def decorate(ax,start=1999):
        ax.grid(axis='y',color='#dddddd',linewidth=.7)
        ax.set_xticks([1999,2004,2009,2012,2016,2021] if start==1999 else [2012,2014,2016,2018,2021])
        ax.set_xlim(start-.25,2021.25);ax.set_ylim(bottom=0)
        ax.set_xlabel('Calendar year')
        ax.yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))
    def save(fig,name,note,left=.08,wspace=.30):
        fig.text(.07,.025,note,fontsize=9,color='#444444',va='bottom')
        fig.subplots_adjust(left=left,right=.97,bottom=.21,top=.81,wspace=wspace,hspace=.43)
        for ext in ('png','svg'):fig.savefig(output/f'{name}.{ext}',facecolor='white')
        plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(12,6))
    fig.suptitle('Recorded harm in road-tractor casualty collisions, Canada',fontsize=17,y=.97)
    for ax,measure in zip(axes,MEASURES):
        x=[r['year'] for r in observed]
        low=[r[f'{measure}_record_scenario_low'] for r in observed]
        high=[r[f'{measure}_record_scenario_high'] for r in observed]
        ax.fill_between(x,low,high,color=colors[0],alpha=.22,label='Record resolution span')
        ax.plot(x,low,color=colors[0],marker='o',markersize=3,label='Identified, certain outcome')
        ax.plot(x,high,color=colors[1],linestyle='--',label='Possible outcome + unresolved rows')
        ax.set_title(measure.title()+' (independent y scales)');ax.set_ylabel('Recorded person count / row scenario');decorate(ax)
    axes[0].legend(frameon=False,fontsize=9)
    save(fig,'annual_harm','Includes people in every involved vehicle and pedestrians, 1999–2021; fatal/injury events with recorded vehicle type 08.\nSpan reflects record handling, not confidence intervals or bounds on true casualties. Unknown severity remains unallocated.')
    fig,axes=plt.subplots(1,2,figsize=(12,6.4))
    fig.suptitle('Who is harmed? Recorded casualty shares, 2012 and 2021',fontsize=17,y=.97)
    for ax,measure in zip(axes,MEASURES):
        for offset,year in [(-.18,2012),(.18,2021)]:
            total=next(r for r in observed if r['year']==year)
            rows=[next(r for r in grouped if r['subset']=='observed' and r['year']==year and r['road_user_group']==group) for group in GROUPS]
            ax.barh([i+offset for i in range(len(GROUPS))],[ratio(r[f'{measure}_record_scenario_low'],total[f'{measure}_record_scenario_low']) for r in rows],height=.33,color=colors[0] if year==2012 else colors[1],label=str(year),hatch=None if year==2012 else '//')
        ax.set_title(measure.title());ax.set_yticks(range(len(GROUPS)),list(GROUPS.values()),fontsize=10)
        ax.invert_yaxis();ax.set_xlim(0,100);ax.set_xlabel('Share of identified, certain-outcome count (%)');ax.grid(axis='x',color='#dddddd',linewidth=.7)
    axes[0].legend(frameon=False)
    fig.subplots_adjust(left=.25,wspace=.95)
    # Long road-user names require dedicated space in each panel.
    fig.set_size_inches(16,6.4)
    save(fig,'harm_shares','Each panel includes unknown and conflicting group categories in its denominator. Selected identified-person scenario only;\nall other scenario shares are exported. “Other motor vehicle occupants” excludes pedestrians, cyclists and motorcyclists.',left=.23,wspace=1.0)
    fig,axes=plt.subplots(2,1,figsize=(11,8.3))
    fig.suptitle('Harm by road-user group, Canada, 2012–2021',fontsize=17,y=.97)
    for ax,measure in zip(axes,MEASURES):
        for i,group in enumerate(list(GROUPS)[:5]):
            rows=[r for r in grouped if r['subset']=='observed' and r['road_user_group']==group and r['year']>=2012]
            ax.plot([r['year'] for r in rows],[r[f'{measure}_record_scenario_low'] for r in rows],label=GROUPS[group],color=colors[i],marker=['o','s','^','d','x'][i],markersize=3,linestyle=['-','--',':','-.','-'][i])
        ax.set_title(measure.title()+' — identified, certain outcome');ax.set_ylabel('People');decorate(ax,2012)
    fig.legend(*axes[0].get_legend_handles_labels(),frameon=False,ncol=3,fontsize=10,loc='upper center',bbox_to_anchor=(.5,.925))
    save(fig,'group_harm_trends','Other/unknown/conflicting road-user groups are retained in the CSV and composition chart, omitted from this five-group trend view.\nObserved public-release records; 2019 benchmark remains disputed. 2020 and 2021 are shown explicitly, not interpreted causally.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path,default=Path('data/derived/casualties'))
    parser.add_argument('--output-dir',type=Path,default=Path('reports/casualties'))
    args=parser.parse_args();data=args.data_dir.resolve();output=args.output_dir.resolve();output.mkdir(parents=True,exist_ok=True)
    annual=read_csv(data/'annual_counts.csv');grouped=read_csv(data/'annual_group_counts.csv')
    assert len(annual)==46 and len(grouped)==46*len(GROUPS)
    index={(r['year'],r['subset']):r for r in annual}
    assert len(index)==len(annual)
    additive=[c for c in annual[0] if c not in ('year','subset')]
    for row in annual:
        parts=[g for g in grouped if g['year']==row['year'] and g['subset']==row['subset']]
        assert {g['road_user_group'] for g in parts}==set(GROUPS)
        for column in additive:assert sum(g[column] for g in parts)==row[column],(row['year'],column)
        for measure in MEASURES:assert row[f'{measure}_record_scenario_low']<=row[f'{measure}_record_scenario_high']
    events_path=data.parent/'ncdb'/'road_tractor_collisions.parquet'
    connection=duckdb.connect()
    event_counts={}
    for subset,predicate in [('observed','TRUE'),('strict','is_analysis_candidate')]:
        event_counts.update({(year,subset):count for year,count in connection.execute(f"SELECT C_YEAR,count(*) FROM read_parquet('{str(events_path).replace(chr(39),chr(39)*2)}') WHERE {predicate} GROUP BY C_YEAR").fetchall()})
    connection.close()
    event_harm=[]
    for row in annual:
        events=event_counts[(row['year'],row['subset'])]
        event_harm.append({'year':row['year'],'subset':row['subset'],'casualty_collisions':events,**{f'{measure}_per_100_casualty_collisions_{scenario}':100*row[f'{measure}_record_scenario_{scenario}']/events for measure in MEASURES for scenario in SCENARIOS}})
    write_csv(output/'harm_per_collision.csv',event_harm)
    shares=[]
    for row in grouped:
        total=index[(row['year'],row['subset'])]
        for measure in MEASURES:
            for scenario in SCENARIOS:
                column=f'{measure}_record_scenario_{scenario}'
                shares.append({'year':row['year'],'subset':row['subset'],'road_user_group':row['road_user_group'],'measure':measure,'record_scenario':scenario,'count':row[column],'all_group_count':total[column],'share_pct':ratio(row[column],total[column])})
    group_pooled=[]
    for subset in ('observed','strict'):
        for start,end in [(1999,2021),(2012,2021),(2016,2021)]:
            for measure in MEASURES:
                for scenario in SCENARIOS:
                    col=f'{measure}_record_scenario_{scenario}'
                    denominator=sum(r[col] for r in annual if r['subset']==subset and start<=r['year']<=end)
                    for group in GROUPS:
                        count=sum(r[col] for r in grouped if r['subset']==subset and start<=r['year']<=end and r['road_user_group']==group)
                        group_pooled.append({'subset':subset,'start_year':start,'end_year':end,'road_user_group':group,'measure':measure,'record_scenario':scenario,'count':count,'all_group_count':denominator,'share_pct':ratio(count,denominator)})
    write_csv(output/'pooled_group_shares.csv',group_pooled)
    changes=[]
    all_rows=[{**r,'road_user_group':'all'} for r in annual]+grouped
    lookup={(r['year'],r['subset'],r['road_user_group']):r for r in all_rows}
    for subset in ('observed','strict'):
        for group in ['all',*GROUPS]:
            for start,end in PERIODS:
                first,last=lookup[(start,subset,group)],lookup[(end,subset,group)]
                for measure in MEASURES:
                    for scenario in SCENARIOS:
                        column=f'{measure}_record_scenario_{scenario}'
                        changes.append({'subset':subset,'road_user_group':group,'start_year':start,'end_year':end,'measure':measure,'record_scenario':scenario,'start_count':first[column],'end_count':last[column],'change_count':last[column]-first[column],'pct_change':100*(last[column]/first[column]-1) if first[column] else None})
    pooled=[]
    for subset in ('observed','strict'):
        for name,start,end,omit in [('2012–2016',2012,2016,False),('2017–2021',2017,2021,False),('2017–2021 excluding 2019',2017,2021,True),('2016–2021',2016,2021,False),('2016–2021 excluding 2019',2016,2021,True),('2012–2019',2012,2019,False),('2012–2018',2012,2018,False)]:
            selected=[r for r in annual if r['subset']==subset and start<=r['year']<=end and not(omit and r['year']==2019)]
            for measure in MEASURES:
                for scenario in SCENARIOS:
                    count=sum(r[f'{measure}_record_scenario_{scenario}'] for r in selected)
                    pooled.append({'period':name,'subset':subset,'measure':measure,'record_scenario':scenario,'included_years':len(selected),'count':count,'mean_annual_count':count/len(selected)})
    sensitivity=[]
    for year in range(1999,2022):
        observed,strict=index[(year,'observed')],index[(year,'strict')]
        row={'year':year}
        for measure in MEASURES:
            for scenario in SCENARIOS:
                col=f'{measure}_record_scenario_{scenario}'
                row[f'{col}_observed']=observed[col];row[f'{col}_strict']=strict[col];row[f'{col}_excluded']=observed[col]-strict[col]
        sensitivity.append(row)
    write_csv(output/'annual_counts.csv',annual);write_csv(output/'annual_group_counts.csv',grouped)
    for name,rows in [('annual_group_shares',shares),('period_changes',changes),('pooled_sensitivity',pooled),('strict_event_sensitivity',sensitivity)]:write_csv(output/f'{name}.csv',rows)
    benchmark=[]
    benchmark_path=data/'occupant_benchmark_comparison.csv'
    if benchmark_path.exists():
        with benchmark_path.open(newline='',encoding='utf-8') as stream:benchmark=list(csv.DictReader(stream))
        write_csv(output/'occupant_benchmark_comparison.csv',benchmark)
    make_figures(output,annual,grouped)
    summary={'created_at_utc':datetime.now(timezone.utc).isoformat(),'coverage':[1999,2021],'target_period':[2016,2025],'status':'record-resolution scenarios, not reconciled national person totals','groups':GROUPS,'checks':{'annual_rows':len(annual),'annual_group_rows':len(grouped),'all_group_additivity':'passed','scenario_ordering':'passed'},'principal_results':[r for r in changes if r['subset']=='observed' and r['road_user_group']=='all' and (r['start_year'],r['end_year']) in [(2012,2021),(2016,2021)]],'input_sha256':{str(p):sha256(p) for p in [*[p for p in sorted(data.glob('*')) if p.suffix in ('.csv','.parquet','.json')],events_path] if p.is_file()},'code_sha256':sha256(Path(__file__)),'software':{'duckdb':duckdb.__version__}}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (output/'findings.md').write_text(report(annual,grouped,shares,changes,pooled,sensitivity,event_harm,benchmark),encoding='utf-8')
    print(json.dumps(summary['checks'],indent=2))


def report(annual,grouped,shares,changes,pooled,sensitivity,event_harm,benchmark):
    index={(r['year'],r['subset']):r for r in annual}
    def span(row,measure):return f"{row[f'{measure}_record_scenario_low']:,}–{row[f'{measure}_record_scenario_high']:,}"
    def c(start,end,measure,scenario='low',group='all'):
        return next(r for r in changes if r['subset']=='observed' and r['road_user_group']==group and r['start_year']==start and r['end_year']==end and r['measure']==measure and r['record_scenario']==scenario)
    def percent(value):return 'undefined (zero baseline)' if value is None else f'{value:+.2f}%'
    text=['# Who is harmed in recorded road-tractor casualty collisions?','','## Answer and scope','',
        f"For 2012–2021, the identified-person, certain-outcome death count changed from {c(2012,2021,'deaths')['start_count']:,} to {c(2012,2021,'deaths')['end_count']:,} ({percent(c(2012,2021,'deaths')['pct_change'])}); injuries changed from {c(2012,2021,'injuries')['start_count']:,} to {c(2012,2021,'injuries')['end_count']:,} ({percent(c(2012,2021,'injuries')['pct_change'])}). The higher record scenario produces changes of {percent(c(2012,2021,'deaths','high')['pct_change'])} for deaths and {percent(c(2012,2021,'injuries','high')['pct_change'])} for injuries. These are counts reconstructed from this public release, with the unresolved identity and severity records visible below.",'',
        'The target remains **2016–2025**. Available records cover **1999–2021**; 2012–2021 is the historical decade and 2016–2021 the available portion of the target. No result here establishes 2022–2025 outcomes, risk per kilometre, fault, or cause. The 2019 event benchmark discrepancy remains unresolved.','',f"Deaths per 100 recorded casualty collisions changed from {next(r['deaths_per_100_casualty_collisions_low'] for r in event_harm if r['year']==2012 and r['subset']=='observed'):.2f} in 2012 to {next(r['deaths_per_100_casualty_collisions_low'] for r in event_harm if r['year']==2021 and r['subset']=='observed'):.2f} in 2021 in the identified, certain-outcome scenario. Thus fewer recorded events coincided with fewer recorded deaths, but deaths declined less than events. This measure is people killed per casualty event, distinct from the fatal-event share; neither measures driving risk. The denominator excludes property-damage-only crashes. Exact annual values for both scenarios and event subsets are in `harm_per_collision.csv`.",'',
        '![Annual recorded harm](annual_harm.png)','','## Counting method and what the scenarios mean','',
        'The pipeline selects whole events with recorded vehicle type 08 (road tractor with or without semitrailer), then uses records for **all people in each selected event**. Its separate contract and validation document identity resolution, raw duplicate treatment, group conflicts and dummy handling. Vehicle ID 99 is a pedestrian dummy vehicle and does not imply a dummy person. Person ID NN represents a dummy person and is excluded from harm counts; unidentified people remain unresolved records. No synthetic identity is created.','',
        'The low scenario counts identified person keys whose coded outcome is certain under the retained record variants. The high scenario counts each identified key if the outcome is possible under its variants and adds every raw unresolved-identity row coded with that outcome. The span therefore exposes alternative record handling. It is **not a confidence interval, not a lower/upper bound on actual casualties, and not an imputation**. Repeated unresolved rows might represent one person or several; missing people and unknown severity cannot be bounded by these data. Separate death and injury highs can overlap for a key with contradictory severity, so those highs must not be added to claim a unique casualty total.','',
        'P_ISEV 3 denotes a recorded fatality, 2 a recorded injury. Not-applicable severity N is counted separately from unknown/unavailable severity. Unknown/unavailable severity is never relabeled as death, injury or uninjured. Group classification uses source road-user and vehicle codes checked for consistency, retaining other/unknown and conflicting groups explicitly. Other motor vehicle occupants exclude pedestrians, cyclists and motorcyclists. Group scenario shares use the corresponding all-group scenario denominator; they are coherent scenario compositions, not bounds on true shares.','','## Annual all-person results','',
        table(['Year','Death record span','Injury record span','Unknown severity: identified keys','Unknown severity: unresolved rows','N severity: identified / unresolved'],[[r['year'],span(r,'deaths'),span(r,'injuries'),r['unknown_severity_identified_keys'],r['unknown_severity_unresolved_rows'],f"{r['not_applicable_severity_identified_keys']} / {r['not_applicable_severity_unresolved_rows']}"] for r in annual if r['subset']=='observed']),'','## Who bears the recorded harm?','','![Group shares](harm_shares.png)','',
        table(['Road-user group','2012 deaths','2021 deaths','2012 injuries','2021 injuries'],[[label,*[span(next(r for r in grouped if r['year']==year and r['subset']=='observed' and r['road_user_group']==group),measure) for measure in MEASURES for year in (2012,2021)]] for group,label in GROUPS.items()]),'',
        f"Other motor vehicle occupants account for {sum(r['deaths_record_scenario_low'] for r in grouped if r['subset']=='observed' and r['road_user_group']=='other_motor_vehicle_occupant' and 2012<=r['year']<=2021):,} of {sum(r['deaths_record_scenario_low'] for r in annual if r['subset']=='observed' and 2012<=r['year']<=2021):,} identified, certain-outcome deaths during 2012–2021 ({ratio(sum(r['deaths_record_scenario_low'] for r in grouped if r['subset']=='observed' and r['road_user_group']=='other_motor_vehicle_occupant' and 2012<=r['year']<=2021),sum(r['deaths_record_scenario_low'] for r in annual if r['subset']=='observed' and 2012<=r['year']<=2021)):.2f}%). This pooled share divides summed deaths by summed all-group deaths, not an average of annual percentages. All pooled group shares and both scenarios are in `pooled_group_shares.csv`.",'',
        f"Deaths among tractor occupants changed from {c(2012,2021,'deaths',group='tractor_occupant')['start_count']} to {c(2012,2021,'deaths',group='tractor_occupant')['end_count']} ({percent(c(2012,2021,'deaths',group='tractor_occupant')['pct_change'])}), while deaths among other motor vehicle occupants changed from {c(2012,2021,'deaths',group='other_motor_vehicle_occupant')['start_count']} to {c(2012,2021,'deaths',group='other_motor_vehicle_occupant')['end_count']} ({percent(c(2012,2021,'deaths',group='other_motor_vehicle_occupant')['pct_change'])}). In 2021 pedestrians, cyclists and motorcyclists together account for {sum(r['deaths_record_scenario_low'] for r in grouped if r['year']==2021 and r['subset']=='observed' and r['road_user_group'] in ('pedestrian','cyclist','motorcyclist'))} deaths, compared with {sum(r['deaths_record_scenario_low'] for r in grouped if r['year']==2012 and r['subset']=='observed' and r['road_user_group'] in ('pedestrian','cyclist','motorcyclist'))} in 2012. These small endpoint subgroup counts can fluctuate: they describe where recorded harm occurred and do not establish a trend in risk or an explanation for the changes.",'',
        'The often quoted approximately 70% finding for other-vehicle occupants in [Transport Canada’s broader commercial-vehicle analysis](https://tc.canada.ca/en/road-transportation/statistics-data/commercial-vehicle-collisions/2021/commercial-vehicle-collisions-canada-2012-2021) is **not assumed to apply to semis**. The following values calculate this study’s other-motor-vehicle-occupant share from its own records, with all unknown/conflicting groups in the denominator. Pedestrians, cyclists and motorcyclists are displayed separately rather than being described as other-vehicle occupants.','',
        table(['Year','Other vehicle death share: low scenario','Other vehicle death share: high scenario','Tractor occupant death share: low','Other/unknown/conflicting death share: low'],[[year,*[f"{next(r['share_pct'] for r in shares if r['year']==year and r['subset']=='observed' and r['road_user_group']==group and r['measure']=='deaths' and r['record_scenario']==scenario):.2f}%" for group,scenario in [('other_motor_vehicle_occupant','low'),('other_motor_vehicle_occupant','high'),('tractor_occupant','low')]],f"{sum(r['share_pct'] for r in shares if r['year']==year and r['subset']=='observed' and r['road_user_group'] in ('other_or_unknown','ambiguous') and r['measure']=='deaths' and r['record_scenario']=='low'):.2f}%"] for year in (2012,2016,2019,2020,2021)]),'','![Group harm trends](group_harm_trends.png)','','## Change over time and sensitivity','',
        table(['Period','Deaths change: low','Deaths change: high','Injuries change: low','Injuries change: high'],[[f'{start}–{end}',*[percent(c(start,end,measure,scenario)['pct_change']) for measure in MEASURES for scenario in SCENARIOS]] for start,end in PERIODS]),'',
        'The 2012–2019 and 2016–2019 comparisons describe the pre-2020 endpoints; 2019–2020 and 2020–2021 show the disruption and rebound directly. These comparisons describe timing, not a causal effect. Because the 2019 published tractor collision benchmark disagrees with this public release, comparisons ending or starting in 2019 carry additional unresolved source-vintage/definition uncertainty. No casualty “correction” is inferred from a difference in collision counts. The 2012–2021 and 2016–2021 endpoint comparisons do not use 2019; the following pooled summaries also show results excluding it.','',
        table(['Block','Scenario','Included years','Deaths total','Mean annual deaths','Injuries total','Mean annual injuries'],[[r['period'],r['record_scenario'],r['included_years'],r['count'],f"{r['mean_annual_count']:.1f}",next(x['count'] for x in pooled if x['period']==r['period'] and x['subset']=='observed' and x['measure']=='injuries' and x['record_scenario']==r['record_scenario']),f"{next(x['mean_annual_count'] for x in pooled if x['period']==r['period'] and x['subset']=='observed' and x['measure']=='injuries' and x['record_scenario']==r['record_scenario']):.1f}"] for r in pooled if r['subset']=='observed' and r['measure']=='deaths']),'',
        'The strict event subset excludes the collision build’s structurally/type-conflicted events and is an alternative cohort, not a corrected series. It can preferentially remove complicated collisions. The table reports excluded recorded harm by year; zero means the same harm count under that scenario, not proof of no source uncertainty.','',
        table(['Year','Excluded deaths: low','Excluded deaths: high','Excluded injuries: low','Excluded injuries: high'],[[r['year'],*[r[f'{measure}_record_scenario_{scenario}_excluded'] for measure in MEASURES for scenario in SCENARIOS]] for r in sensitivity if any(r[f'{measure}_record_scenario_{scenario}_excluded'] for measure in MEASURES for scenario in SCENARIOS)]),'',
        'Every group’s endpoint changes, both scenarios and both event subsets are available in `period_changes.csv`; all annual group scenario shares are in `annual_group_shares.csv`. No statistical significance, sampling confidence interval, or fitted causal model is claimed. The important uncertainty is record identity, outcome/group classification, incomplete reporting, and unresolved source versions.','','## Published tractor-occupant benchmarks','',
        'The person pipeline compares the classified tractor-occupant counts with [Transport Canada’s 2021 report to Parliament, Table 12](https://tc.canada.ca/en/road-transportation/motor-vehicle-safety/motor-carriers-commercial-vehicles-drivers/commercial-vehicle-safety-canada-2021-annual-report-parliament) and the original [2021 traffic collision statistics](https://tc.canada.ca/en/road-transportation/statistics-data/canadian-motor-vehicle-traffic-collision-statistics/2021/canadian-motor-vehicle-traffic-collision-statistics-2021). These occupant-only values do not validate all-person harm totals. Both event subsets and source-specific comparisons are exported in `occupant_benchmark_comparison.csv`.','',
        table(['Source','Year','Measure','Published','Classified low','Classified high','Low difference'],[[r['source_id'],r['year'],r['measure'],r['count'],r['classified_record_scenario_low'],r['classified_record_scenario_high'],r['low_minus_published']] for r in benchmark if r['subset']=='observed']),'',
        'External reconciliation remains partial. In 2021 the classified tractor-occupant death count is 30 versus 29 in the report to Parliament and 28 in the traffic statistics, and injury count 812 versus 806 in both publications. A possible explanation is operational occupant assignment: the extra 2021 death has unknown road-user type and seating position 98 (outside passenger compartment); the six extra injury records have positions 98 or NN. Similar arithmetic occurs for some 2018 and 2020 injury comparisons. This is an **unproven classification hypothesis**, does not explain every discrepancy (including the 2019 source revisions), and does not justify dropping those people from the all-person event totals or forcing agreement. The adopted classification retains positive vehicle evidence while preserving explicit contradictions as ambiguous.','',
        '## Reproduce and inspect','',
        'Run `PYTHONPATH=src MPLCONFIGDIR=/tmp/collisions-matplotlib .venv/bin/python -m truck_collisions.analyze_casualties` after the person pipeline. Default inputs are `data/derived/casualties/annual_counts.csv` and `annual_group_counts.csv`. The analysis asserts all group columns add to all-person annual totals, key uniqueness, expected coverage, seven exhaustive groups and low ≤ high. `summary.json` records input and code hashes and the exact principal results. The notebook independently recomputes selected group shares and change formulas, then embeds all figures.','',
        'Source lineage remains the pinned `data/sources.json` mapping and casualty build’s source manifest, including the inherited 1999–2017 extract and official 2018–2021 files. [Official NCDB catalogue](https://open.canada.ca/data/en/dataset/1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a). The separate person validation outputs carry unresolved identity/severity diagnostics. Matching some external aggregates would not prove identity resolution, and the current record scenarios are not an externally reconciled national casualty series.','','## Next questions supported by this work','',
        'Use the validated person records and explicit scenarios to study whether harm to particular groups changed differently. Weather, road surface, configuration and time comparisons can then describe casualty patterns in reported events, preserving identity scenarios and unknown categories. Exposure rates require a compatible distance/fleet denominator, and policy effects require additional data and a defensible comparison design.','']
    return '\n'.join(text)


if __name__=='__main__':main()
