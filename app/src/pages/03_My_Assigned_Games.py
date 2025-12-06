import streamlit as st
import requests
from datetime import datetime
from modules.nav import SideBarLinks

SideBarLinks()
st.set_page_config(layout='wide')

st.title("My Assigned Games")
st.write("View all games assigned to you as a stat keeper.")

# Stat keeper ID
STAT_KEEPER_ID = 1
API_BASE = "http://web-api:4000/stat-keeper"

# Fetch assigned games with filtering done at API/database level
try:
    upcoming_response = requests.get(f"{API_BASE}/stat-keepers/{STAT_KEEPER_ID}/games?upcoming_only=true")
    past_response = requests.get(f"{API_BASE}/stat-keepers/{STAT_KEEPER_ID}/games?upcoming_only=false")
    
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

# Sort games (API already sorts, but ensure correct order for display)
upcoming_games.sort(key=lambda x: (x['date_played'], x['start_time']))
past_games.sort(key=lambda x: (x['date_played'], x['start_time']), reverse=True)

all_games = upcoming_games + past_games

if not all_games:
    st.info("You have no assigned games yet.")
    st.stop()

# Tabs for upcoming and past games
tab1, tab2 = st.tabs(["📅 Upcoming Games", "📊 Past Games"])

with tab1:
    st.subheader("Upcoming Games")
    
    if upcoming_games:
        # Add dropdown to limit number of games shown
        col_filter, col_info = st.columns([1, 3])
        with col_filter:
            # Always show fixed options: 5, 10, 20, 50, and All
            limit_options = [5, 10, 20, 50]
            
            # Add "All" option (total count) if there are more than 50 games
            # If 50 or fewer, 50 will effectively be "All"
            if len(upcoming_games) > 50:
                limit_options.append(len(upcoming_games))
            
            display_limit = st.selectbox(
                "Show",
                options=limit_options,
                format_func=lambda x: f"{x} games" if x < len(upcoming_games) else "All games",
                index=0 if len(upcoming_games) > 5 else (len(limit_options) - 1),
                key="upcoming_limit"
            )
        with col_info:
            st.caption(f"Showing {min(display_limit, len(upcoming_games))} of {len(upcoming_games)} upcoming games")
        
        # Limit the games to display
        games_to_show = upcoming_games[:display_limit]
        
        for idx, game in enumerate(games_to_show):
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    home_team = game.get('home_team') or 'TBD'
                    away_team = game.get('away_team') or 'TBD'
                    st.write(f"**{home_team}** vs **{away_team}**")
                    if game.get('home_team') is None or game.get('away_team') is None:
                        st.warning("⚠️ Teams not yet assigned")
                    st.write(f"📅 {game['date_played']} | 🕐 {game['start_time']}")
                    st.write(f"📍 {game['location']}")
                    st.write(f"🏆 {game['league_name']} - {game['sport_name']}")
                
                with col2:
                    # Check if game is today or very soon
                    game_date = datetime.strptime(game['date_played'], '%Y-%m-%d').date()
                    days_until = (game_date - today).days
                    
                    if days_until == 0:
                        st.success("**Today!**")
                    elif days_until == 1:
                        st.info("**Tomorrow**")
                    else:
                        st.write(f"**{days_until} days away**")
                    
                    if game.get('assignment_date'):
                        st.caption(f"Assigned: {game['assignment_date']}")
                
                with col3:
                    # Only allow starting live entry if teams are assigned
                    if game.get('home_team') and game.get('away_team'):
                        if st.button("Start Live Entry", key=f"start_{game['game_id']}_{idx}", use_container_width=True):
                            st.session_state['selected_game_id'] = game['game_id']
                            st.switch_page('pages/01_Live_Stat_Entry.py')
                    else:
                        st.button("Start Live Entry", key=f"start_{game['game_id']}_{idx}", use_container_width=True, disabled=True)
                        st.caption("Teams required")
                
                st.divider()
    else:
        st.info("No upcoming games assigned.")

with tab2:
    st.subheader("Past Games")
    
    if past_games:
        # Add dropdown to limit number of games shown
        col_filter, col_info = st.columns([1, 3])
        with col_filter:
            # Hardcoded options: 5 games and All games
            limit_options = [5]
            if len(past_games) > 5:
                limit_options.append(len(past_games))
            
            display_limit = st.selectbox(
                "Show",
                options=limit_options,
                format_func=lambda x: f"{x} games" if x < len(past_games) else "All games",
                index=0 if len(past_games) > 5 else 0,
                key="past_limit"
            )
        with col_info:
            st.caption(f"Showing {min(display_limit, len(past_games))} of {len(past_games)} past games")
        
        # Limit the games to display
        games_to_show = past_games[:display_limit]
        
        for idx, game in enumerate(games_to_show):
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    # Display score if available
                    home_score = game.get('home_score')
                    away_score = game.get('away_score')
                    home_team = game.get('home_team') or 'TBD'
                    away_team = game.get('away_team') or 'TBD'
                    
                    if home_score is not None and away_score is not None:
                        st.write(f"**{home_team}** {home_score} - {away_score} **{away_team}**")
                    else:
                        st.write(f"**{home_team}** vs **{away_team}**")
                    
                    if game.get('home_team') is None or game.get('away_team') is None:
                        st.warning("⚠️ Teams not yet assigned")
                    
                    st.write(f"📅 {game['date_played']} | 🕐 {game['start_time']}")
                    st.write(f"📍 {game['location']}")
                    st.write(f"🏆 {game['league_name']} - {game['sport_name']}")
                
                with col2:
                    # Check if stats are finalized
                    if home_score is not None and away_score is not None:
                        st.success("✅ Finalized")
                    else:
                        st.warning("⚠️ Not finalized")
                    
                    # Get stat count
                    try:
                        stats_response = requests.get(f"{API_BASE}/games/{game['game_id']}/stat-events")
                        if stats_response.status_code == 200:
                            stat_count = len(stats_response.json())
                            st.write(f"**{stat_count}** stat events")
                        else:
                            st.write("**0** stat events")
                    except:
                        st.write("**0** stat events")
                
                with col3:
                    col_view, col_finalize = st.columns(2)
                    
                    with col_view:
                        if st.button("View", key=f"view_{game['game_id']}_{idx}", use_container_width=True):
                            st.session_state['selected_game_id'] = game['game_id']
                            st.switch_page('pages/02_Game_Finalization.py')
                    
                    with col_finalize:
                        if home_score is None or away_score is None:
                            if st.button("Finalize", key=f"finalize_{game['game_id']}_{idx}", use_container_width=True):
                                st.session_state['selected_game_id'] = game['game_id']
                                st.switch_page('pages/02_Game_Finalization.py')
                
                st.divider()
    else:
        st.info("No past games recorded.")

# Summary statistics
st.divider()
st.subheader("Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Assigned", len(all_games))

with col2:
    st.metric("Upcoming", len(upcoming_games))

with col3:
    st.metric("Past", len(past_games))

with col4:
    finalized_count = sum(1 for g in past_games if g.get('home_score') is not None and g.get('away_score') is not None)
    st.metric("Finalized", finalized_count)

