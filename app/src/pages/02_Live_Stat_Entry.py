import streamlit as st
import requests
from datetime import datetime
from modules.nav import SideBarLinks

SideBarLinks()
st.set_page_config(layout='wide')

st.title("Live Stat Entry")
st.write("Quickly log player statistics in real-time during games.")

# Stat keeper ID - using default for now (could be stored in session_state)
STAT_KEEPER_ID = 1
API_BASE = "http://web-api:4000/stat-keeper"

# Define scoring stats and their point values
SCORING_STATS = {
    # Basketball
    "2 points scored": 2,
    "3 points scored": 3,
    "1 point scored (free throw)": 1,
    # Soccer
    "Goal scored": 1,
    # Generic
    "Point scored": 1,
}

def get_points_for_stat(description):
    """Returns the point value for a stat description, or 0 if not a scoring stat."""
    return SCORING_STATS.get(description, 0)

def update_game_score(api_base, game_id, player_id, points, game_data, players_list):
    """Updates the game score based on which team the player is on."""
    if points == 0:
        return True  # No score update needed
    
    # Determine which team the player is on
    player_team_id = None
    for p in players_list:
        if p['player_id'] == player_id:
            player_team_id = p.get('team_id')
            break
    
    if not player_team_id:
        return False
    
    # Get current scores
    current_home_score = game_data.get('home_score') or 0
    current_away_score = game_data.get('away_score') or 0
    
    # Update the appropriate team's score
    if player_team_id == game_data.get('home_team_id'):
        new_home_score = current_home_score + points
        new_away_score = current_away_score
    elif player_team_id == game_data.get('away_team_id'):
        new_home_score = current_home_score
        new_away_score = current_away_score + points
    else:
        return False
    
    # Update score via API
    try:
        update_data = {
            "home_score": new_home_score,
            "away_score": new_away_score
        }
        response = requests.put(f"{api_base}/games/{game_id}", json=update_data)
        return response.status_code == 200
    except:
        return False

# Fetch assigned games with filtering done at API/database level
try:
    games_response = requests.get(f"{API_BASE}/stat-keepers/{STAT_KEEPER_ID}/games?upcoming_only=true")
    if games_response.status_code == 200:
        all_games = games_response.json()
        # Filter out games without teams assigned (can't track stats without teams)
        # This is UI logic, not data filtering, so it's acceptable to do in Python
        available_games = [
            g for g in all_games 
            if g.get('home_team') is not None 
            and g.get('away_team') is not None
        ]
    else:
        available_games = []
        st.error(f"Error fetching games: {games_response.json().get('error', 'Unknown error')}")
except Exception as e:
    st.error(f"Error: {str(e)}")
    available_games = []

if not available_games:
    st.warning("No games available for live stat entry. Please check your assigned games.")
    if st.button("← Back to My Assigned Games"):
        st.switch_page('pages/01_My_Assigned_Games.py')
    st.stop()

# Check if we came from "My Assigned Games" or Game Finalization with a selected game
selected_game_id_from_state = st.session_state.get('selected_game_id')

# Initialize the current game in session state if coming from another page
if selected_game_id_from_state:
    st.session_state['current_stat_entry_game_id'] = selected_game_id_from_state
    # Clear the widget state so it uses the index parameter instead
    if 'stat_entry_game_selector' in st.session_state:
        del st.session_state['stat_entry_game_selector']
    # Clear the navigation state
    del st.session_state['selected_game_id']

# Find the index of the currently selected game
default_index = 0
current_game_id = st.session_state.get('current_stat_entry_game_id')
if current_game_id:
    for idx, g in enumerate(available_games):
        # Ensure type consistency for comparison
        if int(g['game_id']) == int(current_game_id):
            default_index = idx
            break

# Game selector with pre-selection - use a key to maintain state
# If we have a current_game_id, make sure it's selected
selected_game_option = st.selectbox(
    "Select Game",
    options=available_games,
    index=default_index,
    format_func=lambda g: f"{g['date_played']} - {g.get('home_team', 'TBD')} vs {g.get('away_team', 'TBD')} @ {g['location']}",
    key="stat_entry_game_selector"
)

# Update the session state with the currently selected game
if selected_game_option:
    st.session_state['current_stat_entry_game_id'] = selected_game_option['game_id']

if not selected_game_option:
    st.stop()

game_id = selected_game_option['game_id']

# Fetch game details
try:
    game_response = requests.get(f"{API_BASE}/games/{game_id}")
    players_response = requests.get(f"{API_BASE}/games/{game_id}/players")
    stats_response = requests.get(f"{API_BASE}/games/{game_id}/stat-events")
    
    if game_response.status_code == 200:
        game = game_response.json()
    else:
        st.error("Error loading game details")
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

# Split players by team
home_team_id = game.get('home_team_id')
away_team_id = game.get('away_team_id')
home_players = [p for p in players if home_team_id and p.get('team_id') == home_team_id]
away_players = [p for p in players if away_team_id and p.get('team_id') == away_team_id]

# Display game header with live score
col1, col2, col3 = st.columns([2, 1, 2])
with col1:
    home_team_name = game.get('home_team') or 'TBD'
    st.subheader(f"{home_team_name}")
    st.metric("Score", game.get('home_score', 0))
with col2:
    st.write("")
    st.write("**VS**")
    st.write(f"**{game['sport_name']}**")
    st.caption(f"{game['date_played']} @ {game['start_time']}")
    st.caption(game['location'])
with col3:
    away_team_name = game.get('away_team') or 'TBD'
    st.subheader(f"{away_team_name}")
    st.metric("Score", game.get('away_score', 0))

st.divider()

# Main layout: Stat entry on left, Live summary on right
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("Quick Stat Entry")
    
    # Sport-specific stat buttons (basketball example - can be expanded)
    sport_name = game.get('sport_name', '').lower()
    
    if 'basketball' in sport_name:
        common_stats = [
            ("2 Points", "2 points scored"),
            ("3 Points", "3 points scored"),
            ("Free Throw", "1 point scored (free throw)"),
            ("Rebound", "Rebound"),
            ("Assist", "Assist"),
            ("Steal", "Steal"),
            ("Block", "Block"),
            ("Turnover", "Turnover"),
            ("Foul", "Foul")
        ]
    elif 'soccer' in sport_name:
        common_stats = [
            ("Goal", "Goal scored"),
            ("Assist", "Assist"),
            ("Save", "Save"),
            ("Yellow Card", "Yellow card"),
            ("Red Card", "Red card"),
            ("Corner Kick", "Corner kick"),
            ("Offside", "Offside")
        ]
    else:
        # Generic stats
        common_stats = [
            ("Point", "Point scored"),
            ("Assist", "Assist"),
            ("Save", "Save"),
            ("Penalty", "Penalty")
        ]
    
    # Player selection
    all_players_list = home_players + away_players
    
    # Fallback: If no players in game lineup, fetch from teams
    if not players and home_team_id and away_team_id:
        try:
            player_api_base = "http://web-api:4000/player"
            home_team_players_response = requests.get(f"{player_api_base}/teams/{home_team_id}/players")
            away_team_players_response = requests.get(f"{player_api_base}/teams/{away_team_id}/players")
            
            home_team_players = home_team_players_response.json() if home_team_players_response.status_code == 200 else []
            away_team_players = away_team_players_response.json() if away_team_players_response.status_code == 200 else []
            
            # Combine and add team_id to each player
            players = []
            for p in home_team_players:
                p['team_id'] = home_team_id
                players.append(p)
            for p in away_team_players:
                p['team_id'] = away_team_id
                players.append(p)
            
            # Re-filter by team
            home_players = [p for p in players if home_team_id and p.get('team_id') == home_team_id]
            away_players = [p for p in players if away_team_id and p.get('team_id') == away_team_id]
            all_players_list = home_players + away_players
        except Exception as e:
            pass  # If fallback fails, keep players as empty list
    
    # Fallback: if team filtering didn't work, use all players
    if not all_players_list and players:
        all_players_list = players
    
    # Check if we have any players
    if not all_players_list:
        st.warning("⚠️ No players found for this game. Players need to be added to the game lineup before stats can be entered.")
        st.info("💡 **Tip:** Players must be assigned to this game's lineup (via Players_Games table) before stat entry is possible.")
        st.stop()
    
    player_options = {None: "Select Player..."}
    for p in all_players_list:
        team_label = "🏠" if p.get('team_id') == game.get('home_team_id') else "✈️"
        player_options[p['player_id']] = f"{team_label} {p['first_name']} {p['last_name']}"
    
    selected_player_id = st.selectbox(
        "Select Player",
        options=list(player_options.keys()),
        format_func=lambda x: player_options.get(x, "Select Player...")
    )
    
    if selected_player_id:
        # Quick stat buttons
        st.write("**Quick Actions:**")
        button_cols = st.columns(3)
        
        for idx, (label, description) in enumerate(common_stats):
            col_idx = idx % 3
            with button_cols[col_idx]:
                # Add visual indicator for scoring stats
                points = get_points_for_stat(description)
                button_label = f"{label} (+{points})" if points > 0 else label
                
                if st.button(
                    button_label,
                    key=f"quick_stat_{idx}",
                    use_container_width=True,
                    type="primary"
                ):
                    try:
                        # First, record the stat event
                        stat_data = {
                            "performed_by": selected_player_id,
                            "description": description
                        }
                        response = requests.post(
                            f"{API_BASE}/games/{game_id}/stat-events",
                            json=stat_data
                        )
                        if response.status_code == 201:
                            # If it's a scoring stat, also update the game score
                            if points > 0:
                                score_updated = update_game_score(API_BASE, game_id, selected_player_id, points, game, all_players_list)
                                if score_updated:
                                    st.success(f"✅ {label} recorded! (+{points} points)")
                                else:
                                    st.warning(f"✅ {label} recorded, but score update failed")
                            else:
                                st.success(f"✅ {label} recorded!")
                            st.rerun()
                        else:
                            st.error(f"Error: {response.json().get('error', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        
        st.divider()
        
        # Custom stat entry form
        with st.form("custom_stat_form"):
            st.write("**Custom Stat Entry:**")
            custom_description = st.text_input("Stat Description", placeholder="e.g., 2 points scored, assist, rebound")
            
            col_submit, col_cancel = st.columns(2)
            with col_submit:
                if st.form_submit_button("Add Stat", type="primary"):
                    if custom_description:
                        try:
                            stat_data = {
                                "performed_by": selected_player_id,
                                "description": custom_description
                            }
                            response = requests.post(
                                f"{API_BASE}/games/{game_id}/stat-events",
                                json=stat_data
                            )
                            if response.status_code == 201:
                                st.success("Stat added successfully!")
                                st.rerun()
                            else:
                                st.error(f"Error: {response.json().get('error', 'Unknown error')}")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                    else:
                        st.warning("Please enter a stat description")
    
    st.divider()
    
    # Recent stats with undo/delete
    st.subheader("Recent Stats (Last 10)")
    if stat_events:
        recent_stats = stat_events[-10:]  # Last 10 events
        for event in reversed(recent_stats):
            player_name = next(
                (f"{p['first_name']} {p['last_name']}" for p in all_players_list if p['player_id'] == event['performed_by']),
                "Unknown Player"
            )
            
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{player_name}**: {event['description']}")
                st.caption(f"Time: {event.get('time_entered', 'N/A')}")
            
            with col2:
                if st.button("✏️ Edit", key=f"edit_{event['event_id']}"):
                    st.session_state[f"editing_{event['event_id']}"] = True
            
            with col3:
                if st.button("🗑️ Delete", key=f"delete_{event['event_id']}"):
                    try:
                        # Check if this was a scoring stat - we need to subtract points
                        points = get_points_for_stat(event['description'])
                        
                        delete_response = requests.delete(
                            f"{API_BASE}/games/{game_id}/stat-events/{event['event_id']}"
                        )
                        if delete_response.status_code == 200:
                            # If it was a scoring stat, subtract points from the score
                            if points > 0:
                                update_game_score(API_BASE, game_id, event['performed_by'], -points, game, all_players_list)
                                st.success(f"Stat deleted! (-{points} points)")
                            else:
                                st.success("Stat deleted!")
                            st.rerun()
                        else:
                            st.error(f"Error: {delete_response.json().get('error', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            
            # Edit form
            if st.session_state.get(f"editing_{event['event_id']}", False):
                with st.form(f"edit_form_{event['event_id']}"):
                    player_options = {None: "Select Player..."}
                    for p in all_players_list:
                        team_label = "🏠" if p.get('team_id') == game.get('home_team_id') else "✈️"
                        player_options[p['player_id']] = f"{team_label} {p['first_name']} {p['last_name']}"
                    current_player_id = event.get('performed_by')
                    player_keys = list(player_options.keys())
                    default_index = player_keys.index(current_player_id) if current_player_id in player_keys else 0
                    selected_player_id = st.selectbox(
                        "Player",
                        options=player_keys,
                        format_func=lambda x: player_options.get(x, "Select Player..."),
                        index=default_index,
                        key=f"edit_player_{event['event_id']}"
                    )
                    
                    new_description = st.text_input(
                        "Description",
                        value=event['description'],
                        key=f"new_desc_{event['event_id']}"
                    )
                    col_submit, col_cancel = st.columns(2)
                    with col_submit:
                        if st.form_submit_button("Update"):
                            try:
                                update_data = {"description": new_description}
                                if selected_player_id:
                                    update_data["performed_by"] = selected_player_id
                                update_response = requests.put(
                                    f"{API_BASE}/games/{game_id}/stat-events/{event['event_id']}",
                                    json=update_data
                                )
                                if update_response.status_code == 200:
                                    st.success("Stat updated!")
                                    st.session_state[f"editing_{event['event_id']}"] = False
                                    st.rerun()
                                else:
                                    st.error(f"Error: {update_response.json().get('error', 'Unknown error')}")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                    with col_cancel:
                        if st.form_submit_button("Cancel"):
                            st.session_state[f"editing_{event['event_id']}"] = False
                            st.rerun()
            
            st.divider()
    else:
        st.info("No stats recorded yet. Start logging stats above!")

with col_right:
    st.subheader("Live Summary")
    
    # Use the API summary endpoint for team totals and top performers
    try:
        summary_response = requests.get(f"{API_BASE}/games/{game_id}/summary")
        if summary_response.status_code == 200:
            summary = summary_response.json()
            team_totals = summary.get('team_totals', {})
            home_leaders = summary.get('home_team_leaders', [])
            away_leaders = summary.get('away_team_leaders', [])
            
            # Team totals from API
            st.write("**Team Totals:**")
            home_stats_count = team_totals.get('home_team_stat_count', 0) or 0
            away_stats_count = team_totals.get('away_team_stat_count', 0) or 0
            
            col_home, col_away = st.columns(2)
            with col_home:
                st.metric(game['home_team'], home_stats_count)
            with col_away:
                st.metric(game['away_team'], away_stats_count)
            
            st.divider()
            
            # Top performers from API
            st.write("**Top Performers:**")
            all_leaders = home_leaders + away_leaders
            # Sort by stat count and get top 5
            all_leaders_sorted = sorted(all_leaders, key=lambda x: x.get('total_stat_events', 0), reverse=True)[:5]
            
            if all_leaders_sorted and any(l.get('total_stat_events', 0) > 0 for l in all_leaders_sorted):
                for leader in all_leaders_sorted:
                    if leader.get('total_stat_events', 0) > 0:
                        st.write(f"**{leader['first_name']} {leader['last_name']}**: {leader['total_stat_events']} stats")
            else:
                st.info("No stats recorded yet")
        else:
            # Fallback to client-side calculation if API fails
            st.write("**Team Totals:**")
            home_stats_count = len([e for e in stat_events if any(p['player_id'] == e['performed_by'] and p.get('team_id') == game.get('home_team_id') for p in all_players_list)])
            away_stats_count = len([e for e in stat_events if any(p['player_id'] == e['performed_by'] and p.get('team_id') == game.get('away_team_id') for p in all_players_list)])
            
            col_home, col_away = st.columns(2)
            with col_home:
                st.metric(game.get('home_team', 'Home'), home_stats_count)
            with col_away:
                st.metric(game.get('away_team', 'Away'), away_stats_count)
            
            st.divider()
            st.write("**Top Performers:**")
            st.info("Could not load from API")
    except Exception as e:
        st.warning(f"Could not load summary: {str(e)}")
    
    st.divider()
    
    # Auto-refresh option
    if st.button("🔄 Refresh Stats", use_container_width=True):
        st.rerun()
    
    st.divider()
    
    # Proceed to finalization button
    st.write("**Done entering stats?**")
    if st.button("Proceed to Finalization →", type="primary", use_container_width=True):
        st.session_state['selected_game_id'] = game_id
        st.switch_page('pages/03_Game_Finalization.py')