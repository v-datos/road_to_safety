# NCDB source release audit

Audit date: **2026-10-15**. Scope: official public NCDB record resources covering **1999–2021**. This audit does not contact anyone or infer that unpublished data do not exist.

## Evidence and selection rules

The [official NCDB catalogue](https://open.canada.ca/data/en/dataset/1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a) and its [package metadata API](https://open.canada.ca/data/api/action/package_show?id=1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a) enumerate the resources. A fresh successful API response is preserved at `data/raw/ncdb/release_audit_package_metadata.json` (ignored raw evidence). It contains 51 resources; package metadata modification time is `2025-12-17T16:11:47.651332`. Resource creation and modification dates describe catalogue resources; they are not proof of an underlying statistical revision, final status, or publication extract date.

Choose a source using official provenance, documented coverage, schema compatibility, record quality, and reproducibility. Published benchmarks are diagnostic checks, not targets used to choose or alter records. Keep separate releases; never append overlapping releases or assume a shared case ID identifies the same real collision across releases.

The resource-level inventory is [source_release_inventory.csv](../data/reference/source_release_inventory.csv). It includes English and French alternatives, the inherited combined source, dictionary, and the unusable English 2021 catalogue entry. A listed resource is not necessarily a distinct statistical vintage: language and format alternatives can encode identical data.

## Coverage audit

| Years | Official resources found | Selection decision |
|---|---|---|
| 1999–2001 | English/French grouped CSV plus annual English/French XLSX | Retain checksum-pinned inherited extract. Annual/grouped alternatives are catalogued, but their contents have not been validated in this repair; no evidence yet warrants replacement. |
| 2002–2011 | Annual English/French XLSX | Retain checksum-pinned inherited extract. Annual alternatives are catalogued; their contents have not been validated in this repair. |
| 2012–2017 | Annual English/French XLSX | English annual files downloaded and compared: retain inherited 2012–2013 (identical normalized records); promote validated annual 2014–2017 (substantive changes and direct official provenance). |
| 2018 | Annual English/French XLSX | Retain existing official English XLSX; there is no additional dated English release in the current catalogue. French is a language alternative, not established as a revision. |
| 2019 | English/French CSV and English/French XLSX | The later-catalogued English XLSX passed separate collision and person validation and has been promoted. The later catalogue date alone does not establish authority; the residual benchmark difference remains documented. |
| 2020 | English/French CSV | Retain existing English CSV with its pinned checksum. No additional dated English release appears in the current catalogue. |
| 2021 | French CSV; English CSV entry with empty URL | Retain existing French CSV and documented header/encoding translation. An empty URL is not a usable downloadable English source. |

The inherited 1999–2017 file has unknown acquisition date and a recorded SHA-256 checksum. Its legacy URL is preserved as provenance, not evidence that it is the newest extract. Retaining an unvalidated older source is an explicit reproducibility decision; it does not certify that it has no revisions. Metadata coverage has been audited for every available year; full contents have not been exhaustively compared for every language and format.

## Content comparison of 2012–2017

Each official English workbook was downloaded separately without overwriting any existing extract. All 23 canonical columns were compared as a **multiset**, preserving repeated rows. Numeric codes were padded using the production normalization rules; the inherited zero-padded `C_CASE` was converted to its numeric string for this equality check only. This is a file equality diagnostic, not an event linkage procedure. No records are joined across releases to repair identities.

Collision keys are `(year, case)` within each release. Tractor events have at least one `V_TYPE=08` record. Fatal and injury columns refer to unique tractor-involved collisions (`C_SEV=1` and `2`), never person counts or vehicle involvements. The comparison checks raw row counts, distinct rows, unique collision keys, severity conflicts and exact normalized record multiset differences.

| Year | Legacy rows | Annual rows | Legacy collision keys | Annual collision keys | Legacy tractor fatal / injury | Annual tractor fatal / injury | Normalized record multiset |
|---|---:|---:|---:|---:|---:|---:|---|
| 2012 | 322,984 | 322,984 | 124,682 | 124,682 | 197 / 3,103 | 197 / 3,103 | Identical |
| 2013 | 317,149 | 317,149 | 122,132 | 122,132 | 195 / 3,148 | 195 / 3,148 | Identical |
| 2014 | 300,436 | 300,431 | 116,293 | 116,292 | 211 / 3,216 | 211 / 3,216 | Different |
| 2015 | 312,668 | 312,042 | 119,536 | 119,550 | 194 / 2,880 | 194 / 2,881 | Different |
| 2016 | 306,171 | 306,260 | 118,271 | 118,321 | 193 / 2,816 | 193 / 2,817 | Different |
| 2017 | 289,841 | 289,823 | 114,408 | 114,412 | 214 / 2,962 | 216 / 2,962 | Different |

Detailed counts, workbook checksums and directional multiset differences are retained in [source_release_comparison.csv](../data/reference/source_release_comparison.csv). All six workbooks have zero tractor-event collision-severity conflicts.

**Decision:** retain inherited 2012–2013 because normalized record multisets are identical. Promote validated annual 2014–2017: they have directly documented official resource provenance and substantive record changes, with increases and decreases in aggregate record counts. No monotonic count correction or cross-release case matching is applied. The 2013 injury benchmark gap remains after the alternate-file check.

The 2014–2017 candidate source manifest is [historical_annual_candidates.json](../data/source_releases/historical_annual_candidates.json). Candidate collision and person validation runs use the existing production builders in separate ignored outputs at `data/derived/source_revision/historical_2014_2017/`.

## Historical candidate validation result

The existing collision and casualty builders completed successfully for all four annual 2014–2017 candidates, preserving the same counting definitions:

- **12,690 observed tractor events**; event keys unique; zero invalid-key records and zero invalid collision severities.
- Three tractor events retain conflicting vehicle types: one in 2014 and two in 2017. They remain in the observed series and outside the strict sensitivity series. Their keys are release-specific; equal conflict counts do not prove linkage to the old release.
- **33,409 raw person rows**, 33,403 distinct normalized records, and 33,316 identified person keys. Six exact repeated rows were handled explicitly.
- Six person keys have conflicting attributes, including five with conflicting severities. Nine person keys have ambiguous road-user groups. These uncertainties remain visible.
- Twenty-eight raw rows have unresolved identities; 57 rows are dummy people; zero dummy rows claim a positive casualty outcome. No identities were invented.
- Zero event/person row-count mismatches, zero injury events with a fatal identified person, zero invalid event-severity person keys, and zero fatal events without a coded fatal record.
- All four observed tractor event totals match the published fatal/injury benchmark, as a diagnostic result after validation. The match is not a repair rule.

Validation evidence: `data/derived/source_revision/historical_2014_2017/ncdb/validation.json`, the matching `casualties/validation.json`, quality profiles and source manifests. Existing unresolved source-record ambiguity remains; a successful structural run does not prove physical-person identities or statistical completeness. The production source manifest now selects these validated annual 2014–2017 resources and limits the physical legacy 1999–2017 file to selected years 1999–2013. Its physical file coverage and checksum remain unchanged. The full downstream rebuild uses the promoted sources.

## Limits and implications

- The 2019 XLSX does not justify relabelling every June 2023 workbook as a revised or definitive release.
- Alternate annual files can differ in binary format, workbook metadata, or ID formatting without changing statistical content. SHA-256 alone does not establish a content change between CSV and XLSX.
- If a future alternate release differs substantively, run the same collision/person validation and downstream rebuild before changing the selection. Keep the old release and baseline reproducible.
- Residual 2019 benchmark differences remain visible: 196 fatal and 2,579 injury tractor events in the XLSX versus 196 and 2,581 published. The cause of the two-event injury difference is unproven.
- This source audit does not supply missing national 2022–2025 records. See the separate availability register for those years; aggregate totals, vehicle involvements, and provincial records cannot replace missing national event records.
