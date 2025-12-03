import streamlit as st
import requests
from datetime import datetime, date, time
from modules.nav import SideBarLinks

SideBarLinks()

st.set_page_config(layout='wide')

st.title("Game Scheduling & Management")
st.write("Schedule new games and manage your team's upcoming and past games.")

TEAM_ID = 1
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
        for game in upcoming_games:
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.write(f"**{game['home_team']}** vs **{game['away_team']}**")
                    st.write(f"Date: {game['date_played']} | Time: {game['start_time']}")
                    st.write(f"Location: {game['location']}")
                
                with col2:
                    if st.button(f"Edit Game", key=f"edit_{game['game_id']}"):
                        st.session_state[f"editing_game_{game['game_id']}"] = True
                
                with col3:
                    if st.button(f"View Details", key=f"view_{game['game_id']}"):
                        st.session_state[f"viewing_game_{game['game_id']}"] = True
                
                if st.session_state.get(f"editing_game_{game['game_id']}", False):
                    with st.form(f"edit_form_{game['game_id']}"):
                        new_date = st.date_input("Date", value=datetime.strptime(game['date_played'], '%Y-%m-%d').date(), key=f"date_{game['game_id']}")
                        new_time = st.time_input("Time", value=datetime.strptime(str(game['start_time']), '%H:%M:%S').time(), key=f"time_{game['game_id']}")
                        new_location = st.text_input("Location", value=game['location'], key=f"loc_{game['game_id']}")
                        
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
        for game in past_games:
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.write(f"**{game['home_team']}** {game['home_score']} - {game['away_score']} **{game['away_team']}**")
                    st.write(f"Date: {game['date_played']} | Location: {game['location']}")
                
                with col2:
                    if st.button(f"View Stats", key=f"stats_{game['game_id']}"):
                        st.session_state[f"viewing_stats_{game['game_id']}"] = True
                
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
            leagues = [{"league_id": 1, "name": "Fall Basketball League"}]
            teams = [
                {"team_id": 1, "name": "Duncan's Dunkers"},
                {"team_id": 2, "name": "Thunder Bolts"},
                {"team_id": 3, "name": "Sky Hawks"},
                {"team_id": 4, "name": "Fire Dragons"}
            ]
            
            selected_league = st.selectbox("League", options=leagues, format_func=lambda x: x["name"])
            game_date = st.date_input("Game Date", min_value=date.today())
            game_time = st.time_input("Start Time")
            location = st.text_input("Location")
            
            opponent_teams = [t for t in teams if t["team_id"] != TEAM_ID]
            opponent = st.selectbox("Opponent", options=opponent_teams, format_func=lambda x: x["name"])
            is_home = st.radio("Home or Away?", ["Home", "Away"])
            
            if st.form_submit_button("Schedule Game", type="primary"):
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
                        st.success("Game scheduled successfully!")
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
    st.write("Send reminders to your teammates to log their stats after games.")
    
    try:
        upcoming_response = requests.get(f"{API_BASE}/teams/{TEAM_ID}/games?upcoming_only=true")
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
            value="Don't forget to log your stats for tonight's game!",
            height=100
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
                    "team_id": TEAM_ID
                }
                if game_id_for_reminder:
                    reminder_data["game_id"] = game_id_for_reminder
                
                response = requests.post(f"{API_BASE}/reminders", json=reminder_data)
                if response.status_code == 201:
                    st.success("Reminder sent successfully!")
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
        reminders_response = requests.get(f"{API_BASE}/teams/{TEAM_ID}/reminders")
        if reminders_response.status_code == 200:
            reminders = reminders_response.json()
            if reminders:
                for reminder in reminders[:5]:
                    message = reminder['message'].replace('>', '\\>').replace('\n', ' ')
                    time_sent = reminder['time_sent']
                    st.markdown(f"- {message} ({time_sent})")
            else:
                st.info("No reminders sent yet.")
        else:
            st.info("Could not load reminders.")
    except Exception as e:
        st.info("Could not load reminders.")
