import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from modules.nav import SideBarLinks

SideBarLinks()
st.set_page_config(layout='wide')

st.title("📊 Data Management")
st.write("View, filter, and update all system data including sports, leagues, teams, players, and games.")

API_BASE = "http://web-api:4000/system-admin"

# Create tabs for different entity types
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏀 Sports", "🏆 Leagues", "👥 Teams", "🏃 Players", "🎮 Games"])

# ==================== SPORTS TAB ====================
with tab1:
    st.subheader("Sports Management")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("View and manage all sports in the system.")
    with col2:
        if st.button("🔄 Refresh", key="refresh_sports"):
            st.rerun()
    
    try:
        # Fetch all sports
        sports_response = requests.get(f"{API_BASE}/sports")
        if sports_response.status_code == 200:
            sports = sports_response.json()
            
            if sports:
                # Display sports in a table
                df = pd.DataFrame(sports)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Edit sport section
                st.divider()
                st.subheader("Edit Sport")
                sport_options = {f"{s['name']} (ID: {s['sport_id']})": s['sport_id'] for s in sports}
                selected_sport_display = st.selectbox("Select Sport to Edit", options=list(sport_options.keys()))
                selected_sport_id = sport_options[selected_sport_display]
                
                # Get selected sport details
                selected_sport = next((s for s in sports if s['sport_id'] == selected_sport_id), None)
                
                if selected_sport:
                    with st.form(f"edit_sport_{selected_sport_id}"):
                        new_name = st.text_input("Sport Name", value=selected_sport.get('name', ''))
                        new_description = st.text_area("Description", value=selected_sport.get('description', ''))
                        
                        if st.form_submit_button("Update Sport"):
                            update_data = {"name": new_name}
                            if new_description:
                                update_data["description"] = new_description
                            
                            update_response = requests.put(f"{API_BASE}/sports/{selected_sport_id}", json=update_data)
                            if update_response.status_code == 200:
                                st.success("Sport updated successfully!")
                                st.rerun()
                            else:
                                st.error(f"Error: {update_response.json().get('error', 'Unknown error')}")
                
                # Add new sport section
                st.divider()
                st.subheader("Add New Sport")
                with st.form("add_sport"):
                    new_sport_name = st.text_input("Sport Name *")
                    new_sport_description = st.text_area("Description")
                    
                    if st.form_submit_button("Add Sport"):
                        if new_sport_name:
                            create_data = {"name": new_sport_name}
                            if new_sport_description:
                                create_data["description"] = new_sport_description
                            
                            create_response = requests.post(f"{API_BASE}/sports", json=create_data)
                            if create_response.status_code == 201:
                                st.success("Sport created successfully!")
                                st.rerun()
                            else:
                                st.error(f"Error: {create_response.json().get('error', 'Unknown error')}")
                        else:
                            st.error("Sport name is required")
            else:
                st.info("No sports found.")
        else:
            st.error(f"Error loading sports: {sports_response.json().get('error', 'Unknown error')}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

# ==================== LEAGUES TAB ====================
with tab2:
    st.subheader("Leagues Management")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("View and manage all leagues in the system.")
    with col2:
        if st.button("🔄 Refresh", key="refresh_leagues"):
            st.rerun()
    
    try:
        # Fetch all leagues
        leagues_response = requests.get(f"{API_BASE}/leagues")
        if leagues_response.status_code == 200:
            leagues = leagues_response.json()
            
            # Fetch sports for filtering
            sports_response = requests.get(f"{API_BASE}/sports")
            sports = sports_response.json() if sports_response.status_code == 200 else []
            sport_map = {s['sport_id']: s['name'] for s in sports}
            
            if leagues:
                # Filters
                col1, col2, col3 = st.columns(3)
                with col1:
                    sport_filter = st.selectbox("Filter by Sport", options=["All"] + [s['name'] for s in sports], key="league_sport_filter")
                with col2:
                    semester_filter = st.selectbox("Filter by Semester", options=["All", "Fall", "Spring", "Summer", "Winter"], key="league_semester_filter")
                with col3:
                    year_filter = st.number_input("Filter by Year", min_value=2020, max_value=2030, value=2025, key="league_year_filter")
                
                # Apply filters
                filtered_leagues = leagues
                if sport_filter != "All":
                    sport_id = next((s['sport_id'] for s in sports if s['name'] == sport_filter), None)
                    if sport_id:
                        filtered_leagues = [l for l in filtered_leagues if l.get('sport_played') == sport_id]
                if semester_filter != "All":
                    filtered_leagues = [l for l in filtered_leagues if l.get('semester') == semester_filter]
                filtered_leagues = [l for l in filtered_leagues if l.get('year') == year_filter]
                
                # Display leagues
                if filtered_leagues:
                    # Add sport name to display
                    display_leagues = []
                    for league in filtered_leagues:
                        league_display = league.copy()
                        league_display['sport_name'] = sport_map.get(league.get('sport_played'), 'Unknown')
                        display_leagues.append(league_display)
                    
                    df = pd.DataFrame(display_leagues)
                    # Reorder columns for better display
                    if 'sport_name' in df.columns:
                        cols = ['league_id', 'name', 'sport_name', 'semester', 'year', 'league_start', 'league_end', 'max_teams']
                        cols = [c for c in cols if c in df.columns]
                        df = df[cols]
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # Edit league section
                    st.divider()
                    st.subheader("Edit League")
                    league_options = {f"{l['name']} (ID: {l['league_id']})": l['league_id'] for l in leagues}
                    selected_league_display = st.selectbox("Select League to Edit", options=list(league_options.keys()))
                    selected_league_id = league_options[selected_league_display]
                    
                    selected_league = next((l for l in leagues if l['league_id'] == selected_league_id), None)
                    
                    if selected_league:
                        with st.form(f"edit_league_{selected_league_id}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                new_name = st.text_input("League Name", value=selected_league.get('name', ''))
                                new_sport = st.selectbox("Sport", options=[s['sport_id'] for s in sports], 
                                                         format_func=lambda x: sport_map.get(x, f"Sport {x}"),
                                                         index=[s['sport_id'] for s in sports].index(selected_league.get('sport_played')) if selected_league.get('sport_played') in [s['sport_id'] for s in sports] else 0)
                                new_max_teams = st.number_input("Max Teams", min_value=0, value=selected_league.get('max_teams') or 0)
                            with col2:
                                new_semester = st.selectbox("Semester", options=["Fall", "Spring", "Summer", "Winter"], 
                                                           index=["Fall", "Spring", "Summer", "Winter"].index(selected_league.get('semester', 'Fall')) if selected_league.get('semester') in ["Fall", "Spring", "Summer", "Winter"] else 0)
                                new_year = st.number_input("Year", min_value=2020, max_value=2030, value=selected_league.get('year') or 2025)
                                new_start = st.date_input("Start Date", value=datetime.strptime(selected_league.get('league_start', '2025-01-01'), '%Y-%m-%d').date() if selected_league.get('league_start') else datetime.now().date())
                                new_end = st.date_input("End Date", value=datetime.strptime(selected_league.get('league_end', '2025-12-31'), '%Y-%m-%d').date() if selected_league.get('league_end') else datetime.now().date())
                            
                            if st.form_submit_button("Update League"):
                                update_data = {
                                    "name": new_name,
                                    "sport_played": new_sport,
                                    "semester": new_semester,
                                    "year": int(new_year),
                                    "max_teams": int(new_max_teams) if new_max_teams else None,
                                    "league_start": new_start.isoformat(),
                                    "league_end": new_end.isoformat()
                                }
                                
                                update_response = requests.put(f"{API_BASE}/leagues/{selected_league_id}", json=update_data)
                                if update_response.status_code == 200:
                                    st.success("League updated successfully!")
                                    st.rerun()
                                else:
                                    st.error(f"Error: {update_response.json().get('error', 'Unknown error')}")
                    
                    # Add new league section
                    st.divider()
                    st.subheader("Add New League")
                    with st.form("add_league"):
                        col1, col2 = st.columns(2)
                        with col1:
                            new_league_name = st.text_input("League Name *")
                            new_league_sport = st.selectbox("Sport *", options=[s['sport_id'] for s in sports],
                                                           format_func=lambda x: sport_map.get(x, f"Sport {x}"))
                            new_league_max_teams = st.number_input("Max Teams", min_value=0, value=0)
                        with col2:
                            new_league_semester = st.selectbox("Semester", options=["Fall", "Spring", "Summer", "Winter"])
                            new_league_year = st.number_input("Year", min_value=2020, max_value=2030, value=2025)
                            new_league_start = st.date_input("Start Date", value=datetime.now().date())
                            new_league_end = st.date_input("End Date", value=datetime.now().date())
                        
                        if st.form_submit_button("Add League"):
                            if new_league_name:
                                create_data = {
                                    "name": new_league_name,
                                    "sport_played": new_league_sport,
                                    "semester": new_league_semester,
                                    "year": int(new_league_year),
                                    "max_teams": int(new_league_max_teams) if new_league_max_teams else None,
                                    "league_start": new_league_start.isoformat(),
                                    "league_end": new_league_end.isoformat()
                                }
                                
                                create_response = requests.post(f"{API_BASE}/leagues", json=create_data)
                                if create_response.status_code == 201:
                                    st.success("League created successfully!")
                                    st.rerun()
                                else:
                                    st.error(f"Error: {create_response.json().get('error', 'Unknown error')}")
                            else:
                                st.error("League name is required")
                else:
                    st.info("No leagues match the selected filters.")
            else:
                st.info("No leagues found.")
        else:
            st.error(f"Error loading leagues: {leagues_response.json().get('error', 'Unknown error')}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

# ==================== TEAMS TAB ====================
with tab3:
    st.subheader("Teams Management")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("View and manage all teams in the system.")
    with col2:
        if st.button("🔄 Refresh", key="refresh_teams"):
            st.rerun()
    
    try:
        # Fetch all teams
        teams_response = requests.get(f"{API_BASE}/teams")
        if teams_response.status_code == 200:
            teams = teams_response.json()
            
            # Fetch leagues for filtering
            leagues_response = requests.get(f"{API_BASE}/leagues")
            leagues = leagues_response.json() if leagues_response.status_code == 200 else []
            league_map = {l['league_id']: l['name'] for l in leagues}
            
            if teams:
                # Filters
                col1, col2 = st.columns(2)
                with col1:
                    league_filter = st.selectbox("Filter by League", options=["All"] + [l['name'] for l in leagues], key="team_league_filter")
                with col2:
                    search_filter = st.text_input("Search by Team Name", key="team_search_filter")
                
                # Apply filters
                filtered_teams = teams
                if league_filter != "All":
                    league_id = next((l['league_id'] for l in leagues if l['name'] == league_filter), None)
                    if league_id:
                        filtered_teams = [t for t in filtered_teams if t.get('league_played') == league_id]
                if search_filter:
                    filtered_teams = [t for t in filtered_teams if search_filter.lower() in t.get('name', '').lower()]
                
                # Display teams
                if filtered_teams:
                    # Add league name to display
                    display_teams = []
                    for team in filtered_teams:
                        team_display = team.copy()
                        team_display['league_name'] = league_map.get(team.get('league_played'), 'Unknown')
                        display_teams.append(team_display)
                    
                    df = pd.DataFrame(display_teams)
                    # Reorder columns
                    if 'league_name' in df.columns:
                        cols = ['team_id', 'name', 'league_name', 'wins', 'losses', 'founded_date']
                        cols = [c for c in cols if c in df.columns]
                        df = df[cols]
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # Edit team section
                    st.divider()
                    st.subheader("Edit Team")
                    team_options = {f"{t['name']} (ID: {t['team_id']})": t['team_id'] for t in teams}
                    selected_team_display = st.selectbox("Select Team to Edit", options=list(team_options.keys()))
                    selected_team_id = team_options[selected_team_display]
                    
                    selected_team = next((t for t in teams if t['team_id'] == selected_team_id), None)
                    
                    if selected_team:
                        with st.form(f"edit_team_{selected_team_id}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                new_name = st.text_input("Team Name", value=selected_team.get('name', ''))
                                new_league = st.selectbox("League", options=[l['league_id'] for l in leagues],
                                                         format_func=lambda x: league_map.get(x, f"League {x}"),
                                                         index=[l['league_id'] for l in leagues].index(selected_team.get('league_played')) if selected_team.get('league_played') in [l['league_id'] for l in leagues] else 0)
                            with col2:
                                new_wins = st.number_input("Wins", min_value=0, value=selected_team.get('wins', 0))
                                new_losses = st.number_input("Losses", min_value=0, value=selected_team.get('losses', 0))
                                new_founded = st.date_input("Founded Date", value=datetime.strptime(selected_team.get('founded_date', '2025-01-01'), '%Y-%m-%d').date() if selected_team.get('founded_date') else datetime.now().date())
                            
                            if st.form_submit_button("Update Team"):
                                update_data = {
                                    "name": new_name,
                                    "league_played": new_league,
                                    "wins": int(new_wins),
                                    "losses": int(new_losses),
                                    "founded_date": new_founded.isoformat()
                                }
                                
                                update_response = requests.put(f"{API_BASE}/teams/{selected_team_id}", json=update_data)
                                if update_response.status_code == 200:
                                    st.success("Team updated successfully!")
                                    st.rerun()
                                else:
                                    st.error(f"Error: {update_response.json().get('error', 'Unknown error')}")
                    
                    # Add new team section
                    st.divider()
                    st.subheader("Add New Team")
                    with st.form("add_team"):
                        col1, col2 = st.columns(2)
                        with col1:
                            new_team_name = st.text_input("Team Name *")
                            new_team_league = st.selectbox("League *", options=[l['league_id'] for l in leagues],
                                                          format_func=lambda x: league_map.get(x, f"League {x}"))
                        with col2:
                            new_team_wins = st.number_input("Wins", min_value=0, value=0)
                            new_team_losses = st.number_input("Losses", min_value=0, value=0)
                            new_team_founded = st.date_input("Founded Date", value=datetime.now().date())
                        
                        if st.form_submit_button("Add Team"):
                            if new_team_name:
                                create_data = {
                                    "name": new_team_name,
                                    "league_played": new_team_league,
                                    "wins": int(new_team_wins),
                                    "losses": int(new_team_losses),
                                    "founded_date": new_team_founded.isoformat()
                                }
                                
                                create_response = requests.post(f"{API_BASE}/teams", json=create_data)
                                if create_response.status_code == 201:
                                    st.success("Team created successfully!")
                                    st.rerun()
                                else:
                                    st.error(f"Error: {create_response.json().get('error', 'Unknown error')}")
                            else:
                                st.error("Team name is required")
                else:
                    st.info("No teams match the selected filters.")
            else:
                st.info("No teams found.")
        else:
            st.error(f"Error loading teams: {teams_response.json().get('error', 'Unknown error')}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

# ==================== PLAYERS TAB ====================
with tab4:
    st.subheader("Players Management")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("View and manage all players in the system.")
    with col2:
        if st.button("🔄 Refresh", key="refresh_players"):
            st.rerun()
    
    try:
        # Fetch all players
        players_response = requests.get(f"{API_BASE}/players")
        if players_response.status_code == 200:
            players = players_response.json()
            
            if players:
                # Search filter
                search_filter = st.text_input("Search by Name or Email", key="player_search_filter")
                
                # Apply filter
                filtered_players = players
                if search_filter:
                    filtered_players = [p for p in players if 
                                       search_filter.lower() in p.get('first_name', '').lower() or
                                       search_filter.lower() in p.get('last_name', '').lower() or
                                       search_filter.lower() in p.get('email', '').lower()]
                
                # Display players
                if filtered_players:
                    df = pd.DataFrame(filtered_players)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # Edit player section
                    st.divider()
                    st.subheader("Edit Player")
                    player_options = {f"{p['first_name']} {p['last_name']} (ID: {p['player_id']})": p['player_id'] for p in players}
                    selected_player_display = st.selectbox("Select Player to Edit", options=list(player_options.keys()))
                    selected_player_id = player_options[selected_player_display]
                    
                    selected_player = next((p for p in players if p['player_id'] == selected_player_id), None)
                    
                    if selected_player:
                        with st.form(f"edit_player_{selected_player_id}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                new_first_name = st.text_input("First Name", value=selected_player.get('first_name', ''))
                                new_last_name = st.text_input("Last Name", value=selected_player.get('last_name', ''))
                            with col2:
                                new_email = st.text_input("Email", value=selected_player.get('email', ''))
                                new_phone = st.text_input("Phone Number", value=selected_player.get('phone_number', ''))
                            
                            if st.form_submit_button("Update Player"):
                                update_data = {
                                    "first_name": new_first_name,
                                    "last_name": new_last_name,
                                    "email": new_email
                                }
                                if new_phone:
                                    update_data["phone_number"] = new_phone
                                
                                update_response = requests.put(f"{API_BASE}/players/{selected_player_id}", json=update_data)
                                if update_response.status_code == 200:
                                    st.success("Player updated successfully!")
                                    st.rerun()
                                else:
                                    st.error(f"Error: {update_response.json().get('error', 'Unknown error')}")
                    
                    # Add new player section
                    st.divider()
                    st.subheader("Add New Player")
                    with st.form("add_player"):
                        col1, col2 = st.columns(2)
                        with col1:
                            new_player_first = st.text_input("First Name *")
                            new_player_last = st.text_input("Last Name *")
                        with col2:
                            new_player_email = st.text_input("Email *")
                            new_player_phone = st.text_input("Phone Number")
                        
                        if st.form_submit_button("Add Player"):
                            if new_player_first and new_player_last and new_player_email:
                                create_data = {
                                    "first_name": new_player_first,
                                    "last_name": new_player_last,
                                    "email": new_player_email
                                }
                                if new_player_phone:
                                    create_data["phone_number"] = new_player_phone
                                
                                create_response = requests.post(f"{API_BASE}/players", json=create_data)
                                if create_response.status_code == 201:
                                    st.success("Player created successfully!")
                                    st.rerun()
                                else:
                                    st.error(f"Error: {create_response.json().get('error', 'Unknown error')}")
                            else:
                                st.error("First name, last name, and email are required")
                else:
                    st.info("No players match the search criteria.")
            else:
                st.info("No players found.")
        else:
            st.error(f"Error loading players: {players_response.json().get('error', 'Unknown error')}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

# ==================== GAMES TAB ====================
with tab5:
    st.subheader("Games Management")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("View and manage all games in the system.")
    with col2:
        if st.button("🔄 Refresh", key="refresh_games"):
            st.rerun()
    
    try:
        # Fetch all games
        games_response = requests.get(f"{API_BASE}/games")
        if games_response.status_code == 200:
            games = games_response.json()
            
            # Fetch leagues for filtering
            leagues_response = requests.get(f"{API_BASE}/leagues")
            leagues = leagues_response.json() if leagues_response.status_code == 200 else []
            league_map = {l['league_id']: l['name'] for l in leagues}
            
            if games:
                # Filters
                col1, col2 = st.columns(2)
                with col1:
                    league_filter = st.selectbox("Filter by League", options=["All"] + [l['name'] for l in leagues], key="game_league_filter")
                with col2:
                    date_filter = st.date_input("Filter by Date", value=None, key="game_date_filter")
                
                # Apply filters
                filtered_games = games
                if league_filter != "All":
                    league_id = next((l['league_id'] for l in leagues if l['name'] == league_filter), None)
                    if league_id:
                        filtered_games = [g for g in filtered_games if g.get('league_played') == league_id]
                if date_filter:
                    date_str = date_filter.isoformat()
                    filtered_games = [g for g in filtered_games if g.get('date_played') == date_str]
                
                # Display games
                if filtered_games:
                    # Add league name to display
                    display_games = []
                    for game in filtered_games:
                        game_display = game.copy()
                        game_display['league_name'] = league_map.get(game.get('league_played'), 'Unknown')
                        display_games.append(game_display)
                    
                    df = pd.DataFrame(display_games)
                    # Reorder columns
                    if 'league_name' in df.columns:
                        cols = ['game_id', 'date_played', 'start_time', 'location', 'home_team', 'away_team', 'home_score', 'away_score', 'league_name']
                        cols = [c for c in cols if c in df.columns]
                        df = df[cols]
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # Edit game section
                    st.divider()
                    st.subheader("Edit Game")
                    game_options = {f"Game {g['game_id']} - {g.get('home_team', 'TBD')} vs {g.get('away_team', 'TBD')}": g['game_id'] for g in games}
                    selected_game_display = st.selectbox("Select Game to Edit", options=list(game_options.keys()))
                    selected_game_id = game_options[selected_game_display]
                    
                    selected_game = next((g for g in games if g['game_id'] == selected_game_id), None)
                    
                    if selected_game:
                        with st.form(f"edit_game_{selected_game_id}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                new_date = st.date_input("Date", value=datetime.strptime(selected_game.get('date_played', '2025-01-01'), '%Y-%m-%d').date() if selected_game.get('date_played') else datetime.now().date())
                                new_time = st.time_input("Start Time", value=datetime.strptime(selected_game.get('start_time', '12:00:00'), '%H:%M:%S').time() if selected_game.get('start_time') else datetime.now().time())
                                new_location = st.text_input("Location", value=selected_game.get('location', ''))
                            with col2:
                                new_league = st.selectbox("League", options=[l['league_id'] for l in leagues],
                                                          format_func=lambda x: league_map.get(x, f"League {x}"),
                                                          index=[l['league_id'] for l in leagues].index(selected_game.get('league_played')) if selected_game.get('league_played') in [l['league_id'] for l in leagues] else 0)
                                new_home_score = st.number_input("Home Score", min_value=0, value=selected_game.get('home_score') or 0)
                                new_away_score = st.number_input("Away Score", min_value=0, value=selected_game.get('away_score') or 0)
                            
                            if st.form_submit_button("Update Game"):
                                update_data = {
                                    "date_played": new_date.isoformat(),
                                    "start_time": new_time.strftime('%H:%M:%S'),
                                    "location": new_location,
                                    "league_played": new_league,
                                    "home_score": int(new_home_score) if new_home_score else None,
                                    "away_score": int(new_away_score) if new_away_score else None
                                }
                                
                                update_response = requests.put(f"{API_BASE}/games/{selected_game_id}", json=update_data)
                                if update_response.status_code == 200:
                                    st.success("Game updated successfully!")
                                    st.rerun()
                                else:
                                    st.error(f"Error: {update_response.json().get('error', 'Unknown error')}")
                    
                    # Add new game section
                    st.divider()
                    st.subheader("Add New Game")
                    with st.form("add_game"):
                        col1, col2 = st.columns(2)
                        with col1:
                            new_game_date = st.date_input("Date *", value=datetime.now().date())
                            new_game_time = st.time_input("Start Time", value=datetime.now().time())
                            new_game_location = st.text_input("Location")
                        with col2:
                            new_game_league = st.selectbox("League *", options=[l['league_id'] for l in leagues],
                                                          format_func=lambda x: league_map.get(x, f"League {x}"))
                            new_game_home_score = st.number_input("Home Score", min_value=0, value=0)
                            new_game_away_score = st.number_input("Away Score", min_value=0, value=0)
                        
                        if st.form_submit_button("Add Game"):
                            create_data = {
                                "date_played": new_game_date.isoformat(),
                                "start_time": new_game_time.strftime('%H:%M:%S'),
                                "location": new_game_location,
                                "league_played": new_game_league,
                                "home_score": int(new_game_home_score) if new_game_home_score else None,
                                "away_score": int(new_game_away_score) if new_game_away_score else None
                            }
                            
                            create_response = requests.post(f"{API_BASE}/games", json=create_data)
                            if create_response.status_code == 201:
                                st.success("Game created successfully!")
                                st.rerun()
                            else:
                                st.error(f"Error: {create_response.json().get('error', 'Unknown error')}")
                else:
                    st.info("No games match the selected filters.")
            else:
                st.info("No games found.")
        else:
            st.error(f"Error loading games: {games_response.json().get('error', 'Unknown error')}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

