"""Home page."""
import streamlit as st

from ui import footer, load

s, lg, tm, mc, bc = load()
full = s[s.season != "2025/26"]
r_value = full[["points", "squad_value_vs_avg"]].corr().iloc[0, 1]
r_age = full[["points", "avg_age_weighted"]].corr().iloc[0, 1]
allc = bc[bc.bucket == "All changes"].iloc[0]
luck_share = allc.kept_gain / allc.changed_gain

st.title("⚽ Premier League Pulse")
st.markdown(
    "#### What actually drives success in the Premier League: money, youth, stability or the manager?\n"
    f"Every season from **2014/15 to 2025/26**: {len(tm) // 2:,} matches and {len(s)} team-seasons, "
    "combining results with squad value, transfers, squad age and managerial changes.")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Money → points", f"r = {r_value:.2f}",
          help="Correlation between points and squad value relative to that season's average "
               "(2014/15–2024/25). 1.0 would be a perfect link.")
c2.metric("Age → points", f"r = {r_age:.2f}",
          help="Correlation between points and appearance-weighted squad age. Close to zero.")
c3.metric("Home advantage with no fans", f"{lg.set_index('season').loc['2020/21', 'home_advantage_ppg']:+.2f} PPG",
          help="2020/21 was played in empty stadiums. Home teams earned fewer points per game "
               "than away teams for the first time.")
c4.metric("New-manager bounce that is just luck", f"{luck_share:.0%}",
          help="Teams that sacked their manager improved by "
               f"{allc.changed_gain:.2f} points per game; similar teams that kept their manager "
               f"improved by {allc.kept_gain:.2f} anyway.")

st.divider()
st.subheader("Explore")
a, b, c = st.columns(3)
with a:
    st.page_link("views/league_overview.py", label="**League Overview**", icon="📊")
    st.caption("Spending vs points, age, managers, club trends and league health, filtered by season.")
with b:
    st.markdown("🆚 **Team Comparison**  \n*coming next*")
    st.caption("Any team and season against any other, e.g. Arsenal 2025/26 vs Liverpool 2019/20.")
with c:
    st.markdown("🔮 **Season Predictor**  \n*coming soon*")
    st.caption("Title, top-4 and relegation odds from 10,000 simulated seasons.")

footer()
