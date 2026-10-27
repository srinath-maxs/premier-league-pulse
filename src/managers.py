"""Managerial changes worked out from match records (Transfermarkt), not from Wikipedia.

Every Premier League match in Transfermarkt's games table lists the manager in
charge of each team. Going through each club's matches in date order, a change is
any match where the manager differs from the previous match's manager.

Wikipedia (data/manual/manager_changes.csv) is now only used to add the detail
match records can't show: how the manager left (sacked, resigned...) and the
exact date of the announcement.
"""
import unicodedata
import re

import pandas as pd

from config import PREMIER_LEAGUE_ID, RAW, SEASON_CODES, TEAMS, season_label, season_start_year

GAMES = RAW / "transfermarkt" / "games.csv"
MANUAL = RAW.parent / "manual"
DISPLAY_BY_ID = {v[0]: v[1] for v in TEAMS.values()}
LABEL_BY_YEAR = {season_start_year(c): season_label(c) for c in SEASON_CODES}


def norm(name) -> str:
    """Compare names loosely: no accents, no '(interim)', lower case."""
    x = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode().lower()
    x = re.sub(r"\s*\(.*?\)", "", x).replace("&", "and").strip()
    return ALIASES.get(x, x)


# Same person, spelled differently by Wikipedia and Transfermarkt
ALIASES = {"gus poyet": "gustavo poyet", "paddy mccarthy": "patrick mccarthy"}


def load_games() -> pd.DataFrame:
    g = pd.read_csv(GAMES, low_memory=False, parse_dates=["date"])
    g = g[(g.competition_id == PREMIER_LEAGUE_ID) & g.season.isin(LABEL_BY_YEAR)]
    return g.assign(season=g.season.map(LABEL_BY_YEAR))


def club_matches(g: pd.DataFrame) -> pd.DataFrame:
    """One row per club per match, with that club's manager."""
    home = g.rename(columns={"home_club_id": "club_id", "home_club_manager_name": "manager",
                             "home_club_goals": "gf", "away_club_goals": "ga"})
    away = g.rename(columns={"away_club_id": "club_id", "away_club_manager_name": "manager",
                             "away_club_goals": "gf", "home_club_goals": "ga"})
    cols = ["season", "date", "club_id", "manager", "gf", "ga", "attendance"]
    m = pd.concat([home[cols].assign(venue="home"), away[cols].assign(venue="away")])
    m["team"] = m.club_id.map(DISPLAY_BY_ID)
    return m.sort_values(["season", "team", "date"]).reset_index(drop=True)


def changes_from_matches(m: pd.DataFrame) -> pd.DataFrame:
    """Every point in a season where a club's manager differs from the previous match."""
    m = m.copy()
    g = m.groupby(["season", "team"])
    m["prev_manager"] = g.manager.shift()
    m["prev_date"] = g.date.shift()
    m["game_number"] = g.cumcount() + 1
    ch = m[m.prev_manager.notna() & (m.manager.map(norm) != m.prev_manager.map(norm))]
    return ch.rename(columns={"prev_manager": "outgoing_manager", "manager": "incoming_manager",
                              "prev_date": "last_game_old_manager",
                              "date": "first_game_new_manager"})[
        ["season", "team", "outgoing_manager", "incoming_manager", "last_game_old_manager",
         "first_game_new_manager", "game_number"]].reset_index(drop=True)


CARETAKER_MAX_GAMES = 4


def spells(m: pd.DataFrame) -> pd.DataFrame:
    """Unbroken runs of matches under the same manager, per club and season."""
    m = m.copy()
    m["mn"] = m.manager.map(norm)
    g = m.groupby(["season", "team"])
    m["spell"] = (m.mn != g.mn.shift()).groupby([m.season, m.team]).cumsum()
    sp = (m.groupby(["season", "team", "spell"])
          .agg(manager=("manager", "first"), mn=("mn", "first"), games=("date", "size"),
               first_game=("date", "min"), last_game=("date", "max"))
          .reset_index())
    later = sp.merge(sp[["season", "team", "spell", "mn"]], on=["season", "team", "mn"],
                     suffixes=("", "_other"))
    returns = later[later.spell_other > later.spell].groupby(["season", "team", "spell"]).size()
    sp["returns_later"] = sp.set_index(["season", "team", "spell"]).index.isin(returns.index)
    sp["is_last"] = sp.spell == sp.groupby(["season", "team"]).spell.transform("max")
    sp["is_first"] = sp.spell == 1
    # Caretaker: a short stint between two other managers
    sp["caretaker"] = (~sp.is_first) & (sp.games <= CARETAKER_MAX_GAMES) & (~sp.is_last)
    return sp


def departures(m: pd.DataFrame) -> pd.DataFrame:
    """In-season departures: a manager who led the team (started the season or lasted
    5+ games) and did not come back later that season. Temporary stand-ins (e.g. an
    assistant covering one game while the manager was ill) and short caretaker
    stints are not counted as departures."""
    sp = spells(m)
    rows = []
    for (season, team), grp in sp.groupby(["season", "team"]):
        grp = grp.sort_values("spell").reset_index(drop=True)
        for i, r in grp.iterrows():
            if r.is_last or r.returns_later or r.caretaker:
                continue
            nxt = grp.iloc[i + 1:]
            successor = nxt[~nxt.caretaker]
            caretakers = nxt[nxt.caretaker & (nxt.spell < (successor.spell.min() if len(successor) else 999))]
            rows.append({
                "season": season, "team": team, "outgoing_manager": r.manager,
                "games_in_charge": r.games, "last_game_old_manager": r.last_game,
                "first_game_after": grp.iloc[i + 1].first_game,
                "caretaker": ", ".join(caretakers.manager) if len(caretakers) else "",
                "incoming_manager": successor.iloc[0].manager if len(successor) else grp.iloc[i + 1].manager,
            })
    return pd.DataFrame(rows)


def end_of_season_managers(m: pd.DataFrame) -> pd.DataFrame:
    """Manager in charge of each club's last league game of the season."""
    last = m.sort_values("date").groupby(["season", "team"]).tail(1)
    return last[["season", "team", "manager"]].rename(columns={"manager": "manager_last_game"})


def match_to_wikipedia(ch: pd.DataFrame) -> pd.DataFrame:
    """Attach Wikipedia's departure details where they line up with a match-record change."""
    wk = pd.read_csv(MANUAL / "manager_changes.csv", parse_dates=["date_of_vacancy"])
    out = []
    for _, c in ch.iterrows():
        cand = wk[(wk.season == c.season) & (wk.team == c.team)
                  & (wk.outgoing_manager.map(norm) == norm(c.outgoing_manager))]
        if len(cand):
            w = cand.iloc[0]
            out.append({"manner_of_departure": w.manner_of_departure,
                        "date_of_vacancy": w.date_of_vacancy, "wikipedia_match": True})
        else:
            out.append({"manner_of_departure": None, "date_of_vacancy": pd.NaT,
                        "wikipedia_match": False})
    ch = pd.concat([ch.reset_index(drop=True), pd.DataFrame(out)], axis=1)
    # Where Wikipedia has no date, the change happened between the two games
    ch["date_of_vacancy"] = ch.date_of_vacancy.fillna(ch.last_game_old_manager + pd.Timedelta(days=1))
    ch["date_source"] = ch.wikipedia_match.map({True: "Wikipedia", False: "Match records"})
    return ch
