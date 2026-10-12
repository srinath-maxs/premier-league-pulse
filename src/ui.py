"""Shared helpers for the Streamlit dashboards: data loading, colours, chart styling."""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).resolve().parents[1] / "data" / "processed"

# Categorical colours, always used in this order (colour-blind-safe sequence).
# 8 is the maximum: beyond that, colours become impossible to tell apart.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100",
          "#e87ba4", "#008300", "#6250d6", "#e34948"]
# A different marker shape per club, so clubs never rely on colour alone
SYMBOLS = ["circle", "square", "diamond", "triangle-up",
           "star", "cross", "triangle-down", "pentagon"]
MAX_CLUBS = len(SERIES)
OTHER = "#b9b8b2"          # everything not highlighted
INK_MUTED = "#8a8984"
GOOD, BAD = "#1baf7a", "#e34948"


@st.cache_data
def load():
    s = pd.read_csv(DATA / "team_seasons.csv")
    lg = pd.read_csv(DATA / "league_seasons.csv")
    tm = pd.read_csv(DATA / "team_matches.csv", parse_dates=["date"])
    mc = pd.read_csv(DATA / "manager_changes.csv", parse_dates=["date_of_vacancy"])
    bc = pd.read_csv(DATA / "bounce_comparison.csv")
    return s, lg, tm, mc, bc


def seasons(s: pd.DataFrame) -> list[str]:
    return sorted(s.season.unique())


SHORT_NAMES = {"Manchester City": "Man City", "Manchester United": "Man Utd",
               "Nottingham Forest": "Forest", "Newcastle United": "Newcastle"}


def short(team: str) -> str:
    return SHORT_NAMES.get(team, team)


def eur_m(x) -> str:
    """€1,234,000,000 -> '€1,234m'"""
    if pd.isna(x):
        return "–"
    return f"€{x / 1e6:,.0f}m"


def style(fig: go.Figure, height: int = 420, legend: bool = True) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=8, r=8, t=36, b=8),
        hoverlabel=dict(font_size=13),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, title=None),
        font=dict(size=13),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, ticks="outside", ticklen=4)
    fig.update_yaxes(gridwidth=1, zeroline=False)
    return fig


def insight(text: str) -> None:
    """A plain-English takeaway box under a chart."""
    st.info(text, icon="💡")


def footer() -> None:
    st.divider()
    st.caption(
        "Data: match results from football-data.co.uk; squads, market values and transfers "
        "from Transfermarkt; managerial changes from Wikipedia. Money in euros. "
        "2025/26 squad figures use early-season data only. "
        "Built by V. Srinath · [GitHub](https://github.com/srinath-maxs/premier-league-pulse)")
