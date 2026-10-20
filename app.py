"""Premier League Pulse: entry point.

Run locally:  streamlit run app.py
"""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent / "src"))

st.set_page_config(page_title="Premier League Pulse", page_icon="⚽", layout="wide")

nav = st.navigation([
    st.Page("views/home.py", title="Home", icon="⚽", default=True),
    st.Page("views/league_overview.py", title="League Overview", icon="📊"),
    st.Page("views/team_comparison.py", title="Team Comparison", icon="🆚"),
])
nav.run()
