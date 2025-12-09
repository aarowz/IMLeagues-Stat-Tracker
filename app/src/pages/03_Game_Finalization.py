import streamlit as st
import requests
import time
from datetime import datetime
from modules.nav import SideBarLinks

SideBarLinks()
st.set_page_config(layout='wide')

st.title("Game Finalization")
st.write("Review game statistics and finalize scores before submitting.")

# Stat keeper ID
STAT_KEEPER_ID = 1
API_BASE = "http://web-api:4000/stat-keeper"

# Check if we came from Live Stat Entry with a selected game (check BEFORE filtering)
selected_game_id_from_state = st.session_state.get('selected_game_id')

# Fetch assigned games from both upcoming and past endpoints
try:
    # Get both upcoming and past games from API
    upcoming_response = requests.get(f"{API_BASE}/stat-keepers/{STAT_KEEPER_ID}/games?upcoming_only=true")
    past_response = requests.get(f"{API_BASE}/stat-keepers/{STAT_KEEPER_ID}/games?upcoming_only=false")
    
    all_games = []
    if upcoming_response.status_code == 200:
        all_games.extend(upcoming_response.json())
    if past_response.status_code == 200:
        all_games.extend(past_response.json())
    
    if not all_games:
        available_games = []
        if upcoming_response.status_code != 200:
            st.error(f"Error fetching upcoming games: {upcoming_response.json().get('error', 'Unknown error')}")
        if past_response.status_code != 200:
            st.error(f"Error fetching past games: {past_response.json().get('error', 'Unknown error')}")
    else:
        # Filter to games that can be finalized:
        # - Games with teams assigned (required for finalization)
        # - Games from today or past (can't finalize future games)
        # BUT: Include the selected game even if it's in the future (if navigating from Live Stat Entry)
        today = datetime.now().date()
        available_games = [
            g for g in all_games
            if g.get('home_team') is not None 
            and g.get('away_team') is not None
            and (datetime.strptime(g['date_played'], '%Y-%m-%d').date() <= today 
                 or (selected_game_id_from_state and int(g['game_id']) == int(selected_game_id_from_state)))
        ]
        # Remove duplicates by game_id and sort by date (most recent first)
        available_games = list({g['game_id']: g for g in available_games}.values())
        available_games.sort(key=lambda x: x['date_played'], reverse=True)
except Exception as e:
    st.error(f"Error: {str(e)}")
    available_games = []

if not available_games:
    st.warning("No games available for finalization.")
    if st.button("← Back to My Assigned Games"):
        st.switch_page('pages/01_My_Assigned_Games.py')
    st.stop()

# Initialize the current game in session state if coming from Live Stat Entry
if selected_game_id_from_state:
    st.session_state['current_finalization_game_id'] = selected_game_id_from_state
    # Clear the widget state so it uses the index parameter instead
    if 'finalization_game_selector' in st.session_state:
        del st.session_state['finalization_game_selector']
    # Clear the navigation state
    del st.session_state['selected_game_id']

# Find the index of the currently selected game
default_index = 0
current_game_id = st.session_state.get('current_finalization_game_id')
if current_game_id:
    for idx, g in enumerate(available_games):
        # Ensure type consistency for comparison
        if int(g['game_id']) == int(current_game_id):
            default_index = idx
            break

# Game selector with pre-selection - use a key to maintain state
selected_game_option = st.selectbox(
    "Select Game to Finalize",
    options=available_games,
    index=default_index,
    format_func=lambda g: f"{g['date_played']} - {g.get('home_team', 'TBD')} vs {g.get('away_team', 'TBD')} @ {g['location']}",
    key="finalization_game_selector"
)

# Update the session state with the currently selected game
if selected_game_option:
    st.session_state['current_finalization_game_id'] = selected_game_option['game_id']

if not selected_game_option:
    st.stop()

game_id = selected_game_option['game_id']

# Fetch game summary
try:
    summary_response = requests.get(f"{API_BASE}/games/{game_id}/summary")
    players_response = requests.get(f"{API_BASE}/games/{game_id}/players")
    stats_response = requests.get(f"{API_BASE}/games/{game_id}/stat-events")
    
    if summary_response.status_code == 200:
        summary = summary_response.json()
        game = summary['game']
        team_totals = summary.get('team_totals', {})
        home_leaders = summary.get('home_team_leaders', [])
        away_leaders = summary.get('away_team_leaders', [])
    else:
        st.error("Error loading game summary")
        st.stop()
    
    if players_response.status_code == 200:
        players = players_response.json()
    else:
        players = []
    
    if stats_response.status_code == 200:
        stat_events = stats_response.json()
    else:
        stat_events = []
except Exception as e:
    st.error(f"Error loading game data: {str(e)}")
    st.stop()

# Display game header
home_team_name = game.get('home_team') or 'TBD'
away_team_name = game.get('away_team') or 'TBD'
st.header(f"{home_team_name} vs {away_team_name}")
if game.get('home_team') is None or game.get('away_team') is None:
    st.warning("⚠️ Teams not yet assigned - cannot finalize game")
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    st.write(f"**Date:** {game['date_played']}")
with col2:
    st.write(f"**Time:** {game['start_time']}")
with col3:
    st.write(f"**Location:** {game['location']}")
st.write(f"**League:** {game['league_name']} - {game['sport_name']}")

st.divider()

# Score entry/confirmation
st.subheader("Final Score")
col1, col2, col3 = st.columns([2, 1, 2])

with col1:
    st.write(f"**{home_team_name}**")
    current_home_score = game.get('home_score') or 0
    st.metric("Current Score", current_home_score)

with col2:
    st.write("")
    st.write("**VS**")

with col3:
    st.write(f"**{away_team_name}**")
    current_away_score = game.get('away_score') or 0
    st.metric("Current Score", current_away_score)

# Score update form
with st.form("update_score_form"):
    st.write("**Update Final Scores:**")
    col_home, col_away = st.columns(2)
    
    with col_home:
        new_home_score = st.number_input(
            f"{home_team_name} Score",
            min_value=0,
            value=int(current_home_score),
            step=1
        )
    
    with col_away:
        new_away_score = st.number_input(
            f"{away_team_name} Score",
            min_value=0,
            value=int(current_away_score),
            step=1
        )
    
    if st.form_submit_button("Update Scores", type="primary"):
        try:
            update_data = {
                "home_score": new_home_score,
                "away_score": new_away_score
            }
            response = requests.put(f"{API_BASE}/games/{game_id}", json=update_data)
            if response.status_code == 200:
                st.success("Scores updated successfully!")
                st.rerun()
            else:
                st.error(f"Error: {response.json().get('error', 'Unknown error')}")
        except Exception as e:
            st.error(f"Error: {str(e)}")

st.divider()

# Team statistics summary
col_left, col_right = st.columns(2)

with col_left:
    st.subheader(f"{home_team_name} Statistics")
    
    # Team totals
    home_stat_count = team_totals.get('home_team_stat_count', 0)
    st.metric("Total Stat Events", home_stat_count)
    
    # Top performers
    st.write("**Top Performers:**")
    if home_leaders:
        for idx, leader in enumerate(home_leaders[:5], 1):
            st.write(f"{idx}. **{leader['first_name']} {leader['last_name']}**: {leader['total_stat_events']} stats")
    else:
        st.info("No stats recorded")

with col_right:
    st.subheader(f"{away_team_name} Statistics")
    
    # Team totals
    away_stat_count = team_totals.get('away_team_stat_count', 0)
    st.metric("Total Stat Events", away_stat_count)
    
    # Top performers
    st.write("**Top Performers:**")
    if away_leaders:
        for idx, leader in enumerate(away_leaders[:5], 1):
            st.write(f"{idx}. **{leader['first_name']} {leader['last_name']}**: {leader['total_stat_events']} stats")
    else:
        st.info("No stats recorded")

st.divider()

# All stat events
st.subheader("All Stat Events")
if stat_events:
    # Filter options for stat events
    filter_options = {
        "Top 5": 5,
        "Top 10": 10,
        "Top 20": 20,
        "Top 50": 50,
        "All": None
    }
    
    selected_filter = st.radio(
        "Show:",
        options=list(filter_options.keys()),
        horizontal=True,
        index=1  # Default to "Top 10"
    )
    
    # Apply filter
    limit = filter_options[selected_filter]
    if limit:
        filtered_events = stat_events[:limit]
        st.caption(f"Showing {len(filtered_events)} of {len(stat_events)} stat events")
    else:
        filtered_events = stat_events
        st.caption(f"Showing all {len(stat_events)} stat events")
    
    st.divider()
    
    for event in filtered_events:
        # Use player info directly from stat event (already includes first_name, last_name)
        player_name = f"{event.get('first_name', '')} {event.get('last_name', '')}".strip()
        if not player_name:
            player_name = "Unknown Player"
        
        # Get team name directly from stat event (API now includes team_name)
        team_name = event.get('team_name', 'Unknown Team')
        
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            st.write(f"**{player_name}** ({team_name})")
        with col2:
            st.write(event['description'])
        with col3:
            st.caption(event.get('time_entered', 'N/A'))
        
        st.divider()
else:
    st.info("No stat events recorded for this game.")

st.divider()

# Show celebration if flag is set (check this FIRST before redirect check)
celebration_key = f"show_celebration_{game_id}"
if st.session_state.get(celebration_key, False):
    st.success("🎉 Game finalized successfully! Stats are now official and visible to all players and teams.")
    st.balloons()
    st.info("Returning to My Assigned Games...")
    # Clear celebration flag
    del st.session_state[celebration_key]
    time.sleep(3)
    st.switch_page('pages/01_My_Assigned_Games.py')
    st.stop()

# Check if finalization is in progress to prevent duplicate buttons
game_finalizing_key = f"game_finalizing_{game_id}"
if st.session_state.get(game_finalizing_key, False):
    # Finalization already completed, just redirect immediately (no duplicate messages/redirects)
    del st.session_state[game_finalizing_key]
    st.switch_page('pages/01_My_Assigned_Games.py')
    st.stop()

# Finalize game button
st.subheader("Finalize Game")
st.write("Once you've reviewed all statistics and confirmed the final scores, click below to finalize the game.")

col_finalize, col_back = st.columns([2, 1])

with col_finalize:
    if st.button("✅ Finalize and Submit Game", type="primary", use_container_width=True):
        # Finalize by updating scores if needed and marking as complete
        try:
            final_data = {
                "home_score": new_home_score if 'new_home_score' in locals() else current_home_score,
                "away_score": new_away_score if 'new_away_score' in locals() else current_away_score
            }
            response = requests.put(f"{API_BASE}/games/{game_id}", json=final_data)
            if response.status_code == 200:
                # Mark as finalizing in session state and show celebration
                st.session_state[game_finalizing_key] = True
                st.session_state[celebration_key] = True
                st.rerun()  # Rerun to show celebration without duplicate buttons
            else:
                st.error(f"Error finalizing game: {response.json().get('error', 'Unknown error')}")
        except Exception as e:
            st.error(f"Error: {str(e)}")

with col_back:
    if st.button("← Back to Stats Entry", use_container_width=True):
        st.session_state['selected_game_id'] = game_id
        st.switch_page('pages/02_Live_Stat_Entry.py')