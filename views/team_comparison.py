"""Team Comparison: any team-season against any other, across eras."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ui import SERIES, SYMBOLS, eur_m, footer, insight, load, style

s, lg, tm, mc, bc = load()
CLUBS = sorted(s.team.unique())
A_COL, B_COL = SERIES[0], SERIES[1]

st.title("Team Comparison")
st.caption("Pick any club and season on each side, even from different eras. Spending is compared "
           "against each season's league average, so 2014 and 2025 money can be compared fairly.")


# ------------------------------------------------------------------ pickers
def picker(side: str, default_club: str, default_season: str):
    st.markdown(f"**Team {side}**")
    c1, c2 = st.columns([3, 2])
    club = c1.selectbox("Club", CLUBS, index=CLUBS.index(default_club), key=f"club_{side}")
    seasons = sorted(s[s.team == club].season, reverse=True)
    idx = seasons.index(default_season) if default_season in seasons else 0
    season = c2.selectbox("Season", seasons, index=idx, key=f"season_{side}")
    return s[(s.team == club) & (s.season == season)].iloc[0]


left, right = st.columns(2, gap="large")
with left:
    A = picker("A", "Arsenal", "2025/26")
with right:
    B = picker("B", "Liverpool", "2019/20")

name_a, name_b = f"{A.team} {A.season}", f"{B.team} {B.season}"
if name_a == name_b:
    st.warning("You've picked the same team and season twice. Change one side to compare.")
    st.stop()


def ordinal(n) -> str:
    n = int(n)
    return f"{n}{'th' if 11 <= n % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


# ------------------------------------------------------------------ summary
def summary() -> str:
    lines = []
    if A.points == B.points:
        lines.append(f"**{name_a}** and **{name_b}** both finished with **{A.points} points** "
                     f"({ordinal(A.position)} vs {ordinal(B.position)}).")
    else:
        hi, lo = (A, B) if A.points > B.points else (B, A)
        lines.append(f"**{hi.team} {hi.season}** finished **{abs(A.points - B.points)} point{'s' if abs(A.points - B.points) != 1 else ''} ahead** "
                     f"({hi.points} vs {lo.points}; {ordinal(hi.position)} vs {ordinal(lo.position)}).")
    if pd.notna(A.squad_value_vs_avg) and pd.notna(B.squad_value_vs_avg):
        richer, poorer = (A, B) if A.squad_value_vs_avg > B.squad_value_vs_avg else (B, A)
        same_side = (richer.points >= poorer.points)
        lines.append(f"{richer.team} {richer.season} had the more valuable squad for its era "
                     f"({richer.squad_value_vs_avg:.2f}× the league average vs {poorer.squad_value_vs_avg:.2f}×)"
                     + ("." if same_side else f", but {poorer.team} {poorer.season} got more out of less."))
    if pd.notna(A.avg_age_weighted) and pd.notna(B.avg_age_weighted):
        d = A.avg_age_weighted - B.avg_age_weighted
        if abs(d) >= 0.3:
            younger, older = (A, B) if d < 0 else (B, A)
            lines.append(f"{younger.team} {younger.season} was **{abs(d):.1f} years younger** "
                         f"({younger.avg_age_weighted:.1f} vs {older.avg_age_weighted:.1f}).")
        else:
            lines.append(f"The two squads were almost the same age ({A.avg_age_weighted:.1f} vs "
                         f"{B.avg_age_weighted:.1f}).")
    ra = tm[(tm.team == A.team) & (tm.season == A.season)].set_index("game_number").cumulative_points
    rb = tm[(tm.team == B.team) & (tm.season == B.season)].set_index("game_number").cumulative_points
    if 19 in ra and 19 in rb and ra[19] == rb[19]:
        lines.append(f"They were level at the halfway point, both on {ra[19]} points after 19 games.")
    elif 19 in ra and 19 in rb:
        lead, hi_p, lo_p = (name_a, ra[19], rb[19]) if ra[19] > rb[19] else (name_b, rb[19], ra[19])
        lines.append(f"At the halfway point (19 games) {lead} was {hi_p - lo_p} "
                     f"point{'s' if hi_p - lo_p != 1 else ''} ahead ({hi_p} vs {lo_p}).")
    return " ".join(lines)


insight(summary())
if "2025/26" in (A.season, B.season):
    st.caption("2025/26 squad age, value and stability use early-season data only.")

# ------------------------------------------------------------------ metric table
#   (label, column, format, which direction is "better": +1 higher, -1 lower, 0 neither)
ROWS = [
    ("Results", None, None, 0),
    ("Final position", "position", lambda v: ordinal(v), -1),
    ("Points", "points", "{:.0f}", 1),
    ("Points per game", "ppg", "{:.2f}", 1),
    ("Won / drawn / lost", "wdl", "{}", 0),
    ("Goals scored", "goals_for", "{:.0f}", 1),
    ("Goals conceded", "goals_against", "{:.0f}", -1),
    ("Goal difference", "goal_difference", "{:+.0f}", 1),
    ("Share of shots in their games", "shot_share_pct", "{:.0f}%", 1),
    ("Home points per game", "home_ppg", "{:.2f}", 1),
    ("Away points per game", "away_ppg", "{:.2f}", 1),
    ("Squad", None, None, 0),
    ("Average age (by appearances)", "avg_age_weighted", "{:.1f}", 0),
    ("Appearances by under-23s", "u23_share_pct", "{:.0f}%", 0),
    ("Appearances by over-30s", "over30_share_pct", "{:.0f}%", 0),
    ("Squad stability", "stability_pct", "{:.0f}%", 0),
    ("Players used", "players_used", "{:.0f}", 0),
    ("Most valuable player", "most_valuable_player", "{}", 0),
    ("Money", None, None, 0),
    ("Squad value", "squad_value_eur", eur_m, 0),
    ("Squad value vs league average", "squad_value_vs_avg", "{:.2f}×", 0),
    ("Squad value rank that season", "squad_value_rank", lambda v: ordinal(v), 0),
    ("Transfer spend", "transfer_spend_eur", eur_m, 0),
    ("Transfer spend vs league average", "spend_vs_avg", "{:.2f}×", 0),
    ("Net spend", "net_spend_eur", eur_m, 0),
    ("Points per €100m of squad value", "points_per_100m_value", "{:.1f}", 1),
    ("Places above budget rank", "over_performance", "{:+.0f}", 1),
    ("Manager", None, None, 0),
    ("Manager (end of season)", "manager", "{}", 0),
    ("Seasons in charge", "manager_tenure_seasons", "{:.0f}", 0),
    ("In-season manager changes", "in_season_manager_changes", "{:.0f}", 0),
]


def enrich(r: pd.Series) -> pd.Series:
    r = r.copy()
    r["wdl"] = f"{r.wins} / {r.draws} / {r.losses}"
    r["shot_share_pct"] = 100 * r.shot_share
    return r


A2, B2 = enrich(A), enrich(B)


def fmt(f, v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "–"
    return f(v) if callable(f) else f.format(v)


rows = []
for label, col, f, better in ROWS:
    if col is None:
        rows.append({"Measure": f"▸ {label.upper()}", name_a: "", name_b: "", "Difference": "", "Edge": ""})
        continue
    va, vb = A2[col], B2[col]
    diff, edge = "", ""
    if isinstance(va, (int, float, np.number)) and isinstance(vb, (int, float, np.number)) \
            and pd.notna(va) and pd.notna(vb):
        d = va - vb
        if col.endswith("_eur"):
            diff = f"{'+' if d >= 0 else '−'}{eur_m(abs(d))}"
        elif col in ("position", "squad_value_rank"):
            diff = f"{d:+.0f} places"
        elif isinstance(f, str):
            diff = ("+" if d >= 0 else "") + f.format(d).lstrip("+")
        if better and d != 0:
            edge = "✓ A" if (d > 0) == (better > 0) else "✓ B"
    rows.append({"Measure": label, name_a: fmt(f, va), name_b: fmt(f, vb),
                 "Difference": diff, "Edge": edge})

st.subheader("Side by side")
st.caption("Difference = Team A minus Team B. ✓ marks the better side where higher (or lower) is "
           "clearly better; age, spending and stability are shown without a winner.")
st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch", height=1130,
             column_config={"Measure": st.column_config.TextColumn(width="medium"),
                            "Edge": st.column_config.TextColumn("Better", width="small")})

# ------------------------------------------------------------------ points race
st.subheader("The points race")
fig = go.Figure()
for row, colour, sym, nm in [(A, A_COL, SYMBOLS[0], name_a), (B, B_COL, SYMBOLS[1], name_b)]:
    g = tm[(tm.team == row.team) & (tm.season == row.season)].sort_values("game_number")
    fig.add_trace(go.Scatter(
        x=g.game_number, y=g.cumulative_points, name=nm, mode="lines+markers",
        line=dict(color=colour, width=2), marker=dict(size=6, symbol=sym),
        customdata=np.stack([g.opponent, g.venue, g.goals_for, g.goals_against, g.result], axis=-1),
        hovertemplate=f"<b>{nm}</b> · game %{{x}}<br>%{{customdata[4]}} %{{customdata[2]}}–%{{customdata[3]}} "
                      "vs %{customdata[0]} (%{customdata[1]})<br>Total: %{y} points<extra></extra>"))
fig.update_xaxes(title="Game number", range=[0.5, 38.5], dtick=5)
fig.update_yaxes(title="Points so far", rangemode="tozero")
fig.update_layout(hovermode="x unified")
st.plotly_chart(style(fig, 440), width="stretch")
ra = tm[(tm.team == A.team) & (tm.season == A.season)].set_index("game_number").cumulative_points
rb = tm[(tm.team == B.team) & (tm.season == B.season)].set_index("game_number").cumulative_points
gap = (ra - rb).dropna()
if len(gap):
    biggest = gap.abs().idxmax()
    leader = name_a if gap[biggest] > 0 else name_b
    ahead_a = int((gap > 0).sum())
    ahead_b = int((gap < 0).sum())
    insight(f"{name_a} was ahead after **{ahead_a}** of 38 games and {name_b} after **{ahead_b}**. "
            f"The biggest gap was **{abs(int(gap[biggest]))} points** (after game {biggest}, to {leader}).")

# ------------------------------------------------------------------ profile
st.subheader("Team profile")
st.caption("Where each team ranks among all 240 Premier League team-seasons since 2014/15 "
           "(100 = best of all of them). Hover a dot for the actual value.")
pct = pd.DataFrame({
    "Attack (goals per game)": s.goals_for / s.played,
    "Defence (fewest conceded)": -(s.goals_against / s.played),
    "Control (share of shots)": s.shot_share,
    "Home form": s.home_ppg,
    "Away form": s.away_ppg,
    "Squad value (vs era)": s.squad_value_vs_avg,
    "Squad stability": s.stability_pct,
    "Youth (younger = higher)": -s.avg_age_weighted,
}).rank(pct=True) * 100
raw_text = {
    "Attack (goals per game)": lambda r: f"{r.goals_for / r.played:.2f} goals per game",
    "Defence (fewest conceded)": lambda r: f"{r.goals_against / r.played:.2f} conceded per game",
    "Control (share of shots)": lambda r: f"{100 * r.shot_share:.0f}% of shots",
    "Home form": lambda r: f"{r.home_ppg:.2f} points per home game",
    "Away form": lambda r: f"{r.away_ppg:.2f} points per away game",
    "Squad value (vs era)": lambda r: f"{r.squad_value_vs_avg:.2f}× league average",
    "Squad stability": lambda r: f"{r.stability_pct:.0f}% returning players",
    "Youth (younger = higher)": lambda r: f"average age {r.avg_age_weighted:.1f}",
}
dims = list(pct.columns)[::-1]
pa, pb = pct.loc[A.name, dims], pct.loc[B.name, dims]
fig = go.Figure()
for i, d in enumerate(dims):
    fig.add_shape(type="line", x0=min(pa[d], pb[d]), x1=max(pa[d], pb[d]), y0=i, y1=i,
                  line=dict(color="#3a3a3e", width=3))
for vals, row, colour, sym, nm in [(pa, A, A_COL, SYMBOLS[0], name_a), (pb, B, B_COL, SYMBOLS[1], name_b)]:
    fig.add_trace(go.Scatter(
        x=vals.values, y=list(range(len(dims))), mode="markers", name=nm,
        marker=dict(size=14, color=colour, symbol=sym, line=dict(width=1.5, color="#000000")),
        customdata=[raw_text[d](row) for d in dims],
        hovertemplate=f"<b>{nm}</b><br>%{{customdata}}<br>Better than %{{x:.0f}}% of team-seasons<extra></extra>"))
fig.update_yaxes(tickvals=list(range(len(dims))), ticktext=dims, showgrid=False)
fig.update_xaxes(range=[0, 101], title="Percentile (0 = lowest, 100 = highest of all 240)", showgrid=True,
                 dtick=25)
st.plotly_chart(style(fig, 420), width="stretch")
diffs = (pa - pb).sort_values()
insight(f"{name_a}'s biggest edge: **{diffs.index[-1].split(' (')[0].lower()}** "
        f"({pa[diffs.index[-1]]:.0f} vs {pb[diffs.index[-1]]:.0f}). "
        f"{name_b}'s biggest edge: **{diffs.index[0].split(' (')[0].lower()}** "
        f"({pb[diffs.index[0]]:.0f} vs {pa[diffs.index[0]]:.0f}).")

# ------------------------------------------------------------------ similar teams
st.subheader("Most similar teams in history")
st.caption("Teams from other seasons with the closest profile on squad value, spending, age, stability, "
           "goals scored and conceded, and share of shots. How did they finish?")
FEATURES = ["squad_value_vs_avg", "spend_vs_avg", "avg_age_weighted", "stability_pct",
            "gf_pg", "ga_pg", "shot_share"]
X = s.assign(gf_pg=s.goals_for / s.played, ga_pg=s.goals_against / s.played)[FEATURES]
Z = (X - X.mean()) / X.std()


def similar(row: pd.Series, k: int = 3) -> pd.DataFrame:
    z = Z.loc[row.name]
    if z.isna().any():
        return pd.DataFrame()
    dist = np.sqrt(((Z - z) ** 2).sum(axis=1, min_count=len(FEATURES)))
    dist = dist.drop(row.name).dropna()
    dist = dist[s.loc[dist.index, "season"] != row.season]   # other seasons only
    near = s.loc[dist.nsmallest(k).index].assign(distance=dist.nsmallest(k))
    return near


c1, c2 = st.columns(2, gap="large")
for col, row, nm in [(c1, A, name_a), (c2, B, name_b)]:
    near = similar(row)
    with col:
        st.markdown(f"**Most like {nm}**")
        if near.empty:
            st.caption("Not enough data for this team-season.")
            continue
        show = pd.DataFrame({
            "#": range(1, len(near) + 1),
            "Team": near.team + " " + near.season,
            "Finished": near.position.map(ordinal),
            "Points": near.points,
            "Squad value": near.squad_value_vs_avg.map(lambda v: f"{v:.2f}×"),
        })
        st.dataframe(show, hide_index=True, width="stretch")
        st.caption(f"Their average finish: {ordinal(round(near.position.mean()))} with "
                   f"{near.points.mean():.0f} points. {nm} actually finished "
                   f"{ordinal(row.position)} with {row.points}.")

footer()
