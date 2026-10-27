"""League Overview: how money, age, managers and the league itself have changed."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ui import BAD, GOOD, MAX_CLUBS, OTHER, SERIES, SYMBOLS, eur_m, footer, insight, load, seasons, short, style

s_all, lg_all, tm, mc_all, bc = load()
ALL_SEASONS = seasons(s_all)
CLUBS = sorted(s_all.team.unique())

st.title("📊 League Overview")
st.caption("How money, squad age, managers and the league itself have shaped the Premier League.")

# ------------------------------------------------------------------ filters
f1, f2 = st.columns([3, 2])
with f1:
    lo, hi = st.select_slider("Seasons", options=ALL_SEASONS,
                              value=(ALL_SEASONS[0], ALL_SEASONS[-1]))
with f2:
    highlight = st.multiselect(f"Highlight clubs (up to {MAX_CLUBS})", CLUBS, max_selections=MAX_CLUBS,
                               default=["Arsenal", "Liverpool", "Manchester City"])

chosen = ALL_SEASONS[ALL_SEASONS.index(lo): ALL_SEASONS.index(hi) + 1]
s = s_all[s_all.season.isin(chosen)].copy()
lg = lg_all[lg_all.season.isin(chosen)]
mc = mc_all[mc_all.season.isin(chosen)]
span = lo if lo == hi else f"{lo} – {hi}"
COLOR = {club: SERIES[i] for i, club in enumerate(highlight)}
SHAPE = {club: SYMBOLS[i] for i, club in enumerate(highlight)}

# ------------------------------------------------------------------ KPI row
champs = lg.champion.value_counts()
k1, k2, k3, k4 = st.columns(4)
k1.metric("Most titles" if len(lg) > 1 else "Champion",
          f"{short(champs.index[0])} ×{champs.iloc[0]}" if len(lg) > 1 else short(champs.index[0]),
          help="Champions: " + ", ".join(f"{c} ({n})" for c, n in champs.items()))
k2.metric("Points needed to stay up", f"{lg.safety_points.mean():.0f}",
          help="Average points of the 17th-placed team (the last safe spot).")
k3.metric("Home advantage", f"{lg.home_advantage_ppg.mean():+.2f} PPG",
          help="Average extra points per game home teams earned compared with away teams.")
k4.metric("Transfer spend (all clubs)", eur_m(lg.total_transfer_spend_eur.sum()))


def scatter(df, x, y, xtitle, ytitle, hover_x):
    """Every team-season as a dot: highlighted clubs in colour, the rest grey."""
    fig = go.Figure()
    rest = df[~df.team.isin(highlight)]
    hover = ("<b>%{customdata[0]} %{customdata[1]}</b><br>Finished %{customdata[2]}"
             "<br>" + hover_x + "<br>Points: %{y}<extra></extra>")
    cd = ["team", "season", "pos_label", "hover_x"]
    fig.add_trace(go.Scatter(x=rest[x], y=rest[y], mode="markers", name="Other clubs",
                             marker=dict(size=8, color=OTHER, opacity=0.55),
                             customdata=rest[cd], hovertemplate=hover))
    for club in highlight:
        d = df[df.team == club]
        fig.add_trace(go.Scatter(
            x=d[x], y=d[y], mode="markers", name=club,
            marker=dict(size=11, color=COLOR[club], symbol=SHAPE[club], line=dict(width=1.5, color="#fcfcfb")),
            customdata=d[cd], hovertemplate=hover))
    # Straight-line trend through all dots
    ok = df[[x, y]].dropna()
    if len(ok) > 5:
        b, a = np.polyfit(ok[x], ok[y], 1)
        xs = np.linspace(ok[x].min(), ok[x].max(), 50)
        fig.add_trace(go.Scatter(x=xs, y=a + b * xs, mode="lines", name="Trend",
                                 line=dict(color=INK, width=2, dash="dot"), hoverinfo="skip"))
    fig.update_xaxes(title=xtitle)
    fig.update_yaxes(title=ytitle)
    return style(fig, 460)


INK = "#52514e"
s["pos_label"] = s.position.map(lambda p: f"{p}{'st' if p == 1 else 'nd' if p == 2 else 'rd' if p == 3 else 'th'}")

tab_money, tab_squad, tab_mgr, tab_trend, tab_league, tab_table = st.tabs(
    ["💰 Money", "🧒 Age & stability", "🧑‍💼 Managers", "📈 Club trends",
     "🏟️ League health", "📋 Final tables"])

# ------------------------------------------------------------------ money
with tab_money:
    st.subheader("Does money buy points?")
    measure = st.radio("Measure of spending power",
                       ["Squad value (vs season average)", "Transfer spend (vs season average)"],
                       horizontal=True)
    col = "squad_value_vs_avg" if measure.startswith("Squad") else "spend_vs_avg"
    raw = "squad_value_eur" if col == "squad_value_vs_avg" else "transfer_spend_eur"
    d = s.dropna(subset=[col]).copy()
    d["hover_x"] = d[raw].map(eur_m) + " (" + d[col].map(lambda v: f"{v:.2f}") + "× average)"
    st.plotly_chart(scatter(d, col, "points", "Spending power (1.0 = league average that season)",
                            "Points", "%{customdata[3]}"), width="stretch")
    r = d[[col, "points"]].corr().iloc[0, 1]
    b = np.polyfit(d[col], d.points, 1)[0]
    insight(f"**{span}:** correlation r = {r:.2f}. On average, a club with twice the league-average "
            f"{'squad value' if col == 'squad_value_vs_avg' else 'transfer spend'} earned about "
            f"**{b:.0f} more points** than an average one."
            + (" Squad value is the stronger predictor: what a club *has* matters more than what it "
               "spent this summer." if col == "squad_value_vs_avg" else
               " Transfer spend is a weaker predictor than squad value: one summer's spending "
               "says less than the whole squad's quality."))

    st.markdown("##### Who beat their budget, and who wasted it?")
    st.caption("Places above (+) or below (−) where their squad value ranked them that season.")
    d = s.dropna(subset=["over_performance"]).copy()
    d["label"] = d.team + " " + d.season.str[2:]
    left, right = st.columns(2)
    for colm, title, asc, colour in [(left, "Best over-performers", False, GOOD),
                                     (right, "Biggest under-performers", True, BAD)]:
        top = d.sort_values(["over_performance", "points"], ascending=[asc, asc]).head(10)[::-1]
        fig = go.Figure(go.Bar(
            x=top.over_performance.abs(), y=top.label, orientation="h", marker_color=colour,
            text=top.over_performance.map(lambda v: f"{v:+.0f} places"), textposition="outside",
            cliponaxis=False,
            customdata=top[["pos_label", "squad_value_rank", "points"]],
            hovertemplate="<b>%{y}</b><br>Finished %{customdata[0]} with %{customdata[2]} pts"
                          "<br>Squad value rank: %{customdata[1]}<extra></extra>"))
        fig.update_layout(title=title)
        fig.update_xaxes(visible=False, range=[0, d.over_performance.abs().max() * 1.3])
        with colm:
            st.plotly_chart(style(fig, 400, legend=False), width="stretch")
    best = d.sort_values("over_performance", ascending=False).iloc[0]
    insight(f"**{best.team} {best.season}** is the biggest over-achievement in this period: "
            f"the {int(best.squad_value_rank)}th most valuable squad finished {best.pos_label}.")

# ------------------------------------------------------------------ age & stability
with tab_squad:
    st.subheader("Does a younger or older squad do better?")
    d = s.dropna(subset=["avg_age_weighted"]).copy()
    d["hover_x"] = "Average age: " + d.avg_age_weighted.map(lambda v: f"{v:.1f}")
    st.plotly_chart(scatter(d, "avg_age_weighted", "points",
                            "Average age (weighted by appearances)", "Points", "%{customdata[3]}"),
                    width="stretch")

    bands = pd.cut(d.avg_age_weighted, [0, 25, 26, 27, 28, 99],
                   labels=["Under 25", "25–26", "26–27", "27–28", "28+"], right=False)
    by = d.groupby(bands, observed=True).agg(points=("points", "mean"), n=("team", "size"),
                                              value=("squad_value_vs_avg", "mean")).reset_index()
    by.columns = ["band", "points", "n", "value"]
    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure(go.Bar(
            x=by.band.astype(str), y=by.points, marker_color=SERIES[0],
            text=by.points.map(lambda v: f"{v:.0f}"), textposition="outside",
            customdata=by[["n", "value"]],
            hovertemplate="<b>%{x}</b><br>Average points: %{y:.1f}<br>Team-seasons: %{customdata[0]}"
                          "<br>Avg squad value: %{customdata[1]:.2f}× league average<extra></extra>"))
        fig.update_layout(title="Average points by squad age")
        fig.update_yaxes(title="Points", rangemode="tozero")
        st.plotly_chart(style(fig, 360, legend=False), width="stretch")
    with c2:
        fig = go.Figure(go.Scatter(
            x=lg.season, y=lg.avg_age_weighted, mode="lines+markers",
            line=dict(color=SERIES[0], width=2), marker=dict(size=8),
            hovertemplate="%{x}: %{y:.2f} years<extra></extra>"))
        fig.update_layout(title="League average age by season")
        fig.update_yaxes(title="Years")
        st.plotly_chart(style(fig, 360, legend=False), width="stretch")
    r_age = d[["avg_age_weighted", "points"]].corr().iloc[0, 1]
    best_band = by.loc[by.points.idxmax()]
    richest = by.loc[by.value.idxmax()]
    text = (f"Age on its own barely matters (r = {r_age:.2f}). Squads aged **{best_band.band}** earned the "
            f"most points on average ({best_band.points:.0f}, from {best_band.n} team-seasons)")
    if richest.band == best_band.band:
        text += (f", but they were also the richest ({best_band.value:.2f}× average squad value). "
                 "Money, not age, is doing the work.")
    else:
        text += "."
    insight(text)

    st.subheader("Does keeping the squad together help?")
    d = s.dropna(subset=["stability_pct"]).copy()
    d["hover_x"] = "Returning players: " + d.stability_pct.map(lambda v: f"{v:.0f}%") + " of appearances"
    st.plotly_chart(scatter(d, "stability_pct", "points",
                            "Share of appearances by players who were at the club last season (%)",
                            "Points", "%{customdata[3]}"), width="stretch")
    r_st = d[["stability_pct", "points"]].corr().iloc[0, 1]
    insight(f"Stability matters more than age (r = {r_st:.2f}). Partly this is cause and effect "
            "the other way round: successful clubs keep their players, struggling clubs rebuild.")

# ------------------------------------------------------------------ managers
with tab_mgr:
    st.subheader("Is the \"new manager bounce\" real?")
    allc = bc[bc.bucket == "All changes"].iloc[0]
    m1, m2, m3 = st.columns(3)
    m1.metric("Managers who left mid-season", f"{len(mc)}",
              help=f"In {span}. Worked out from match records; short caretaker stints and "
                   "temporary stand-ins (e.g. a manager missing one game) are not counted.")
    m2.metric("Improvement after a change", f"{allc.changed_gain:+.2f} PPG",
              help="Points per game in the 10 games after the change minus the 10 games before.")
    m3.metric("Improvement if manager kept", f"{allc.kept_gain:+.2f} PPG",
              help="Clubs on equally bad 10-game runs that did not change manager.")

    b = bc[bc.bucket != "All changes"]
    fig = go.Figure()
    for name, colm, colour in [("Changed manager", "changed_gain", SERIES[0]),
                               ("Kept manager", "kept_gain", SERIES[1])]:
        fig.add_trace(go.Bar(
            x=b.bucket, y=b[colm], name=name, marker_color=colour,
            text=b[colm].map(lambda v: f"{v:+.2f}"), textposition="outside",
            customdata=b[["changes", "control_windows"]],
            hovertemplate=f"<b>{name}</b><br>Form before: %{{x}} PPG<br>Change in PPG: %{{y:+.2f}}"
                          "<br>Cases: " + ("%{customdata[0]}" if colm == "changed_gain" else "%{customdata[1]}")
                          + "<extra></extra>"))
    fig.update_layout(barmode="group", bargap=0.3, bargroupgap=0.08,
                      title="Change in points per game over the next 10 games, by form before")
    fig.update_xaxes(title="Points per game in the 10 games before (how bad the run was)")
    fig.update_yaxes(title="Change in points per game", zeroline=True, zerolinecolor="#d6d5d0")
    fig = style(fig, 460)
    fig.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.22, x=0), margin=dict(t=48))
    st.plotly_chart(fig, width="stretch")
    insight(f"Teams that changed manager improved by **{allc.changed_gain:.2f} points per game**, but "
            f"clubs on equally bad runs that kept their manager improved by **{allc.kept_gain:.2f}** anyway. "
            f"So about **{allc.kept_gain / allc.changed_gain:.0%} of the \"bounce\" is a bad run "
            f"evening out**; the change itself adds only {allc.extra_gain_from_change:+.2f} PPG "
            f"(about {allc.extra_gain_from_change * 10:+.1f} points over 10 games). "
            "This uses all 12 seasons, whatever the season filter.")
    st.caption("Method: compares each change (with 10+ games before and after) against every "
               "10-game run by clubs that made no change within four months, grouped by how bad "
               f"the run was. {int(allc.changes)} changes vs {int(allc.control_windows):,} comparison runs. "
               "The worst-form group is small (36 comparison runs), so read it with care.")

    st.markdown("##### Every mid-season departure")
    show = mc.sort_values("date_of_vacancy", ascending=False)[
        ["season", "team", "outgoing_manager", "manner_of_departure", "caretaker", "incoming_manager",
         "date_of_vacancy", "ppg_last10_before", "ppg_next10_after", "bounce_ppg"]]
    st.dataframe(show, hide_index=True, width="stretch", column_config={
        "season": "Season", "team": "Club", "outgoing_manager": "Out", "incoming_manager": "Next manager",
        "caretaker": "Caretaker in between",
        "manner_of_departure": "How", "date_of_vacancy": st.column_config.DateColumn("Date"),
        "ppg_last10_before": st.column_config.NumberColumn("PPG before", format="%.2f",
                                                           help="Last 10 games (or fewer)"),
        "ppg_next10_after": st.column_config.NumberColumn("PPG after", format="%.2f",
                                                          help="Next 10 games (or fewer)"),
        "bounce_ppg": st.column_config.NumberColumn("Change", format="%+.2f")})

# ------------------------------------------------------------------ club trends
with tab_trend:
    st.subheader("How clubs have changed over time")
    t1, t2 = st.columns([3, 2])
    with t1:
        clubs = st.multiselect(f"Clubs (up to {MAX_CLUBS})", CLUBS, max_selections=MAX_CLUBS,
                               default=highlight or ["Arsenal"], key="trend_clubs")
    metrics = {
        "League position": ("position", "Position", lambda v: f"{v:.0f}"),
        "Points": ("points", "Points", lambda v: f"{v:.0f}"),
        "Squad value (vs league average)": ("squad_value_vs_avg", "× league average", lambda v: f"{v:.2f}×"),
        "Squad value (€m)": ("squad_value_m", "€m", lambda v: f"€{v:,.0f}m"),
        "Transfer spend (€m)": ("spend_m", "€m", lambda v: f"€{v:,.0f}m"),
        "Average age": ("avg_age_weighted", "Years", lambda v: f"{v:.1f}"),
        "Squad stability (%)": ("stability_pct", "% of appearances", lambda v: f"{v:.0f}%"),
    }
    with t2:
        metric = st.selectbox("Measure", list(metrics))
    colm, ytitle, fmt = metrics[metric]
    d = s.assign(squad_value_m=s.squad_value_eur / 1e6, spend_m=s.transfer_spend_eur / 1e6)
    fig = go.Figure()
    for i, club in enumerate(clubs):
        c = d[d.team == club].sort_values("season")
        c = c.set_index("season").reindex(chosen).reset_index()   # gaps for seasons out of the PL
        mgr = c.manager.fillna("") + np.where(c.new_manager == True, " (new)", "")
        fig.add_trace(go.Scatter(
            x=c.season, y=c[colm], name=club, mode="lines+markers", connectgaps=False,
            line=dict(color=SERIES[i], width=2),
            marker=dict(size=9, symbol=SYMBOLS[i], line=dict(width=1.5, color="#fcfcfb")),
            customdata=np.stack([mgr, c.position.fillna(0)], axis=-1),
            hovertemplate=f"<b>{club} %{{x}}</b><br>{metric}: %{{y}}<br>Manager: %{{customdata[0]}}"
                          "<extra></extra>"))
    fig.update_yaxes(title=ytitle)
    if colm == "position":
        worst = d[d.team.isin(clubs)].position.max() if clubs else 20
        fig.update_yaxes(range=[worst + 0.5, 0.5], tickvals=[1, 4, 8, 12, 17, 20],
                         title="League position (1 = champions)")
    fig.update_xaxes(type="category", categoryorder="array", categoryarray=chosen)
    st.plotly_chart(style(fig, 460), width="stretch")
    st.caption("Gaps mean the club was not in the Premier League that season. "
               "Hover to see the manager; \"(new)\" marks a different manager from the year before.")
    if clubs:
        lines = []
        for club in clubs:
            c = d[d.team == club].sort_values("season").dropna(subset=[colm])
            if len(c) >= 2:
                first, last = c.iloc[0], c.iloc[-1]
                lines.append(f"**{club}**: {fmt(first[colm])} in {first.season} → "
                             f"{fmt(last[colm])} in {last.season}")
        if lines:
            insight("  \n".join(lines))

# ------------------------------------------------------------------ league health
with tab_league:
    st.subheader("Home advantage, and the season without fans")
    colours = [SERIES[1] if f.startswith("No") else SERIES[0] for f in lg.fans_in_stadiums]
    fig = go.Figure(go.Bar(
        x=lg.season, y=lg.home_advantage_ppg, marker_color=colours,
        text=lg.home_advantage_ppg.map(lambda v: f"{v:+.2f}"), textposition="outside",
        customdata=lg[["home_win_pct", "away_win_pct", "fans_in_stadiums"]],
        hovertemplate="<b>%{x}</b><br>Home advantage: %{y:+.2f} PPG<br>Home wins: %{customdata[0]:.0f}%"
                      "<br>Away wins: %{customdata[1]:.0f}%<br>Fans: %{customdata[2]}<extra></extra>"))
    if "2020/21" in set(lg.season):
        v = lg.set_index("season").loc["2020/21", "home_advantage_ppg"]
        fig.add_annotation(x="2020/21", y=max(v, 0) + 0.12, text="<b>No fans</b>", showarrow=False,
                           font=dict(color="#52514e"))
    fig.update_yaxes(title="Extra points per game for home teams", zeroline=True, zerolinecolor="#d6d5d0")
    fig.update_xaxes(type="category")
    st.plotly_chart(style(fig, 380, legend=False), width="stretch")
    normal = lg[~lg.fans_in_stadiums.str.startswith("No")].home_advantage_ppg.mean()
    if "2020/21" in set(lg.season):
        insight(f"With fans, home teams earned about **{normal:+.2f} extra points per game**. In 2020/21, "
                f"played behind closed doors, that advantage **disappeared** "
                f"({v:+.2f}): the crowd is a big part of home advantage.")

    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure(go.Scatter(
            x=lg.season, y=lg.big_six_gap, mode="lines+markers", line=dict(color=SERIES[0], width=2),
            marker=dict(size=8), customdata=lg[["big_six_avg_points", "rest_avg_points"]],
            hovertemplate="<b>%{x}</b><br>Gap: %{y:.1f} points<br>Big Six average: %{customdata[0]:.1f}"
                          "<br>Everyone else: %{customdata[1]:.1f}<extra></extra>"))
        fig.update_layout(title="Big Six vs the rest (average points gap)")
        fig.update_yaxes(title="Points", rangemode="tozero")
        fig.update_xaxes(type="category")
        st.plotly_chart(style(fig, 340, legend=False), width="stretch")
    with c2:
        fig = go.Figure(go.Scatter(
            x=lg.season, y=lg.safety_points, mode="lines+markers", line=dict(color=SERIES[0], width=2),
            marker=dict(size=8), hovertemplate="<b>%{x}</b><br>17th place: %{y} points<extra></extra>"))
        fig.update_layout(title="Points needed to survive (17th place)")
        fig.update_yaxes(title="Points")
        fig.update_xaxes(type="category")
        st.plotly_chart(style(fig, 340, legend=False), width="stretch")
    if len(lg) > 1:
        tight = lg.loc[lg.big_six_gap.idxmin()]
        wide = lg.loc[lg.big_six_gap.idxmax()]
        insight(f"The Big Six were furthest ahead in **{wide.season}** ({wide.big_six_gap:.0f} points per team) "
                f"and closest in **{tight.season}** ({tight.big_six_gap:.0f}).")

    st.subheader("Promoted teams: who survives?")
    p = s[s.promoted == True].copy()
    if len(p):
        p["fate"] = np.where(p.position <= 17, "Survived", "Relegated")
        per = p.groupby("season").fate.apply(lambda f: (f == "Survived").sum()).reindex(chosen).dropna()
        c1, c2 = st.columns([3, 2])
        with c1:
            fig = go.Figure(go.Bar(x=per.index, y=per.values, marker_color=SERIES[0],
                                   text=[f"{int(v)} of 3" for v in per.values], textposition="outside",
                                   hovertemplate="%{x}: %{y} of 3 survived<extra></extra>"))
            fig.update_layout(title="Promoted teams that stayed up")
            fig.update_yaxes(range=[0, 3.6], dtick=1, title="Teams")
            fig.update_xaxes(type="category")
            st.plotly_chart(style(fig, 320, legend=False), width="stretch")
        with c2:
            comp = p.groupby("fate").agg(clubs=("team", "size"),
                                         value=("squad_value_vs_avg", "mean"),
                                         spend=("spend_vs_avg", "mean"),
                                         age=("avg_age_weighted", "mean"),
                                         stability=("stability_pct", "mean"))
            st.markdown("**Survivors vs relegated**")
            st.dataframe(comp.T.rename(index={
                "clubs": "Clubs", "value": "Squad value (× avg)", "spend": "Transfer spend (× avg)",
                "age": "Average age", "stability": "Stability (%)"}).round(2), width="stretch")
        if {"Survived", "Relegated"} <= set(p.fate):
            sv, rl = comp.loc["Survived"], comp.loc["Relegated"]
            insight(f"{int(sv.clubs)} of {len(p)} promoted teams survived. Survivors had a "
                    f"{sv.value:.2f}× average squad value vs {rl.value:.2f}× for those relegated, and "
                    f"spent {sv.spend:.2f}× vs {rl.spend:.2f}× the league average on transfers.")
    else:
        st.caption("No promoted teams in this range (2014/15 has no promotion data).")

# ------------------------------------------------------------------ tables
with tab_table:
    season = st.selectbox("Season", chosen[::-1])
    t = s[s.season == season].sort_values("position").assign(
        value_m=lambda x: x.squad_value_eur / 1e6, spend_m=lambda x: x.transfer_spend_eur / 1e6,
        net_m=lambda x: x.net_spend_eur / 1e6)
    st.dataframe(
        t[["position", "team", "played", "wins", "draws", "losses", "goal_difference", "points",
           "avg_age_weighted", "value_m", "spend_m", "net_m", "stability_pct", "manager"]],
        hide_index=True, width="stretch", height=740,
        column_config={
            "position": "Pos", "team": "Club", "played": "P", "wins": "W", "draws": "D",
            "losses": "L", "goal_difference": "GD", "points": "Pts",
            "avg_age_weighted": st.column_config.NumberColumn("Avg age", format="%.1f"),
            "value_m": st.column_config.NumberColumn("Squad value", format="€%.0fm"),
            "spend_m": st.column_config.NumberColumn("Spent", format="€%.0fm"),
            "net_m": st.column_config.NumberColumn("Net spend", format="€%.0fm"),
            "stability_pct": st.column_config.NumberColumn("Stability", format="%.0f%%"),
            "manager": "Manager (end of season)"})
    notes = t[t.points_deduction != 0]
    for _, n in notes.iterrows():
        st.caption(f"{n.team}: {int(n.points_deduction)} point deduction.")
    if season == "2025/26":
        st.caption("2025/26 squad age, value and stability use early-season data only.")

footer()
