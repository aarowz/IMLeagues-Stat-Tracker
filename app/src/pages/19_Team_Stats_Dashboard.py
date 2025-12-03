import streamlit as st
import requests
import pandas as pd
from modules.nav import SideBarLinks

SideBarLinks()

st.set_page_config(layout='wide')

st.title("Team Stats Dashboard")
st.write("Review and edit your team's statistics and track performance over time.")

TEAM_ID = 1
API_BASE = "http://web-api:4000/team-captain"

try:
    performance_response = requests.get(f"{API_BASE}/teams/{TEAM_ID}/performance")
    performance_over_time_response = requests.get(f"{API_BASE}/teams/{TEAM_ID}/performance-over-time")
    
    if performance_response.status_code == 200:
        performance = performance_response.json()
    else:
        performance = None
    
    if performance_over_time_response.status_code == 200:
        performance_over_time = performance_over_time_response.json()
    else:
        performance_over_time = []
except Exception as e:
    st.error(f"Error fetching performance data: {str(e)}")
    performance = None
    performance_over_time = []

if performance:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Wins", performance.get("wins", 0))
    with col2:
        st.metric("Losses", performance.get("losses", 0))
    with col3:
        st.metric("Games Played", performance.get("games_played", 0))
    with col4:
        avg_points = performance.get("avg_points_scored", 0)
        if avg_points:
            st.metric("Avg Points Scored", f"{round(avg_points, 1)}")
        else:
            st.metric("Avg Points Scored", "0.0")

st.divider()

tab1, tab2 = st.tabs(["Performance Over Time", "Edit Game Stats"])

with tab1:
    st.subheader("Team Performance Over Time")
    
    if performance_over_time:
        df = pd.DataFrame(performance_over_time)
        df['date_played'] = pd.to_datetime(df['date_played'])
        df = df.sort_values('date_played')
        
        st.line_chart(df.set_index('date_played')['points_scored'], use_container_width=True)
        st.caption("Points Scored Per Game")
        
        col1, col2 = st.columns(2)
        
        with col1:
            results_df = pd.DataFrame({
                'Result': df['result'].value_counts().index,
                'Count': df['result'].value_counts().values
            })
            st.bar_chart(results_df.set_index('Result'), use_container_width=True)
            st.caption("Win/Loss Record")
        
        with col2:
            st.dataframe(df[['date_played', 'points_scored', 'points_allowed', 'result']], use_container_width=True)
    else:
        st.info("No performance data available yet.")

with tab2:
    st.subheader("Edit Game Statistics")
    st.write("Select a game to review and edit its statistics.")
    
    try:
        past_response = requests.get(f"{API_BASE}/teams/{TEAM_ID}/games?upcoming_only=false")
        if past_response.status_code == 200:
            past_games = past_response.json()
        else:
            past_games = []
    except Exception as e:
        st.error(f"Error fetching games: {str(e)}")
        past_games = []
    
    if past_games:
        selected_game = st.selectbox(
            "Select Game",
            options=past_games,
            format_func=lambda g: f"{g['date_played']} - {g['home_team']} vs {g['away_team']}"
        )
        
        if selected_game:
            game_id = selected_game['game_id']
            
            try:
                stats_response = requests.get(f"{API_BASE}/games/{game_id}/teams/{TEAM_ID}/stat-events")
                if stats_response.status_code == 200:
                    stat_events = stats_response.json()
                else:
                    stat_events = []
            except Exception as e:
                st.error(f"Error fetching stats: {str(e)}")
                stat_events = []
            
            if stat_events:
                st.write("**Current Stat Events:**")
                
                for event in stat_events:
                    with st.container():
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            st.write(f"{event['first_name']} {event['last_name']}: {event['description']}")
                            st.caption(f"Time: {event['time_entered']}")
                        
                        with col2:
                            if st.button("Edit", key=f"edit_stat_{event['event_id']}"):
                                st.session_state[f"editing_stat_{event['event_id']}"] = True
                        
                        with col3:
                            if st.button("Delete", key=f"delete_stat_{event['event_id']}"):
                                try:
                                    delete_response = requests.delete(f"{API_BASE}/stats/{event['event_id']}")
                                    if delete_response.status_code == 200:
                                        st.success("Stat event deleted!")
                                        st.rerun()
                                    else:
                                        st.error(f"Error: {delete_response.json().get('error', 'Unknown error')}")
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                        
                        if st.session_state.get(f"editing_stat_{event['event_id']}", False):
                            with st.form(f"edit_stat_form_{event['event_id']}"):
                                new_description = st.text_input("Stat Description", value=event['description'], key=f"desc_{event['event_id']}")
                                
                                col_submit, col_cancel = st.columns(2)
                                with col_submit:
                                    if st.form_submit_button("Update"):
                                        try:
                                            update_data = {"description": new_description}
                                            update_response = requests.put(f"{API_BASE}/stats/{event['event_id']}", json=update_data)
                                            if update_response.status_code == 200:
                                                st.success("Stat updated successfully!")
                                                st.session_state[f"editing_stat_{event['event_id']}"] = False
                                                st.rerun()
                                            else:
                                                st.error(f"Error: {update_response.json().get('error', 'Unknown error')}")
                                        except Exception as e:
                                            st.error(f"Error: {str(e)}")
                                
                                with col_cancel:
                                    if st.form_submit_button("Cancel"):
                                        st.session_state[f"editing_stat_{event['event_id']}"] = False
                                        st.rerun()
                        
                        st.divider()
            else:
                st.info("No stat events recorded for this game.")
    else:
        st.info("No past games available.")
