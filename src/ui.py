"""Shared helpers for the Streamlit dashboards: theme, data loading, colours, chart styling."""
import html
import re
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).resolve().parents[1] / "data" / "processed"
APP_NAME = "Premier League Dashboard"
LIVE_URL = "https://pl-tracker-srinath-8keccaagskcutxicsgvjqu.streamlit.app"
GITHUB_URL = "https://github.com/srinath-maxs/premier-league-pulse"

# ---------------------------------------------------------------- design tokens
BG = "#000000"          # page: true black, like Instagram's dark mode
SURFACE = "#121212"     # floating controls and cards
RAISED = "#1c1c1e"      # hover / selected
LINE = "#262626"        # hairline borders
INK = "#f5f5f5"         # main text
MUTED = "#a8a8a8"       # secondary text
IG_GRADIENT = "linear-gradient(45deg, #feda75 0%, #fa7e1e 25%, #d62976 50%, #962fbf 75%, #4f5bd5 100%)"

# Chart colours, always used in this order. These are the dark-mode steps of a
# colour-blind-safe palette, checked against the black background.
SERIES = ["#3987e5", "#d95926", "#199e70", "#c98500",
          "#d55181", "#008300", "#9085e9", "#e66767"]
# A different marker shape per club, so clubs never rely on colour alone
SYMBOLS = ["circle", "square", "diamond", "triangle-up",
           "star", "cross", "triangle-down", "pentagon"]
MAX_CLUBS = len(SERIES)
OTHER = "#5a5a5e"       # everything not highlighted
INK_MUTED = MUTED
GOOD, BAD = "#199e70", "#e66767"
GRID = "#1f1f22"
ZERO = "#3a3a3e"


def apply_theme() -> None:
    """Instagram-style dark theme: floating controls, soft depth, smooth motion."""
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700;800&display=swap');

html, body, .stApp, .stMarkdown, p, li, label, input, textarea, button,
h1, h2, h3, h4, h5, h6, [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {{
  font-family: 'Figtree', -apple-system, BlinkMacSystemFont, sans-serif !important;
}}
.stApp :is(div, span, a, p, li, label, button, input, h1, h2, h3, h4, h5, h6)
  :not([data-testid="stIconMaterial"]):not(.material-symbols-rounded) {{
  font-family: 'Figtree', -apple-system, BlinkMacSystemFont, sans-serif !important;
}}
[data-testid="stIconMaterial"], .material-symbols-rounded {{
  font-family: 'Material Symbols Rounded' !important;
}}

.stApp {{ background: {BG}; }}
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stMainBlockContainer"] {{ padding-top: 3rem; max-width: 1280px; }}

h1 {{ font-weight: 800 !important; letter-spacing: -0.03em; }}
h2, h3 {{ font-weight: 700 !important; letter-spacing: -0.015em; }}
p, li {{ color: {INK}; }}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {{ color: {MUTED} !important; }}
hr {{ border-color: {LINE} !important; }}

/* ---------- sidebar ---------- */
[data-testid="stSidebar"] {{ background: {BG}; border-right: 1px solid {LINE}; }}
[data-testid="stSidebarNav"] a {{
  border-radius: 12px; margin: 2px 8px; padding: 10px 12px !important;
  transition: background .2s ease;
}}
[data-testid="stSidebarNav"] a:hover {{ background: {SURFACE}; }}
[data-testid="stSidebarNav"] a[aria-current="page"] {{ background: {RAISED}; }}
[data-testid="stSidebarNav"] a[aria-current="page"] span {{ font-weight: 700; }}

/* ---------- floating controls ---------- */
[data-baseweb="select"] > div, [data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input {{
  background: {SURFACE} !important; border: 1px solid {LINE} !important;
  border-radius: 14px !important;
  box-shadow: 0 6px 20px rgba(0,0,0,.55), inset 0 1px 0 rgba(255,255,255,.03);
  transition: transform .2s ease, border-color .2s ease, box-shadow .2s ease;
}}
[data-baseweb="select"] > div:hover {{
  transform: translateY(-1px); border-color: #3a3a3e !important;
  box-shadow: 0 10px 28px rgba(0,0,0,.7), inset 0 1px 0 rgba(255,255,255,.04);
}}
[data-baseweb="popover"] ul, [data-baseweb="menu"] {{
  background: {RAISED} !important; border-radius: 14px !important; border: 1px solid {LINE};
}}
[data-baseweb="tag"] {{ border-radius: 999px !important; }}

/* slider handle: white with a soft glow */
[data-testid="stSlider"] [role="slider"] {{
  background: #fff !important; box-shadow: 0 0 0 5px rgba(0,149,246,.22) !important;
}}

/* radio as floating pills */
[data-testid="stRadio"] [role="radiogroup"] {{ gap: 8px; }}
[data-testid="stRadio"] label[data-baseweb="radio"] {{
  background: {SURFACE}; border: 1px solid {LINE}; border-radius: 999px;
  padding: 8px 16px 8px 12px; box-shadow: 0 6px 20px rgba(0,0,0,.55);
  transition: transform .2s ease, border-color .2s ease;
}}
[data-testid="stRadio"] label[data-baseweb="radio"]:hover {{ transform: translateY(-1px); border-color: #3a3a3e; }}

/* tabs as a floating pill bar */
[data-testid="stTabs"] [role="tablist"] {{
  background: {SURFACE}; border: 1px solid {LINE}; border-radius: 999px;
  padding: 5px; gap: 2px; width: fit-content; max-width: 100%; overflow-x: auto;
  box-shadow: 0 10px 30px rgba(0,0,0,.6);
}}
[data-testid="stTabs"] [role="tab"] {{
  border-radius: 999px; padding: 8px 16px; height: auto; color: {MUTED};
  transition: background .2s ease, color .2s ease;
}}
[data-testid="stTabs"] [role="tab"]:hover {{ color: {INK}; }}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{ background: {RAISED}; color: {INK}; }}
[data-testid="stTab"] > div:not([data-testid]),
[data-testid="stTabs"] [data-baseweb="tab-highlight"],
[data-testid="stTabs"] [data-baseweb="tab-border"] {{ display: none; }}
[data-testid="stTab"] p {{ color: inherit; }}

/* metrics as quiet floating tiles */
[data-testid="stMetric"] {{
  background: {SURFACE}; border: 1px solid {LINE}; border-radius: 18px;
  padding: 16px 18px; box-shadow: 0 10px 30px rgba(0,0,0,.6);
}}
[data-testid="stMetricLabel"] p {{ color: {MUTED} !important; }}
[data-testid="stMetricValue"] {{ font-weight: 700; letter-spacing: -0.02em; font-size: 1.7rem; }}

/* page links (used inside the sidebar and elsewhere) */
[data-testid="stPageLink"] a {{ border-radius: 12px; }}

/* tables and charts sit on soft cards */
[data-testid="stDataFrame"] {{
  border: 1px solid {LINE}; border-radius: 16px; overflow: hidden;
  box-shadow: 0 10px 30px rgba(0,0,0,.6);
}}

/* tooltips (the ⓘ next to headings and labels) */
[data-baseweb="tooltip"] > div {{
  background: {RAISED} !important; color: {INK} !important; border: 1px solid #333;
  border-radius: 12px !important; box-shadow: 0 12px 32px rgba(0,0,0,.7);
}}

/* insight cards: hairline Instagram-gradient edge */
.pl-insight {{
  position: relative; margin: 6px 0 22px; padding: 14px 18px 14px 20px;
  border-radius: 16px; background: {SURFACE}; color: {INK};
  border: 1px solid {LINE}; box-shadow: 0 10px 30px rgba(0,0,0,.6);
  line-height: 1.55; font-size: 0.98rem;
}}
.pl-insight::before {{
  content: ""; position: absolute; left: 0; top: 12px; bottom: 12px; width: 3px;
  border-radius: 3px; background: {IG_GRADIENT};
}}
.pl-insight b {{ color: #fff; }}

@media (prefers-reduced-motion: reduce) {{
  * {{ transition: none !important; animation: none !important; }}
}}
</style>
""", unsafe_allow_html=True)


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
    """Dark chart styling: transparent background, quiet grid, readable labels."""
    fig.update_layout(
        height=height, margin=dict(l=8, r=8, t=40, b=8),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Figtree, sans-serif", size=13, color=INK),
        title_font=dict(size=15, color=INK),
        hoverlabel=dict(bgcolor=RAISED, bordercolor="#333333", font=dict(color=INK, size=13,
                                                                         family="Figtree, sans-serif")),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, title=None,
                    font=dict(color=MUTED)),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, ticks="outside", ticklen=4, tickcolor=LINE,
                     linecolor=LINE, tickfont=dict(color=MUTED), title_font=dict(color=MUTED))
    fig.update_yaxes(gridwidth=1, gridcolor=GRID, zeroline=False, tickfont=dict(color=MUTED),
                     title_font=dict(color=MUTED))
    fig.update_traces(selector=dict(type="bar"), textfont=dict(color=INK))
    return fig


def _md_to_html(text: str) -> str:
    t = html.escape(text)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<i>\1</i>", t)
    return t.replace("  \n", "<br>").replace("\n", "<br>")


def insight(text: str) -> None:
    """A plain-English takeaway under a chart."""
    st.markdown(f'<div class="pl-insight">{_md_to_html(text)}</div>', unsafe_allow_html=True)


def footer() -> None:
    st.divider()
    st.caption(
        "Data: match results from football-data.co.uk; squads, market values, transfers and "
        "managers from Transfermarkt; how each manager left from Wikipedia. Money in euros. "
        "2025/26 squad figures use early-season data only. "
        f"Built by V. Srinath · [Live app]({LIVE_URL}) · [GitHub]({GITHUB_URL})")
