"""Shared settings for the Premier League Pulse project."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

# Seasons covered, written the way the source files name them ("1415" = 2014/15)
SEASON_CODES = ["1415", "1516", "1617", "1718", "1819", "1920",
                "2021", "2122", "2223", "2324", "2425", "2526"]


def season_label(code: str) -> str:
    """'1415' -> '2014/15'"""
    return f"20{code[:2]}/{code[2:]}"


def season_tm(code: str) -> str:
    """'1415' -> '14/15' (Transfermarkt style)"""
    return f"{code[:2]}/{code[2:]}"


def season_start_year(code: str) -> int:
    return 2000 + int(code[:2])


# Match-results data (originally from football-data.co.uk, mirrored on GitHub)
RESULTS_URL = ("https://raw.githubusercontent.com/datasets/football-datasets/"
               "main/datasets/premier-league/season-{code}.csv")

# Squad, transfer and market-value data (scraped from Transfermarkt, published on GitHub)
TM_BASE = ("https://media.githubusercontent.com/media/salimt/football-datasets/"
           "main/datalake/transfermarkt/")
TM_FILES = {
    "player_performances": "player_performances/player_performances.csv",
    "player_profiles": "player_profiles/player_profiles.csv",
    "player_market_value": "player_market_value/player_market_value.csv",
    "transfer_history": "transfer_history/transfer_history.csv",
    "team_competitions_seasons": "team_competitions_seasons/team_competitions_seasons.csv",
}

# Match-by-match records incl. each team's manager (Transfermarkt, via
# github.com/dcaribou/transfermarkt-datasets). Used to work out managerial changes.
TM_GAMES_URL = "https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data/games.csv.gz"

PREMIER_LEAGUE_ID = "GB1"

# Results-file team name -> (Transfermarkt club id, display name)
TEAMS = {
    "Arsenal": (11, "Arsenal"),
    "Aston Villa": (405, "Aston Villa"),
    "Bournemouth": (989, "Bournemouth"),
    "Brentford": (1148, "Brentford"),
    "Brighton": (1237, "Brighton"),
    "Burnley": (1132, "Burnley"),
    "Cardiff": (603, "Cardiff City"),
    "Chelsea": (631, "Chelsea"),
    "Crystal Palace": (873, "Crystal Palace"),
    "Everton": (29, "Everton"),
    "Fulham": (931, "Fulham"),
    "Huddersfield": (1110, "Huddersfield Town"),
    "Hull": (3008, "Hull City"),
    "Ipswich": (677, "Ipswich Town"),
    "Leeds": (399, "Leeds United"),
    "Leicester": (1003, "Leicester City"),
    "Liverpool": (31, "Liverpool"),
    "Luton": (1031, "Luton Town"),
    "Man City": (281, "Manchester City"),
    "Man United": (985, "Manchester United"),
    "Middlesbrough": (641, "Middlesbrough"),
    "Newcastle": (762, "Newcastle United"),
    "Norwich": (1123, "Norwich City"),
    "Nott'm Forest": (703, "Nottingham Forest"),
    "QPR": (1039, "QPR"),
    "Sheffield United": (350, "Sheffield United"),
    "Southampton": (180, "Southampton"),
    "Stoke": (512, "Stoke City"),
    "Sunderland": (289, "Sunderland"),
    "Swansea": (2288, "Swansea City"),
    "Tottenham": (148, "Tottenham"),
    "Watford": (1010, "Watford"),
    "West Brom": (984, "West Brom"),
    "West Ham": (379, "West Ham"),
    "Wolves": (543, "Wolves"),
}

# The traditional "Big Six", used for the competitive-balance view
BIG_SIX = ["Arsenal", "Chelsea", "Liverpool", "Manchester City",
           "Manchester United", "Tottenham"]
