# Data dictionary

All tables are in `data/processed/`. Money is in euros (€).

## team_seasons.csv — the master table (one row per team per season, 240 rows)

| Column | Meaning |
|---|---|
| season, position, team, team_id | Season (e.g. 2019/20), final league position, club name, Transfermarkt club id |
| played, wins, draws, losses | Results record |
| goals_for, goals_against, goal_difference | Goals |
| points | Official points (after any deduction) |
| points_on_pitch, points_deduction | Points earned in matches, and any deduction (e.g. Everton −8 in 2023/24) |
| ppg, home_points, away_points, home_ppg, away_ppg | Points per game, overall and by venue |
| shots, shots_against, shots_on_target, shots_on_target_against | Shot totals |
| shot_share, shots_on_target_share | Share of all shots in the team's games that the team took (dominance; xG stand-in) |
| avg_age_weighted | Average age on 1 January of the season, weighted by league appearances |
| avg_age_squad, avg_age_core14 | Plain average age of everyone used; average age of the 14 most-used players |
| age_vs_avg | Years older (+) or younger (−) than that season's league average |
| u23_share_pct, over30_share_pct | Share of appearances made by under-23s / over-30s |
| players_used | Number of players who appeared in the league |
| stability_pct | Share of appearances made by players who also played for the club the season before |
| squad_value_eur | Total market value of the players used, on 1 September of the season |
| squad_value_core14_eur | Market value of the 14 most-used players |
| squad_value_vs_avg | Squad value ÷ that season's league average (1.0 = average; good for comparing eras) |
| squad_value_rank | Rank of squad value within the season (1 = richest) |
| most_valuable_player | Highest market value in the squad |
| transfer_spend_eur, transfer_income_eur, net_spend_eur | Fees paid, fees received, and the difference (summer + winter windows of that season) |
| signings, record_signing_fee_eur | Number of incoming transfers/loans and the biggest fee |
| spend_vs_avg, spend_rank | Transfer spend relative to the season average, and its rank |
| points_per_100m_value | Points per €100m of squad value (efficiency) |
| over_performance | Squad value rank minus league position (+5 = finished 5 places higher than its budget suggests) |
| manager | Manager at the end of the season (from Transfermarkt; 2025/26 from the last match) |
| new_manager | True if the end-of-season manager differs from the previous season's |
| manager_tenure_seasons | Consecutive seasons in charge, including this one |
| in_season_manager_changes | Managers who left during the season (worked out from match records; short caretaker stints and one-game stand-ins don't count) |
| promoted, relegated, big_six | Flags (2014/15 has no promoted flag because 2013/14 is not in the data) |
| data_note | Warnings, e.g. partial squad data for 2025/26 |

## team_matches.csv — one row per team per match (9,120 rows)

Each match appears twice, once from each team's point of view: `season, date, venue, team, opponent, goals_for, goals_against, shots..., result (W/D/L), points, game_number (1–38), cumulative_points, cumulative_goal_diff`. Used for the points-race charts.

## matches.csv — one row per match (4,560 rows)

Home/away teams, goals, result (H/D/A), shots, shots on target, cards.

## league_seasons.csv — one row per season (12 rows)

Home/draw/away win %, home vs away points per game, `home_advantage_ppg`, goals per game, champion and points, title margin, 4th-place points, safety points (17th), Big Six vs rest average points and `big_six_gap`, `points_spread_sd` (competitive balance), promoted teams that survived, league average age, total transfer spend, average squad value, and whether fans were in stadiums.

## manager_changes.csv — one row per mid-season managerial departure (95 rows)

Worked out from Transfermarkt's match records (`src/managers.py`): a departure is a manager who led the team (started the season or lasted 5+ games) and did not come back that season.

`season, team, date_of_vacancy` (announcement date from Wikipedia, or the day after the last game if Wikipedia has none), `last_game_old_manager, outgoing_manager, games_in_charge, manner_of_departure` (Wikipedia), `caretaker` (anyone who covered 1–4 games in between), `incoming_manager, interim_or_caretaker, date_source, games_played_before, ppg_season_before, ppg_last10_before, ppg_next10_after, ppg_rest_of_season, games_after, bounce_ppg` (next-10 PPG minus last-10 PPG).

## bounce_comparison.csv — is the new-manager bounce real? (made by `src/analysis.py`)

One row per form band (points per game in the 10 games before), plus an "All changes" row. `changed_*` columns are teams that changed manager mid-season; `kept_*` columns are clubs on equally bad 10-game runs that made no change within four months (the comparison group). `*_gain` = next-10 PPG minus last-10 PPG; `extra_gain_from_change` = the difference between the two.
