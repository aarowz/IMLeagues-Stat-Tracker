import streamlit as st
import requests
from datetime import datetime
from modules.nav import SideBarLinks

SideBarLinks()
st.set_page_config(layout='wide')

st.title("📅 My Games & Schedule")
st.write("View your upcoming and past games.")

# Player ID
PLAYER_ID = 2
API_BASE = "http://web-api:4000/player"

# Fetch player games
try:
    upcoming_response = requests.get(f"{API_BASE}/players/{PLAYER_ID}/games?upcoming_only=true")
    past_response = requests.get(f"{API_BASE}/players/{PLAYER_ID}/games?upcoming_only=false")
    
    if upcoming_response.status_code == 200:
        upcoming_games = upcoming_response.json()
    else:
        upcoming_games = []
        st.error(f"Error fetching upcoming games: {upcoming_response.json().get('error', 'Unknown error')}")
    
    if past_response.status_code == 200:
        past_games = past_response.json()
    else:
        past_games = []
        st.error(f"Error fetching past games: {past_response.json().get('error', 'Unknown error')}")
except Exception as e:
    st.error(f"Error: {str(e)}")
    upcoming_games = []
    past_games = []

# Tabs for upcoming and past games
tab1, tab2 = st.tabs(["📅 Upcoming Games", "📊 Past Games"])

with tab1:
    st.subheader("Upcoming Games")
    
    if upcoming_games:
        today = datetime.now().date()
        
        for idx, game in enumerate(upcoming_games):
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    home_team = game.get('home_team') or 'TBD'
                    away_team = game.get('away_team') or 'TBD'
                    st.write(f"**{home_team}** vs **{away_team}**")
                    
                    game_date = datetime.strptime(game['date_played'], '%Y-%m-%d').date()
                    days_until = (game_date - today).days
                    
                    st.write(f"📅 {game['date_played']} | 🕐 {game['start_time']}")
                    st.write(f"📍 {game['location']}")
                    st.write(f"🏆 {game['league_name']} - {game['sport_name']}")
                    
                    # Show player's role/position if available
                    if game.get('is_starter') is not None:
                        starter_text = "Starter" if game.get('is_starter') else "Bench"
                        position_text = f" ({game.get('position', 'N/A')})" if game.get('position') else ""
                        st.caption(f"Your role: {starter_text}{position_text}")
                
                with col2:
                    if days_until == 0:
                        st.success("**Today!**")
                    elif days_until == 1:
                        st.info("**Tomorrow**")
                    elif days_until <= 7:
                        st.warning(f"**{days_until} days away**")
                    else:
                        st.write(f"**{days_until} days away**")
                
                with col3:
                    if st.button("View Details", key=f"view_upcoming_{game['game_id']}_{idx}", use_container_width=True):
                        st.session_state[f"viewing_game_{game['game_id']}"] = True
                
                # Game details expandable
                if st.session_state.get(f"viewing_game_{game['game_id']}", False):
                    try:
                        game_response = requests.get(f"{API_BASE}/games/{game['game_id']}")
                        if game_response.status_code == 200:
                            game_details = game_response.json()
                            
                            with st.expander("Game Details", expanded=True):
                                st.write(f"**League:** {game_details.get('league_name', 'N/A')}")
                                st.write(f"**Sport:** {game_details.get('sport_name', 'N/A')}")
                                st.write(f"**Date:** {game_details.get('date_played', 'N/A')}")
                                st.write(f"**Time:** {game_details.get('start_time', 'N/A')}")
                                st.write(f"**Location:** {game_details.get('location', 'N/A')}")
                                
                                if st.button("Close", key=f"close_{game['game_id']}"):
                                    st.session_state[f"viewing_game_{game['game_id']}"] = False
                                    st.rerun()
                    except Exception as e:
                        st.error(f"Error loading game details: {str(e)}")
                
                st.divider()
    else:
        st.info("No upcoming games scheduled.")

with tab2:
    st.subheader("Past Games")
    
    if past_games:
        for idx, game in enumerate(past_games):
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    home_team = game.get('home_team') or 'TBD'
                    away_team = game.get('away_team') or 'TBD'
                    home_score = game.get('home_score')
                    away_score = game.get('away_score')
                    
                    if home_score is not None and away_score is not None:
                        st.write(f"**{home_team}** {home_score} - {away_score} **{away_team}**")
                    else:
                        st.write(f"**{home_team}** vs **{away_team}**")
                    
                    st.write(f"📅 {game['date_played']} | 🕐 {game['start_time']}")
                    st.write(f"📍 {game['location']}")
                    st.write(f"🏆 {game['league_name']} - {game['sport_name']}")
                    
                    # Show player's role/position
                    if game.get('is_starter') is not None:
                        starter_text = "Starter" if game.get('is_starter') else "Bench"
                        position_text = f" ({game.get('position', 'N/A')})" if game.get('position') else ""
                        st.caption(f"Your role: {starter_text}{position_text}")
                
                with col2:
                    if home_score is not None and away_score is not None:
                        # Determine if player's team won (need to check which team player is on)
                        # For now, just show the score
                        st.metric("Final Score", f"{home_score} - {away_score}")
                    else:
                        st.info("Score not available")
                
                with col3:
                    if st.button("View Details", key=f"view_past_{game['game_id']}_{idx}", use_container_width=True):
                        st.session_state[f"viewing_past_game_{game['game_id']}"] = True
                
                # Game details expandable
                if st.session_state.get(f"viewing_past_game_{game['game_id']}", False):
                    try:
                        game_response = requests.get(f"{API_BASE}/games/{game['game_id']}")
                        if game_response.status_code == 200:
                            game_details = game_response.json()
                            
                            with st.expander("Game Details", expanded=True):
                                st.write(f"**League:** {game_details.get('league_name', 'N/A')}")
                                st.write(f"**Sport:** {game_details.get('sport_name', 'N/A')}")
                                st.write(f"**Date:** {game_details.get('date_played', 'N/A')}")
                                st.write(f"**Time:** {game_details.get('start_time', 'N/A')}")
                                st.write(f"**Location:** {game_details.get('location', 'N/A')}")
                                
                                if home_score is not None and away_score is not None:
                                    st.write(f"**Final Score:** {home_score} - {away_score}")
                                
                                if st.button("Close", key=f"close_past_{game['game_id']}"):
                                    st.session_state[f"viewing_past_game_{game['game_id']}"] = False
                                    st.rerun()
                    except Exception as e:
                        st.error(f"Error loading game details: {str(e)}")
                
                st.divider()
    else:
        st.info("No past games recorded.")

# Summary statistics
st.divider()
st.subheader("📊 Summary")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Upcoming Games", len(upcoming_games))

with col2:
    st.metric("Past Games", len(past_games))

with col3:
    total_games = len(upcoming_games) + len(past_games)
    st.metric("Total Games", total_games)

