import streamlit as st
import requests
import time as time_module
from datetime import datetime, date, time
from modules.nav import SideBarLinks

SideBarLinks()

st.set_page_config(layout='wide')

st.title("Game Scheduling & Management")
st.write("Schedule new games and manage your team's upcoming and past games.")

TEAM_ID = st.session_state.get('team_id', 1)
API_BASE = "http://web-api:4000/team-captain"

try:
    upcoming_response = requests.get(f"{API_BASE}/teams/{TEAM_ID}/games?upcoming_only=true")
    past_response = requests.get(f"{API_BASE}/teams/{TEAM_ID}/games?upcoming_only=false")
    
    if upcoming_response.status_code == 200:
        upcoming_games = upcoming_response.json()
    else:
        try:
            error_data = upcoming_response.json()
            st.error(f"Upcoming games API error: {error_data.get('error', 'Unknown error')}")
        except:
            st.error(f"Upcoming games API returned status {upcoming_response.status_code}: {upcoming_response.text[:200]}")
        upcoming_games = []
    
    if past_response.status_code == 200:
        past_games = past_response.json()
    else:
        try:
            error_data = past_response.json()
            st.error(f"Past games API error: {error_data.get('error', 'Unknown error')}")
        except:
            st.error(f"Past games API returned status {past_response.status_code}: {past_response.text[:200]}")
        past_games = []
except Exception as e:
    st.error(f"Error fetching games: {str(e)}")
    upcoming_games = []
    past_games = []

tab1, tab2, tab3, tab4 = st.tabs(["Upcoming Games", "Past Games", "Schedule New Game", "Send Reminders"])

with tab1:
    st.subheader("Upcoming Games")
    
    if upcoming_games:
        for idx, game in enumerate(upcoming_games):
            with st.container():
                col1, col2 = st.columns([3, 2])
                
                with col1:
                    st.write(f"**{game['home_team']}** vs **{game['away_team']}**")
                    st.write(f"Date: {game['date_played']} | Time: {game['start_time']}")
                    st.write(f"Location: {game['location']}")
                
                with col2:
                    col_edit, col_delete = st.columns(2)
                    with col_edit:
                        if st.button(f"Edit", key=f"edit_upcoming_{game['game_id']}_{idx}"):
                            st.session_state[f"editing_game_{game['game_id']}"] = True
                    with col_delete:
                        if st.button(f"Delete", key=f"delete_upcoming_{game['game_id']}_{idx}", type="secondary"):
                            st.session_state[f"confirming_delete_{game['game_id']}"] = True
                
                if st.session_state.get(f"confirming_delete_{game['game_id']}", False):
                    st.warning(f"Are you sure you want to delete the game: {game['home_team']} vs {game['away_team']} on {game['date_played']}?")
                    col_confirm, col_cancel_del = st.columns(2)
                    with col_confirm:
                        if st.button(f"Confirm Delete", key=f"confirm_delete_{game['game_id']}_{idx}", type="primary"):
                            try:
                                response = requests.delete(f"{API_BASE}/games/{game['game_id']}")
                                if response.status_code == 200:
                                    st.success("Game deleted successfully!")
                                    st.session_state[f"confirming_delete_{game['game_id']}"] = False
                                    st.rerun()
                                else:
                                    try:
                                        error_msg = response.json().get('error', f'HTTP {response.status_code}: {response.text[:200]}')
                                    except:
                                        error_msg = f'HTTP {response.status_code}: {response.text[:200]}'
                                    st.error(f"Error deleting game: {error_msg}")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                    with col_cancel_del:
                        if st.button(f"Cancel", key=f"cancel_delete_{game['game_id']}_{idx}"):
                            st.session_state[f"confirming_delete_{game['game_id']}"] = False
                            st.rerun()
                
                if st.session_state.get(f"editing_game_{game['game_id']}", False):
                    st.write("**Stat Keepers:**")
                    try:
                        assigned_response = requests.get(f"{API_BASE}/games/{game['game_id']}/stat-keepers")
                        assigned_keepers = assigned_response.json() if assigned_response.status_code == 200 else []
                    except:
                        assigned_keepers = []
                    try:
                        all_keepers_response = requests.get(f"{API_BASE}/stat-keepers")
                        all_keepers = all_keepers_response.json() if all_keepers_response.status_code == 200 else []
                    except:
                        all_keepers = []
                    
                    if assigned_keepers:
                        st.write("**Currently Assigned:**")
                        for keeper in assigned_keepers:
                            col_display, col_remove = st.columns([3, 1])
                            with col_display:
                                st.write(f"- {keeper['first_name']} {keeper['last_name']} ({keeper['email']})")
                            with col_remove:
                                if st.button("Remove", key=f"remove_keeper_edit_{game['game_id']}_{keeper['keeper_id']}_{idx}"):
                                    try:
                                        remove_response = requests.delete(
                                            f"{API_BASE}/games/{game['game_id']}/stat-keepers",
                                            json={"keeper_id": keeper['keeper_id']}
                                        )
                                        if remove_response.status_code == 200:
                                            st.success("Stat keeper removed!")
                                            st.rerun()
                                        else:
                                            st.error(f"Error: {remove_response.json().get('error', 'Unknown error')}")
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                    
                    if all_keepers:
                        assigned_keeper_ids = {k['keeper_id'] for k in assigned_keepers}
                        available_keepers = [k for k in all_keepers if k['keeper_id'] not in assigned_keeper_ids]
                        
                        if available_keepers:
                            st.write("**Assign New Stat Keeper:**")
                            col_assign, col_assign_btn = st.columns([4, 1])
                            with col_assign:
                                keeper_options = {None: "No Stat Keeper"} | {k['keeper_id']: f"{k['first_name']} {k['last_name']} ({k['email']})" for k in available_keepers}
                                selected_keeper_display = st.selectbox("Stat Keeper", options=list(keeper_options.keys()), format_func=lambda x: keeper_options.get(x, "No Stat Keeper"), key=f"assign_keeper_edit_{game['game_id']}_{idx}")
                            with col_assign_btn:
                                st.markdown('<div style="height: 1.5rem;"></div>', unsafe_allow_html=True)
                                if selected_keeper_display and st.button("Assign", key=f"assign_keeper_btn_{game['game_id']}_{idx}", use_container_width=True):
                                    try:
                                        assign_response = requests.post(
                                            f"{API_BASE}/games/{game['game_id']}/stat-keepers",
                                            json={"keeper_id": selected_keeper_display}
                                        )
                                        if assign_response.status_code == 201:
                                            st.success("Stat keeper assigned!")
                                            st.rerun()
                                        else:
                                            st.error(f"Error: {assign_response.json().get('error', 'Unknown error')}")
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                    
                    st.divider()
                    with st.form(f"edit_form_upcoming_{game['game_id']}_{idx}"):
                        new_date = st.date_input("Date", value=datetime.strptime(game['date_played'], '%Y-%m-%d').date(), key=f"date_upcoming_{game['game_id']}_{idx}")
                        new_time = st.time_input("Time", value=datetime.strptime(str(game['start_time']), '%H:%M:%S').time(), key=f"time_upcoming_{game['game_id']}_{idx}")
                        new_location = st.text_input("Location", value=game['location'], key=f"loc_upcoming_{game['game_id']}_{idx}")
                        
                        col_submit, col_cancel = st.columns(2)
                        with col_submit:
                            if st.form_submit_button("Update Game"):
                                try:
                                    update_data = {
                                        "date_played": str(new_date),
                                        "start_time": str(new_time),
                                        "location": new_location
                                    }
                                    response = requests.put(f"{API_BASE}/games/{game['game_id']}", json=update_data)
                                    if response.status_code == 200:
                                        st.success("Game updated successfully!")
                                        st.session_state[f"editing_game_{game['game_id']}"] = False
                                        st.rerun()
                                    else:
                                        st.error(f"Error updating game: {response.json().get('error', 'Unknown error')}")
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                        
                        with col_cancel:
                            if st.form_submit_button("Cancel"):
                                st.session_state[f"editing_game_{game['game_id']}"] = False
                                st.rerun()
                
                st.divider()
    else:
        st.info("No upcoming games scheduled.")

with tab2:
    st.subheader("Past Games")
    
    if past_games:
        for idx, game in enumerate(past_games):
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.write(f"**{game['home_team']}** {game['home_score']} - {game['away_score']} **{game['away_team']}**")
                    st.write(f"Date: {game['date_played']} | Location: {game['location']}")
                
                with col2:
                    is_viewing = st.session_state.get(f"viewing_stats_{game['game_id']}", False)
                    button_text = "Collapse Stats" if is_viewing else "View Stats"
                    if st.button(button_text, key=f"stats_past_{game['game_id']}_{idx}"):
                        st.session_state[f"viewing_stats_{game['game_id']}"] = not is_viewing
                        st.rerun()
                
                if st.session_state.get(f"viewing_stats_{game['game_id']}", False):
                    try:
                        stats_response = requests.get(f"{API_BASE}/games/{game['game_id']}/teams/{TEAM_ID}/stat-events")
                        if stats_response.status_code == 200:
                            stat_events = stats_response.json()
                            if stat_events:
                                st.write("**Stat Events:**")
                                for event in stat_events:
                                    st.write(f"- {event['first_name']} {event['last_name']}: {event['description']} ({event['time_entered']})")
                            else:
                                st.info("No stat events recorded for this game.")
                    except Exception as e:
                        st.error(f"Error fetching stats: {str(e)}")
                
                st.divider()
    else:
        st.info("No past games recorded.")

with tab3:
    st.subheader("Schedule New Game")
    st.write("Create a new game for your team.")
    
    with st.form("schedule_game_form"):
        try:
            # Fetch leagues from API (filtered by team using SQL)
            leagues_response = requests.get(f"{API_BASE}/leagues?team_id={TEAM_ID}")
            if leagues_response.status_code == 200:
                leagues = leagues_response.json()
            else:
                st.error(f"Error fetching leagues: {leagues_response.status_code}")
                leagues = []
            
            if not leagues:
                st.warning("No leagues available. Please contact system admin.")
                st.stop()
            
            selected_league = st.selectbox("League", options=leagues, format_func=lambda x: f"{x['name']} ({x.get('semester', 'N/A')} {x.get('year', 'N/A')})", key="schedule_league_select")
            
            game_date = st.date_input("Game Date", min_value=date.today())
            game_time = st.time_input("Start Time")
            location = st.text_input("Location")
            
            # Fetch teams in the selected league (filtered by SQL to exclude current team)
            opponent_teams = []
            captain_team_in_league = True  # Assume true since leagues are now pre-filtered
            if selected_league and 'league_id' in selected_league:
                try:
                    league_id = selected_league['league_id']
                    # Use SQL filtering to exclude current team and get teams in league
                    teams_response = requests.get(f"{API_BASE}/leagues/{league_id}/teams?exclude_team_id={TEAM_ID}")
                    if teams_response.status_code == 200:
                        opponent_teams = teams_response.json()
                        
                        # Verify captain's team is in this league (safety check, should always pass since leagues are pre-filtered)
                        captain_team_check = requests.get(f"{API_BASE}/leagues/{league_id}/teams")
                        if captain_team_check.status_code == 200:
                            all_teams_in_league = captain_team_check.json()
                            captain_team_in_league = any(t.get("team_id") == TEAM_ID for t in all_teams_in_league)
                            
                            if not captain_team_in_league:
                                st.error(f"Your team (ID: {TEAM_ID}) is not in the selected league '{selected_league.get('name', 'this league')}'. Please select a league that your team belongs to.")
                            elif not opponent_teams:
                                if len(all_teams_in_league) == 1:
                                    st.info(f"Only your team is in this league. You need at least one opponent team to schedule a game.")
                                else:
                                    st.warning(f"No opponent teams available in {selected_league.get('name', 'this league')}.")
                        else:
                            st.warning(f"Could not verify if your team is in this league.")
                    elif teams_response.status_code == 404:
                        st.warning(f"League not found.")
                    else:
                        try:
                            error_data = teams_response.json()
                            st.warning(f"Error fetching teams: {error_data.get('error', f'HTTP {teams_response.status_code}')}")
                        except:
                            st.warning(f"Error fetching teams: HTTP {teams_response.status_code} - {teams_response.text[:200]}")
                except Exception as e:
                    st.error(f"Error fetching teams: {str(e)}")
            
            opponent = None
            is_home = None
            if opponent_teams:
                opponent = st.selectbox("Opponent", options=opponent_teams, format_func=lambda x: x["name"], key="schedule_opponent_select")
                is_home = st.radio("Home or Away?", ["Home", "Away"], key="schedule_home_away")
            elif selected_league and 'league_id' in selected_league:
                st.warning(f"No opponent teams available in {selected_league.get('name', 'this league')}.")
            
            st.divider()
            st.write("**Assign Stat Keeper (Optional):**")
            try:
                keepers_response = requests.get(f"{API_BASE}/stat-keepers")
                all_keepers = keepers_response.json() if keepers_response.status_code == 200 else []
            except:
                all_keepers = []
            
            selected_keeper_id = None
            if all_keepers:
                keeper_options = {None: "No Stat Keeper"} | {k['keeper_id']: f"{k['first_name']} {k['last_name']} ({k['email']})" for k in all_keepers}
                selected_keeper_display = st.selectbox("Stat Keeper", options=list(keeper_options.keys()), format_func=lambda x: keeper_options.get(x, "No Stat Keeper"))
                selected_keeper_id = selected_keeper_display
            else:
                st.info("No stat keepers available.")
            
            if st.form_submit_button("Schedule Game", type="primary"):
                if not selected_league:
                    st.error("Please select a league.")
                elif not captain_team_in_league:
                    st.error("Your team is not in the selected league. Please select a league that your team belongs to.")
                elif not opponent_teams:
                    st.error("No opponent teams available in the selected league.")
                elif not opponent:
                    st.error("Please select an opponent team.")
                elif not location:
                    st.error("Please enter a location.")
                elif is_home is None:
                    st.error("Please select Home or Away.")
                else:
                    try:
                        formatted_date = game_date.strftime('%Y-%m-%d')
                        formatted_time = game_time.strftime('%H:%M:%S')
                        
                        game_data = {
                            "league_played": selected_league["league_id"],
                            "date_played": formatted_date,
                            "start_time": formatted_time,
                            "location": location,
                            "home_team_id": TEAM_ID if is_home == "Home" else opponent["team_id"],
                            "away_team_id": opponent["team_id"] if is_home == "Home" else TEAM_ID
                        }
                        
                        response = requests.post(f"{API_BASE}/games", json=game_data)
                        if response.status_code == 201:
                            game_result = response.json()
                            new_game_id = game_result.get("game_id")
                            if selected_keeper_id and new_game_id:
                                try:
                                    keeper_response = requests.post(
                                        f"{API_BASE}/games/{new_game_id}/stat-keepers",
                                        json={"keeper_id": selected_keeper_id}
                                    )
                                    if keeper_response.status_code == 201:
                                        st.success("Game scheduled and stat keeper assigned successfully!")
                                    else:
                                        st.success("Game scheduled successfully!")
                                        st.warning(f"Stat keeper assignment failed: {keeper_response.json().get('error', 'Unknown error')}")
                                except Exception as e:
                                    st.success("Game scheduled successfully!")
                                    st.warning(f"Stat keeper assignment failed: {str(e)}")
                            else:
                                st.success("Game scheduled successfully!")
                            time_module.sleep(3)  # Show success message for 3 seconds
                            st.rerun()
                        else:
                            try:
                                error_msg = response.json().get('error', f'HTTP {response.status_code}: {response.text[:200]}')
                            except:
                                error_msg = f'HTTP {response.status_code}: {response.text[:200]}'
                            st.error(f"Error scheduling game: {error_msg}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        except Exception as e:
            st.error(f"Error loading form data: {str(e)}")

with tab4:
    st.subheader("Send Reminders to Teammates")
    st.write("Send reminders to your teammates to log their stats after games. This demonstrates user story Miles-4: sending reminders to teammates to record their stats so that no data is missing.")
    
    # Get team info for dropdown - fetch from API to ensure valid team IDs
    try:
        # Try to get team info from the summary endpoint to validate team exists
        team_summary_response = requests.get(f"{API_BASE}/teams/{TEAM_ID}/summary")
        if team_summary_response.status_code == 200:
            team_summary = team_summary_response.json()
            teams = [{"team_id": TEAM_ID, "name": team_summary.get("name", "My Team")}]
        else:
            # Fallback: try to get teams from system admin API
            try:
                admin_api_base = "http://web-api:4000/system-admin"
                admin_teams_response = requests.get(f"{admin_api_base}/teams")
                if admin_teams_response.status_code == 200:
                    admin_teams = admin_teams_response.json()
                    teams = [{"team_id": t["team_id"], "name": t["name"]} for t in admin_teams[:5]]  # Limit to first 5
                else:
                    teams = [{"team_id": TEAM_ID, "name": "Team " + str(TEAM_ID)}]
            except:
                teams = [{"team_id": TEAM_ID, "name": "Team " + str(TEAM_ID)}]
        
        selected_team = st.selectbox(
            "Select Team",
            options=teams,
            format_func=lambda x: x["name"],
            key="reminder_team_select"
        )
        selected_team_id = selected_team["team_id"] if selected_team else TEAM_ID
    except Exception as e:
        st.warning(f"Could not fetch team info: {str(e)}. Using default team ID {TEAM_ID}.")
        selected_team_id = TEAM_ID
    
    try:
        upcoming_response = requests.get(f"{API_BASE}/teams/{selected_team_id}/games?upcoming_only=true")
        if upcoming_response.status_code == 200:
            upcoming_games = upcoming_response.json()
        else:
            upcoming_games = []
    except Exception as e:
        st.error(f"Error fetching games: {str(e)}")
        upcoming_games = []
    
    with st.form("reminder_form"):
        reminder_message = st.text_area(
            "Reminder Message",
            value="Don't forget to log your stats from today's game!",
            height=100,
            key="reminder_message"
        )
        
        if upcoming_games:
            game_options = [None] + [{"game_id": g['game_id'], "label": f"{g['date_played']} - {g['home_team']} vs {g['away_team']}"} for g in upcoming_games]
            selected_game_option = st.selectbox(
                "Link to Game (Optional)",
                options=game_options,
                format_func=lambda x: x["label"] if x else "No specific game"
            )
            game_id_for_reminder = selected_game_option["game_id"] if selected_game_option else None
        else:
            game_id_for_reminder = None
        
        if st.form_submit_button("Send Reminder", type="primary"):
            try:
                reminder_data = {
                    "message": reminder_message,
                    "team_id": selected_team_id
                }
                if game_id_for_reminder:
                    reminder_data["game_id"] = game_id_for_reminder
                
                response = requests.post(f"{API_BASE}/reminders", json=reminder_data)
                if response.status_code == 201:
                    st.success("✅ Reminder sent successfully! The team will receive this notification to prompt stat entry via our POST /reminders route.")
                    st.rerun()
                else:
                    try:
                        error_data = response.json()
                        st.error(f"Error sending reminder: {error_data.get('error', 'Unknown error')}")
                    except:
                        st.error(f"Error sending reminder: HTTP {response.status_code}")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    st.divider()
    st.write("**Recent Reminders:**")
    try:
        reminders_response = requests.get(f"{API_BASE}/teams/{selected_team_id}/reminders")
        if reminders_response.status_code == 200:
            reminders = reminders_response.json()
            if reminders:
                recent_count = min(5, len(reminders))
                for reminder in reminders[:recent_count]:
                    message = reminder.get('message', '').replace('>', '\\>').replace('\n', ' ')
                    time_sent = reminder.get('time_sent', 'Unknown time')
                    game_date = reminder.get('date_played')
                    home_team = reminder.get('home_team')
                    away_team = reminder.get('away_team')
                    home_score = reminder.get('home_score')
                    away_score = reminder.get('away_score')
                    
                    reminder_text = f"- {message} ({time_sent})"
                    if game_date and home_team and away_team:
                        if home_score is not None and away_score is not None:
                            reminder_text += f" - Game: {home_team} vs {away_team} ({home_score}-{away_score}) on {game_date}"
                        else:
                            reminder_text += f" - Game: {home_team} vs {away_team} on {game_date}"
                    elif game_date:
                        reminder_text += f" - Game: {game_date}"
                    st.markdown(reminder_text)
                
                if len(reminders) > 5:
                    with st.expander(f"View all reminders ({len(reminders)} total)"):
                        for reminder in reminders:
                            message = reminder.get('message', '').replace('>', '\\>').replace('\n', ' ')
                            time_sent = reminder.get('time_sent', 'Unknown time')
                            game_date = reminder.get('date_played')
                            home_team = reminder.get('home_team')
                            away_team = reminder.get('away_team')
                            home_score = reminder.get('home_score')
                            away_score = reminder.get('away_score')
                            
                            reminder_text = f"- {message} ({time_sent})"
                            if game_date and home_team and away_team:
                                if home_score is not None and away_score is not None:
                                    reminder_text += f" - Game: {home_team} vs {away_team} ({home_score}-{away_score}) on {game_date}"
                                else:
                                    reminder_text += f" - Game: {home_team} vs {away_team} on {game_date}"
                            elif game_date:
                                reminder_text += f" - Game: {game_date}"
                            st.markdown(reminder_text)
            else:
                st.info("No reminders sent yet.")
        else:
            try:
                error_data = reminders_response.json()
                st.error(f"Error loading reminders: {error_data.get('error', 'Unknown error')}")
            except:
                st.error(f"Error loading reminders: HTTP {reminders_response.status_code}")
    except Exception as e:
        st.error(f"Error loading reminders: {str(e)}")
