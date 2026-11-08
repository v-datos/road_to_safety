"""Fit the frozen chronological comparison and resume verified candidate results."""
import argparse
import fcntl
from hashlib import file_digest
from itertools import product
import json
import os
from pathlib import Path
import sys
import time
import warnings

import duckdb
import joblib
from lightgbm import LGBMClassifier
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss
from sklearn.preprocessing import OneHotEncoder

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from road_to_safety.fit_severity import evaluate, validation_threshold

HERE = Path(__file__).resolve().parent
OUTPUT = ROOT / "data/derived/tree_comparison_v1"
TABLES = ROOT / "reports/tables/tree_comparison_v1"
TOL = 1e-10
SEED = 2026
YEARS = list(range(2014, 2020))
KEYS = ["source_id", "C_YEAR", "C_CASE"]
CONTRACT = ROOT / "data/reference/modeling_contract.json"
SOURCE = ROOT / "data/derived/collisions.parquet"
THREADS = min(8, os.cpu_count() or 1)


def digest(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def save_json(path, data):
    pending = path.with_suffix(path.suffix + ".tmp")
    pending.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    pending.replace(path)


def verify_archive():
    verified = set()
    for name in ("severity", "temporal_calibration_v1", "calibration_stress_v1"):
        protocol = json.loads((ROOT / f"data/reference/{name}_protocol.json").read_text())
        for relative, expected in protocol.get("input_fingerprints", protocol.get("input_sha256", {})).items():
            if (relative, expected) not in verified:
                if digest(ROOT / relative) != expected:
                    raise ValueError(f"Archived input fingerprint mismatch: {relative}")
                verified.add((relative, expected))
    print(f"Verified {len(verified)} archived input fingerprints", flush=True)


def protocol():
    configurations = {"prevalence": {}, "logistic": {
        "C": 1.0, "solver": "lbfgs", "max_iter": 1000, "tol": 1e-7,
        "fit_intercept": True, "random_state": SEED,
    }}
    for index, (depth, leaf, features) in enumerate(product([8, 16], [200, 50], ["sqrt", 0.5]), 1):
        configurations[f"rf_{index:02}"] = {
            "n_estimators": 300, "bootstrap": True, "max_depth": depth,
            "min_samples_leaf": leaf, "max_features": features, "random_state": SEED,
            "n_jobs": THREADS,
        }
    for index, (leaves, child, l2) in enumerate(product([15, 31, 63], [500, 100], [1, 0]), 1):
        configurations[f"lgbm_{index:02}"] = {
            "n_estimators": 500, "learning_rate": 0.03, "objective": "binary",
            "num_leaves": leaves, "min_child_samples": child, "reg_lambda": l2,
            "random_state": SEED, "deterministic": True, "force_col_wise": True,
            "n_jobs": THREADS, "verbosity": -1,
        }
    inputs = [SOURCE, CONTRACT, HERE / "uv.lock", Path(__file__),
              ROOT / "src/road_to_safety/fit_severity.py",
              ROOT / "data/reference/severity_protocol.json"]
    return {
        "experiment": "tree_comparison_v1",
        "inputs": {str(path.relative_to(ROOT)): digest(path) for path in inputs},
        "folds": [{"train_start": 1999, "train_end": year - 1, "evaluation": year} for year in YEARS],
        "configurations": configurations,
        "selection_tolerance": TOL,
        "threshold_year": 2019,
        "minimum_recall": 0.8,
        "stress_years": [2020, 2021],
        "permutation_repeats": 5,
    }


def load_data():
    contract = json.loads(CONTRACT.read_text())
    features = contract["features"]
    with duckdb.connect(config={"threads": "4"}) as connection:
        frame = connection.execute(
            "SELECT source_id, C_YEAR::INTEGER AS C_YEAR, C_CASE, is_fatal, severity_eligible, "
            + ", ".join(features) + " FROM read_parquet(?) ORDER BY C_YEAR, source_id, C_CASE",
            [str(SOURCE)],
        ).df()
    if (len(frame) != 2949846 or frame[KEYS].duplicated().any()
            or not frame.severity_eligible.all() or not frame.is_fatal.isin([0, 1]).all()
            or int(frame.is_fatal.sum()) != 47793 or set(frame.C_YEAR) != set(range(1999, 2022))):
        raise ValueError("Unexpected collision population")
    domains = contract["categorical_domains"]
    for feature in features:
        if not frame[feature].isin(domains[feature]).all():
            raise ValueError(f"Unexpected category in {feature}")
    references = json.loads((ROOT / "data/reference/severity_protocol.json").read_text())["reference_levels"]
    encoder = OneHotEncoder(
        categories=[domains[name] for name in features], drop=[references[name] for name in features],
        handle_unknown="error", dtype=np.float32,
    )
    return frame, features, encoder


def fit_model(name, params, x, y):
    if name == "prevalence":
        return float(y.mean())
    if name == "logistic":
        estimator = LogisticRegression(**params)
    elif name.startswith("rf_"):
        estimator = RandomForestClassifier(**params)
    else:
        estimator = LGBMClassifier(**params)
    with warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        estimator.fit(x, y)
    return estimator


def predict(model, x):
    if isinstance(model, float):
        return np.full(x.shape[0], model)
    if isinstance(model, LGBMClassifier):
        return model.booster_.predict(x, num_threads=THREADS)
    return model.predict_proba(x)[:, 1]


def scores(y, p):
    if not (np.isfinite(p).all() and ((0 <= p) & (p <= 1)).all()):
        raise ValueError("Invalid probabilities")
    return {"log_loss": float(log_loss(y, p, labels=[0, 1])), "brier_score": float(brier_score_loss(y, p))}


def candidate(folder, name, params, x_train, y_train, x_eval, y_eval, protocol_hash):
    marker = folder / f"{name}.json"
    model_file = folder / f"{name}.joblib"
    pred_file = folder / f"{name}.npy"
    if marker.exists():
        saved = json.loads(marker.read_text())
        if (saved["protocol_sha256"] != protocol_hash
                or saved["model_sha256"] != digest(model_file)
                or saved["prediction_sha256"] != digest(pred_file)):
            raise ValueError(f"Candidate fingerprint mismatch: {marker}")
        return saved
    start = time.monotonic()
    model = fit_model(name, params, x_train, y_train)
    p = predict(model, x_eval)
    row = scores(y_eval, p)
    joblib.dump(model, model_file, compress=1)
    np.save(pred_file, p, allow_pickle=False)
    row.update(protocol_sha256=protocol_hash, model_sha256=digest(model_file),
               prediction_sha256=digest(pred_file), train_n=len(y_train), n=len(y_eval),
               fatal=int(y_eval.sum()), seconds=round(time.monotonic() - start, 2),
               parameters=model.get_params() if not isinstance(model, float) else {})
    save_json(marker, row)
    print(f"{folder.name} {name} completed in {row['seconds']} seconds", flush=True)
    return row


def select(grid, configurations):
    macro = grid.groupby("configuration")[["log_loss", "brier_score"]].mean()
    decision = {}
    logistic = grid[grid.configuration.eq("logistic")].set_index("year")
    for family in ("rf", "lgbm"):
        ids = [key for key in configurations if key.startswith(family + "_")]
        best_loss = macro.loc[ids, "log_loss"].min()
        tied = [key for key in ids if macro.at[key, "log_loss"] <= best_loss + TOL]
        best_brier = macro.loc[tied, "brier_score"].min()
        winner = next(key for key in tied if macro.at[key, "brier_score"] <= best_brier + TOL)
        deltas = grid[grid.configuration.eq(winner)].set_index("year").log_loss - logistic.log_loss
        decision[family] = {
            "configuration": winner, "macro_log_loss": float(macro.at[winner, "log_loss"]),
            "macro_brier_score": float(macro.at[winner, "brier_score"]),
            "annual_log_loss_wins": int((deltas < -TOL).sum()),
            "passes_development_gate": bool(deltas.mean() < -TOL and (deltas < -TOL).sum() >= 4
                and macro.at[winner, "brier_score"] <= macro.at["logistic", "brier_score"] + TOL),
        }
    return decision


def subgroup_masks(frame, features):
    values = frame[features]
    for label, codes in (("unknown", ["U", "UU"]), ("other", ["Q", "QQ"]),
                         ("unavailable", ["X", "XX"])):
        present = values.isin(codes).any(axis=1).to_numpy()
        yield f"any_{label}", present
        yield f"no_{label}", ~present


def finish(frame, features, encoder, target, year, grid, frozen, protocol_hash):
    decision = select(grid, frozen["configurations"])
    selected = ["prevalence", "logistic", *(row["configuration"] for row in decision.values())]
    dev_2019 = year == 2019
    thresholds = {
        name: validation_threshold(target[dev_2019], np.load(OUTPUT / "2019" / f"{name}.npy"))
        for name in selected
    }
    selection = {"protocol_sha256": protocol_hash, "development": decision, "thresholds": thresholds}
    frozen_selection = OUTPUT / "selection.json"
    if frozen_selection.exists() and json.loads(frozen_selection.read_text()) != selection:
        raise ValueError("Selection differs from frozen development result")
    if not frozen_selection.exists():
        save_json(frozen_selection, selection)

    encoder.fit(frame.loc[year < 2019, features])
    joblib.dump(encoder, OUTPUT / "encoder.joblib", compress=1)
    stress = year >= 2020
    stress_frame = frame.loc[stress].reset_index(drop=True)
    stress_matrix = encoder.transform(stress_frame[features])
    stress_targets = target[stress]
    predictions = stress_frame[KEYS].copy()
    predictions["is_fatal"] = stress_targets
    metrics, calibration, importance, dev_metrics = [], [], [], []
    stress_years = stress_frame.C_YEAR.to_numpy()
    for name in selected:
        model = joblib.load(OUTPUT / "2019" / f"{name}.joblib")
        probability = predict(model, stress_matrix)
        scores(stress_targets, probability)
        predictions[name] = probability
        for label, mask in (("pooled", np.ones(len(stress_frame), dtype=bool)),
                            *((str(y), stress_years == y) for y in [2020, 2021])):
            y, p = stress_targets[mask], probability[mask]
            row = evaluate(y, p, thresholds[name])
            metrics.append({"model": name, "period": label, "group": "all",
                            **row, "flagged_fraction": float((p >= thresholds[name]).mean())})
            if label != "pooled":
                for group, included in subgroup_masks(stress_frame.loc[mask], features):
                    if included.any():
                        result = evaluate(y[included], p[included], thresholds[name])
                        metrics.append({"model": name, "period": label, "group": group, **result,
                                        "flagged_fraction": float((p[included] >= thresholds[name]).mean())})
            edges = [0, .005, .01, .015, .02, .03, .05, .1, .2, .3, .5, 1.0]
            indices = np.searchsorted(edges[1:-1], p, side="right")
            for index, (lo, hi) in enumerate(zip(edges, edges[1:])):
                inside = indices == index
                count = int(inside.sum())
                calibration.append({"model": name, "period": label, "lower": lo, "upper": hi,
                    "n": count, "fatal": int(y[inside].sum()),
                    "mean_prediction": float(p[inside].mean()) if count else None,
                    "observed": float(y[inside].mean()) if count else None})
    with duckdb.connect() as connection:
        connection.register("predictions", predictions)
        connection.execute("COPY predictions TO ? (FORMAT PARQUET)", [str(OUTPUT / "stress_predictions.parquet")])
    for fold_year in YEARS:
        mask = year == fold_year
        observed = target[mask]
        data = frame.loc[mask, features].reset_index(drop=True)
        for name in selected:
            original = np.load(OUTPUT / str(fold_year) / f"{name}.npy")
            row = evaluate(observed, original, thresholds[name] if fold_year == 2019 else 0.5)
            dev_metrics.append({"year": fold_year, "model": name, **row})
            if name == "prevalence":
                continue
            model = joblib.load(OUTPUT / str(fold_year) / f"{name}.joblib")
            base_loss = row["log_loss"]
            for index, feature in enumerate(features):
                original_values = data[feature].copy()
                for repeat in range(5):
                    rng = np.random.default_rng(np.random.SeedSequence([SEED, fold_year, index, repeat]))
                    data[feature] = rng.permutation(original_values.to_numpy())
                    p = predict(model, encoder.transform(data))
                    importance.append({"year": fold_year, "model": name, "feature": feature,
                        "repeat": repeat + 1, "delta_log_loss": log_loss(observed, p, labels=[0, 1]) - base_loss})
                data[feature] = original_values
        print(f"{fold_year} selected-model permutation analysis complete", flush=True)
    for filename, rows in (("stress_metrics", metrics), ("stress_calibration", calibration),
                           ("permutation_importance", importance), ("development_metrics", dev_metrics)):
        pd.DataFrame(rows).to_csv(TABLES / f"{filename}.csv", index=False)
    print(json.dumps(selection, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-archive", action="store_true")
    args = parser.parse_args()
    verify_archive()
    if args.verify_archive:
        return
    OUTPUT.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / "run.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        frozen = protocol()
        spec = OUTPUT / "protocol.json"
        if spec.exists() and json.loads(spec.read_text()) != frozen:
            raise ValueError("Existing run protocol or inputs differ")
        if not spec.exists():
            save_json(spec, frozen)
        protocol_hash = digest(spec)
        frame, features, encoder = load_data()
        target = frame.is_fatal.to_numpy(dtype=np.uint8)
        year = frame.C_YEAR.to_numpy()
        grid = []
        for fold_year in YEARS:
            train, test = year < fold_year, year == fold_year
            x_train = encoder.fit_transform(frame.loc[train, features]).tocsc()
            x_eval = encoder.transform(frame.loc[test, features])
            folder = OUTPUT / str(fold_year)
            folder.mkdir(exist_ok=True)
            for name, params in frozen["configurations"].items():
                row = candidate(folder, name, params, x_train, target[train], x_eval, target[test], protocol_hash)
                grid.append({"year": fold_year, "configuration": name,
                    **{k: row[k] for k in ("train_n", "n", "fatal", "log_loss", "brier_score", "seconds")}})
            del x_train, x_eval
        grid = pd.DataFrame(grid)
        grid.to_csv(TABLES / "development_grid.csv", index=False)
        finish(frame, features, encoder, target, year, grid, frozen, protocol_hash)


if __name__ == "__main__":
    main()
