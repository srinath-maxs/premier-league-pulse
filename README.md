# Premier League Pulse ⚽📊

**What actually drives success in the Premier League — money, youth, stability or the manager? And who wins this season?**

An end-to-end analytics project covering every Premier League season from **2014/15 to 2025/26** (240 team-seasons, 4,560 matches). It combines match results with squad, transfer and manager data to answer business-style questions and power three interactive dashboards.

> 🚧 **Status:** Data pipeline and League Overview dashboard complete. Team Comparison and Season Predictor in progress.

---

## The questions

1. **Does money buy points?** How strongly does squad value and transfer spend predict where a team finishes, and who gets the most out of their budget?
2. **Does youth matter?** Do younger squads (appearance-weighted age) perform differently from older ones?
3. **Do managers make a difference?** Is the "new manager bounce" real, or is it just bad luck evening out?
4. **How do teams compare across eras?** Is this year's champion better than Liverpool 2019/20? (Spending is compared *relative to its season* so different eras are comparable.)
5. **Who will win this season?** Title, top-4 and relegation odds from 10,000 simulated seasons.

## Dashboards (Streamlit, free)

| Dashboard | What it shows |
|---|---|
| **Team Comparison** | Any team + season vs any other team + season: points, goals, age, squad value, spending, manager, stability; points race; radar profile; the 3 most similar historical teams; a plain-English summary |
| **League Overview** | Season filter; spending vs points; age vs points; growth trends by club; efficiency ranking; manager changes; competitive balance; promoted teams; the COVID "no fans" season |
| **Season Predictor** | Title / top-4 / relegation odds, updated each gameweek; which factors matter most (SHAP) |

## Phase 1 headline numbers

- **Squad value explains a lot:** correlation of 0.77 between points and squad value relative to the season average (2014/15–2024/25).
- **Age barely matters on its own:** correlation of −0.10 between points and appearance-weighted age.
- **Stability matters:** teams that keep their players do better (correlation 0.44 between points and the share of appearances by returning players).
- **Home advantage vanished without fans:** in 2020/21, home teams averaged *fewer* points per game than away teams (−0.07 PPG gap vs +0.45 in 2014/15).
- **Promoted teams:** only 16 of 33 survived their first season.
- **The "new manager bounce" is mostly luck:** teams that changed manager mid-season improved by 0.46 points per game over the next 10 games, but clubs on equally bad runs that *kept* their manager improved by 0.41 anyway. About 88% of the bounce is a bad run evening out (regression to the mean).

## Project structure

```
premier-league-pulse/
├── app.py                 # Streamlit entry point (streamlit run app.py)
├── views/                 # dashboard pages
│   ├── home.py
│   └── league_overview.py
├── src/
│   ├── config.py          # seasons, sources, team name mapping
│   ├── fetch_data.py      # Step 1: download raw data
│   ├── build_dataset.py   # Step 2: build the clean tables
│   ├── analysis.py        # Step 3: manager-bounce comparison
│   └── ui.py              # shared dashboard helpers (colours, charts)
├── data/
│   ├── raw/               # downloaded files (not in git: ~300 MB)
│   ├── manual/            # small hand-checked files (manager changes)
│   └── processed/         # clean tables used by the dashboards
├── DATA_DICTIONARY.md
└── requirements.txt
```

## How to run

```bash
pip install -r requirements.txt
python src/fetch_data.py      # downloads ~300 MB, a few minutes
python src/build_dataset.py   # builds data/processed/
python src/analysis.py        # manager-bounce comparison
streamlit run app.py          # opens the dashboard in your browser
```

The processed data is already in the repo, so to just view the dashboard you only need the first and last lines.

## Data sources

| Data | Source | Coverage |
|---|---|---|
| Match results, shots | [football-data.co.uk](https://www.football-data.co.uk/) via [datasets/football-datasets](https://github.com/datasets/football-datasets) | 2014/15–2025/26, complete |
| Squads, ages, market values, transfers | [Transfermarkt](https://www.transfermarkt.com/) via [salimt/football-datasets](https://github.com/salimt/football-datasets) | 2014/15–2024/25 complete; 2025/26 early season only |
| Managers (end of season) | Transfermarkt; 2025/26 hand-checked | All seasons |
| In-season managerial changes | Wikipedia season pages, hand-checked into `data/manual/` | All seasons |

## Method notes and limitations

- **Spending power = squad market value** (Transfermarkt, at 1 September of each season), plus transfer spend. Reliable free wage data does not exist for all clubs and seasons, so wages are not used. All money is in **euros (€)**.
- **Cross-era comparisons** use relative measures (`squad_value_vs_avg`, `spend_rank`) because transfer prices have inflated sharply since 2014.
- **Age** is weighted by league appearances, so a teenager who never plays does not make a squad look younger. (Transfermarkt minutes data is incomplete, so appearances are used instead.)
- **2025/26 squad metrics** (age, value, stability) come from a data snapshot taken a few weeks into that season. Results for 2025/26 are complete.
- **Shots and shots on target** stand in for expected goals (xG), as free xG data could not be included reliably.
- **Points deductions** (Everton −8 and Nottingham Forest −4 in 2023/24) are applied to the final table.
