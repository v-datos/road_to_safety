"""Build collision-level NCDB tables without multiplying events by person rows.

Run from the repository root: PYTHONPATH=src .venv/bin/python -m truck_collisions.build
"""

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import tempfile

import duckdb
from openpyxl import load_workbook


COLUMNS = "C_YEAR C_MNTH C_WDAY C_HOUR C_SEV C_VEHS C_CONF C_RCFG C_WTHR C_RSUR C_RALN C_TRAF V_ID V_TYPE V_YEAR P_ID P_SEX P_AGE P_PSN P_ISEV P_SAFE P_USER C_CASE".split()
COLLISION_FIELDS = [c for c in COLUMNS if c.startswith("C_") and c not in ("C_YEAR", "C_CASE")]
PERSON_FIELDS = "P_SEX P_AGE P_PSN P_ISEV P_SAFE P_USER".split()
TWO_DIGIT = set("C_MNTH C_HOUR C_VEHS C_CONF C_RCFG C_TRAF V_ID V_TYPE P_ID P_AGE P_PSN P_SAFE".split())
FRENCH_HEADERS = dict(zip(
    "C_ANNÉE C_MOIS C_JSEM C_HEURE C_GRAVITÉ C_VÉH C_CFG C_CFGR C_MÉTEO C_ÉCHSÉ C_TRAR C_CIRC V_ID V_TYPE V_ANNÉE P_ID P_SEXE P_ÂGE P_LOCP P_ISEV P_SÉCURITÉ P_USAG C_CAS".split(),
    COLUMNS,
))


def quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def prepare_csv(path, source, temporary):
    """Translate headers/encoding only; keep official originals unchanged."""
    if path.suffix.lower() == ".xlsx":
        workbook = load_workbook(path, read_only=True, data_only=True)
        sheet = workbook[source.get("sheet", workbook.sheetnames[0])]
        target = temporary / (source["id"] + ".csv")
        with target.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            for row in sheet.iter_rows(values_only=True):
                if any(value is not None for value in row):
                    writer.writerow(row)
        workbook.close()
        path = target
    encoding = source.get("encoding", "utf-8-sig") if path.suffix != ".xlsx" else "utf-8-sig"
    # A converted workbook is always UTF-8.
    if source.get("sheet"):
        encoding = "utf-8-sig"
    with path.open(encoding=encoding, newline="") as handle:
        header = next(csv.reader(handle))
    mapped = [FRENCH_HEADERS.get(name.strip(), name.strip()) for name in header]
    if mapped != COLUMNS:
        raise ValueError(f"Unexpected schema in {source['id']}: {mapped}")
    if encoding.lower() not in ("utf-8", "utf-8-sig"):
        target = temporary / (source["id"] + "_utf8.csv")
        with path.open(encoding=encoding, newline="") as original, target.open("w", encoding="utf-8", newline="") as converted:
            for line in original:
                converted.write(line)
        path = target
    return path, header


def rows_as_dicts(connection, sql):
    result = connection.execute(sql)
    names = [column[0] for column in result.description]
    return [dict(zip(names, row)) for row in result.fetchall()]


def export(connection, query, path):
    options = "HEADER, DELIMITER ','" if path.suffix == ".csv" else "FORMAT PARQUET, COMPRESSION ZSTD"
    connection.execute(f"COPY ({query}) TO {quote(path)} ({options})")


def build_dataset(root, sources, output):
    root, output = Path(root), Path(output)
    if len({source['id'] for source in sources}) != len(sources):
        raise ValueError("Source IDs must be unique")
    output.mkdir(parents=True, exist_ok=True)
    staging = output / "staging.duckdb"
    if staging.exists():
        staging.unlink()
    connection = duckdb.connect(str(staging))
    connection.execute("SET memory_limit='2GB'")
    connection.execute("SET threads=2")
    connection.execute("SET preserve_insertion_order=false")
    manifest = []
    try:
        with tempfile.TemporaryDirectory(prefix="ncdb-", dir=output) as temporary:
            for source in sources:
                original = root / source["path"]
                checksum = sha256(original)
                if source.get("sha256") and source["sha256"] != checksum:
                    raise ValueError(f"Checksum mismatch: {original}")
                path, header = prepare_csv(original, source, Path(temporary))
                expressions = []
                for original_name, name in zip(header, COLUMNS):
                    value = 'trim("' + original_name.replace('"', '""') + '")'
                    if name in TWO_DIGIT:
                        value = f"CASE WHEN regexp_full_match({value}, '[0-9]') THEN '0'||{value} ELSE {value} END"
                    expressions.append(f'{value} AS "{name}"')
                query = f"SELECT {quote(source['id'])} AS source_id, {', '.join(expressions)} FROM read_csv({quote(path)}, header=true, all_varchar=true, strict_mode=true)"
                verb = "CREATE TABLE records AS" if not manifest else "INSERT INTO records"
                connection.execute(f"{verb} {query}")
                years = connection.execute("SELECT DISTINCT try_cast(C_YEAR AS INTEGER) FROM records WHERE source_id=? ORDER BY 1", [source["id"]]).fetchall()
                expected = list(range(source["first_year"], source["last_year"] + 1))
                if [row[0] for row in years] != expected:
                    raise ValueError(f"Year coverage mismatch for {source['id']}: {years}")
                manifest.append({**source, "sha256": checksum, "size_bytes": original.stat().st_size})
                print(f"Loaded {source['id']}", flush=True)

        overlap = connection.execute("SELECT C_YEAR FROM records GROUP BY C_YEAR HAVING count(DISTINCT source_id)>1").fetchall()
        if overlap:
            raise ValueError(f"Overlapping source years: {overlap}")
        connection.execute("""CREATE TABLE invalid_key_records AS
            SELECT * FROM records WHERE C_CASE IS NULL OR NOT regexp_full_match(C_CASE, '[0-9]+')
            OR try_cast(C_CASE AS DECIMAL(38,0)) IS NULL OR try_cast(C_CASE AS DECIMAL(38,0)) <= 0
            OR C_YEAR IS NULL OR NOT regexp_full_match(C_YEAR, '[0-9]{4}')""")
        connection.execute("""CREATE TABLE clean AS SELECT DISTINCT * FROM records
            WHERE C_CASE IS NOT NULL AND regexp_full_match(C_CASE, '[0-9]+')
            AND try_cast(C_CASE AS DECIMAL(38,0)) > 0 AND regexp_full_match(C_YEAR, '[0-9]{4}')""")
        connection.execute("""CREATE TABLE input_counts AS
            SELECT source_id,C_YEAR,C_CASE,count(*) AS input_record_rows
            FROM records GROUP BY ALL""")

        for index, field in enumerate(COLLISION_FIELDS):
            query = f"""WITH conflicting_keys AS (
                SELECT source_id,C_YEAR,C_CASE FROM clean GROUP BY source_id,C_YEAR,C_CASE
                HAVING min(coalesce({field},'<NULL>'))<>max(coalesce({field},'<NULL>'))
              ) SELECT source_id,C_YEAR,C_CASE,{quote(field)} AS field,
                string_agg(DISTINCT coalesce({field}, '<NULL>'), '|' ORDER BY coalesce({field}, '<NULL>')) AS values
                FROM clean JOIN conflicting_keys USING(source_id,C_YEAR,C_CASE)
                GROUP BY source_id,C_YEAR,C_CASE"""
            verb = "CREATE TABLE collision_attribute_conflicts AS" if index == 0 else "INSERT INTO collision_attribute_conflicts"
            connection.execute(f"{verb} {query}")
        connection.execute("""CREATE TABLE vehicle_type_conflicts AS
            SELECT source_id,C_YEAR,C_CASE,V_ID,
              string_agg(DISTINCT coalesce(V_TYPE,'<NULL>'), '|' ORDER BY coalesce(V_TYPE,'<NULL>')) AS vehicle_types,
              bool_or(V_TYPE='08') AS involves_tractor_type
            FROM clean WHERE regexp_full_match(V_ID,'[0-9]{2}') AND V_ID BETWEEN '01' AND '98'
            GROUP BY source_id,C_YEAR,C_CASE,V_ID
            HAVING count(DISTINCT coalesce(V_TYPE,'<NULL>'))>1""")
        person_struct = "struct_pack(" + ",".join(f"{field}:={field}" for field in PERSON_FIELDS) + ")"
        connection.execute(f"""CREATE TABLE person_attribute_conflicts AS
            SELECT source_id,C_YEAR,C_CASE,V_ID,P_ID,count(*) AS record_variants
            FROM clean WHERE regexp_full_match(P_ID,'[0-9]{{2}}')
              AND regexp_full_match(V_ID,'[0-9]{{2}}') AND V_ID BETWEEN '01' AND '99'
            GROUP BY source_id,C_YEAR,C_CASE,V_ID,P_ID HAVING min({person_struct}) IS DISTINCT FROM max({person_struct})""")

        attributes = ",\n".join(f"CASE WHEN min(coalesce({field}, '<NULL>'))=max(coalesce({field}, '<NULL>')) THEN min({field}) END AS {field}" for field in COLLISION_FIELDS)
        connection.execute(f"""CREATE TABLE event_aggregates AS
            SELECT source_id,cast(C_YEAR AS INTEGER) AS C_YEAR,C_CASE,{attributes},
              bool_or(coalesce(V_TYPE='08',false)) AS is_road_tractor,
              bool_or(coalesce(V_TYPE='07',false)) AS is_heavy_unit_truck,
              count(DISTINCT V_ID) FILTER (WHERE regexp_full_match(V_ID,'[0-9]{{2}}') AND V_ID BETWEEN '01' AND '98') AS known_vehicle_count,
              count(DISTINCT V_ID) FILTER (WHERE V_TYPE='08' AND regexp_full_match(V_ID,'[0-9]{{2}}') AND V_ID BETWEEN '01' AND '98') AS road_tractor_vehicle_count,
              bool_or(V_TYPE='08' AND NOT coalesce(regexp_full_match(V_ID,'[0-9]{{2}}') AND V_ID BETWEEN '01' AND '98',false)) AS has_unidentified_tractor,
              bool_or(NOT coalesce(regexp_full_match(V_ID,'[0-9]{{2}}') AND V_ID BETWEEN '01' AND '99',false)) AS has_unidentified_vehicle,
              bool_or(NOT coalesce(regexp_full_match(V_TYPE,'[0-9]{{2}}') OR V_TYPE='NN',false)) AS has_unknown_vehicle_type,
              bool_or(coalesce(V_TYPE='NN',false)) AS has_dummy_pedestrian_vehicle,
              bool_or(P_ID='UU' OR P_ID IS NULL) AS has_unknown_person_id,
              bool_or(coalesce(P_ISEV='3',false)) AS fatal_person_record_present,
              count(*) AS distinct_record_rows
            FROM clean GROUP BY source_id,C_YEAR,C_CASE""")
        connection.execute("""CREATE TABLE collisions AS
            WITH joined AS (
              SELECT e.*,i.input_record_rows,
                coalesce(c.conflicts,0) AS collision_attribute_conflict_count,
                coalesce(v.conflicts,0) AS vehicle_type_conflict_count,
                NOT coalesce(v.tractor_conflict,false) AS no_tractor_type_conflict,
                coalesce(p.conflicts,0) AS person_attribute_conflict_count,
                CASE WHEN C_VEHS<>'99' THEN known_vehicle_count - try_cast(C_VEHS AS INTEGER) END AS vehicle_count_difference,
                coalesce(C_VEHS='99',false) AS reported_vehicle_count_top_coded,
                ((C_SEV='1') <> fatal_person_record_present) AS fatality_consistency_warning
              FROM event_aggregates e JOIN input_counts i USING(source_id,C_YEAR,C_CASE)
              LEFT JOIN (SELECT source_id,C_YEAR,C_CASE,count(*) AS conflicts FROM collision_attribute_conflicts GROUP BY ALL) c USING(source_id,C_YEAR,C_CASE)
              LEFT JOIN (SELECT source_id,C_YEAR,C_CASE,count(*) AS conflicts,bool_or(involves_tractor_type) AS tractor_conflict FROM vehicle_type_conflicts GROUP BY ALL) v USING(source_id,C_YEAR,C_CASE)
              LEFT JOIN (SELECT source_id,C_YEAR,C_CASE,count(*) AS conflicts FROM person_attribute_conflicts GROUP BY ALL) p USING(source_id,C_YEAR,C_CASE)
            )
            SELECT *, coalesce(collision_attribute_conflict_count=0 AND C_SEV IN ('1','2'),false) AS is_structurally_valid,
              coalesce(collision_attribute_conflict_count=0 AND C_SEV IN ('1','2') AND no_tractor_type_conflict,false) AS is_analysis_candidate
            FROM joined""")

        # Source issues remain visible; no imputation or benchmark adjustment.
        exports = {
            "collisions.parquet": "SELECT * FROM collisions ORDER BY C_YEAR,C_CASE",
            "road_tractor_collisions.parquet": "SELECT * FROM collisions WHERE is_road_tractor ORDER BY C_YEAR,C_CASE",
            "road_tractor_collisions.csv": "SELECT * FROM collisions WHERE is_road_tractor ORDER BY C_YEAR,C_CASE",
            "road_tractor_collisions_strict.parquet": "SELECT * FROM collisions WHERE is_road_tractor AND is_analysis_candidate ORDER BY C_YEAR,C_CASE",
            "excluded_tractor_collisions.parquet": "SELECT * FROM collisions WHERE is_road_tractor AND NOT is_analysis_candidate ORDER BY C_YEAR,C_CASE",
        }
        for table in ("invalid_key_records", "collision_attribute_conflicts", "vehicle_type_conflicts", "person_attribute_conflicts"):
            exports[table + ".parquet"] = "SELECT * FROM " + table
        for name, query in exports.items():
            export(connection, query, output / name)

        connection.execute("""CREATE TABLE annual_counts AS SELECT C_YEAR AS year,source_id,
            count(*) AS all_casualty_collisions,
            count(*) FILTER (WHERE is_road_tractor) AS observed_tractor_collisions,
            count(*) FILTER (WHERE is_road_tractor AND C_SEV='1') AS observed_fatal_tractor_collisions,
            count(*) FILTER (WHERE is_road_tractor AND C_SEV='2') AS observed_injury_tractor_collisions,
            count(*) FILTER (WHERE is_road_tractor AND is_analysis_candidate) AS strict_tractor_collisions,
            count(*) FILTER (WHERE is_road_tractor AND is_analysis_candidate AND C_SEV='1') AS strict_fatal_tractor_collisions,
            count(*) FILTER (WHERE is_road_tractor AND is_analysis_candidate AND C_SEV='2') AS strict_injury_tractor_collisions,
            sum(road_tractor_vehicle_count) FILTER (WHERE is_road_tractor AND is_analysis_candidate) AS strict_known_tractor_vehicle_involvements,
            count(*) FILTER (WHERE NOT is_structurally_valid) AS invalid_collision_events,
            count(*) FILTER (WHERE is_road_tractor AND NOT is_analysis_candidate) AS excluded_tractor_events
            FROM collisions GROUP BY C_YEAR,source_id ORDER BY C_YEAR""")
        export(connection, "SELECT * FROM annual_counts ORDER BY year", output / "annual_counts.csv")
        export(connection, """SELECT C_YEAR AS year,is_road_tractor,count(*) AS collisions,
            sum(input_record_rows-distinct_record_rows) AS duplicate_record_rows_removed,
            count(*) FILTER (WHERE collision_attribute_conflict_count>0) AS collision_field_conflicts,
            count(*) FILTER (WHERE vehicle_type_conflict_count>0) AS vehicle_type_conflicts,
            count(*) FILTER (WHERE person_attribute_conflict_count>0) AS person_attribute_conflicts,
            count(*) FILTER (WHERE vehicle_count_difference<>0) AS vehicle_count_disagreements,
            count(*) FILTER (WHERE try_cast(C_VEHS AS INTEGER) IS NULL) AS nonnumeric_reported_vehicle_counts,
            count(*) FILTER (WHERE has_unidentified_tractor) AS unidentified_tractor_events,
            count(*) FILTER (WHERE has_unknown_vehicle_type) AS unknown_vehicle_type_events,
            count(*) FILTER (WHERE fatality_consistency_warning) AS fatality_consistency_warnings
            FROM collisions GROUP BY ALL ORDER BY 1,2""", output / "quality_by_year.csv")

        profiles = []
        for field in COLLISION_FIELDS:
            profiles.append(f"SELECT C_YEAR AS year,{quote(field)} AS field,coalesce({field},'<NULL>') AS code,count(*) AS collisions FROM collisions GROUP BY C_YEAR,{field}")
        export(connection, "SELECT * FROM (" + " UNION ALL ".join(profiles) + ") ORDER BY year,field,code", output / "collision_code_profile.csv")
        export(connection, """SELECT cast(C_YEAR AS INTEGER) AS year,V_TYPE,V_ID,count(*) AS person_record_rows
            FROM clean WHERE NOT coalesce(regexp_full_match(V_TYPE,'[0-9]{2}'),false)
              OR NOT coalesce(regexp_full_match(V_ID,'[0-9]{2}') AND V_ID BETWEEN '01' AND '99',false)
            GROUP BY ALL ORDER BY 1,2,3""", output / "special_vehicle_codes.csv")
        export(connection, """SELECT cast(C_YEAR AS INTEGER) AS year,V_TYPE,
            CASE WHEN V_TYPE IN ('01','05','06','07','08','09','10','11','14','16','17','18','19','20','21','22','23') THEN 'defined_vehicle_type'
              WHEN V_TYPE='NN' THEN 'not_applicable_dummy'
              WHEN V_TYPE='QQ' THEN 'other' WHEN V_TYPE='UU' THEN 'unknown'
              WHEN V_TYPE='XX' THEN 'not_provided' ELSE 'unexpected_code' END AS code_class,
            count(*) AS distinct_record_rows,count(DISTINCT C_CASE) AS collision_events
            FROM clean GROUP BY ALL ORDER BY 1,2""", output / "vehicle_type_profile.csv")

        benchmark = root / "data/reference/tractor_collision_benchmark.csv"
        connection.execute(f"""CREATE TABLE reconciliation AS SELECT a.*,
            b.fatal_collisions AS published_fatal,b.injury_collisions AS published_injury,
            a.observed_fatal_tractor_collisions-b.fatal_collisions AS fatal_difference,
            a.observed_injury_tractor_collisions-b.injury_collisions AS injury_difference,
            CASE WHEN b.year IS NULL THEN 'no_tractor_benchmark'
              WHEN a.observed_fatal_tractor_collisions=b.fatal_collisions AND a.observed_injury_tractor_collisions=b.injury_collisions THEN 'exact_match'
              ELSE 'unresolved_difference' END AS external_reconciliation
            FROM annual_counts a LEFT JOIN read_csv_auto({quote(benchmark)},header=true) b USING(year)""")
        export(connection, "SELECT * FROM reconciliation ORDER BY year", output / "reconciliation.csv")
        checks = {
            "collision_key_unique": connection.execute("SELECT count(*)=count(DISTINCT (C_YEAR,C_CASE)) FROM collisions").fetchone()[0],
            "invalid_key_record_rows": connection.execute("SELECT count(*) FROM invalid_key_records").fetchone()[0],
            "invalid_collision_events": connection.execute("SELECT count(*) FROM collisions WHERE NOT is_structurally_valid").fetchone()[0],
            "excluded_tractor_events": connection.execute("SELECT count(*) FROM collisions WHERE is_road_tractor AND NOT is_analysis_candidate").fetchone()[0],
            "external_mismatch_years": [row[0] for row in connection.execute("SELECT year FROM reconciliation WHERE external_reconciliation='unresolved_difference' ORDER BY year").fetchall()],
        }
        summary = {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "duckdb_version": duckdb.__version__,
            "pipeline_sha256": sha256(Path(__file__)),
            "status": "structurally_valid_external_reconciliation_open",
            "scope": "Public NCDB fatal and injury collisions; road tractor V_TYPE=08 with or without semitrailer",
            "checks": checks,
            "source_profile": rows_as_dicts(connection, "SELECT source_id,count(*) AS input_record_rows,count(DISTINCT (C_YEAR,C_CASE)) AS collision_keys FROM records GROUP BY source_id ORDER BY source_id"),
            "annual_counts": rows_as_dicts(connection, "SELECT * FROM reconciliation ORDER BY year"),
        }
        if not checks["collision_key_unique"] or any(checks[k] for k in ("invalid_key_record_rows", "invalid_collision_events", "excluded_tractor_events")):
            summary["status"] = "partial_structural_exclusions_review_required"
        elif not checks["external_mismatch_years"]:
            summary["status"] = "structurally_valid"
        (output / "validation.json").write_text(json.dumps(summary, indent=2) + "\n")
        (output / "source_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        print(json.dumps({"status": summary["status"], "checks": checks}), flush=True)
        return summary
    finally:
        connection.close()
        staging.unlink(missing_ok=True)
        Path(str(staging) + ".wal").unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", default="data/sources.json")
    parser.add_argument("--output", default="data/derived/ncdb")
    args = parser.parse_args()
    root = Path.cwd()
    sources = json.loads((root / args.sources).read_text())
    build_dataset(root, sources, root / args.output)


if __name__ == "__main__":
    main()
