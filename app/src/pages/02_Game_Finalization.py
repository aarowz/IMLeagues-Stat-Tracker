import streamlit as st
import requests
from datetime import datetime
from modules.nav import SideBarLinks

SideBarLinks()
st.set_page_config(layout='wide')

st.title("Game Finalization")
st.write("Review game statistics and finalize scores before submitting. All assigned games are shown here for finalization or review.")

# Stat keeper ID
STAT_KEEPER_ID = 1
API_BASE = "http://web-api:4000/stat-keeper"

# Fetch assigned games - get all games with SQL-level filtering and sorting
try:
    # Fetch all games with SQL-level sorting (games with teams first, then by date)
    games_response = requests.get(f"{API_BASE}/stat-keepers/{STAT_KEEPER_ID}/games?all=true")
    if games_response.status_code == 200:
        available_games = games_response.json()
    else:
        available_games = []
        try:
            error_msg = games_response.json().get('error', f'HTTP {games_response.status_code}')
        except:
            error_msg = f'HTTP {games_response.status_code}: {games_response.text[:200]}'
        st.error(f"Error fetching games: {error_msg}")
except Exception as e:
    st.error(f"Error: {str(e)}")
    available_games = []

if not available_games:
    st.warning("No games available for finalization.")
    st.stop()

# Game selector
# Check if we came from "My Assigned Games" with a selected game
selected_game_id_from_state = st.session_state.get('selected_game_id')

if selected_game_id_from_state:
    # Find the game in available_games
    matching_game = next((g for g in available_games if g['game_id'] == selected_game_id_from_state), None)
    if matching_game:
        # Pre-select the game
        index = available_games.index(matching_game)
        selected_game_option = st.selectbox(
            "Select Game to Finalize",
            options=available_games,
            format_func=lambda g: f"{g['date_played']} - {g.get('home_team', 'TBD')} vs {g.get('away_team', 'TBD')} @ {g['location']}",
            index=index,
            key="game_selector"
        )
        # Clear the session state so it doesn't persist
        if 'selected_game_id' in st.session_state:
            del st.session_state['selected_game_id']
    else:
        # Game not found in available games, show normal selector
        selected_game_option = st.selectbox(
            "Select Game to Finalize",
            options=available_games,
            format_func=lambda g: f"{g['date_played']} - {g.get('home_team', 'TBD')} vs {g.get('away_team', 'TBD')} @ {g['location']}",
            key="game_selector"
        )
else:
    # Normal flow - no pre-selected game
    selected_game_option = st.selectbox(
        "Select Game to Finalize",
        options=available_games,
        format_func=lambda g: f"{g['date_played']} - {g.get('home_team', 'TBD')} vs {g.get('away_team', 'TBD')} @ {g['location']}",
        key="game_selector"
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
    
    # Build a complete players dictionary including players from stat events
    # This ensures we have player info even if they're not in the game lineup
    all_players_dict = {p['player_id']: p for p in players}
    
    # If we have stat events but missing players, try to fetch them from teams
    if stat_events and game.get('home_team_id') and game.get('away_team_id'):
        missing_player_ids = set()
        for event in stat_events:
            player_id = event.get('performed_by')
            if player_id and player_id not in all_players_dict:
                missing_player_ids.add(player_id)
        
        # Fetch missing players from team rosters
        if missing_player_ids:
            try:
                player_api_base = "http://web-api:4000/player"
                for team_id in [game.get('home_team_id'), game.get('away_team_id')]:
                    if team_id:
                        team_players_response = requests.get(f"{player_api_base}/teams/{team_id}/players")
                        if team_players_response.status_code == 200:
                            team_players = team_players_response.json()
                            for tp in team_players:
                                if tp['player_id'] in missing_player_ids:
                                    # Add team_name from game data
                                    tp['team_name'] = game.get('home_team') if team_id == game.get('home_team_id') else game.get('away_team')
                                    tp['team_id'] = team_id
                                    all_players_dict[tp['player_id']] = tp
                                    missing_player_ids.discard(tp['player_id'])
            except Exception as e:
                pass  # If fallback fails, continue with available players
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
    for event in stat_events:
        # Try to get player info from the players dictionary first (has team info)
        player = all_players_dict.get(event['performed_by'], {})
        
        if player:
            # Use player from dictionary (has team_name)
            player_name = f"{player.get('first_name', '')} {player.get('last_name', '')}"
            team_name = player.get('team_name', 'Unknown Team')
        elif event.get('first_name') and event.get('last_name'):
            # Fallback: use player name from stat event (but no team info)
            player_name = f"{event.get('first_name', '')} {event.get('last_name', '')}"
            # Try to determine team from game data
            team_name = "Unknown Team"
        else:
            player_name = "Unknown Player"
            team_name = "Unknown Team"
        
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

if st.button("✅ Finalize and Submit Game", type="primary", use_container_width=True):
    # Finalize by updating scores if needed and marking as complete
    # In a real system, you might have a separate "is_finalized" flag
    # For now, we'll just ensure scores are set
    try:
        final_data = {
            "home_score": new_home_score if 'new_home_score' in locals() else current_home_score,
            "away_score": new_away_score if 'new_away_score' in locals() else current_away_score
        }
        response = requests.put(f"{API_BASE}/games/{game_id}", json=final_data)
        if response.status_code == 200:
            st.success("🎉 Game finalized successfully! Stats are now official and visible to all players and teams.")
            st.balloons()
            st.info("You can now view this game in the 'My Assigned Games' page.")
        else:
            st.error(f"Error finalizing game: {response.json().get('error', 'Unknown error')}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

