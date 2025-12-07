import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from modules.nav import SideBarLinks

SideBarLinks()
st.set_page_config(layout='wide')

st.title("📊 Data Management")
st.write("View, filter, and update all system data including sports, leagues, teams, players, and games.")

API_BASE = "http://web-api:4000/system-admin"

# Create tabs for different entity types
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🏀 Sports", "🏆 Leagues", "👥 Teams", "🏃 Players", "🎮 Games", "📊 Stat Keepers"])

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
                            # Prevent multiple rapid submissions - use st.stop() to halt execution
                            update_key = f"updating_sport_{selected_sport_id}"
                            if update_key in st.session_state:
                                st.warning("Update already in progress. Please wait...")
                                st.stop()  # Completely stop execution to prevent navigation issues
                            
                            st.session_state[update_key] = True
                            update_data = {"name": new_name}
                            if new_description:
                                update_data["description"] = new_description
                            
                            update_response = requests.put(f"{API_BASE}/sports/{selected_sport_id}", json=update_data)
                            
                            # Clear flag immediately
                            if update_key in st.session_state:
                                del st.session_state[update_key]
                            
                            if update_response.status_code == 200:
                                st.success("Sport updated successfully!")
                            else:
                                st.error(f"Error: {update_response.json().get('error', 'Unknown error')}")
                
                # Delete sport section (only show if there are sports to delete)
                st.divider()
                st.subheader("Delete Sport")
                delete_sport_options = {f"{s['name']} (ID: {s['sport_id']})": s['sport_id'] for s in sports}
                selected_delete_sport_display = st.selectbox("Select Sport to Delete", options=list(delete_sport_options.keys()), key="delete_sport_select")
                selected_delete_sport_id = delete_sport_options[selected_delete_sport_display]
                
                if st.button("🗑️ Delete Sport", key="delete_sport_button", type="secondary"):
                    try:
                        delete_response = requests.delete(f"{API_BASE}/sports/{selected_delete_sport_id}")
                        if delete_response.status_code == 200:
                            st.success("Sport deleted successfully!")
                            st.rerun()  # Need explicit rerun for button clicks (not forms)
                        else:
                            try:
                                error_msg = delete_response.json().get('error', f'HTTP {delete_response.status_code}')
                            except:
                                error_msg = f'HTTP {delete_response.status_code}: {delete_response.text[:200]}'
                            st.error(f"Error: {error_msg}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            else:
                st.info("No sports found.")
            
            # Add new sport section (always visible, even when no sports exist)
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
                            # Form will auto-rerun, no need to call st.rerun()
                        else:
                            st.error(f"Error: {create_response.json().get('error', 'Unknown error')}")
                    else:
                        st.error("Sport name is required")
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
            # Reset all filter values to defaults by explicitly setting session state
            # This ensures the widgets reset to their default values
            st.session_state["league_sport_filter"] = "All"
            st.session_state["league_semester_filter"] = "All"
            st.session_state["league_min_year_filter"] = 2020
            st.session_state["league_max_year_filter"] = 2030
            st.rerun()
    
    try:
        # Fetch sports for filtering dropdown
        sports_response = requests.get(f"{API_BASE}/sports")
        sports = sports_response.json() if sports_response.status_code == 200 else []
        sport_map = {s['sport_id']: s['name'] for s in sports}
        
        # Filters UI
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            sorted_sports = sorted(sports, key=lambda x: x.get('name', ''))
            sport_display_to_id = {f"{s['name']} (ID: {s['sport_id']})": s['sport_id'] for s in sorted_sports}
            sport_filter_options = ["All"] + list(sport_display_to_id.keys())
            # Ensure default value is set if not already in session state or if value is invalid
            if "league_sport_filter" not in st.session_state or st.session_state.get("league_sport_filter") not in sport_filter_options:
                st.session_state["league_sport_filter"] = "All"
            sport_filter = st.selectbox("Filter by Sport", options=sport_filter_options, key="league_sport_filter")
        with col2:
            semester_filter_options = ["All", "Fall", "Spring", "Summer", "Winter"]
            if "league_semester_filter" not in st.session_state or st.session_state.get("league_semester_filter") not in semester_filter_options:
                st.session_state["league_semester_filter"] = "All"
            semester_filter = st.selectbox("Filter by Semester", options=semester_filter_options, key="league_semester_filter")
        with col3:
            if "league_min_year_filter" not in st.session_state:
                st.session_state["league_min_year_filter"] = 2020
            min_year_filter = st.number_input("Min Year", min_value=2020, max_value=2030, value=st.session_state.get("league_min_year_filter", 2020), key="league_min_year_filter")
        with col4:
            if "league_max_year_filter" not in st.session_state:
                st.session_state["league_max_year_filter"] = 2030
            max_year_filter = st.number_input("Max Year", min_value=2020, max_value=2030, value=st.session_state.get("league_max_year_filter", 2030), key="league_max_year_filter")
        
        # Build API request with filter parameters
        league_params = {}
        if sport_filter != "All":
            league_params["sport_id"] = sport_display_to_id.get(sport_filter)
        if semester_filter != "All":
            league_params["semester"] = semester_filter
        league_params["min_year"] = min_year_filter
        league_params["max_year"] = max_year_filter
        
        # Fetch leagues with filters applied via SQL
        leagues_response = requests.get(f"{API_BASE}/leagues", params=league_params)
        if leagues_response.status_code == 200:
            leagues = leagues_response.json()
            
            if leagues:
                # Display leagues
                filtered_leagues = leagues  # Already filtered by backend
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
                    league_options = {f"{l['name']} ({l.get('year', 'N/A')}) (ID: {l['league_id']})": l['league_id'] for l in leagues}
                    selected_league_display = st.selectbox("Select League to Edit", options=list(league_options.keys()))
                    selected_league_id = league_options[selected_league_display]
                    
                    selected_league = next((l for l in leagues if l['league_id'] == selected_league_id), None)
                    
                    if selected_league:
                        with st.form(f"edit_league_{selected_league_id}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                new_name = st.text_input("League Name", value=selected_league.get('name', ''))
                                new_sport = st.selectbox("Sport", options=[s['sport_id'] for s in sports], 
                                                         format_func=lambda x: f"{sport_map.get(x, 'Unknown')} (ID: {x})",
                                                         index=[s['sport_id'] for s in sports].index(selected_league.get('sport_played')) if selected_league.get('sport_played') in [s['sport_id'] for s in sports] else 0)
                                new_max_teams = st.number_input("Max Teams", min_value=0, value=selected_league.get('max_teams') or 0)
                            with col2:
                                new_semester = st.selectbox("Semester", options=["Fall", "Spring", "Summer", "Winter"], 
                                                           index=["Fall", "Spring", "Summer", "Winter"].index(selected_league.get('semester', 'Fall')) if selected_league.get('semester') in ["Fall", "Spring", "Summer", "Winter"] else 0)
                                new_year = st.number_input("Year", min_value=2020, max_value=2030, value=selected_league.get('year') or 2025)
                                new_start = st.date_input("Start Date", value=datetime.strptime(selected_league.get('league_start', '2025-01-01'), '%Y-%m-%d').date() if selected_league.get('league_start') else datetime.now().date())
                                new_end = st.date_input("End Date", value=datetime.strptime(selected_league.get('league_end', '2025-12-31'), '%Y-%m-%d').date() if selected_league.get('league_end') else datetime.now().date())
                            
                            if st.form_submit_button("Update League"):
                                # Prevent multiple rapid submissions - use st.stop() to halt execution
                                update_key = f"updating_league_{selected_league_id}"
                                if update_key in st.session_state:
                                    st.warning("Update already in progress. Please wait...")
                                    st.stop()  # Completely stop execution to prevent navigation issues
                                
                                st.session_state[update_key] = True
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
                                
                                # Clear flag immediately
                                if update_key in st.session_state:
                                    del st.session_state[update_key]
                                
                                if update_response.status_code == 200:
                                    st.success("League updated successfully!")
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
                                                           format_func=lambda x: f"{sport_map.get(x, 'Unknown')} (ID: {x})")
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
                                else:
                                    st.error(f"Error: {create_response.json().get('error', 'Unknown error')}")
                            else:
                                st.error("League name is required")
                    
                    # Delete league section
                    st.divider()
                    st.subheader("Delete League")
                    delete_league_options = {f"{l['name']} ({l.get('year', 'N/A')}) (ID: {l['league_id']})": l['league_id'] for l in leagues}
                    selected_delete_league_display = st.selectbox("Select League to Delete", options=list(delete_league_options.keys()), key="delete_league_select")
                    selected_delete_league_id = delete_league_options[selected_delete_league_display]
                    
                    if st.button("🗑️ Delete League", key="delete_league_button", type="secondary"):
                        try:
                            delete_response = requests.delete(f"{API_BASE}/leagues/{selected_delete_league_id}")
                            if delete_response.status_code == 200:
                                st.success("League deleted successfully!")
                                st.rerun()  # Need explicit rerun for button clicks (not forms)
                            else:
                                try:
                                    error_msg = delete_response.json().get('error', f'HTTP {delete_response.status_code}')
                                except:
                                    error_msg = f'HTTP {delete_response.status_code}: {delete_response.text[:200]}'
                                st.error(f"Error: {error_msg}")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
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
        # Fetch leagues for filtering dropdown
        leagues_response = requests.get(f"{API_BASE}/leagues")
        leagues = leagues_response.json() if leagues_response.status_code == 200 else []
        league_map = {l['league_id']: f"{l['name']} ({l.get('year', 'N/A')}) (ID: {l['league_id']})" for l in leagues}
        
        # Filters UI
        col1, col2 = st.columns(2)
        with col1:
            sorted_leagues = sorted(leagues, key=lambda x: x.get('league_start') or '', reverse=True)
            league_display_to_id = {f"{l['name']} ({l.get('year', 'N/A')}) (ID: {l['league_id']})": l['league_id'] for l in sorted_leagues}
            league_filter_options = ["All"] + list(league_display_to_id.keys())
            league_filter = st.selectbox("Filter by League", options=league_filter_options, key="team_league_filter")
        with col2:
            search_filter = st.text_input("Search by Team Name", key="team_search_filter")
        
        # Build API request with filter parameters
        team_params = {}
        if league_filter != "All":
            team_params["league_id"] = league_display_to_id.get(league_filter)
        if search_filter:
            team_params["name_search"] = search_filter
        
        # Fetch teams with filters applied via SQL
        teams_response = requests.get(f"{API_BASE}/teams", params=team_params)
        if teams_response.status_code == 200:
            teams = teams_response.json()
            
            if teams:
                # Display teams
                filtered_teams = teams  # Already filtered by backend
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
                                                         format_func=lambda x: league_map.get(x, f"Unknown (ID: {x})"),
                                                         index=[l['league_id'] for l in leagues].index(selected_team.get('league_played')) if selected_team.get('league_played') in [l['league_id'] for l in leagues] else 0)
                            with col2:
                                new_wins = st.number_input("Wins", min_value=0, value=selected_team.get('wins', 0))
                                new_losses = st.number_input("Losses", min_value=0, value=selected_team.get('losses', 0))
                                new_founded = st.date_input("Founded Date", value=datetime.strptime(selected_team.get('founded_date', '2025-01-01'), '%Y-%m-%d').date() if selected_team.get('founded_date') else datetime.now().date())
                            
                            if st.form_submit_button("Update Team"):
                                # Prevent multiple rapid submissions - use st.stop() to halt execution
                                update_key = f"updating_team_{selected_team_id}"
                                if update_key in st.session_state:
                                    st.warning("Update already in progress. Please wait...")
                                    st.stop()  # Completely stop execution to prevent navigation issues
                                
                                st.session_state[update_key] = True
                                update_data = {
                                    "name": new_name,
                                    "league_played": new_league,
                                    "wins": int(new_wins),
                                    "losses": int(new_losses),
                                    "founded_date": new_founded.isoformat()
                                }
                                
                                update_response = requests.put(f"{API_BASE}/teams/{selected_team_id}", json=update_data)
                                
                                # Clear flag immediately
                                if update_key in st.session_state:
                                    del st.session_state[update_key]
                                
                                if update_response.status_code == 200:
                                    st.success("Team updated successfully!")
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
                                                          format_func=lambda x: league_map.get(x, f"Unknown (ID: {x})"))
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
                                else:
                                    st.error(f"Error: {create_response.json().get('error', 'Unknown error')}")
                            else:
                                st.error("Team name is required")
                    
                    # Delete team section
                    st.divider()
                    st.subheader("Delete Team")
                    delete_team_options = {f"{t['name']} (ID: {t['team_id']})": t['team_id'] for t in teams}
                    selected_delete_team_display = st.selectbox("Select Team to Delete", options=list(delete_team_options.keys()), key="delete_team_select")
                    selected_delete_team_id = delete_team_options[selected_delete_team_display]
                    
                    if st.button("🗑️ Delete Team", key="delete_team_button", type="secondary"):
                        try:
                            delete_response = requests.delete(f"{API_BASE}/teams/{selected_delete_team_id}")
                            if delete_response.status_code == 200:
                                st.success("Team deleted successfully!")
                                st.rerun()  # Need explicit rerun for button clicks (not forms)
                            else:
                                try:
                                    error_msg = delete_response.json().get('error', f'HTTP {delete_response.status_code}')
                                except:
                                    error_msg = f'HTTP {delete_response.status_code}: {delete_response.text[:200]}'
                                st.error(f"Error: {error_msg}")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
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
        # Search filter (applied at API/database level)
        search_filter = st.text_input("Search by Name or Email", key="player_search_filter")
        
        # Build API request with search parameter
        player_params = {}
        if search_filter:
            player_params["search"] = search_filter
        
        # Fetch players with search filter applied via SQL
        players_response = requests.get(f"{API_BASE}/players", params=player_params)
        if players_response.status_code == 200:
            players = players_response.json()
            
            if players:
                # Display players (already filtered by backend)
                filtered_players = players
                
                # Display players
                if filtered_players:
                    df = pd.DataFrame(filtered_players)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # Edit player section
                    st.divider()
                    st.subheader("Edit Player")
                    edit_search = st.text_input("Search Player to Edit (by name, email, or ID)", key="edit_player_search")
                    
                    # Fetch players with edit search filter applied via SQL
                    edit_player_params = {}
                    if edit_search:
                        edit_player_params["search"] = edit_search
                    
                    edit_players_response = requests.get(f"{API_BASE}/players", params=edit_player_params)
                    edit_filtered_players = []
                    if edit_players_response.status_code == 200:
                        edit_filtered_players = edit_players_response.json()
                        # Also check if search matches player_id exactly
                        if edit_search and edit_search.isdigit():
                            all_players_response = requests.get(f"{API_BASE}/players")
                            if all_players_response.status_code == 200:
                                all_players = all_players_response.json()
                                matching_id = [p for p in all_players if p.get('player_id') == int(edit_search)]
                                # Add ID matches if not already in filtered list
                                for p in matching_id:
                                    if p not in edit_filtered_players:
                                        edit_filtered_players.append(p)
                    
                    if edit_filtered_players and edit_search:
                        # Show matching players as selectable options
                        player_options = {f"{p['first_name']} {p['last_name']} ({p['email']}) (ID: {p['player_id']})": p['player_id'] for p in edit_filtered_players}
                        selected_player_display = st.selectbox("Select from results", options=list(player_options.keys()), key="edit_player_select")
                        selected_player_id = player_options[selected_player_display]
                        selected_player = next((p for p in edit_filtered_players if p['player_id'] == selected_player_id), None)
                    elif not edit_search:
                        st.info("Enter a search term above to find a player to edit.")
                        selected_player = None
                    else:
                        st.warning("No players found matching your search.")
                        selected_player = None
                    
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
                                # Prevent multiple rapid submissions - use st.stop() to halt execution
                                update_key = f"updating_player_{selected_player_id}"
                                if update_key in st.session_state:
                                    st.warning("Update already in progress. Please wait...")
                                    st.stop()  # Completely stop execution to prevent navigation issues
                                
                                st.session_state[update_key] = True
                                # Validate email contains @northeastern.edu
                                if new_email and "@northeastern.edu" not in new_email:
                                    if update_key in st.session_state:
                                        del st.session_state[update_key]
                                    st.error("Email must be a valid Northeastern email address (@northeastern.edu)")
                                else:
                                    try:
                                        update_data = {
                                            "first_name": new_first_name,
                                            "last_name": new_last_name,
                                            "email": new_email
                                        }
                                        if new_phone:
                                            update_data["phone_number"] = new_phone
                                        
                                        update_response = requests.put(f"{API_BASE}/players/{selected_player_id}", json=update_data)
                                        
                                        # Clear flag immediately
                                        if update_key in st.session_state:
                                            del st.session_state[update_key]
                                        
                                        if update_response.status_code == 200:
                                            st.success("Player updated successfully!")
                                        else:
                                            try:
                                                error_msg = update_response.json().get('error', f'HTTP {update_response.status_code}')
                                            except:
                                                error_msg = f'HTTP {update_response.status_code}: {update_response.text[:200]}'
                                            st.error(f"Error: {error_msg}")
                                    except Exception as e:
                                        if update_key in st.session_state:
                                            del st.session_state[update_key]
                                        st.error(f"Error: {str(e)}")
                    
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
                                # Validate email contains @northeastern.edu
                                if "@northeastern.edu" not in new_player_email:
                                    st.error("Email must be a valid Northeastern email address (@northeastern.edu)")
                                else:
                                    try:
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
                                        else:
                                            try:
                                                error_msg = create_response.json().get('error', f'HTTP {create_response.status_code}')
                                            except:
                                                error_msg = f'HTTP {create_response.status_code}: {create_response.text[:200]}'
                                            st.error(f"Error: {error_msg}")
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                            else:
                                st.error("First name, last name, and email are required")
                    
                    # Delete player section
                    st.divider()
                    st.subheader("Delete Player")
                    delete_search = st.text_input("Search Player to Delete (by name, email, or ID)", key="delete_player_search")
                    
                    # Fetch players with delete search filter applied via SQL
                    delete_player_params = {}
                    if delete_search:
                        delete_player_params["search"] = delete_search
                    
                    delete_players_response = requests.get(f"{API_BASE}/players", params=delete_player_params)
                    delete_filtered_players = []
                    if delete_players_response.status_code == 200:
                        delete_filtered_players = delete_players_response.json()
                        # Also check if search matches player_id exactly
                        if delete_search and delete_search.isdigit():
                            all_players_response = requests.get(f"{API_BASE}/players")
                            if all_players_response.status_code == 200:
                                all_players = all_players_response.json()
                                matching_id = [p for p in all_players if p.get('player_id') == int(delete_search)]
                                # Add ID matches if not already in filtered list
                                for p in matching_id:
                                    if p not in delete_filtered_players:
                                        delete_filtered_players.append(p)
                    
                    if delete_filtered_players and delete_search:
                        # Show matching players as selectable options
                        delete_player_options = {f"{p['first_name']} {p['last_name']} ({p['email']}) (ID: {p['player_id']})": p['player_id'] for p in delete_filtered_players}
                        selected_delete_player_display = st.selectbox("Select from results", options=list(delete_player_options.keys()), key="delete_player_select")
                        selected_delete_player_id = delete_player_options[selected_delete_player_display]
                        
                        if st.button("🗑️ Delete Player", key="delete_player_button", type="secondary"):
                            try:
                                delete_response = requests.delete(f"{API_BASE}/players/{selected_delete_player_id}")
                                if delete_response.status_code == 200:
                                    st.success("Player deleted successfully!")
                                    st.rerun()  # Need explicit rerun for button clicks (not forms)
                                else:
                                    try:
                                        error_msg = delete_response.json().get('error', f'HTTP {delete_response.status_code}')
                                    except:
                                        error_msg = f'HTTP {delete_response.status_code}: {delete_response.text[:200]}'
                                    st.error(f"Error: {error_msg}")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                    elif not delete_search:
                        st.info("Enter a search term above to find a player to delete.")
                    else:
                        st.warning("No players found matching your search.")
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
        # Fetch leagues for filtering dropdown
        leagues_response = requests.get(f"{API_BASE}/leagues")
        leagues = leagues_response.json() if leagues_response.status_code == 200 else []
        league_map = {l['league_id']: f"{l['name']} ({l.get('year', 'N/A')}) (ID: {l['league_id']})" for l in leagues}
        
        # Filters UI
        col1, col2, col3 = st.columns(3)
        with col1:
            sorted_leagues = sorted(leagues, key=lambda x: x.get('league_start') or '', reverse=True)
            league_display_to_id = {f"{l['name']} ({l.get('year', 'N/A')}) (ID: {l['league_id']})": l['league_id'] for l in sorted_leagues}
            league_filter_options = ["All"] + list(league_display_to_id.keys())
            league_filter = st.selectbox("Filter by League", options=league_filter_options, key="game_league_filter")
        with col2:
            min_date_filter = st.date_input("Min Date", value=None, key="game_min_date_filter")
        with col3:
            max_date_filter = st.date_input("Max Date", value=None, key="game_max_date_filter")
        
        # Build API request with filter parameters
        game_params = {}
        if league_filter != "All":
            game_params["league_id"] = league_display_to_id.get(league_filter)
        if min_date_filter:
            game_params["min_date"] = min_date_filter.isoformat()
        if max_date_filter:
            game_params["max_date"] = max_date_filter.isoformat()
        
        # Fetch games with filters applied via SQL
        games_response = requests.get(f"{API_BASE}/games", params=game_params)
        if games_response.status_code == 200:
            games = games_response.json()
            
            if games:
                # Display games (already filtered by SQL to only include games with both teams)
                display_games = []
                for game in games:
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
                                                          format_func=lambda x: league_map.get(x, f"Unknown (ID: {x})"),
                                                          index=[l['league_id'] for l in leagues].index(selected_game.get('league_played')) if selected_game.get('league_played') in [l['league_id'] for l in leagues] else 0)
                                new_home_score = st.number_input("Home Score", min_value=0, value=selected_game.get('home_score') or 0)
                                new_away_score = st.number_input("Away Score", min_value=0, value=selected_game.get('away_score') or 0)
                            
                            if st.form_submit_button("Update Game"):
                                # Prevent multiple rapid submissions - use st.stop() to halt execution
                                update_key = f"updating_game_{selected_game_id}"
                                if update_key in st.session_state:
                                    st.warning("Update already in progress. Please wait...")
                                    st.stop()  # Completely stop execution to prevent navigation issues
                                
                                st.session_state[update_key] = True
                                update_data = {
                                    "date_played": new_date.isoformat(),
                                    "start_time": new_time.strftime('%H:%M:%S'),
                                    "location": new_location,
                                    "league_played": new_league,
                                    "home_score": int(new_home_score) if new_home_score else None,
                                    "away_score": int(new_away_score) if new_away_score else None
                                }
                                
                                update_response = requests.put(f"{API_BASE}/games/{selected_game_id}", json=update_data)
                                
                                # Clear flag immediately
                                if update_key in st.session_state:
                                    del st.session_state[update_key]
                                
                                if update_response.status_code == 200:
                                    st.success("Game updated successfully!")
                                else:
                                    st.error(f"Error: {update_response.json().get('error', 'Unknown error')}")
            else:
                st.info("No games found.")
            
            # Add new game section (always visible, even when no games exist)
            st.divider()
            st.subheader("Add New Game")
            
            # Fetch all teams for team selection
            teams_response = requests.get(f"{API_BASE}/teams")
            all_teams = teams_response.json() if teams_response.status_code == 200 else []
            team_map = {t['team_id']: f"{t['name']} (ID: {t['team_id']})" for t in all_teams}
            
            with st.form("add_game"):
                col1, col2 = st.columns(2)
                with col1:
                    new_game_date = st.date_input("Date *", value=datetime.now().date())
                    new_game_time = st.time_input("Start Time", value=datetime.now().time())
                    new_game_location = st.text_input("Location")
                    new_game_league = st.selectbox("League *", options=[l['league_id'] for l in leagues],
                                                  format_func=lambda x: league_map.get(x, f"Unknown (ID: {x})"))
                with col2:
                    new_game_home_team = st.selectbox("Home Team *", options=[None] + [t['team_id'] for t in all_teams],
                                                     format_func=lambda x: team_map.get(x, "Select Team...") if x else "Select Team...")
                    new_game_away_team = st.selectbox("Away Team *", options=[None] + [t['team_id'] for t in all_teams],
                                                     format_func=lambda x: team_map.get(x, "Select Team...") if x else "Select Team...")
                    new_game_home_score = st.number_input("Home Score", min_value=0, value=0)
                    new_game_away_score = st.number_input("Away Score", min_value=0, value=0)
                
                if st.form_submit_button("Add Game"):
                    # Validate required fields
                    if not new_game_home_team or not new_game_away_team:
                        st.error("Both Home Team and Away Team are required.")
                    elif new_game_home_team == new_game_away_team:
                        st.error("Home Team and Away Team must be different.")
                    else:
                        try:
                            create_data = {
                                "date_played": new_game_date.isoformat(),
                                "start_time": new_game_time.strftime('%H:%M:%S'),
                                "location": new_game_location if new_game_location else None,
                                "league_played": new_game_league,
                                "home_team_id": int(new_game_home_team),
                                "away_team_id": int(new_game_away_team),
                                "home_score": int(new_game_home_score) if new_game_home_score else None,
                                "away_score": int(new_game_away_score) if new_game_away_score else None
                            }
                            
                            create_response = requests.post(f"{API_BASE}/games", json=create_data)
                            if create_response.status_code == 201:
                                st.success("Game created successfully!")
                                # Form will auto-rerun, no need to call st.rerun()
                            else:
                                try:
                                    error_msg = create_response.json().get('error', f'HTTP {create_response.status_code}')
                                except:
                                    error_msg = f'HTTP {create_response.status_code}: {create_response.text[:200]}'
                                st.error(f"Error: {error_msg}")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
            if games:
                st.divider()
                st.subheader("Assign Stat Keepers to Games")
                assign_game_options = {f"Game {g['game_id']} - {g.get('home_team', 'TBD')} vs {g.get('away_team', 'TBD')} ({g.get('date_played', 'N/A')})": g['game_id'] for g in games}
                selected_assign_game_display = st.selectbox("Select Game", options=list(assign_game_options.keys()), key="assign_keeper_game_select")
                selected_assign_game_id = assign_game_options[selected_assign_game_display]
                try:
                    assigned_keepers_response = requests.get(f"{API_BASE}/games/{selected_assign_game_id}/stat-keepers")
                    assigned_keepers = assigned_keepers_response.json() if assigned_keepers_response.status_code == 200 else []
                except:
                    assigned_keepers = []
                try:
                    all_keepers_response = requests.get(f"{API_BASE}/stat-keepers")
                    all_keepers = all_keepers_response.json() if all_keepers_response.status_code == 200 else []
                except:
                    all_keepers = []
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Currently Assigned Stat Keepers:**")
                    if assigned_keepers:
                        for keeper in assigned_keepers:
                            col_display, col_remove = st.columns([3, 1])
                            with col_display:
                                st.write(f"- {keeper['first_name']} {keeper['last_name']} ({keeper['email']})")
                            with col_remove:
                                if st.button("Remove", key=f"remove_keeper_{selected_assign_game_id}_{keeper['keeper_id']}"):
                                    try:
                                        remove_response = requests.delete(
                                            f"{API_BASE}/games/{selected_assign_game_id}/stat-keepers",
                                            json={"keeper_id": keeper['keeper_id']}
                                        )
                                        if remove_response.status_code == 200:
                                            st.success("Stat keeper removed!")
                                            st.rerun()
                                        else:
                                            st.error(f"Error: {remove_response.json().get('error', 'Unknown error')}")
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                    else:
                        st.info("No stat keepers assigned to this game.")
                
                with col2:
                    st.write("**Assign New Stat Keeper:**")
                    if all_keepers:
                        assigned_keeper_ids = {k['keeper_id'] for k in assigned_keepers}
                        available_keepers = [k for k in all_keepers if k['keeper_id'] not in assigned_keeper_ids]
                        
                        if available_keepers:
                            keeper_options = {f"{k['first_name']} {k['last_name']} ({k['email']})": k['keeper_id'] for k in available_keepers}
                            selected_keeper_display = st.selectbox("Select Stat Keeper", options=list(keeper_options.keys()), key=f"assign_keeper_select_{selected_assign_game_id}")
                            selected_keeper_id = keeper_options[selected_keeper_display]
                            
                            if st.button("Assign Stat Keeper", key=f"assign_keeper_button_{selected_assign_game_id}"):
                                try:
                                    assign_response = requests.post(
                                        f"{API_BASE}/games/{selected_assign_game_id}/stat-keepers",
                                        json={"keeper_id": selected_keeper_id}
                                    )
                                    if assign_response.status_code == 201:
                                        st.success("Stat keeper assigned successfully!")
                                        st.rerun()
                                    else:
                                        st.error(f"Error: {assign_response.json().get('error', 'Unknown error')}")
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                        else:
                            st.info("All stat keepers are already assigned to this game.")
                    else:
                        st.warning("No stat keepers available.")
            
            # Delete game section (only show if there are games to delete)
            if games:
                st.divider()
                st.subheader("Delete Game")
                delete_game_options = {f"Game {g['game_id']} - {g.get('home_team', 'TBD')} vs {g.get('away_team', 'TBD')} ({g.get('date_played', 'N/A')})": g['game_id'] for g in games}
                selected_delete_game_display = st.selectbox("Select Game to Delete", options=list(delete_game_options.keys()), key="delete_game_select")
                selected_delete_game_id = delete_game_options[selected_delete_game_display]
                
                if st.button("🗑️ Delete Game", key="delete_game_button", type="secondary"):
                    try:
                        delete_response = requests.delete(f"{API_BASE}/games/{selected_delete_game_id}")
                        if delete_response.status_code == 200:
                            st.success("Game deleted successfully!")
                            st.rerun()  # Need explicit rerun for button clicks (not forms)
                        else:
                            try:
                                error_msg = delete_response.json().get('error', f'HTTP {delete_response.status_code}')
                            except:
                                error_msg = f'HTTP {delete_response.status_code}: {delete_response.text[:200]}'
                            st.error(f"Error: {error_msg}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        else:
            st.error(f"Error loading games: {games_response.json().get('error', 'Unknown error')}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

# ==================== STAT KEEPERS TAB ====================
with tab6:
    st.subheader("Stat Keepers Management")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("View and manage all stat keepers in the system.")
    with col2:
        if st.button("🔄 Refresh", key="refresh_stat_keepers"):
            st.rerun()
    
    try:
        search_filter = st.text_input("Search by Name or Email", key="stat_keeper_search_filter")
        keeper_params = {}
        if search_filter:
            keeper_params["search"] = search_filter
        keepers_response = requests.get(f"{API_BASE}/stat-keepers", params=keeper_params)
        if keepers_response.status_code == 200:
            stat_keepers = keepers_response.json()
            
            if stat_keepers:
                filtered_keepers = stat_keepers
                
                if filtered_keepers:
                    df = pd.DataFrame(filtered_keepers)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    st.divider()
                    st.subheader("Edit Stat Keeper")
                    edit_search = st.text_input("Search Stat Keeper to Edit (by name, email, or ID)", key="edit_keeper_search")
                    edit_keeper_params = {}
                    if edit_search:
                        edit_keeper_params["search"] = edit_search
                    
                    edit_keepers_response = requests.get(f"{API_BASE}/stat-keepers", params=edit_keeper_params)
                    edit_filtered_keepers = []
                    if edit_keepers_response.status_code == 200:
                        edit_filtered_keepers = edit_keepers_response.json()
                        if edit_search and edit_search.isdigit():
                            all_keepers_response = requests.get(f"{API_BASE}/stat-keepers")
                            if all_keepers_response.status_code == 200:
                                all_keepers = all_keepers_response.json()
                                matching_id = [k for k in all_keepers if k.get('keeper_id') == int(edit_search)]
                                for k in matching_id:
                                    if k not in edit_filtered_keepers:
                                        edit_filtered_keepers.append(k)
                    
                    if edit_filtered_keepers and edit_search:
                        keeper_options = {f"{k['first_name']} {k['last_name']} ({k['email']}) (ID: {k['keeper_id']})": k['keeper_id'] for k in edit_filtered_keepers}
                        selected_keeper_display = st.selectbox("Select from results", options=list(keeper_options.keys()), key="edit_keeper_select")
                        selected_keeper_id = keeper_options[selected_keeper_display]
                        selected_keeper = next((k for k in edit_filtered_keepers if k['keeper_id'] == selected_keeper_id), None)
                    elif not edit_search:
                        st.info("Enter a search term above to find a stat keeper to edit.")
                        selected_keeper = None
                    else:
                        st.warning("No stat keepers found matching your search.")
                        selected_keeper = None
                    
                    if selected_keeper:
                        with st.form(f"edit_keeper_{selected_keeper_id}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                new_first_name = st.text_input("First Name", value=selected_keeper.get('first_name', ''))
                                new_last_name = st.text_input("Last Name", value=selected_keeper.get('last_name', ''))
                            with col2:
                                new_email = st.text_input("Email", value=selected_keeper.get('email', ''))
                                new_total_games = st.number_input("Total Games Tracked", min_value=0, value=selected_keeper.get('total_games_tracked', 0))
                            
                            if st.form_submit_button("Update Stat Keeper"):
                                update_key = f"updating_keeper_{selected_keeper_id}"
                                if update_key in st.session_state:
                                    st.warning("Update already in progress. Please wait...")
                                    st.stop()
                                
                                st.session_state[update_key] = True
                                try:
                                    update_data = {
                                        "first_name": new_first_name,
                                        "last_name": new_last_name,
                                        "email": new_email,
                                        "total_games_tracked": int(new_total_games)
                                    }
                                    
                                    update_response = requests.put(f"{API_BASE}/stat-keepers/{selected_keeper_id}", json=update_data)
                                    
                                    if update_key in st.session_state:
                                        del st.session_state[update_key]
                                    
                                    if update_response.status_code == 200:
                                        st.success("Stat keeper updated successfully!")
                                    else:
                                        try:
                                            error_msg = update_response.json().get('error', f'HTTP {update_response.status_code}')
                                        except:
                                            error_msg = f'HTTP {update_response.status_code}: {update_response.text[:200]}'
                                        st.error(f"Error: {error_msg}")
                                except Exception as e:
                                    if update_key in st.session_state:
                                        del st.session_state[update_key]
                                    st.error(f"Error: {str(e)}")
                    st.divider()
                    st.subheader("Add New Stat Keeper")
                    with st.form("add_keeper"):
                        col1, col2 = st.columns(2)
                        with col1:
                            new_keeper_first = st.text_input("First Name *", key="new_keeper_first")
                            new_keeper_last = st.text_input("Last Name *", key="new_keeper_last")
                        with col2:
                            new_keeper_email = st.text_input("Email *", key="new_keeper_email")
                            new_keeper_games = st.number_input("Total Games Tracked", min_value=0, value=0, key="new_keeper_games")
                        
                        if st.form_submit_button("Add Stat Keeper"):
                            if new_keeper_first and new_keeper_last and new_keeper_email:
                                try:
                                    create_data = {
                                        "first_name": new_keeper_first,
                                        "last_name": new_keeper_last,
                                        "email": new_keeper_email,
                                        "total_games_tracked": int(new_keeper_games)
                                    }
                                    
                                    create_response = requests.post(f"{API_BASE}/stat-keepers", json=create_data)
                                    if create_response.status_code == 201:
                                        st.success("Stat keeper created successfully!")
                                    else:
                                        try:
                                            error_msg = create_response.json().get('error', f'HTTP {create_response.status_code}')
                                        except:
                                            error_msg = f'HTTP {create_response.status_code}: {create_response.text[:200]}'
                                        st.error(f"Error: {error_msg}")
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                            else:
                                st.error("First name, last name, and email are required")
                    st.divider()
                    st.subheader("Delete Stat Keeper")
                    delete_search = st.text_input("Search Stat Keeper to Delete (by name, email, or ID)", key="delete_keeper_search")
                    
                    delete_keeper_params = {}
                    if delete_search:
                        delete_keeper_params["search"] = delete_search
                    
                    delete_keepers_response = requests.get(f"{API_BASE}/stat-keepers", params=delete_keeper_params)
                    delete_filtered_keepers = []
                    if delete_keepers_response.status_code == 200:
                        delete_filtered_keepers = delete_keepers_response.json()
                        if delete_search and delete_search.isdigit():
                            all_keepers_response = requests.get(f"{API_BASE}/stat-keepers")
                            if all_keepers_response.status_code == 200:
                                all_keepers = all_keepers_response.json()
                                matching_id = [k for k in all_keepers if k.get('keeper_id') == int(delete_search)]
                                for k in matching_id:
                                    if k not in delete_filtered_keepers:
                                        delete_filtered_keepers.append(k)
                    
                    if delete_filtered_keepers and delete_search:
                        delete_keeper_options = {f"{k['first_name']} {k['last_name']} ({k['email']}) (ID: {k['keeper_id']})": k['keeper_id'] for k in delete_filtered_keepers}
                        selected_delete_keeper_display = st.selectbox("Select from results", options=list(delete_keeper_options.keys()), key="delete_keeper_select")
                        selected_delete_keeper_id = delete_keeper_options[selected_delete_keeper_display]
                        
                        if st.button("🗑️ Delete Stat Keeper", key="delete_keeper_button", type="secondary"):
                            try:
                                delete_response = requests.delete(f"{API_BASE}/stat-keepers/{selected_delete_keeper_id}")
                                if delete_response.status_code == 200:
                                    st.success("Stat keeper deleted successfully!")
                                    st.rerun()
                                else:
                                    try:
                                        error_msg = delete_response.json().get('error', f'HTTP {delete_response.status_code}')
                                    except:
                                        error_msg = f'HTTP {delete_response.status_code}: {delete_response.text[:200]}'
                                    st.error(f"Error: {error_msg}")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                    elif not delete_search:
                        st.info("Enter a search term above to find a stat keeper to delete.")
                    else:
                        st.warning("No stat keepers found matching your search.")
                    
                    st.divider()
                    st.subheader("Assign Games to Stat Keeper")
                    assign_keeper_options = {f"{k['first_name']} {k['last_name']} ({k['email']}) (ID: {k['keeper_id']})": k['keeper_id'] for k in filtered_keepers}
                    selected_assign_keeper_display = st.selectbox("Select Stat Keeper", options=list(assign_keeper_options.keys()), key="assign_game_keeper_select")
                    selected_assign_keeper_id = assign_keeper_options[selected_assign_keeper_display]
                    
                    try:
                        assigned_games_response = requests.get(f"{API_BASE}/stat-keepers/{selected_assign_keeper_id}/games")
                        assigned_games = assigned_games_response.json() if assigned_games_response.status_code == 200 else []
                    except:
                        assigned_games = []
                    
                    try:
                        games_response = requests.get(f"{API_BASE}/games")
                        all_games = games_response.json() if games_response.status_code == 200 else []
                    except:
                        all_games = []
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Currently Assigned Games:**")
                        if assigned_games:
                            for idx, game in enumerate(assigned_games):
                                col_display, col_remove = st.columns([3, 1])
                                with col_display:
                                    game_label = f"{game.get('date_played', 'N/A')} - {game.get('home_team', 'TBD')} vs {game.get('away_team', 'TBD')}"
                                    st.write(f"- {game_label}")
                                with col_remove:
                                    if st.button("Remove", key=f"remove_game_{selected_assign_keeper_id}_{game['game_id']}_{idx}"):
                                        try:
                                            remove_response = requests.delete(
                                                f"{API_BASE}/games/{game['game_id']}/stat-keepers",
                                                json={"keeper_id": selected_assign_keeper_id}
                                            )
                                            if remove_response.status_code == 200:
                                                st.success("Game removed!")
                                                st.rerun()
                                            else:
                                                st.error(f"Error: {remove_response.json().get('error', 'Unknown error')}")
                                        except Exception as e:
                                            st.error(f"Error: {str(e)}")
                        else:
                            st.info("No games assigned to this stat keeper.")
                    
                    with col2:
                        st.write("**Assign New Game:**")
                        if all_games:
                            assigned_game_ids = {g['game_id'] for g in assigned_games}
                            available_games = [g for g in all_games if g.get('game_id') not in assigned_game_ids]
                            
                            if available_games:
                                game_options = {f"Game {g['game_id']} - {g.get('home_team', 'TBD')} vs {g.get('away_team', 'TBD')} ({g.get('date_played', 'N/A')})": g['game_id'] for g in available_games}
                                selected_game_display = st.selectbox("Select Game", options=list(game_options.keys()), key=f"assign_game_select_{selected_assign_keeper_id}")
                                selected_game_id = game_options[selected_game_display]
                                
                                if st.button("Assign Game", key=f"assign_game_button_{selected_assign_keeper_id}"):
                                    try:
                                        assign_response = requests.post(
                                            f"{API_BASE}/games/{selected_game_id}/stat-keepers",
                                            json={"keeper_id": selected_assign_keeper_id}
                                        )
                                        if assign_response.status_code == 201:
                                            st.success("Game assigned successfully!")
                                            st.rerun()
                                        else:
                                            st.error(f"Error: {assign_response.json().get('error', 'Unknown error')}")
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                            else:
                                st.info("All games are already assigned to this stat keeper.")
                        else:
                            st.warning("No games available.")
                else:
                    st.info("No stat keepers match the search criteria.")
            else:
                st.info("No stat keepers found.")
        else:
            st.error(f"Error loading stat keepers: {keepers_response.json().get('error', 'Unknown error')}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

