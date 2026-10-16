# Source selections and preserved baseline

`../sources.json` is the active production selection. A source ID identifies one physical release, not merely a calendar year. The manifest pins original bytes by SHA256. It is permissible to select only explicitly listed `selected_years` from a multi-year source; its original `first_year`/`last_year` coverage is still checked before selection. Replacement annual files must not overlap selected legacy years.

## Baseline before the source-version repair

- Git commit: `c7baeb3` (`feat: initialize Canadian truck collision analysis project`).
- `baseline_c7baeb3.json`: the original five-source selection, including the 2019 CSV.
- `baseline_output_manifest.json`: file sizes and SHA256 hashes of the saved outputs and project archive.
- Local snapshot: `data/derived/baselines/pre_source_revision_20261015/`. It contains collision/person outputs, reports, executed notebooks, the source selection, a Git archive, and its manifest. This generated snapshot is excluded from Git.
- Raw originals remain at their original paths. Neither the inherited extract nor the old 2019 CSV is overwritten or deleted.

Case numbers may change meaning across official exports. Compare releases using independently computed annual/group results; never join or merge them on case number to infer additions, removals or specific people. Collision keys are unique within the active one-source-per-year selection; cross-release keys must also include `source_id`. Person keys already include source identity.

## Reproduce an earlier event selection

```bash
PYTHONPATH=src .venv/bin/python -m truck_collisions.build \
  --sources data/source_releases/baseline_c7baeb3.json \
  --output data/derived/reproduced_baseline/ncdb
```

For the exact earlier code and executed artifacts, use the preserved Git commit/archive and output snapshot. Running an old source selection with newer code is a source comparison, not proof of byte-identical earlier outputs. Preserve current outputs before any rollback. Candidate builds use separate directories and never silently replace production.

`historical_annual_candidates.json` records the annual 2014–2017 sources evaluated in the release audit. Their promotion decision and quality gates are documented in `docs/source_release_audit.md` and `docs/source_release_update.md`. A closer aggregate match alone is insufficient reason to select a source.
