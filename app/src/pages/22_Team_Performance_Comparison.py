import streamlit as st
import requests
import pandas as pd
from modules.nav import SideBarLinks

SideBarLinks()

st.set_page_config(layout='wide')

st.title("Team Performance Comparison")
st.write("Compare your team's performance to league averages, view home/away splits, and analyze performance against specific opponents.")

TEAM_ID = 1
API_BASE = "http://web-api:4000/team-captain"

try:
    summary_response = requests.get(f"{API_BASE}/teams/{TEAM_ID}/summary")
    comparison_response = requests.get(f"{API_BASE}/teams/{TEAM_ID}/league-comparison")
    splits_response = requests.get(f"{API_BASE}/teams/{TEAM_ID}/home-away-splits")
    opponents_response = requests.get(f"{API_BASE}/teams/{TEAM_ID}/opponents")
    
    if summary_response.status_code == 200:
        summary = summary_response.json()
    else:
        summary = None
    
    if comparison_response.status_code == 200:
        comparison = comparison_response.json()
    else:
        comparison = None
    
    if splits_response.status_code == 200:
        splits = splits_response.json()
    else:
        splits = []
    
    if opponents_response.status_code == 200:
        opponents = opponents_response.json()
    else:
        opponents = []
except Exception as e:
    st.error(f"Error fetching data: {str(e)}")
    summary = None
    comparison = None
    splits = []
    opponents = []

if summary:
    st.subheader(f"Team Summary: {summary.get('name', 'Unknown Team')}")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Wins", summary.get("wins", 0))
    with col2:
        st.metric("Losses", summary.get("losses", 0))
    with col3:
        st.metric("Total Players", summary.get("total_players", 0))
    with col4:
        st.metric("Games Played", summary.get("games_played", 0))
    with col5:
        st.metric("Total Stat Events", summary.get("total_stat_events", 0))
    
    st.write(f"**League:** {summary.get('league_name', 'Unknown')}")

st.divider()

if comparison:
    st.subheader("Team vs League Averages")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Points Scored**")
        team_avg_scored = comparison["team"]["avg_points_scored"]
        league_avg_scored = comparison["league"]["avg_points_scored"]
        
        comparison_df = pd.DataFrame({
            "Metric": ["Your Team", "League Average"],
            "Points Scored": [team_avg_scored, league_avg_scored]
        })
        st.bar_chart(comparison_df.set_index("Metric"), use_container_width=True)
        
        diff_scored = team_avg_scored - league_avg_scored
        if diff_scored > 0:
            st.success(f"Your team scores {round(diff_scored, 1)} more points on average than the league!")
        elif diff_scored < 0:
            st.warning(f"Your team scores {round(abs(diff_scored), 1)} fewer points on average than the league.")
        else:
            st.info("Your team scores exactly at the league average.")
    
    with col2:
        st.write("**Points Allowed**")
        team_avg_allowed = comparison["team"]["avg_points_allowed"]
        league_avg_allowed = comparison["league"]["avg_points_allowed"]
        
        comparison_df_allowed = pd.DataFrame({
            "Metric": ["Your Team", "League Average"],
            "Points Allowed": [team_avg_allowed, league_avg_allowed]
        })
        st.bar_chart(comparison_df_allowed.set_index("Metric"), use_container_width=True)
        
        diff_allowed = team_avg_allowed - league_avg_allowed
        if diff_allowed < 0:
            st.success(f"Your team allows {round(abs(diff_allowed), 1)} fewer points on average than the league!")
        elif diff_allowed > 0:
            st.warning(f"Your team allows {round(diff_allowed, 1)} more points on average than the league.")
        else:
            st.info("Your team allows exactly at the league average.")
    
    st.divider()
    st.write("**Detailed Comparison:**")
    
    diff_scored_str = ""
    if diff_scored >= 0:
        diff_scored_str = f"+{round(diff_scored, 1)}"
    else:
        diff_scored_str = f"{round(diff_scored, 1)}"
    
    diff_allowed_str = ""
    if diff_allowed >= 0:
        diff_allowed_str = f"+{round(diff_allowed, 1)}"
    else:
        diff_allowed_str = f"{round(diff_allowed, 1)}"
    
    comparison_table = pd.DataFrame({
        "Metric": ["Average Points Scored", "Average Points Allowed"],
        "Your Team": [team_avg_scored, team_avg_allowed],
        "League Average": [league_avg_scored, league_avg_allowed],
        "Difference": [
            diff_scored_str,
            diff_allowed_str
        ]
    })
    st.dataframe(comparison_table, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Home vs Away Performance")

if splits:
    home_data = next((s for s in splits if s.get('location_type') == 'Home'), None)
    away_data = next((s for s in splits if s.get('location_type') == 'Away'), None)
    
    if home_data and away_data:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Home Games**")
            home_wins = home_data.get('wins', 0)
            home_games = home_data.get('total_games', 0)
            if home_games > 0:
                home_win_pct = (home_wins / home_games * 100)
            else:
                home_win_pct = 0
            
            if home_data.get('avg_points_scored'):
                home_avg_scored = float(home_data.get('avg_points_scored', 0))
            else:
                home_avg_scored = 0
            
            st.metric("Win Percentage", f"{round(home_win_pct, 1)}%")
            st.metric("Games", home_games)
            st.metric("Wins", home_wins)
            st.metric("Avg Points Scored", f"{round(home_avg_scored, 1)}")
        
        with col2:
            st.write("**Away Games**")
            away_wins = away_data.get('wins', 0)
            away_games = away_data.get('total_games', 0)
            if away_games > 0:
                away_win_pct = (away_wins / away_games * 100)
            else:
                away_win_pct = 0
            
            if away_data.get('avg_points_scored'):
                away_avg_scored = float(away_data.get('avg_points_scored', 0))
            else:
                away_avg_scored = 0
            
            st.metric("Win Percentage", f"{round(away_win_pct, 1)}%")
            st.metric("Games", away_games)
            st.metric("Wins", away_wins)
            st.metric("Avg Points Scored", f"{round(away_avg_scored, 1)}")
        
        splits_df = pd.DataFrame({
            "Location": ["Home", "Away"],
            "Win %": [home_win_pct, away_win_pct],
            "Avg Points Scored": [home_avg_scored, away_avg_scored]
        })
        
        col1, col2 = st.columns(2)
        with col1:
            st.bar_chart(splits_df.set_index("Location")["Win %"], use_container_width=True)
            st.caption("Win Percentage: Home vs Away")
        
        with col2:
            st.bar_chart(splits_df.set_index("Location")["Avg Points Scored"], use_container_width=True)
            st.caption("Average Points Scored: Home vs Away")
    else:
        st.info("Not enough data for home/away splits.")
else:
    st.info("No home/away split data available.")

st.divider()
st.subheader("Performance Against Specific Opponent")

if opponents:
    opponent_options = [None] + [{"team_id": o["team_id"], "name": o["name"]} for o in opponents]
    selected_opponent = st.selectbox(
        "Select Opponent",
        options=opponent_options,
        format_func=lambda x: x["name"] if x else "All Opponents"
    )
    
    if selected_opponent:
        try:
            opponent_stats_response = requests.get(f"{API_BASE}/teams/{TEAM_ID}/opponent/{selected_opponent['team_id']}")
            if opponent_stats_response.status_code == 200:
                opponent_stats = opponent_stats_response.json()
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_games = opponent_stats.get('total_games', 0)
                    if total_games:
                        total_games = int(total_games)
                    else:
                        total_games = 0
                    st.metric("Games Played", total_games)
                
                with col2:
                    wins = opponent_stats.get('wins', 0)
                    if wins:
                        wins = int(wins)
                    else:
                        wins = 0
                    
                    losses = opponent_stats.get('losses', 0)
                    if losses:
                        losses = int(losses)
                    else:
                        losses = 0
                    
                    if total_games > 0:
                        win_pct = (wins / total_games * 100)
                    else:
                        win_pct = 0
                    st.metric("Win %", f"{round(win_pct, 1)}%")
                
                with col3:
                    if opponent_stats.get('avg_points_scored'):
                        avg_scored = float(opponent_stats.get('avg_points_scored', 0))
                    else:
                        avg_scored = 0
                    st.metric("Avg Points Scored", f"{round(avg_scored, 1)}")
                
                with col4:
                    if opponent_stats.get('avg_points_allowed'):
                        avg_allowed = float(opponent_stats.get('avg_points_allowed', 0))
                    else:
                        avg_allowed = 0
                    st.metric("Avg Points Allowed", f"{round(avg_allowed, 1)}")
                
                st.write(f"**Record:** {wins}W - {losses}L")
            else:
                st.info("No games found against this opponent.")
        except Exception as e:
            st.error(f"Error fetching opponent stats: {str(e)}")
else:
    st.info("No opponent data available.")

st.divider()
st.subheader("Shareable Team Summary")

if summary:
    wins = summary.get('wins', 0)
    losses = summary.get('losses', 0)
    total_games = wins + losses
    if total_games > 0:
        win_pct = (wins / total_games * 100)
    else:
        win_pct = 0
    
    summary_text = f"""
# {summary.get('name', 'Team')} Season Summary

**League:** {summary.get('league_name', 'Unknown')}

## Record
- Wins: {wins}
- Losses: {losses}
- Win Percentage: {round(win_pct, 1)}%

## Team Stats
- Total Players: {summary.get('total_players', 0)}
- Games Played: {summary.get('games_played', 0)}
- Total Stat Events: {summary.get('total_stat_events', 0)}
"""
    
    if comparison:
        summary_text += f"""
## Performance vs League
- Points Scored: {round(comparison['team']['avg_points_scored'], 1)} (League Avg: {round(comparison['league']['avg_points_scored'], 1)})
- Points Allowed: {round(comparison['team']['avg_points_allowed'], 1)} (League Avg: {round(comparison['league']['avg_points_allowed'], 1)})
"""
    
    st.text_area("Summary Text", value=summary_text, height=300)
    
    st.info("Copy the text above to share your team's performance summary!")
else:
    st.info("No summary data available.")
