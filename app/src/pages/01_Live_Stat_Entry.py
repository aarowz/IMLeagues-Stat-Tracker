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
    st.stop()

# Game selector
selected_game_option = st.selectbox(
    "Select Game",
    options=available_games,
    format_func=lambda g: f"{g['date_played']} - {g.get('home_team', 'TBD')} vs {g.get('away_team', 'TBD')} @ {g['location']}"
)

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
    
    # Fallback: if team filtering didn't work, use all players
    if not all_players_list and players:
        all_players_list = players
    
    # DEBUG: Show what we have (TEMPORARY - will remove after debugging)
    with st.expander("🔍 Debug Info (Click to expand)"):
        st.write(f"**Game ID:** {game_id}")
        st.write(f"**Home Team ID:** {home_team_id}")
        st.write(f"**Away Team ID:** {away_team_id}")
        st.write(f"**Total players from API:** {len(players)}")
        st.write(f"**Home players (filtered):** {len(home_players)}")
        st.write(f"**Away players (filtered):** {len(away_players)}")
        st.write(f"**All players list:** {len(all_players_list)}")
        if players:
            st.write("**Sample player data:**")
            for p in players[:3]:
                st.write(f"- {p.get('first_name')} {p.get('last_name')} (Team ID: {p.get('team_id')})")
        else:
            st.write("**No players returned from API**")
    
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
                if st.button(
                    label,
                    key=f"quick_stat_{idx}",
                    use_container_width=True,
                    type="primary"
                ):
                    try:
                        stat_data = {
                            "performed_by": selected_player_id,
                            "description": description
                        }
                        response = requests.post(
                            f"{API_BASE}/games/{game_id}/stat-events",
                            json=stat_data
                        )
                        if response.status_code == 201:
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
                        delete_response = requests.delete(
                            f"{API_BASE}/games/{game_id}/stat-events/{event['event_id']}"
                        )
                        if delete_response.status_code == 200:
                            st.success("Stat deleted!")
                            st.rerun()
                        else:
                            st.error(f"Error: {delete_response.json().get('error', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            
            # Edit form
            if st.session_state.get(f"editing_{event['event_id']}", False):
                with st.form(f"edit_form_{event['event_id']}"):
                    new_description = st.text_input(
                        "New Description",
                        value=event['description'],
                        key=f"new_desc_{event['event_id']}"
                    )
                    col_submit, col_cancel = st.columns(2)
                    with col_submit:
                        if st.form_submit_button("Update"):
                            try:
                                update_data = {"description": new_description}
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
    
    # Team totals
    st.write("**Team Totals:**")
    home_stats_count = len([e for e in stat_events if any(p['player_id'] == e['performed_by'] and p['team_id'] == game['home_team_id'] for p in all_players_list)])
    away_stats_count = len([e for e in stat_events if any(p['player_id'] == e['performed_by'] and p['team_id'] == game['away_team_id'] for p in all_players_list)])
    
    col_home, col_away = st.columns(2)
    with col_home:
        st.metric(game['home_team'], home_stats_count)
    with col_away:
        st.metric(game['away_team'], away_stats_count)
    
    st.divider()
    
    # Top performers
    st.write("**Top Performers:**")
    
    # Count stats per player
    player_stat_counts = {}
    for event in stat_events:
        player_id = event['performed_by']
        if player_id not in player_stat_counts:
            player_stat_counts[player_id] = 0
        player_stat_counts[player_id] += 1
    
    # Sort and display top 5
    top_players = sorted(player_stat_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    if top_players:
        for player_id, count in top_players:
            player_name = next(
                (f"{p['first_name']} {p['last_name']}" for p in all_players_list if p['player_id'] == player_id),
                "Unknown Player"
            )
            st.write(f"**{player_name}**: {count} stats")
    else:
        st.info("No stats recorded yet")
    
    st.divider()
    
    # Auto-refresh option
    if st.button("🔄 Refresh Stats", use_container_width=True):
        st.rerun()

