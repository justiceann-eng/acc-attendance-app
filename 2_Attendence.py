# Lab 3: API data page - ACC football attendance explorer
# Data: College Football Data API (https://api.collegefootballdata.com/games)
# All processing below is our own Python code (no AI on this page).

import requests
import streamlit as st
import pandas as pd

BASE_URL = "https://api.collegefootballdata.com/games"
SEASONS = [2021, 2022, 2023, 2024, 2025]  # 2020 skipped (COVID-limited crowds)

# Stadium capacities for the 18 ACC schools (approximate - double-check before the demo).
# Keys must match the team names the API uses.
ACC_CAPACITY = {
    "Boston College": 44500,
    "California": 62467,
    "Clemson": 81500,
    "Duke": 40004,
    "Florida State": 79560,
    "Georgia Tech": 55000,
    "Louisville": 60800,
    "Miami": 64767,
    "North Carolina": 50500,
    "NC State": 56919,
    "Notre Dame": 77622,
    "Pittsburgh": 68400,
    "SMU": 32000,
    "Stanford": 50424,
    "Syracuse": 49057,
    "Virginia": 61500,
    "Virginia Tech": 65632,
    "Wake Forest": 31500,
}
ACC_TEAMS = sorted(ACC_CAPACITY.keys())


def get_field(game: dict, *names):
    """Return the first key that exists in the game dict (API may use camelCase or snake_case)."""
    for name in names:
        if name in game:
            return game[name]
    return None


def fetch_games(team, year):
    """Get every game a team played in one season from the API."""
    headers = {"Authorization": f"Bearer {st.secrets['CFBD_API_KEY']}"}
    response = requests.get(
        BASE_URL,
        params={"year": year, "team": team},
        headers=headers,
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def build_home_games(team: str, years: list) -> pd.DataFrame:
    """Keep only the team's HOME games that have an attendance number."""
    rows = []
    for year in years:
        for game in fetch_games(team, year):
            home = get_field(game, "homeTeam", "home_team")
            attendance = get_field(game, "attendance")
            if home != team or not attendance:
                continue
            rows.append(
                {
                    "Season": year,
                    "Week": get_field(game, "week"),
                    "Opponent": get_field(game, "awayTeam", "away_team"),
                    "Venue": get_field(game, "venue"),
                    "Attendance": int(attendance),
                    "Conference Game": bool(get_field(game, "conferenceGame", "conference_game")),
                }
            )
    return pd.DataFrame(rows)


def project_next_season(season_avgs):
    """Straight-line trend through the season averages, extended one season ahead."""
    years = sorted(season_avgs)
    if len(years) == 1:
        return season_avgs[years[0]]
    n = len(years)
    mean_x = sum(years) / n
    mean_y = sum(season_avgs[y] for y in years) / n
    denominator = sum((x - mean_x) ** 2 for x in years)
    slope = sum((x - mean_x) * (season_avgs[x] - mean_y) for x in years) / denominator
    return mean_y + slope * (max(years) + 1 - mean_x)


def opponent_factor(df: pd.DataFrame, opponent: str):
    """How much bigger/smaller the crowd was against this opponent vs. that season's average."""
    season_avg = df.groupby("Season")["Attendance"].mean()
    ratios = []
    for row in df[df["Opponent"] == opponent].itertuples():
        #print(row.Points)
        ratios.append(row["Attendance"] / season_avg[row["Season"]])
    if not ratios:
        return 1.0, 0
    return sum(ratios) / len(ratios), len(ratios)


# ---------------- Page ----------------
st.title("ACC Football Attendance ")
st.write(
    "These graphs are designed to be used by athletic department staff. You can look at past home attendance, then estimate "
    "a future game to help plan staffing, concessions, seating, and more."
)

# Inputs
col1, col2 = st.columns(2)
with col1:
    team = st.selectbox("Home team", ACC_TEAMS, index=ACC_TEAMS.index("Georgia Tech"))
with col2:
    years = st.multiselect("Seasons to include", SEASONS, default=SEASONS)

if not years:
    st.info("Pick at least one season to get data.")
    st.stop()

try:
    df = build_home_games(team, years)
except Exception as error:
    st.error(f"Sorry, we couldn't load data from the API: {error}")
    st.stop()

if df.empty:
    st.warning("No home games with attendance numbers were found for that selection.")
    st.stop()

# Visual 1: trend across seasons
st.header(f"{team} home attendance by season")
season_avgs = df.groupby("Season")["Attendance"].mean().round().to_dict()
trend = pd.DataFrame({"Average attendance": season_avgs})
st.line_chart(trend)

# Visual 2: game-by-game for one season
season_choice = st.selectbox("See every home game for season", sorted(years, reverse=True))
season_df = df[df["Season"] == season_choice].sort_values("Week")
st.subheader(f"{team} home games, {season_choice}")
st.bar_chart(season_df.set_index("Opponent")["Attendance"])
st.dataframe(season_df[["Week", "Opponent", "Venue", "Attendance"]], hide_index=True)

# Estimate
st.header("Estimate a future game based on past seasons")
opponents = ["Not specified"] + [t for t in ACC_TEAMS if t != team]
opponent = st.selectbox("Opponent", opponents)
adjustment = st.slider("Expected demand adjustment (%)", -20, 20, 0)

base = project_next_season(season_avgs)
factor= 1.0
games_found= 0 
if opponent != "Not specified":
    factor, games_found = opponent_factor(df, opponent)
estimate = base * factor * (1 + adjustment / 100)

capacity = ACC_CAPACITY[team]
percent_full = estimate / capacity * 100

c1, c2, c3 = st.columns(3)
c1.metric(f"Estimated attendance ({max(years) + 1})", f"{estimate:,.0f}")
c2.metric("Stadium capacity", f"{capacity:,}")
c3.metric("Percent full", f"{percent_full:.1f}%")
st.progress(min(percent_full / 100, 1.0))

if opponent != "Not specified":
    if games_found:
        st.caption(
            f"Based on {games_found} past home game(s) vs. {opponent}: crowds were "
            f"{(factor - 1) * 100:+.1f}% compared to that season's average."
        )
    else:
        st.caption(f"No past home games vs. {opponent} in the selected seasons, so no opponent effect was applied.")
st.caption("This is a simple estimate based off of past seasons, not a prediction model.")

