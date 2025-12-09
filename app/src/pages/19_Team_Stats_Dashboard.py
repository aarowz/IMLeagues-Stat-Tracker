import streamlit as st
import requests
import pandas as pd
from modules.nav import SideBarLinks

SideBarLinks()

st.set_page_config(layout='wide')

st.title("Team Stats Dashboard")
st.write("Review and edit your team's statistics and track performance over time.")

TEAM_ID = st.session_state.get('team_id', 1)
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

st.subheader("Team Performance Over Time")
st.write("Track your team's scoring trend across the season and compare performance to league averages.")

if performance_over_time:
        df = pd.DataFrame(performance_over_time)
        df['date_played'] = pd.to_datetime(df['date_played'])
        df = df.sort_values('date_played')
        
        # Top graph: Average points per game over time
        st.write("**Scoring Trend: Points Per Game Over Time**")
        st.line_chart(df.set_index('date_played')['points_scored'], use_container_width=True)
        st.caption("This line chart shows points per game over time, demonstrating user story Miles-3: seeing a dashboard that tracks team performance and improvement over time.")
        
        st.divider()
        
        # Bottom section: Win/Loss record and log of past results
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.write("**Win/Loss Record**")
            results_df = pd.DataFrame({
                'Result': df['result'].value_counts().index,
                'Count': df['result'].value_counts().values
            })
            st.bar_chart(results_df.set_index('Result'), use_container_width=True)
            st.caption("Team win/loss breakdown")
        
        with col2:
            st.write("**Log of All Past Results**")
            # Format the dataframe nicely
            display_df = df[['date_played', 'points_scored', 'points_allowed', 'result']].copy()
            display_df['date_played'] = display_df['date_played'].dt.strftime('%Y-%m-%d')
            display_df.columns = ['Date', 'Points Scored', 'Points Allowed', 'Result']
            st.dataframe(display_df, use_container_width=True, hide_index=True)
else:
    st.info("No performance data available yet.")
