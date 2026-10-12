"""Step 2: turn the raw files into clean tables for the dashboards.

Run:  python src/build_dataset.py

Creates in data/processed/:
  matches.csv        one row per match
  team_matches.csv   one row per team per match (with running points totals)
  team_seasons.csv   one row per team per season  <- the master table
  league_seasons.csv one row per season (league-wide trends)
  manager_changes.csv one row per in-season managerial change (form before/after)
"""
import numpy as np
import pandas as pd

from config import (BIG_SIX, PREMIER_LEAGUE_ID, PROCESSED, RAW, SEASON_CODES,
                    TEAMS, season_label, season_start_year, season_tm)

TM = RAW / "transfermarkt"
MANUAL = RAW.parent / "manual"   # small hand-checked files (managers), kept in git
SEASONS = [season_label(c) for c in SEASON_CODES]
TM_TO_LABEL = {season_tm(c): season_label(c) for c in SEASON_CODES}
CLUB_ID = {v[1]: v[0] for v in TEAMS.values()}          # display name -> club id
DISPLAY = {k: v[1] for k, v in TEAMS.items()}           # results name -> display name


# ---------------------------------------------------------------- results
def load_matches() -> pd.DataFrame:
    frames = []
    for code in SEASON_CODES:
        d = pd.read_csv(RAW / "results" / f"season-{code}.csv")
        d["season"] = season_label(code)
        frames.append(d)
    m = pd.concat(frames, ignore_index=True)
    m = m.rename(columns={
        "Date": "date", "HomeTeam": "home_team", "AwayTeam": "away_team",
        "FTHG": "home_goals", "FTAG": "away_goals", "FTR": "result",
        "HS": "home_shots", "AS": "away_shots",
        "HST": "home_shots_on_target", "AST": "away_shots_on_target",
        "HY": "home_yellows", "AY": "away_yellows", "HR": "home_reds", "AR": "away_reds",
    })
    m["home_team"] = m["home_team"].map(DISPLAY)
    m["away_team"] = m["away_team"].map(DISPLAY)
    assert m[["home_team", "away_team"]].notna().all().all(), "unmapped team name"
    m["date"] = pd.to_datetime(m["date"])
    keep = ["season", "date", "home_team", "away_team", "home_goals", "away_goals",
            "result", "home_shots", "away_shots", "home_shots_on_target",
            "away_shots_on_target", "home_yellows", "away_yellows", "home_reds", "away_reds"]
    return m[keep].sort_values(["date", "home_team"]).reset_index(drop=True)


def team_view(m: pd.DataFrame) -> pd.DataFrame:
    """Turn each match into two rows: one from each team's point of view."""
    def side(venue):
        me, op = ("home", "away") if venue == "home" else ("away", "home")
        d = pd.DataFrame({
            "season": m["season"], "date": m["date"], "venue": venue,
            "team": m[f"{me}_team"], "opponent": m[f"{op}_team"],
            "goals_for": m[f"{me}_goals"], "goals_against": m[f"{op}_goals"],
            "shots": m[f"{me}_shots"], "shots_against": m[f"{op}_shots"],
            "shots_on_target": m[f"{me}_shots_on_target"],
            "shots_on_target_against": m[f"{op}_shots_on_target"],
        })
        return d
    t = pd.concat([side("home"), side("away")], ignore_index=True)
    t["result"] = np.select([t.goals_for > t.goals_against, t.goals_for == t.goals_against],
                            ["W", "D"], "L")
    t["points"] = t["result"].map({"W": 3, "D": 1, "L": 0})
    t = t.sort_values(["season", "team", "date"]).reset_index(drop=True)
    g = t.groupby(["season", "team"])
    t["game_number"] = g.cumcount() + 1
    t["cumulative_points"] = g["points"].cumsum()
    t["cumulative_goal_diff"] = (t.goals_for - t.goals_against).groupby([t.season, t.team]).cumsum()
    return t


def season_table(t: pd.DataFrame) -> pd.DataFrame:
    g = t.groupby(["season", "team"])
    s = g.agg(played=("points", "size"), wins=("result", lambda r: (r == "W").sum()),
              draws=("result", lambda r: (r == "D").sum()),
              losses=("result", lambda r: (r == "L").sum()),
              goals_for=("goals_for", "sum"), goals_against=("goals_against", "sum"),
              points_on_pitch=("points", "sum"), shots=("shots", "sum"),
              shots_against=("shots_against", "sum"),
              shots_on_target=("shots_on_target", "sum"),
              shots_on_target_against=("shots_on_target_against", "sum")).reset_index()
    for venue in ["home", "away"]:
        v = t[t.venue == venue].groupby(["season", "team"])["points"].agg(["sum", "mean"])
        v.columns = [f"{venue}_points", f"{venue}_ppg"]
        s = s.merge(v.reset_index(), on=["season", "team"])
    s["goal_difference"] = s.goals_for - s.goals_against
    # Share of all shots in a team's games that it took: a simple "dominance" measure
    s["shot_share"] = s.shots / (s.shots + s.shots_against)
    s["shots_on_target_share"] = s.shots_on_target / (s.shots_on_target + s.shots_on_target_against)
    return s


# ---------------------------------------------------------------- transfermarkt
def load_tm():
    perf = pd.read_csv(TM / "player_performances.csv", low_memory=False,
                       usecols=["player_id", "season_name", "competition_id",
                                "team_id", "nb_in_group", "nb_on_pitch"])
    prof = pd.read_csv(TM / "player_profiles.csv", low_memory=False,
                       usecols=["player_id", "player_name", "date_of_birth", "main_position"])
    prof["player_name"] = prof.player_name.str.replace(r"\s*\(\d+\)$", "", regex=True)
    mv = pd.read_csv(TM / "player_market_value.csv")
    tr = pd.read_csv(TM / "transfer_history.csv", low_memory=False)
    tcs = pd.read_csv(TM / "team_competitions_seasons.csv", low_memory=False)
    return perf, prof, mv, tr, tcs


def market_value_at(players: pd.DataFrame, mv: pd.DataFrame) -> pd.Series:
    """Each player's market value on 1 September of the season's first year.
    Falls back to the first valuation in the following 12 months if none earlier."""
    mv = mv.rename(columns={"date_unix": "mv_date"}).copy()
    mv["mv_date"] = pd.to_datetime(mv["mv_date"], errors="coerce")
    mv = mv.dropna(subset=["mv_date", "value"]).sort_values("mv_date")
    q = players[["player_id", "ref_date"]].reset_index().sort_values("ref_date")
    before = pd.merge_asof(q, mv, left_on="ref_date", right_on="mv_date", by="player_id",
                           direction="backward")
    after = pd.merge_asof(q, mv, left_on="ref_date", right_on="mv_date", by="player_id",
                          direction="forward", tolerance=pd.Timedelta(days=365))
    val = before.set_index("index")["value"].fillna(after.set_index("index")["value"])
    return val.reindex(players.index)


def squad_metrics(perf, prof, mv) -> pd.DataFrame:
    pl = perf[(perf.competition_id == PREMIER_LEAGUE_ID)
              & perf.season_name.isin(TM_TO_LABEL) & (perf.nb_on_pitch > 0)].copy()
    pl["season"] = pl.season_name.map(TM_TO_LABEL)
    pl = pl.merge(prof, on="player_id", how="left")
    start = pl.season.str[:4].astype(int)
    mid = pd.to_datetime(start.add(1).astype(str) + "-01-01")          # 1 Jan, mid-season
    pl["age"] = (mid - pd.to_datetime(pl.date_of_birth, errors="coerce")).dt.days / 365.25
    pl["ref_date"] = pd.to_datetime(start.astype(str) + "-09-01")
    pl["market_value"] = market_value_at(pl, mv)

    # Squad stability: did this player also play for this club last season (any competition)?
    played = perf[perf.nb_on_pitch > 0][["player_id", "team_id", "season_name"]].drop_duplicates()
    played["next_season"] = played.season_name.map(
        lambda s: f"{int(s[:2]) + 1:02d}/{int(s[3:]) + 1:02d}" if s[:2].isdigit() else None)
    returning = played[["player_id", "team_id", "next_season"]].rename(
        columns={"next_season": "season_name"}).assign(returning=True)
    pl = pl.merge(returning, on=["player_id", "team_id", "season_name"], how="left")
    pl["returning"] = pl.returning.fillna(False).astype(bool)

    def agg(g):
        w = g.nb_on_pitch
        a = g.dropna(subset=["age"])
        top = g.sort_values("nb_on_pitch", ascending=False).head(14)
        return pd.Series({
            "players_used": g.player_id.nunique(),
            "avg_age_weighted": np.average(a.age, weights=a.nb_on_pitch) if len(a) else np.nan,
            "avg_age_squad": a.age.mean(),
            "avg_age_core14": top.age.mean(),
            "squad_value_eur": g.market_value.sum(min_count=1),
            "squad_value_core14_eur": top.market_value.sum(min_count=1),
            "most_valuable_player": g.loc[g.market_value.idxmax(), "player_name"]
            if g.market_value.notna().any() else None,
            "stability_pct": 100 * (w * g.returning).sum() / w.sum(),
            "u23_share_pct": 100 * (w * (g.age < 23)).sum() / w.sum(),
            "over30_share_pct": 100 * (w * (g.age >= 30)).sum() / w.sum(),
        })

    return pl.groupby(["season", "team_id"]).apply(agg, include_groups=False).reset_index()


def transfer_metrics(tr) -> pd.DataFrame:
    tr = tr[tr.season_name.isin(TM_TO_LABEL) & tr.transfer_type.isin(["Transfer", "Loan"])].copy()
    tr["season"] = tr.season_name.map(TM_TO_LABEL)
    tr["fee"] = pd.to_numeric(tr.transfer_fee, errors="coerce").fillna(0)
    ids = set(CLUB_ID.values())
    spent = (tr[tr.to_team_id.isin(ids)].groupby(["season", "to_team_id"])
             .agg(transfer_spend_eur=("fee", "sum"), signings=("player_id", "nunique"),
                  record_signing_fee_eur=("fee", "max")))
    spent.index.names = ["season", "team_id"]
    sold = tr[tr.from_team_id.isin(ids)].groupby(["season", "from_team_id"]).agg(
        transfer_income_eur=("fee", "sum"))
    sold.index.names = ["season", "team_id"]
    out = spent.join(sold, how="outer").fillna(0).reset_index()
    out["net_spend_eur"] = out.transfer_spend_eur - out.transfer_income_eur
    return out


def manager_metrics(tcs) -> pd.DataFrame:
    """Manager listed for each club-season (from its league entry, any division)."""
    lg = tcs[tcs.competition_id == tcs.season_league_competition_id]
    lg = lg[["club_id", "season_id", "competition_id", "season_manager_manager_name",
             "season_points", "season_rank"]].drop_duplicates(["club_id", "season_id"]).copy()
    # Transfermarkt's 2025/26 snapshot predates the end of that season: use the
    # hand-checked end-of-season list instead.
    eos = pd.read_csv(MANUAL / "managers_end_of_season_2025_26.csv")
    eos = dict(zip(eos.team.map(CLUB_ID), eos.manager))
    last = lg.season_id == 2025
    lg.loc[last, "season_manager_manager_name"] = lg.loc[last, "club_id"].map(eos).fillna(
        lg.loc[last, "season_manager_manager_name"])
    lg = lg.sort_values(["club_id", "season_id"])
    prev = lg.groupby("club_id").season_manager_manager_name.shift()
    prev_season = lg.groupby("club_id").season_id.shift()
    known = (prev.notna() & lg.season_manager_manager_name.notna()
             & (prev_season == lg.season_id - 1))
    lg["new_manager"] = (lg.season_manager_manager_name != prev).astype(object).where(known, None)
    # Tenure: consecutive seasons in charge, counting this one
    block = (lg.season_manager_manager_name != prev).cumsum()
    lg["manager_tenure_seasons"] = lg.groupby(["club_id", block]).cumcount() + 1
    lg = lg[lg.competition_id == PREMIER_LEAGUE_ID]
    lg["season"] = lg.season_id.map({season_start_year(c): season_label(c) for c in SEASON_CODES})
    lg = lg.dropna(subset=["season"])
    return lg.rename(columns={"club_id": "team_id", "season_manager_manager_name": "manager",
                              "season_points": "official_points_tm"})[
        ["season", "team_id", "manager", "new_manager", "manager_tenure_seasons",
         "official_points_tm"]]


def manager_change_events(t: pd.DataFrame) -> pd.DataFrame:
    """One row per in-season managerial change, with form before and after.

    'In-season' means the vacancy happened between the team's first and last league
    game. Form is points per game over (up to) the 10 league games before the
    vacancy and the 10 games after it."""
    ch = pd.read_csv(MANUAL / "manager_changes.csv", parse_dates=["date_of_vacancy"])
    span = t.groupby(["season", "team"]).date.agg(["min", "max"]).reset_index()
    ch = ch.merge(span, on=["season", "team"], how="inner")
    ch = ch[(ch.date_of_vacancy > ch["min"]) & (ch.date_of_vacancy < ch["max"])].copy()
    rows = []
    for _, c in ch.iterrows():
        g = t[(t.season == c.season) & (t.team == c.team)]
        before = g[g.date < c.date_of_vacancy]
        after = g[g.date > c.date_of_vacancy]
        rows.append({
            "season": c.season, "team": c.team, "date_of_vacancy": c.date_of_vacancy.date(),
            "outgoing_manager": c.outgoing_manager, "manner_of_departure": c.manner_of_departure,
            "incoming_manager": c.incoming_manager,
            "interim_or_caretaker": any(w in str(c.incoming_manager).lower()
                                        for w in ["interim", "caretaker"]),
            "games_played_before": len(before),
            "ppg_season_before": before.points.mean(),
            "ppg_last10_before": before.tail(10).points.mean(),
            "ppg_next10_after": after.head(10).points.mean(),
            "ppg_rest_of_season": after.points.mean(),
            "games_after": len(after),
        })
    ev = pd.DataFrame(rows)
    ev["bounce_ppg"] = ev.ppg_next10_after - ev.ppg_last10_before
    return ev.round(3)


# ---------------------------------------------------------------- assemble
def build():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    matches = load_matches()
    tm_long = team_view(matches)
    s = season_table(tm_long)
    s["team_id"] = s.team.map(CLUB_ID)

    perf, prof, mv, tr, tcs = load_tm()
    s = (s.merge(squad_metrics(perf, prof, mv), on=["season", "team_id"], how="left")
          .merge(transfer_metrics(tr), on=["season", "team_id"], how="left")
          .merge(manager_metrics(tcs), on=["season", "team_id"], how="left"))
    for c in ["transfer_spend_eur", "transfer_income_eur", "net_spend_eur", "signings"]:
        s[c] = s[c].fillna(0)

    events = manager_change_events(tm_long)
    n_changes = events.groupby(["season", "team"]).size().rename("in_season_manager_changes")
    s = s.merge(n_changes.reset_index(), on=["season", "team"], how="left")
    s["in_season_manager_changes"] = s.in_season_manager_changes.fillna(0).astype(int)

    # Points deductions (e.g. Everton & Forest 2023/24): official table vs pitch results.
    # Only trusted for completed seasons that Transfermarkt captured in full.
    complete = s.season != "2025/26"
    s["points_deduction"] = 0
    diff = (s.official_points_tm - s.points_on_pitch).where(complete & s.official_points_tm.notna(), 0)
    s.loc[diff < 0, "points_deduction"] = diff[diff < 0].astype(int)
    s["points"] = s.points_on_pitch + s.points_deduction
    s = s.drop(columns="official_points_tm")

    s = s.sort_values(["season", "points", "goal_difference", "goals_for"],
                      ascending=[True, False, False, False])
    s["position"] = s.groupby("season").cumcount() + 1
    s["ppg"] = s.points / s.played

    # Relative-to-season measures, so different eras can be compared fairly
    g = s.groupby("season")
    s["squad_value_vs_avg"] = s.squad_value_eur / g.squad_value_eur.transform("mean")
    s["squad_value_rank"] = g.squad_value_eur.rank(ascending=False, method="min")
    s["spend_vs_avg"] = s.transfer_spend_eur / g.transfer_spend_eur.transform("mean")
    s["spend_rank"] = g.transfer_spend_eur.rank(ascending=False, method="min")
    s["age_vs_avg"] = s.avg_age_weighted - g.avg_age_weighted.transform("mean")
    s["points_per_100m_value"] = s.points / (s.squad_value_eur / 1e8)
    s["over_performance"] = s.squad_value_rank - s.position   # +ve: finished above budget rank

    # Promotion / survival flags
    order = {lab: i for i, lab in enumerate(SEASONS)}
    in_pl = set(zip(s.season.map(order), s.team))
    s["promoted"] = [(order[x] - 1, t) not in in_pl if order[x] > 0 else np.nan
                     for x, t in zip(s.season, s.team)]
    s["relegated"] = s.position >= 18
    s["big_six"] = s.team.isin(BIG_SIX)
    s["data_note"] = np.where(
        s.season == "2025/26",
        "Squad age, value and stability based on the first few games only", "")

    cols = ["season", "position", "team", "team_id", "played", "wins", "draws", "losses",
            "goals_for", "goals_against", "goal_difference", "points", "points_on_pitch",
            "points_deduction", "ppg", "home_points", "away_points", "home_ppg", "away_ppg",
            "shots", "shots_against", "shots_on_target", "shots_on_target_against",
            "shot_share", "shots_on_target_share",
            "avg_age_weighted", "avg_age_squad", "avg_age_core14", "age_vs_avg",
            "u23_share_pct", "over30_share_pct", "players_used", "stability_pct",
            "squad_value_eur", "squad_value_core14_eur", "squad_value_vs_avg",
            "squad_value_rank", "most_valuable_player",
            "transfer_spend_eur", "transfer_income_eur", "net_spend_eur", "signings",
            "record_signing_fee_eur", "spend_vs_avg", "spend_rank",
            "points_per_100m_value", "over_performance",
            "manager", "new_manager", "manager_tenure_seasons", "in_season_manager_changes",
            "promoted", "relegated", "big_six", "data_note"]
    s = s[cols].round(3)

    league = league_trends(matches, s)

    matches.to_csv(PROCESSED / "matches.csv", index=False)
    tm_long.to_csv(PROCESSED / "team_matches.csv", index=False)
    s.to_csv(PROCESSED / "team_seasons.csv", index=False)
    league.to_csv(PROCESSED / "league_seasons.csv", index=False)
    events.to_csv(PROCESSED / "manager_changes.csv", index=False)
    print(f"matches: {len(matches)} rows | team_matches: {len(tm_long)} | "
          f"team_seasons: {len(s)} | league_seasons: {len(league)} | "
          f"in-season manager changes: {len(events)}")
    return s


def league_trends(matches, s) -> pd.DataFrame:
    rows = []
    for season, m in matches.groupby("season"):
        t = s[s.season == season].set_index("position")
        n = len(m)
        home_pts = (3 * (m.result == "H") + (m.result == "D")).mean()
        away_pts = (3 * (m.result == "A") + (m.result == "D")).mean()
        rows.append({
            "season": season,
            "home_win_pct": 100 * (m.result == "H").mean(),
            "draw_pct": 100 * (m.result == "D").mean(),
            "away_win_pct": 100 * (m.result == "A").mean(),
            "home_ppg": home_pts, "away_ppg": away_pts,
            "home_advantage_ppg": home_pts - away_pts,
            "goals_per_game": (m.home_goals + m.away_goals).sum() / n,
            "champion": t.loc[1, "team"], "champion_points": t.loc[1, "points"],
            "title_margin": t.loc[1, "points"] - t.loc[2, "points"],
            "fourth_place_points": t.loc[4, "points"],
            "safety_points": t.loc[17, "points"],
            "big_six_avg_points": t[t.big_six].points.mean(),
            "rest_avg_points": t[~t.big_six].points.mean(),
            "points_spread_sd": t.points.std(),
            "promoted_survived": int(((t.promoted == True) & (t.index <= 17)).sum()),
            "avg_age_weighted": t.avg_age_weighted.mean(),
            "total_transfer_spend_eur": t.transfer_spend_eur.sum(),
            "avg_squad_value_eur": t.squad_value_eur.mean(),
            "fans_in_stadiums": "No (COVID)" if season == "2020/21" else
            ("Partly (from June 2020 no fans)" if season == "2019/20" else "Yes"),
        })
    out = pd.DataFrame(rows)
    out["big_six_gap"] = out.big_six_avg_points - out.rest_avg_points
    return out.round(3)


if __name__ == "__main__":
    build()
