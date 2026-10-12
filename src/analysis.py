"""Step 3: extra analysis tables used by the dashboards.

Run:  python src/analysis.py   (after build_dataset.py)

Creates in data/processed/:
  bounce_comparison.csv  Is the "new manager bounce" real? Compares form after a
                         managerial change with form after equally bad runs where
                         the club kept its manager (the "control group").
"""
import numpy as np
import pandas as pd

from config import PROCESSED

WINDOW = 10          # games before / after
BUCKETS = [0, 0.5, 0.8, 1.1, 1.5, 3.01]
BUCKET_LABELS = ["0–0.5", "0.5–0.8", "0.8–1.1", "1.1–1.5", "1.5+"]


def team_game_windows(t: pd.DataFrame) -> pd.DataFrame:
    """For every team and match, points per game over the previous 10 and next 10 games."""
    t = t.sort_values(["season", "team", "game_number"]).copy()
    g = t.groupby(["season", "team"]).points
    t["ppg_last10"] = g.transform(lambda p: p.rolling(WINDOW).mean())
    t["ppg_next10"] = g.transform(lambda p: p[::-1].rolling(WINDOW).mean()[::-1].shift(-1))
    return t.dropna(subset=["ppg_last10", "ppg_next10"])


def bounce_comparison() -> pd.DataFrame:
    t = pd.read_csv(PROCESSED / "team_matches.csv", parse_dates=["date"])
    ev = pd.read_csv(PROCESSED / "manager_changes.csv", parse_dates=["date_of_vacancy"])
    ev = ev[(ev.games_played_before >= WINDOW) & (ev.games_after >= WINDOW)].copy()

    w = team_game_windows(t)
    # Control group: windows where the club made NO change in the 10 games either side
    # (all in-season changes count here, including ones too early/late to analyse)
    all_ev = pd.read_csv(PROCESSED / "manager_changes.csv", parse_dates=["date_of_vacancy"])
    key = ["season", "team", "game_number"]
    m = w[key + ["date"]].merge(all_ev[["season", "team", "date_of_vacancy"]],
                                on=["season", "team"], how="inner")
    m = m[(m.date - m.date_of_vacancy).abs() < pd.Timedelta(days=120)]
    near = w.set_index(key).index.isin(m.set_index(key).index)
    control = w.loc[~near]

    ev["bucket"] = pd.cut(ev.ppg_last10_before, BUCKETS, right=False, labels=BUCKET_LABELS)
    control = control.assign(bucket=pd.cut(control.ppg_last10, BUCKETS, right=False,
                                           labels=BUCKET_LABELS))
    a = ev.groupby("bucket", observed=False).agg(
        changes=("team", "size"), changed_before=("ppg_last10_before", "mean"),
        changed_after=("ppg_next10_after", "mean"))
    b = control.groupby("bucket", observed=False).agg(
        control_windows=("team", "size"), kept_before=("ppg_last10", "mean"),
        kept_after=("ppg_next10", "mean"))
    out = a.join(b).reset_index()
    out["changed_gain"] = out.changed_after - out.changed_before
    out["kept_gain"] = out.kept_after - out.kept_before
    out["extra_gain_from_change"] = out.changed_gain - out.kept_gain

    # Overall figure, weighting the control group to match the sacked managers' runs
    wts = out.changes / out.changes.sum()
    summary = pd.DataFrame([{
        "bucket": "All changes",
        "changes": int(out.changes.sum()),
        "changed_before": ev.ppg_last10_before.mean(),
        "changed_after": ev.ppg_next10_after.mean(),
        "control_windows": int(out.control_windows.sum()),
        "kept_before": np.nansum(wts * out.kept_before),
        "kept_after": np.nansum(wts * out.kept_after),
    }])
    summary["changed_gain"] = summary.changed_after - summary.changed_before
    summary["kept_gain"] = summary.kept_after - summary.kept_before
    summary["extra_gain_from_change"] = summary.changed_gain - summary.kept_gain
    return pd.concat([out, summary], ignore_index=True).round(3)


if __name__ == "__main__":
    b = bounce_comparison()
    b.to_csv(PROCESSED / "bounce_comparison.csv", index=False)
    print(b.to_string(index=False))
