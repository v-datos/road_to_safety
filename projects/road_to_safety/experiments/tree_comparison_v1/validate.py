"""Reconcile the full experiment from saved probabilities and the pinned event table."""
import argparse
import json

import duckdb
import joblib
import numpy as np
import pandas as pd
from scipy.stats import rankdata

from run import OUTPUT, ROOT, SOURCE, TABLES, digest, load_data, predict, save_json

EPSILON = np.finfo(np.float64).eps


def independent_scores(labels, probabilities):
    assert np.isfinite(probabilities).all() and np.all((probabilities >= 0) & (probabilities <= 1))
    clipped = np.clip(probabilities, EPSILON, 1 - EPSILON)
    loss = -np.mean(np.where(labels == 1, np.log(clipped), np.log1p(-clipped)))
    brier = np.mean(np.square(probabilities - labels))
    return float(loss), float(brier)


def close(left, right):
    np.testing.assert_allclose(left, right, rtol=0, atol=1e-11)


def validate():
    spec_path = OUTPUT / "protocol.json"
    protocol = json.loads(spec_path.read_text())
    for relative, expected in protocol["inputs"].items():
        assert digest(ROOT / relative) == expected, relative
    configs = list(protocol["configurations"])
    grid = pd.read_csv(TABLES / "development_grid.csv", dtype={"configuration": str})
    assert len(grid) == 132 and not grid.duplicated(["year", "configuration"]).any()
    assert set(zip(grid.year, grid.configuration)) == {(year, name) for year in range(2014, 2020) for name in configs}
    with duckdb.connect() as conn:
        events = conn.execute(
            "SELECT source_id, C_YEAR::INTEGER AS C_YEAR, C_CASE, is_fatal FROM read_parquet(?) "
            "ORDER BY C_YEAR,source_id,C_CASE", [str(SOURCE)]).df()
        stress = conn.execute("SELECT * FROM read_parquet(?)",
                              [str(OUTPUT / "stress_predictions.parquet")]).df()
    keys = ["source_id", "C_YEAR", "C_CASE", "is_fatal"]
    pd.testing.assert_frame_equal(stress[keys], events.loc[events.C_YEAR.ge(2020), keys].reset_index(drop=True),
                                  check_dtype=False)
    assert len(events) == 2949846 and int(events.is_fatal.sum()) == 47793
    assert not events[keys[:3]].duplicated().any()
    protocol_hash = digest(spec_path)
    for row in grid.itertuples():
        folder = OUTPUT / str(row.year)
        name = row.configuration
        marker = json.loads((folder / f"{name}.json").read_text())
        assert marker["protocol_sha256"] == protocol_hash
        assert marker["model_sha256"] == digest(folder / f"{name}.joblib")
        assert marker["prediction_sha256"] == digest(folder / f"{name}.npy")
        y = events.loc[events.C_YEAR.eq(row.year), "is_fatal"].to_numpy()
        assert len(y) == row.n and int(y.sum()) == row.fatal and row.train_n == int(events.C_YEAR.lt(row.year).sum())
        p = np.load(folder / f"{name}.npy", allow_pickle=False)
        close(independent_scores(y, p), [row.log_loss, row.brier_score])
    selection = json.loads((OUTPUT / "selection.json").read_text())
    assert selection["protocol_sha256"] == protocol_hash
    tolerance = protocol["selection_tolerance"]
    annual = grid.pivot(index="year", columns="configuration", values="log_loss")
    mean_loss = annual.mean()
    mean_brier = grid.groupby("configuration").brier_score.mean()
    for family, result in selection["development"].items():
        family_ids = [name for name in configs if name.startswith(family + "_")]
        loss_floor = min(mean_loss[name] for name in family_ids)
        contenders = [name for name in family_ids if mean_loss[name] - loss_floor <= tolerance]
        brier_floor = min(mean_brier[name] for name in contenders)
        winner = next(name for name in contenders if mean_brier[name] - brier_floor <= tolerance)
        assert winner == result["configuration"]
        close([mean_loss[winner], mean_brier[winner]], [result["macro_log_loss"], result["macro_brier_score"]])
        wins = int((annual[winner] < annual.logistic - tolerance).sum())
        assert wins == result["annual_log_loss_wins"]
        assert result["passes_development_gate"] == (wins >= 4
            and mean_loss[winner] < mean_loss.logistic - tolerance
            and mean_brier[winner] <= mean_brier.logistic + tolerance)

    frame, features, _ = load_data()
    frame = frame.loc[frame.C_YEAR.ge(2020)].reset_index(drop=True)
    encoder = joblib.load(OUTPUT / "encoder.joblib")
    matrix = encoder.transform(frame[features])
    metrics = pd.read_csv(TABLES / "stress_metrics.csv", dtype={"period": str})
    bins = pd.read_csv(TABLES / "stress_calibration.csv", dtype={"period": str})
    y_2019 = events.loc[events.C_YEAR.eq(2019), "is_fatal"].to_numpy()
    for name, threshold in selection["thresholds"].items():
        p_2019 = np.load(OUTPUT / "2019" / f"{name}.npy", allow_pickle=False)
        ranked = pd.DataFrame({"p": p_2019, "fatal": y_2019}).groupby("p").fatal.agg(["sum", "count"])
        ranked = ranked.sort_index(ascending=False).cumsum()
        eligible = ranked[ranked["sum"] / y_2019.sum() >= .8]
        assert (eligible["sum"] / eligible["count"]).idxmax() == threshold
        model = joblib.load(OUTPUT / "2019" / f"{name}.joblib")
        close(predict(model, matrix), stress[name].to_numpy())
    for row in metrics.itertuples():
        mask = np.ones(len(stress), dtype=bool) if row.period == "pooled" else stress.C_YEAR.eq(int(row.period)).to_numpy()
        if row.group != "all":
            polarity, category = row.group.split("_")
            codes = {"unknown": ["U", "UU"], "other": ["Q", "QQ"], "unavailable": ["X", "XX"]}[category]
            present = frame[features].isin(codes).any(axis=1).to_numpy()
            mask &= present if polarity == "any" else ~present
        y = stress.loc[mask, "is_fatal"].to_numpy()
        p = stress.loc[mask, row.model].to_numpy()
        predicted = p >= selection["thresholds"][row.model]
        tp, fp = int(y[predicted].sum()), int(predicted.sum() - y[predicted].sum())
        fn = int(y.sum()) - tp
        tn = len(y) - tp - fp - fn
        assert (row.tp, row.fp, row.fn, row.tn, row.n, row.fatal) == (tp, fp, fn, tn, len(y), y.sum())
        close(independent_scores(y, p), [row.log_loss, row.brier_score])
        close([(tp + fp) / len(y), p.mean(), y.mean()], [row.flagged_fraction, row.mean_prediction, row.observed_prevalence])
        close([tp / (tp + fp) if tp + fp else 0, tp / (tp + fn) if tp + fn else 0,
               2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0],
              [row.precision, row.recall, row.f1])
        positives = int(y.sum())
        negatives = len(y) - positives
        if positives and negatives:
            auc = (rankdata(p)[y == 1].sum() - positives * (positives + 1) / 2) / (positives * negatives)
            ranked = pd.DataFrame({"p": p, "fatal": y}).groupby("p").fatal.agg(["sum", "count"])
            ranked = ranked.sort_index(ascending=False)
            ap = ((ranked["sum"].cumsum() / ranked["count"].cumsum()) * (ranked["sum"] / positives)).sum()
            close([auc, ap], [row.roc_auc, row.average_precision])
        else:
            assert pd.isna(row.roc_auc) and pd.isna(row.average_precision)
    for row in bins.itertuples():
        period = stress if row.period == "pooled" else stress[stress.C_YEAR.eq(int(row.period))]
        p = period[row.model]
        inside = p.ge(row.lower) & (p.le(row.upper) if row.upper == 1 else p.lt(row.upper))
        assert row.n == inside.sum() and row.fatal == period.loc[inside, "is_fatal"].sum()
        if row.n:
            close([p[inside].mean(), period.loc[inside, "is_fatal"].mean()], [row.mean_prediction, row.observed])
    importance = pd.read_csv(TABLES / "permutation_importance.csv")
    assert len(importance) == 6 * 3 * 8 * 5
    assert not importance.duplicated(["year", "model", "feature", "repeat"]).any()
    assert np.isfinite(importance.delta_log_loss).all()
    artifacts = [*TABLES.glob("*.csv"), OUTPUT / "stress_predictions.parquet",
                 OUTPUT / "selection.json", spec_path, OUTPUT / "encoder.joblib"]
    receipt = {"status": "passed", "development_rows": len(grid), "tree_fits": 120,
               "stress_n": len(stress), "stress_fatal": int(stress.is_fatal.sum()),
               "artifact_sha256": {str(path.relative_to(ROOT)): digest(path) for path in sorted(artifacts)}}
    save_json(OUTPUT / "validation.json", receipt)
    print("Passed independent validation of 132 fits, selection, thresholds, stress predictions and evidence tables")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    validate()
