"""Collision-level feature availability, rare groups and release-year stability.

Run: python -m road_to_safety.analyze_stability
All percentages are conditional on the archived fatal/injury collision releases.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import duckdb
import pandas as pd

FEATURES = 'C_MNTH C_WDAY C_HOUR C_RCFG C_WTHR C_RSUR C_RALN C_TRAF'.split()
CLASSES = ['stated', 'unknown', 'other', 'jurisdiction_unavailable', 'not_applicable',
           'conflict', 'null', 'blank', 'unresolved_star_code', 'out_of_domain']


def fingerprint(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def classify(value, conflict, domain):
    if conflict:
        return 'conflict'
    if value is None:
        return 'null'
    if value == '':
        return 'blank'
    if value not in domain:
        return 'unresolved_star_code' if '*' in value else 'out_of_domain'
    if set(value) == {'U'}:
        return 'unknown'
    if set(value) == {'X'}:
        return 'jurisdiction_unavailable'
    if set(value) == {'Q'}:
        return 'other'
    if set(value) == {'N'}:
        return 'not_applicable'
    return 'stated'


def run(root: Path):
    root = Path(root).resolve()
    receipt = json.loads((root/'data/derived/prepared_validation.json').read_text())
    assert receipt['status'] == 'passed' and not receipt['failures']
    for name in ['data/derived/collisions.parquet', 'data/reference/modeling_contract.json',
                 'data/derived/preparation_manifest.json']:
        assert fingerprint(root/name) == receipt['input_fingerprints'][name], name
    assert fingerprint(root/'reports/tables/validation_annual.csv') == receipt['tables']['reports/tables/validation_annual.csv']
    manifest = json.loads((root/'data/derived/preparation_manifest.json').read_text())
    missingness_hash = next(item['sha256'] for item in manifest['outputs'] if item['path'] == 'reports/tables/preparation_missingness.csv')
    assert fingerprint(root/'reports/tables/preparation_missingness.csv') == missingness_hash
    contract = json.loads((root/'data/reference/modeling_contract.json').read_text())
    assert contract['features'] == FEATURES
    connection = duckdb.connect()
    connection.read_parquet(str(root/'data/derived/collisions.parquet')).create_view('collisions')
    annual = connection.execute('SELECT source_id,C_YEAR AS year,count(*) collisions,sum(is_fatal)::BIGINT fatal_collisions FROM collisions GROUP BY ALL ORDER BY year').df()
    expected = pd.read_csv(root/'reports/tables/validation_annual.csv', dtype={'C_YEAR': str})
    actual = annual.rename(columns={'year': 'C_YEAR'})[['source_id','C_YEAR','collisions','fatal_collisions']]
    pd.testing.assert_frame_equal(actual.reset_index(drop=True), expected[actual.columns].reset_index(drop=True), check_dtype=False)
    assert connection.execute('SELECT count(*) FROM collisions WHERE NOT severity_eligible OR is_fatal IS NULL').fetchone()[0] == 0
    values = []
    for field in FEATURES:
        groups = connection.execute(f'SELECT source_id,C_YEAR AS year,{field} AS code,{field}_conflict AS conflict,count(*) collisions,sum(is_fatal)::BIGINT fatal_collisions FROM collisions GROUP BY ALL').df()
        domain = contract['categorical_domains'][field]
        for row in groups.to_dict('records'):
            row.update(field=field, value_class=classify(row['code'], row['conflict'], domain), observed=True)
            values.append(row)
        # Explicit zero rows distinguish unsupported observations from supported but unobserved codes.
        for source in annual.to_dict('records'):
            present = set(groups.loc[groups.year == source['year'], 'code'])
            for code in domain:
                if code not in present:
                    values.append(dict(source_id=source['source_id'],year=source['year'],code=code,conflict=False,
                                       collisions=0,fatal_collisions=0,field=field,
                                       value_class=classify(code,False,domain),observed=False))
    values = pd.DataFrame(values).merge(annual[['source_id','year','collisions']].rename(columns={'collisions':'collision_denominator'}), on=['source_id','year'], validate='many_to_one')
    values['collision_share'] = values.collisions / values.collision_denominator
    values['fatal_proportion'] = values.fatal_collisions.div(values.collisions.where(values.collisions > 0))
    values = values.sort_values(['year','field','code'],kind='stable').reset_index(drop=True)
    # Reconcile every observed value, including original sentinel identity, with preparation evidence.
    preparation = pd.read_csv(root/'reports/tables/preparation_missingness.csv',dtype=str,keep_default_na=False)
    wanted = {(r.observed_year,r.field,r.value,r.value_class == 'conflict'):int(r.collisions) for r in preparation[preparation.field.isin(FEATURES)].itertuples()}
    got = {(r.year,r.field,'' if r.code is None else r.code,bool(r.conflict)):int(r.collisions) for r in values[values.observed].itertuples()}
    assert got == wanted, 'Prepared feature value reconciliation failed'
    quality_rows = []
    for (year,field), rows in values.groupby(['year','field'],sort=True):
        denominator = int(rows.collision_denominator.iloc[0])
        for cls in CLASSES:
            subset = rows[rows.value_class == cls]
            quality_rows.append(dict(year=year,field=field,value_class=cls,collisions=int(subset.collisions.sum()),fatal_collisions=int(subset.fatal_collisions.sum()),collision_denominator=denominator))
    quality = pd.DataFrame(quality_rows)
    pooled = quality.groupby(['field','value_class'],as_index=False)[['collisions','fatal_collisions']].sum()
    pooled['year'] = 'ALL'
    pooled['collision_denominator'] = int(annual.collisions.sum())
    quality = pd.concat([quality,pooled],ignore_index=True)
    quality['collision_share'] = quality.collisions/quality.collision_denominator
    # Fully stated means numeric dictionary-supported codes for all eight fields.
    clauses = []
    for field in FEATURES:
        codes = [code for code in contract['categorical_domains'][field] if code.isdigit()]
        clauses.append(f"({field} IN ({','.join(repr(code) for code in codes)}) AND NOT {field}_conflict)")
    complete = connection.execute('SELECT source_id,C_YEAR AS year,count(*) collisions,sum(is_fatal)::BIGINT fatal_collisions,sum(CASE WHEN '+ ' AND '.join(clauses) +' THEN 1 ELSE 0 END)::BIGINT fully_stated_collisions,sum(CASE WHEN '+ ' AND '.join(clauses) +' THEN is_fatal ELSE 0 END)::BIGINT fully_stated_fatal_collisions FROM collisions GROUP BY ALL ORDER BY year').df()
    pooled_complete = complete.drop(columns=['source_id','year']).sum().to_dict()
    complete = pd.concat([complete,pd.DataFrame([dict(source_id='ALL',year='ALL',**pooled_complete)])],ignore_index=True)
    complete['not_fully_stated_collisions'] = complete.collisions-complete.fully_stated_collisions
    complete['fully_stated_share'] = complete.fully_stated_collisions/complete.collisions
    complete['all_fatal_proportion'] = complete.fatal_collisions/complete.collisions
    complete['fully_stated_fatal_proportion'] = complete.fully_stated_fatal_collisions/complete.fully_stated_collisions
    complete['not_fully_stated_fatal_proportion'] = (complete.fatal_collisions-complete.fully_stated_fatal_collisions)/complete.not_fully_stated_collisions
    sparse = values.copy()
    sparse['small_collision_count'] = sparse.collisions < 100
    sparse['small_fatal_count'] = sparse.fatal_collisions < 5
    sparse['sparse'] = sparse.small_collision_count | sparse.small_fatal_count
    changes = []
    for field, rows in values.groupby('field'):
        for before,after in zip(annual.year.iloc[:-1],annual.year.iloc[1:]):
            a = rows[rows.year == before].set_index('code').collision_share
            b = rows[rows.year == after].set_index('code').collision_share
            delta = b.subtract(a,fill_value=0)
            code = delta.abs().idxmax()
            changes.append(dict(field=field,previous_year=before,year=after,total_variation_distance=float(delta.abs().sum()/2),largest_shift_code=code,largest_shift_percentage_points=float(delta[code]*100)))
    changes = pd.DataFrame(changes)
    assert all(values.groupby(['year','field']).collisions.sum().to_numpy() == values.groupby(['year','field']).collision_denominator.first().to_numpy())
    tables = root/'reports/tables'
    tables.mkdir(parents=True,exist_ok=True)
    outputs = {'eda_quality_values.csv':values,'eda_quality_missingness.csv':quality,
               'eda_quality_complete_cases.csv':complete,'eda_quality_year_changes.csv':changes,
               'eda_sparse_categories.csv':sparse}
    for name,table in outputs.items():
        table.to_csv(tables/name,index=False)
    plot_quality(root,quality,complete)
    write_findings(root,annual,quality,complete,sparse,changes)
    return {'status':'passed','collisions':int(annual.collisions.sum()),'fatal_collisions':int(annual.fatal_collisions.sum()),
            'complete_case_collisions':int(pooled_complete['fully_stated_collisions']),
            'input_sha256':fingerprint(root/'data/derived/collisions.parquet'),
            'checks':['validated input fingerprints','annual counts and target counts agree','all observed values agree with preparation_missingness','feature denominators conserved'],
            'tables':{name:len(table) for name,table in outputs.items()}}


def plot_quality(root,quality,complete):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    figures = root/'reports/figures'
    figures.mkdir(parents=True,exist_ok=True)
    unknown = quality[(quality.year != 'ALL') & (quality.value_class == 'unknown')].pivot(index='field',columns='year',values='collision_share').reindex(FEATURES)*100
    fig,ax=plt.subplots(figsize=(13,5),layout='constrained')
    im=ax.imshow(unknown.to_numpy(),aspect='auto',cmap='YlOrRd',vmin=0)
    ax.set_xticks(range(len(unknown.columns)),unknown.columns,rotation=45,ha='right')
    ax.set_yticks(range(len(FEATURES)),FEATURES)
    ax.set_title('Unknown-coded feature values by release year',loc='left',weight='bold')
    ax.set_xlabel('Collision year (selected annual release)')
    fig.colorbar(im,ax=ax,label='% of that year’s candidate collisions')
    fig.savefig(figures/'quality_unknown_by_year.png',dpi=180)
    plt.close(fig)
    annual=complete[complete.year!='ALL']
    fig,axes=plt.subplots(1,2,figsize=(13,4.5),layout='constrained')
    years=annual.year.astype(int)
    axes[0].plot(years,annual.fully_stated_share*100,marker='o',color='#246a73')
    axes[0].set_ylim(0,100)
    axes[0].set_ylabel('% of candidate collisions')
    axes[0].set_title('All eight features have stated numeric codes',loc='left',weight='bold')
    for col,label,color in [('all_fatal_proportion','All collisions','#666666'),('fully_stated_fatal_proportion','All eight stated','#246a73'),('not_fully_stated_fatal_proportion','At least one non-stated','#b55b35')]:
        axes[1].plot(years,annual[col]*100,label=label,color=color)
    axes[1].set_ylabel('Fatal-collision proportion (%)')
    axes[1].set_title('Complete-case selection changes the sample',loc='left',weight='bold')
    axes[1].legend(frameon=False,fontsize=9)
    for ax in axes:
        ax.set_xlabel('Collision year')
        ax.set_xticks([1999, 2005, 2010, 2015, 2021])
        ax.grid(alpha=.2)
    fig.savefig(figures/'quality_complete_cases.png',dpi=180)
    plt.close(fig)


def write_findings(root,annual,quality,complete,sparse,changes):
    pooled=complete[complete.year=='ALL'].iloc[0]
    q=quality[quality.year=='ALL']
    n=int(pooled.collisions)
    lines=['# Feature availability, sparse groups and source-year stability','',
           'This descriptive analysis uses the validated collision-level table only: one candidate collision per selected source, year and case. It covers 1999–2021, all released road users, and fatal/injury collisions only. It does not estimate the chance of a collision occurring, individual death risk, or causal effects. Counts describe this archived release selection; they are not substituted for later national statistical revisions.','',
           '## Definitions and reproducibility','',
           '`python -m road_to_safety.analyze_stability` recomputes all accompanying CSVs, figures and this document. The routine verifies the prepared-validation success receipt, collision/contract/preparation-manifest hashes, the annual evidence hash, and the preparation-missingness hash. Every observed year–field–value count reconciles exactly to preparation evidence; annual collision/fatal counts reconcile exactly to independent validation. No input, target or prepared dataset is changed.','',
           'Unknown (`U/UU`), other (`Q/QQ`), jurisdiction unavailable (`X/XX`), documented not applicable, blank, null, conflict and out-of-domain states are separate. A numeric dictionary-supported value is “stated.” Other is an observed category, not silently imputed or combined with unknown. Zero-count supported codes are enumerated so absence of observations is explicit. Denominators are all candidate collisions in the same source year, or all collisions for pooled rows. Percentages in CSVs are fractions, except explicitly named percentage-point changes.','',
           'A year–field–category is flagged sparse when its collision count is <100 **or** its fatal count is <5. These are predeclared descriptive warning thresholds, not exclusion criteria, disclosure rules or significance tests. Flags include non-stated categories; unobserved supported codes are distinguished by `observed=False`. The same collision can appear in eight feature summaries, so feature-level counts must not be added to estimate distinct collisions.','',
           '## Pooled feature availability','',
           '| Feature | Stated | Unknown | Other | Remaining states | Unknown % |',
           '|---|---:|---:|---:|---:|---:|']
    for field in FEATURES:
        part=q[q.field==field].set_index('value_class').collisions
        remaining=int(part.drop(['stated','unknown','other']).sum())
        lines.append(f'| {field} | {int(part.stated):,} | {int(part.unknown):,} | {int(part.other):,} | {remaining:,} | {part.unknown/n*100:.4f} |')
    lines+=['',f'Total: **{n:,} candidate collisions**, **{int(pooled.fatal_collisions):,} fatal**, fatal proportion **{pooled.all_fatal_proportion*100:.4f}%**. All eight predictor domains have zero conflicts, blanks, nulls, jurisdiction-unavailable, documented-not-applicable, star-code and out-of-domain observations in this selected dataset. Dictionary-supported but unobserved sentinel codes remain explicitly present as zero rows.','',
            '## Complete-case sensitivity (diagnostic only)','',
            f'Requiring all eight numeric stated codes retains **{int(pooled.fully_stated_collisions):,} collisions ({pooled.fully_stated_share*100:.4f}%)** and would remove **{int(pooled.not_fully_stated_collisions):,} ({(1-pooled.fully_stated_share)*100:.4f}%)**. The retained set has **{int(pooled.fully_stated_fatal_collisions):,} fatal collisions**, fatal proportion **{pooled.fully_stated_fatal_proportion*100:.4f}%**; collisions with at least one non-stated feature have fatal proportion **{pooled.not_fully_stated_fatal_proportion*100:.4f}%**. This composition difference means complete-case exclusion would change the analytical population. It is not evidence that missingness causes severity. Unknown and other categories remain available for downstream modeling; no complete-case filter is applied.','',
            '| Year | All collisions | Fatal | All-eight-stated % | All fatal % | Stated-set fatal % | Non-stated-set fatal % |',
            '|---|---:|---:|---:|---:|---:|---:|']
    for row in complete[complete.year!='ALL'].itertuples():
        lines.append(f'| {row.year} | {row.collisions:,} | {row.fatal_collisions:,} | {row.fully_stated_share*100:.3f} | {row.all_fatal_proportion*100:.3f} | {row.fully_stated_fatal_proportion*100:.3f} | {row.not_fully_stated_fatal_proportion*100:.3f} |')
    lines+=['','## Unknown-code variation across releases','',
            '| Feature | Lowest unknown % (year) | Highest unknown % (year) | 2019 % | 2020 % | 2021 % |','|---|---:|---:|---:|---:|---:|']
    for field in FEATURES:
        part=quality[(quality.field==field)&(quality.year!='ALL')&(quality.value_class=='unknown')].set_index('year').collision_share
        lines.append(f'| {field} | {part.min()*100:.4f} ({part.idxmin()}) | {part.max()*100:.4f} ({part.idxmax()}) | {part["2019"]*100:.4f} | {part["2020"]*100:.4f} | {part["2021"]*100:.4f} |')
    lines+=['','## Sparse and unobserved groups','',
            '| Feature | Observed year-category groups | Observed sparse | Observed sparse numeric stated | Unobserved supported year-category groups |',
            '|---|---:|---:|---:|---:|']
    for field in FEATURES:
        part=sparse[sparse.field==field]
        lines.append(f'| {field} | {int(part.observed.sum()):,} | {int((part.observed & part['sparse']).sum()):,} | {int((part.observed & part['sparse'] & (part.value_class=="stated")).sum()):,} | {int((~part.observed).sum()):,} |')
    lines+=['','The complete `eda_sparse_categories.csv` includes every supported code for every year, observed indicators, both sparse triggers, collision/fatal counts, denominators, category shares and conditional fatal proportions. A zero-count group has a blank fatal proportion. Sparse groups should retain warning flags in charts and model evaluation; avoid ranking them as stable high-risk conditions. No p-values or significance claims are made.','',
            '## Distribution changes and late-period checks','',
            'For each feature and adjacent pair of years, total variation distance is one half the sum of absolute changes in category shares, including non-stated states. It ranges from 0 (same composition) to 1 (disjoint composition). This is a descriptive compositional distance, not a causal estimate or a hypothesis test. The table lists the largest adjacent-year change per feature; full adjacent comparisons are in `eda_quality_year_changes.csv`.','',
            '| Feature | Previous → current | Total variation | Largest changing code | Change (percentage points) |',
            '|---|---|---:|---|---:|']
    for field in FEATURES:
        row=changes[changes.field==field].sort_values('total_variation_distance',ascending=False).iloc[0]
        lines.append(f'| {field} | {row.previous_year} → {row.year} | {row.total_variation_distance:.5f} | {row.largest_shift_code} | {row.largest_shift_percentage_points:+.4f} |')
    lines+=['','| Feature | 2019 → 2020 total variation | 2020 → 2021 total variation |','|---|---:|---:|']
    for field in FEATURES:
        part=changes[changes.field==field].set_index('year')
        lines.append(f'| {field} | {part.loc["2020","total_variation_distance"]:.5f} | {part.loc["2021","total_variation_distance"]:.5f} |')
    a=annual.set_index('year')
    for before,after in [('2019','2020'),('2020','2021')]:
        lines+=['',f'{before} → {after}: collision count changes from **{a.loc[before,"collisions"]:,} to {a.loc[after,"collisions"]:,} ({(a.loc[after,"collisions"]/a.loc[before,"collisions"]-1)*100:+.3f}%)**; fatal collisions change from **{a.loc[before,"fatal_collisions"]:,} to {a.loc[after,"fatal_collisions"]:,} ({(a.loc[after,"fatal_collisions"]/a.loc[before,"fatal_collisions"]-1)*100:+.3f}%)**.']
    lines+=['','Treat 2020–2021 as a distinct late-period sensitivity. Archived file formats/languages also differ (2020 CSV; 2021 French CSV). The preparation process normalized bilingual headers and numeric formatting and independently validated values. These observations cannot attribute changes to travel exposure, reporting practice, source vintage or real severity changes. There are no travel-exposure denominators or provincial fields in this table. Annual stratification and future chronological validation are needed; pooled feature associations must not be presented as invariant across years.','',
            '## Artifacts and practical implications','',
            '- `reports/tables/eda_quality_values.csv`: collision-level category counts and shares, annual denominators and source IDs, including zero supported codes.',
            '- `reports/tables/eda_quality_missingness.csv`: annual and pooled separate availability classes for each predictor.',
            '- `reports/tables/eda_quality_complete_cases.csv`: annual/pooled complete-case sensitivity; no records excluded.',
            '- `reports/tables/eda_quality_year_changes.csv`: every adjacent-year distribution distance and largest category change.',
            '- `reports/tables/eda_sparse_categories.csv`: full category grid and transparent sparse flags.',
            '- `reports/figures/quality_unknown_by_year.png`: unknown-code percentages using annual collision denominators.',
            '- `reports/figures/quality_complete_cases.png`: completeness and severity-composition sensitivity.',
            '',f'Input collision SHA256: `{fingerprint(root/"data/derived/collisions.parquet")}`.',
            '', 'Proceed with explicit categorical unknown/other handling, sparse-group flags, and year-aware interpretation. Keep all target-valid events. The next modeling design should fix chronological development/validation/test periods before fitting transforms and compare temporal stability and calibration; none of these exploratory summaries establishes an operational forecasting model.','']
    (root/'docs/stability_findings.md').write_text('\n'.join(lines))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    args=parser.parse_args()
    print(json.dumps(run(args.root),indent=2))


if __name__ == '__main__':
    main()
