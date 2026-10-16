"""Render descriptive condition tables/figures after analyze_conditions; no input mutation."""
from pathlib import Path
import csv
import json

COHORTS = ('tractor', 'no_recorded_tractor')
COLORS = ('#175b80', '#b66d15')
NAMES = ('Tractor involved', 'No recorded tractor')
PRIMARY = 'primary_2012_2021'
FIELDS = ('C_WTHR', 'C_RSUR', 'C_CONF', 'C_RCFG', 'C_HOUR', 'C_MNTH', 'C_WDAY', 'C_RALN', 'C_TRAF', 'HOUR_BAND')


def load(path):
    with path.open(newline='') as handle:
        return list(csv.DictReader(handle))


def match(rows, **kwargs):
    return [row for row in rows if all(str(row.get(k)) == str(v) for k, v in kwargs.items())]


def one(rows, **kwargs):
    selected = match(rows, **kwargs)
    assert len(selected) == 1, (kwargs, len(selected))
    return selected[0]


def num(row, key):
    return float(row[key]) if row[key] else None


def cell(row):
    return f"{int(row['code_events']):,}/{int(row['events']):,} ({float(row['share_pct']):.2f}%)"


def table(headers, rows):
    return '\n'.join(['| '+' | '.join(headers)+' |', '| '+' | '.join(['---']*len(headers))+' |'] + ['| '+' | '.join(map(str,row))+' |' for row in rows])


def report(root):
    root = Path(root)
    output = root/'reports/conditions'
    period = load(output/'period_distributions.csv')
    annual = load(output/'annual_distributions.csv')
    fatal = load(output/'category_fatal_shares.csv')
    primary = match(period, period=PRIMARY, subset='observed')
    book = json.loads((root/'data/reference/collision_codebook.json').read_text())['fields']
    labels = {field: book[field]['label'] for field in FIELDS if field in book}
    labels['HOUR_BAND'] = 'Hour bands (derived, six-hour intervals)'
    figures(output, primary, annual, fatal, labels)
    lines = ['# Descriptive conditions in tractor-involved casualty collisions', '',
        '## Scope and interpretation', '',
        '**Canada, 2012–2021; observed events.** Each collision counts once. Tractor involved means at least one recorded vehicle type 08, road tractor with or without a semitrailer. The comparator has no recorded tractor: it includes other heavy trucks and uncertain vehicle types and is not car-only. These are police-reported fatal and injury collisions; property-damage-only events are outside the dataset.', '',
        'All-event shares use every event in that cohort, period and severity stratum as denominator, including unknown, valid residual Q/QQ other and any unavailable fields. Fatal-stratum distributions use only fatal events; injury-stratum distributions use only injury events. A category’s fatal-event share instead divides its fatal events by all its fatal and injury events. These describe different quantities. A fatal event can contain multiple deaths; no person death counts are estimated here.', '',
        'No exposure denominators are available. None of the following shares estimates risk per kilometre, weather exposure, causal effects or fault. Hour is clock time, not darkness. Road configuration/alignment do not supply a complete road-class measure. A reference dictionary and valid code syntax do not prove identical reporting practices across years or jurisdictions.', '',
        '## Main comparisons', '']
    # Selected, predeclared descriptive contrasts; exact n/N carried with every percentage.
    selected = [('C_WTHR','4'), ('C_RSUR','5'), ('C_CONF','21'), ('C_CONF','31'), ('C_RCFG','01'), ('C_TRAF','18')]
    rows = []
    for field, code in selected:
        left = one(primary, cohort=COHORTS[0], severity='all', field=field, code=code)
        right = one(primary, cohort=COHORTS[1], severity='all', field=field, code=code)
        rows.append([labels[field]+': '+left['label'], cell(left), cell(right), f"{num(left,'share_pct')-num(right,'share_pct'):+.2f}"])
    lines += [table(['Recorded category','Tractor events n/N (%)','No recorded tractor n/N (%)','Difference (pp)'],rows), '',
        'These are differences in the mix of recorded casualty collisions. They can reflect traffic exposure, where and when vehicles travel, geography, reporting, and collision mechanisms; this analysis cannot separate those explanations.', '',
        '![Weather and surface distributions](pooled_weather_surface.png)', '',
        '## How selected shares changed over time', '',
        'Annual comparisons retain each year’s cohort denominator. The following selected series are descriptive and were not chosen as significance-tested findings. The pandemic period changes travel and freight patterns; endpoint changes cannot identify their contribution.', '',
        '![Selected annual condition shares](annual_condition_mix.png)', '']
    endpoint_rows = []
    for field, code in [('C_WTHR','4'),('C_CONF','21'),('C_CONF','31'),('HOUR_BAND','00–05')]:
        for cohort, name in zip(COHORTS,NAMES):
            before=one(annual,subset='observed',severity='all',year=2012,cohort=cohort,field=field,code=code)
            after=one(annual,subset='observed',severity='all',year=2021,cohort=cohort,field=field,code=code)
            endpoint_rows.append([before['label'],name,cell(before),cell(after),f"{num(after,'share_pct')-num(before,'share_pct'):+.2f}"])
    lines += [table(['Category','Cohort','2012 n/N (%)','2021 n/N (%)','Change (pp)'],endpoint_rows),'',
        '## Conditional fatal-event shares', '',
        '![Conditional fatal-event shares](configuration_fatal_share.png)', '',
        'Among tractor head-on casualty collisions, 641/1,939 (33.06%) were fatal events, compared with 271/7,572 (3.58%) of tractor rear-end collisions. Head-on collisions were 1,939/29,496 (6.57%) of all tractor events but 641/1,919 (33.40%) of tractor fatal events. These different denominators explain why a relatively uncommon configuration contributes a substantial fraction of recorded fatal events.', '',
        'The chart compares fatal events within each recorded configuration, not deaths per collision and not collision incidence. The labels give fatal/all-category event counts. Unknown and Q/QQ other are separate, observed categories; their conditional fatal shares are not assigned to named configurations. Rare categories and cross-tabulations should be read as counts, without inferential ranking.', '',
        '## Full category tables: fatal/injury strata and comparison population', '',
        'Every field and hour-band table below is exhaustive over its export domain, including zero-count categories and explicit special-code rows. Each cell is category events / stratum events (percentage). “Other” is Q/QQ; named dictionary categories that contain the word “other” remain defined. A zero denominator produces an undefined percentage; a zero numerator with a positive denominator legitimately produces 0%.', '']
    for field in FIELDS:
        categories=match(primary,field=field,cohort='tractor',severity='all')
        full=[]
        for category in categories:
            code=category['code']
            full.append([f"{code}: {category['label']} [{category['status']}]", *[cell(one(primary,field=field,code=code,cohort=cohort,severity=severity)) for cohort in COHORTS for severity in ('all','fatal','injury')]])
        lines += [f"### {labels[field]}",'',table(['Category','Tractor all','Tractor fatal','Tractor injury','Comparator all','Comparator fatal','Comparator injury'],full),'']
    sensitivity_rows=[]
    sensitivity_specs=[(PRIMARY,'observed','Primary'),(PRIMARY,'strict','Strict'),('pre2020_2012_2019','observed','2012–2019'),('omit2019_2012_2021','observed','Omit 2019'),('target_available_2016_2021','observed','2016–2021 available')]
    for period_name,subset,scenario in sensitivity_specs:
        for cohort,name in zip(COHORTS,NAMES):
            selected_rows=[one(period,period=period_name,subset=subset,cohort=cohort,severity='all',field=f,code=c) for f,c in [('C_WTHR','4'),('C_CONF','31'),('HOUR_BAND','00–05')]]
            sensitivity_rows.append([scenario,name,int(selected_rows[0]['events']),*[cell(r) for r in selected_rows]])
    changes=load(output/'period_changes.csv')
    change_rows=[]
    for field,code in [('C_WTHR','4'),('C_CONF','21'),('C_CONF','31'),('HOUR_BAND','00–05')]:
        for cohort,name in zip(COHORTS,NAMES):
            row=one(changes,subset='observed',severity='all',cohort=cohort,field=field,code=code)
            change_rows.append([row['label'],name,f"{int(row['early_code_events']):,}/{int(row['early_events']):,} ({num(row,'early_share_pct'):.2f}%)",f"{int(row['late_code_events']):,}/{int(row['late_events']):,} ({num(row,'late_share_pct'):.2f}%)",f"{num(row,'share_change_pp'):+.2f}"])
    lines += ['## Sensitivities and cross-tabulations','',
        '### Early versus late period','',
        'These are volume-weighted pooled event shares: summed category counts divided by summed event counts, not unweighted annual averages. Each period contains five years; the late period includes 2020–2021.', '',
        table(['Category','Cohort','2012–2016 n/N (%)','2017–2021 n/N (%)','Change (pp)'],change_rows),'',
        '### Strict and alternative period windows','',
        table(['Scenario','Cohort','Events','Snow n/N (%)','Head-on n/N (%)','00:00–05:59 n/N (%)'],sensitivity_rows),'',
        'For these selected contrasts, the higher tractor shares of snow, head-on and 00:00–05:59 collisions persist across the strict, pre-2020, omit-2019 and available-2016–2021 views. This is descriptive stability of composition differences, not proof that reporting or exposure confounding is absent. It does not establish identical stability for every small category.', '',
        'The machine-readable tables retain observed and strict cohorts, early 2012–2016 versus late 2017–2021, pre-2020, omission of 2019, and the available 2016–2021 target-period segment. Strict excludes existing inconsistent-event/type cases and is a sensitivity, not a corrected truth. Source revisions are already applied; the selected release is fingerprinted. A source-identification check accompanies annual denominators. Sensitivity period windows answer different descriptive questions and must not be presented as interchangeable estimates.', '',
        'The weather × surface and crash configuration × hour-band exports retain the full category grid, including zero and special-code cells, separately for both cohorts and all/fatal/injury strata. These are exploratory tables, not tests of interaction, causality or fault. Sparse cells retain visible counts rather than being suppressed or modelled.', '',
        '## Limits and next decision','',
        'The audit found a substantial 1999–2000 configuration-distribution shift; primary comparisons therefore start in 2012 and do not pool 1999. The intended 2016–2025 study remains incomplete: national event records stop at 2021. Two injury-event differences in 2013 and 2019 and partial occupant benchmark discrepancies remain unresolved. No benchmark total has been used to patch these distributions.', '',
        'These comparisons support targeted follow-up on collision mechanisms and timing. Exposure-adjusted analyses require suitable denominators; policy evaluation needs justified comparison groups and intervention timing. Vehicle manoeuvres and fault cannot be recovered from crash configuration. Person-harm analyses must preserve the separate casualty identity/outcome scenarios.', '',
        '## Reproduction and evidence','',
        'Run `PYTHONPATH=src MPLCONFIGDIR=/tmp/collisions-matplotlib .venv/bin/python -m truck_collisions.analyze_conditions`, then the same command with `truck_collisions.report_conditions`. The notebook reruns both modules and independently checks selected direct-event counts and formulas.', '',
        '- [Annual category distributions](annual_distributions.csv) and [period distributions](period_distributions.csv).',
        '- [Cohort comparisons](cohort_comparisons.csv), [period changes](period_changes.csv), and [conditional fatal shares](category_fatal_shares.csv).',
        '- [Joint distributions](joint_distributions.csv), [run evidence](summary.json), [quality assessment](../../docs/conditions_quality.md), and [source release repair](../../docs/source_release_update.md).', '']
    (output/'findings.md').write_text('\n'.join(lines))


def figures(output, primary, annual, fatal, labels):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
    def save(fig,name,note):
        fig.text(.04,.025,note,fontsize=9,color='#444444',va='bottom')
        fig.savefig(output/f'{name}.png',dpi=180,facecolor='white')
        fig.savefig(output/f'{name}.svg',facecolor='white')
        plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(15,7))
    fig.suptitle('Recorded weather and surface mix, Canada 2012–2021',fontsize=16,y=.98)
    for ax,field in zip(axes,('C_WTHR','C_RSUR')):
        categories=match(primary,cohort='tractor',severity='all',field=field)
        # Display named categories plus every observed special category; CSVs retain all zeros.
        categories=[r for r in categories if r['status']=='defined' or any(int(x['code_events']) for x in match(primary,field=field,code=r['code'],severity='all'))]
        for offset,cohort,color,name in zip((-.18,.18),COHORTS,COLORS,NAMES):
            rows=[one(primary,cohort=cohort,severity='all',field=field,code=r['code']) for r in categories]
            ax.barh([i+offset for i in range(len(rows))],[num(r,'share_pct') for r in rows],height=.34,color=color,label=f"{name} (N={int(rows[0]['events']):,})")
        ax.set_yticks(range(len(categories)),[r['label'] for r in categories]);ax.invert_yaxis()
        ax.set_title(labels[field]);ax.set_xlabel('Share of all cohort casualty events (%)');ax.set_xlim(left=0);ax.grid(axis='x',alpha=.2)
        ax.legend(fontsize=9,loc='lower right',frameon=False)
    fig.subplots_adjust(left=.18,right=.98,wspace=.72,top=.88,bottom=.18)
    save(fig,'pooled_weather_surface','Event grain; fatal + injury collisions. Residual Q/QQ other and unknown remain separate.\nNamed zero-count categories are retained; unobserved special-code rows are in the CSV. Shares do not measure exposure-adjusted risk.')
    fig,axes=plt.subplots(2,2,figsize=(13,8))
    fig.suptitle('Selected shares of recorded casualty collisions, 2012–2021',fontsize=16,y=.98)
    specs=[('C_WTHR','4','Snow'),('C_CONF','21','Rear-end'),('C_CONF','31','Head-on'),('HOUR_BAND','00–05','00:00–05:59')]
    for ax,(field,code,title) in zip(axes.flat,specs):
        for cohort,color,name in zip(COHORTS,COLORS,NAMES):
            rows=sorted(match(annual,subset='observed',cohort=cohort,severity='all',field=field,code=code),key=lambda r:int(r['year']))
            ax.plot([int(r['year']) for r in rows],[num(r,'share_pct') for r in rows],color=color,marker='o',markersize=3,label=name)
        ax.set_title(title);ax.set_ylim(bottom=0);ax.set_xticks([2012,2015,2018,2021]);ax.set_ylabel('All-event share (%)');ax.grid(axis='y',alpha=.2)
    axes[0,0].legend(frameon=False,fontsize=9)
    fig.subplots_adjust(left=.08,right=.97,top=.88,bottom=.19,wspace=.27,hspace=.44)
    save(fig,'annual_condition_mix','Each share uses all fatal + injury events in that year and cohort, including unknown/other values in the denominator.\nThese lines show selected categories, not an exhaustive composition. Annual n/N, other and unknown shares are in annual_distributions.csv.')
    fig,ax=plt.subplots(figsize=(13,7))
    codes=['21','31','35','05','QQ','UU']
    all_values=[]
    for offset,cohort,color,name in zip((-.17,.17),COHORTS,COLORS,NAMES):
        rows=[one(fatal,period=PRIMARY,subset='observed',cohort=cohort,field='C_CONF',code=code) for code in codes]
        y=[i+offset for i in range(len(rows))]
        values=[num(r,'fatal_share_pct') for r in rows]
        all_values.extend(v for v in values if v is not None)
        ax.barh(y,values,height=.31,color=color,label=name)
        for yi,value,row in zip(y,values,rows):
            if value is not None:ax.text(value+.3,yi,f"{int(row['fatal_events']):,}/{int(row['category_events']):,}",va='center',fontsize=9,color=color)
    labels_here=[one(primary,cohort='tractor',severity='all',field='C_CONF',code=code)['label'] for code in codes]
    ax.set_yticks(range(len(codes)),labels_here);ax.invert_yaxis();ax.set_xlim(0,max(all_values)*1.35)
    ax.set_xlabel('Fatal / (fatal + injury) events within category (%)');ax.grid(axis='x',alpha=.2)
    ax.legend(frameon=False,loc='lower right');fig.suptitle('Fatal-event shares within selected configurations, 2012–2021',fontsize=16,y=.97)
    fig.subplots_adjust(left=.23,right=.97,top=.87,bottom=.19)
    save(fig,'configuration_fatal_share','Labels are fatal/category events (n/N); all observed event records. Other Q/QQ and unknown UU are separate.\nThis is conditional severity among recorded casualty collisions, not collision risk, person fatality rates or fault.')


if __name__=='__main__':
    report(Path.cwd())
