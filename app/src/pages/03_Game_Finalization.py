import streamlit as st
import requests
from datetime import datetime
from modules.nav import SideBarLinks

SideBarLinks()
st.set_page_config(layout='wide')

st.title("Game Finalization")
st.write("Review game statistics and finalize scores before submitting.")

# Stat keeper ID
STAT_KEEPER_ID = 1
API_BASE = "http://web-api:4000/stat-keeper"

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
        today = datetime.now().date()
        available_games = [
            g for g in all_games
            if g.get('home_team') is not None 
            and g.get('away_team') is not None
            and datetime.strptime(g['date_played'], '%Y-%m-%d').date() <= today
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

# Check if we came from Live Stat Entry with a selected game
selected_game_id_from_state = st.session_state.get('selected_game_id')
default_index = 0

if selected_game_id_from_state:
    # Find the game in available_games
    for idx, g in enumerate(available_games):
        if g['game_id'] == selected_game_id_from_state:
            default_index = idx
            break
    # Clear the session state so it doesn't persist on future visits
    del st.session_state['selected_game_id']

# Game selector with pre-selection
selected_game_option = st.selectbox(
    "Select Game to Finalize",
    options=available_games,
    index=default_index,
    format_func=lambda g: f"{g['date_played']} - {g.get('home_team', 'TBD')} vs {g.get('away_team', 'TBD')} @ {g['location']}"
)

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
    
    # Players list
    st.write("**Players:**")
    home_players = [p for p in players if p['team_id'] == game['home_team_id']]
    for player in home_players:
        player_stats = [e for e in stat_events if e['performed_by'] == player['player_id']]
        st.write(f"- {player['first_name']} {player['last_name']} ({len(player_stats)} stats)")

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
    
    # Players list
    st.write("**Players:**")
    away_players = [p for p in players if p['team_id'] == game['away_team_id']]
    for player in away_players:
        player_stats = [e for e in stat_events if e['performed_by'] == player['player_id']]
        st.write(f"- {player['first_name']} {player['last_name']} ({len(player_stats)} stats)")

st.divider()

# All stat events
st.subheader("All Stat Events")
if stat_events:
    all_players_dict = {p['player_id']: p for p in players}
    
    for event in stat_events:
        player = all_players_dict.get(event['performed_by'], {})
        player_name = f"{player.get('first_name', '')} {player.get('last_name', '')}" if player else "Unknown Player"
        team_name = next(
            (p['team_name'] for p in players if p['player_id'] == event['performed_by']),
            "Unknown Team"
        )
        
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
                st.success("🎉 Game finalized successfully! Stats are now official and visible to all players and teams.")
                st.balloons()
                st.info("Returning to My Assigned Games...")
                st.switch_page('pages/01_My_Assigned_Games.py')
            else:
                st.error(f"Error finalizing game: {response.json().get('error', 'Unknown error')}")
        except Exception as e:
            st.error(f"Error: {str(e)}")

with col_back:
    if st.button("← Back to Stats Entry", use_container_width=True):
        st.session_state['selected_game_id'] = game_id
        st.switch_page('pages/02_Live_Stat_Entry.py')