"""Home page: just the name and three story-ring buttons."""
import streamlit as st

from ui import APP_NAME, GITHUB_URL, ACCENT_GRADIENT, INK, LINE, MUTED, SURFACE

ICON_OVERVIEW = """<svg viewBox="0 0 24 24" width="34" height="34" fill="none" stroke="currentColor"
 stroke-width="1.8" stroke-linecap="round"><path d="M5 20V12"/><path d="M12 20V5"/><path d="M19 20v-9"/></svg>"""
ICON_COMPARE = """<svg viewBox="0 0 24 24" width="34" height="34" fill="none" stroke="currentColor"
 stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 8h13"/><path d="M14 4.5 17.5 8 14 11.5"/>
 <path d="M20 16H7"/><path d="M10 12.5 6.5 16l3.5 3.5"/></svg>"""
ICON_PREDICT = """<svg viewBox="0 0 24 24" width="34" height="34" fill="none" stroke="currentColor"
 stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 17l5-5 4 3 4-6"/>
 <path d="M16 9l5-3" stroke-dasharray="1.5 2.5"/><circle cx="21" cy="6" r="1.2" fill="currentColor"/></svg>"""

RINGS = [
    {"href": "league_overview", "label": "League Overview", "icon": ICON_OVERVIEW, "live": True,
     "tip": "Spending vs points, squad age, managers, club trends and league health. "
            "Filter by season and highlight up to 8 clubs."},
    {"href": "team_comparison", "label": "Team Comparison", "icon": ICON_COMPARE, "live": True,
     "tip": "Any club and season against any other, even from different eras. "
            "Try Arsenal 2025/26 vs Liverpool 2019/20."},
    {"href": None, "label": "Season Predictor", "icon": ICON_PREDICT, "live": False,
     "tip": "Coming soon: title, top-4 and relegation odds from 10,000 simulated seasons."},
]

st.markdown(f"""
<style>
[data-testid="stMainBlockContainer"] {{ padding-top: 0; }}
.pl-home {{
  min-height: calc(100vh - 140px); display: flex; flex-direction: column;
  align-items: center; justify-content: center; text-align: center; gap: 56px;
}}
.pl-home h1 {{
  font-size: clamp(2.4rem, 6vw, 4.6rem); line-height: 1.02; margin: 0; padding: 0;
  font-weight: 800; letter-spacing: -0.045em; color: {INK};
}}
.pl-home .pl-range {{ color: {MUTED}; font-size: 1rem; margin-top: 14px; letter-spacing: 0.01em; }}
.pl-rings {{ display: flex; gap: clamp(28px, 6vw, 64px); flex-wrap: wrap; justify-content: center; }}
.pl-ring {{
  position: relative; display: flex; flex-direction: column; align-items: center; gap: 14px;
  text-decoration: none !important; color: {INK} !important; outline: none;
  animation: pl-rise .7s cubic-bezier(.2,.8,.2,1) both;
}}
.pl-ring:nth-child(2) {{ animation-delay: .08s; }}
.pl-ring:nth-child(3) {{ animation-delay: .16s; }}
@keyframes pl-rise {{ from {{ opacity: 0; transform: translateY(14px); }} to {{ opacity: 1; transform: none; }} }}

.pl-ring .ring {{
  width: 132px; height: 132px; border-radius: 50%; padding: 3px; background: {ACCENT_GRADIENT};
  box-shadow: 0 18px 40px rgba(0,0,0,.8);
  transition: transform .35s cubic-bezier(.2,.8,.2,1), box-shadow .35s ease;
}}
.pl-ring.off .ring {{ background: #3a3a3e; }}
.pl-ring .inner {{
  width: 100%; height: 100%; border-radius: 50%; border: 4px solid #000; background: {SURFACE};
  display: flex; align-items: center; justify-content: center; color: {INK};
}}
.pl-ring.off .inner {{ color: {MUTED}; }}
.pl-ring .name {{ font-size: 0.98rem; font-weight: 600; }}
.pl-ring.off .name {{ color: {MUTED}; }}
.pl-ring:hover .ring, .pl-ring:focus-visible .ring {{
  transform: translateY(-6px) scale(1.04);
  box-shadow: 0 26px 50px rgba(0,0,0,.9), 0 0 36px rgba(4,200,255,.30);
}}
.pl-ring.off:hover .ring {{ box-shadow: 0 26px 50px rgba(0,0,0,.9); }}
.pl-ring:focus-visible .inner {{ outline: 2px solid #0095f6; outline-offset: 2px; }}

.pl-ring .tip {{
  position: absolute; top: calc(100% + 12px); left: 50%; width: 240px;
  transform: translate(-50%, -6px); opacity: 0; pointer-events: none;
  background: #1c1c1e; color: {INK}; border: 1px solid #333; border-radius: 14px;
  padding: 12px 14px; font-size: 0.86rem; line-height: 1.45; text-align: left;
  box-shadow: 0 16px 40px rgba(0,0,0,.8); transition: opacity .2s ease, transform .2s ease; z-index: 5;
}}
.pl-ring .tip::after {{
  content: ""; position: absolute; bottom: 100%; left: 50%; transform: translateX(-50%);
  border: 7px solid transparent; border-bottom-color: #1c1c1e;
}}
.pl-ring:hover .tip, .pl-ring:focus-visible .tip {{ opacity: 1; transform: translate(-50%, 0); }}

.pl-credit {{ color: {MUTED}; font-size: 0.82rem; }}
.pl-credit a {{ color: {MUTED} !important; text-decoration: none; border-bottom: 1px solid {LINE}; }}
.pl-credit a:hover {{ color: {INK} !important; }}
@media (prefers-reduced-motion: reduce) {{ .pl-ring {{ animation: none; }} }}
</style>
""", unsafe_allow_html=True)

rings_html = ""
for r in RINGS:
    body = (f'<span class="tip" role="tooltip">{r["tip"]}</span>'
            f'<span class="ring"><span class="inner">{r["icon"]}</span></span>'
            f'<span class="name">{r["label"]}</span>')
    if r["live"]:
        rings_html += f'<a class="pl-ring" href="{r["href"]}" target="_self" aria-label="{r["label"]}">{body}</a>'
    else:
        rings_html += (f'<div class="pl-ring off" tabindex="0" aria-label="{r["label"]}, coming soon">'
                       f'{body}</div>')

st.markdown(f"""
<div class="pl-home">
  <div>
    <h1>{APP_NAME}</h1>
    <div class="pl-range">2014/15 to 2025/26</div>
  </div>
  <nav class="pl-rings">{rings_html}</nav>
  <div class="pl-credit">Built by V. Srinath · <a href="{GITHUB_URL}" target="_blank">GitHub</a></div>
</div>
""", unsafe_allow_html=True)
