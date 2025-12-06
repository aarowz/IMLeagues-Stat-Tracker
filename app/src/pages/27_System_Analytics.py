import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from modules.nav import SideBarLinks

SideBarLinks()
st.set_page_config(layout='wide')

st.title("📈 System Analytics & Configuration")
st.write("View system usage statistics, add new sports/leagues, and configure league rules.")

API_BASE = "http://web-api:4000/system-admin"

# Create tabs for different functionalities
tab1, tab2, tab3 = st.tabs(["📊 Analytics Dashboard", "➕ Add Sports/Leagues", "⚙️ League Rules"])

# ==================== ANALYTICS DASHBOARD TAB ====================
with tab1:
    st.subheader("System Usage Analytics")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("View comprehensive statistics about system usage, popular sports, and busiest days.")
    with col2:
        if st.button("🔄 Refresh", key="refresh_analytics"):
            st.rerun()
    
    try:
        # Fetch analytics dashboard data
        analytics_response = requests.get(f"{API_BASE}/analytics/dashboard")
        if analytics_response.status_code == 200:
            analytics_data = analytics_response.json()
            
            # Overall Statistics
            st.subheader("Overall Statistics")
            overall_stats = analytics_data.get('overall_statistics', {})
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Sports", overall_stats.get('total_sports', 0))
            with col2:
                st.metric("Total Leagues", overall_stats.get('total_leagues', 0))
            with col3:
                st.metric("Total Teams", overall_stats.get('total_teams', 0))
            with col4:
                st.metric("Total Players", overall_stats.get('total_players', 0))
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Games", overall_stats.get('total_games', 0))
            with col2:
                st.metric("Stat Keepers", overall_stats.get('total_stat_keepers', 0))
            with col3:
                st.metric("Stat Events", overall_stats.get('total_stat_events', 0))
            with col4:
                st.metric("", "")  # Empty for spacing
            
            st.divider()
            
            # Popular Sports
            st.subheader("Popular Sports")
            popular_sports = analytics_data.get('popular_sports', [])
            
            if popular_sports:
                # Create bar chart
                sports_df = pd.DataFrame(popular_sports)
                fig_sports = px.bar(
                    sports_df,
                    x='sport_name',
                    y='game_count',
                    title='Games by Sport',
                    labels={'sport_name': 'Sport', 'game_count': 'Number of Games'},
                    color='game_count',
                    color_continuous_scale='Blues'
                )
                fig_sports.update_layout(showlegend=False)
                st.plotly_chart(fig_sports, use_container_width=True)
                
                # Display table
                st.write("**Detailed Sport Statistics:**")
                display_df = sports_df[['sport_name', 'league_count', 'team_count', 'game_count']]
                display_df.columns = ['Sport', 'Leagues', 'Teams', 'Games']
                st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.info("No sports data available.")
            
            st.divider()
            
            # Busiest Days
            st.subheader("Busiest Game Days")
            busiest_days = analytics_data.get('busiest_days', [])
            
            if busiest_days:
                # Create bar chart
                days_df = pd.DataFrame(busiest_days)
                days_df['game_date'] = pd.to_datetime(days_df['game_date'])
                days_df = days_df.sort_values('game_date')
                
                fig_days = px.bar(
                    days_df,
                    x='game_date',
                    y='game_count',
                    title='Games by Date (Top 10)',
                    labels={'game_date': 'Date', 'game_count': 'Number of Games'},
                    color='game_count',
                    color_continuous_scale='Greens'
                )
                fig_days.update_layout(showlegend=False, xaxis_title="Date", yaxis_title="Number of Games")
                st.plotly_chart(fig_days, use_container_width=True)
                
                # Display table
                st.write("**Top 10 Busiest Days:**")
                display_days_df = days_df[['game_date', 'game_count']]
                display_days_df.columns = ['Date', 'Games']
                st.dataframe(display_days_df, use_container_width=True, hide_index=True)
            else:
                st.info("No game date data available.")
        else:
            st.error(f"Error loading analytics: {analytics_response.json().get('error', 'Unknown error')}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

# ==================== ADD SPORTS/LEAGUES TAB ====================
with tab2:
    st.subheader("Add New Sports and Leagues")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("Expand the application by adding new sports and leagues.")
    with col2:
        if st.button("🔄 Refresh", key="refresh_add"):
            st.rerun()
    
    # Add New Sport Section
    st.divider()
    st.subheader("Add New Sport")
    
    try:
        # Fetch existing sports
        sports_response = requests.get(f"{API_BASE}/sports")
        existing_sports = []
        if sports_response.status_code == 200:
            existing_sports = sports_response.json()
        
        with st.form("add_sport_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_sport_name = st.text_input("Sport Name *", placeholder="e.g., Tennis, Baseball")
            with col2:
                new_sport_description = st.text_area("Description", placeholder="Brief description of the sport")
            
            if st.form_submit_button("Add Sport"):
                if new_sport_name:
                    sport_data = {"name": new_sport_name}
                    if new_sport_description:
                        sport_data["description"] = new_sport_description
                    
                    create_response = requests.post(f"{API_BASE}/sports", json=sport_data)
                    if create_response.status_code == 201:
                        st.success("Sport added successfully!")
                        st.rerun()
                    else:
                        st.error(f"Error: {create_response.json().get('error', 'Unknown error')}")
                else:
                    st.error("Sport name is required")
        
        # Display existing sports
        if existing_sports:
            st.write("**Existing Sports:**")
            sports_df = pd.DataFrame(existing_sports)
            st.dataframe(sports_df, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"Error: {str(e)}")
    
    # Add New League Section
    st.divider()
    st.subheader("Add New League")
    
    try:
        # Fetch sports for league creation
        sports_response = requests.get(f"{API_BASE}/sports")
        sports = sports_response.json() if sports_response.status_code == 200 else []
        
        if sports:
            with st.form("add_league_form"):
                col1, col2 = st.columns(2)
                with col1:
                    new_league_name = st.text_input("League Name *", placeholder="e.g., Spring Basketball League")
                    new_league_sport = st.selectbox("Sport *", options=[s['sport_id'] for s in sports],
                                                   format_func=lambda x: next((s['name'] for s in sports if s['sport_id'] == x), f"Sport {x}"))
                    new_league_max_teams = st.number_input("Max Teams", min_value=0, value=0)
                with col2:
                    new_league_semester = st.selectbox("Semester", options=["Fall", "Spring", "Summer", "Winter"])
                    new_league_year = st.number_input("Year", min_value=2020, max_value=2030, value=datetime.now().year)
                    new_league_start = st.date_input("Start Date", value=datetime.now().date())
                    new_league_end = st.date_input("End Date", value=datetime.now().date())
                
                if st.form_submit_button("Add League"):
                    if new_league_name:
                        league_data = {
                            "name": new_league_name,
                            "sport_played": new_league_sport,
                            "semester": new_league_semester,
                            "year": int(new_league_year),
                            "max_teams": int(new_league_max_teams) if new_league_max_teams else None,
                            "league_start": new_league_start.isoformat(),
                            "league_end": new_league_end.isoformat()
                        }
                        
                        create_response = requests.post(f"{API_BASE}/leagues", json=league_data)
                        if create_response.status_code == 201:
                            st.success("League added successfully!")
                            st.rerun()
                        else:
                            st.error(f"Error: {create_response.json().get('error', 'Unknown error')}")
                    else:
                        st.error("League name is required")
        else:
            st.warning("No sports available. Please add a sport first.")
    except Exception as e:
        st.error(f"Error: {str(e)}")

# ==================== LEAGUE RULES TAB ====================
with tab3:
    st.subheader("Configure League Rules")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("Set and update rules for leagues including team size, league size, season length, and game length.")
    with col2:
        if st.button("🔄 Refresh", key="refresh_rules"):
            st.rerun()
    
    try:
        # Fetch all sports
        sports_response = requests.get(f"{API_BASE}/sports")
        if sports_response.status_code == 200:
            sports = sports_response.json()
            
            if sports:
                # Select sport
                sport_options = {f"{s['name']}": s['sport_id'] for s in sports}
                selected_sport_display = st.selectbox("Select Sport", options=list(sport_options.keys()))
                selected_sport_id = sport_options[selected_sport_display]
                
                # Get existing rules for this sport
                rules_response = requests.get(f"{API_BASE}/sports/{selected_sport_id}/rules")
                existing_rules = []
                if rules_response.status_code == 200:
                    existing_rules = rules_response.json()
                
                # Display existing rules
                if existing_rules:
                    st.write("**Current Rules:**")
                    rules_df = pd.DataFrame(existing_rules)
                    display_cols = ['team_size', 'league_size', 'season_length', 'game_length', 'description']
                    display_cols = [c for c in display_cols if c in rules_df.columns]
                    st.dataframe(rules_df[display_cols], use_container_width=True, hide_index=True)
                    
                    # Update rules section
                    st.divider()
                    st.subheader("Update Rules")
                    if existing_rules:
                        current_rule = existing_rules[0]  # Use first rule if multiple exist
                        
                        with st.form("update_rules_form"):
                            col1, col2 = st.columns(2)
                            with col1:
                                team_size = st.number_input("Team Size", min_value=1, value=current_rule.get('team_size') or 5)
                                league_size = st.number_input("League Size (Max Teams)", min_value=1, value=current_rule.get('league_size') or 10)
                            with col2:
                                season_length = st.number_input("Season Length (Weeks)", min_value=1, value=current_rule.get('season_length') or 10)
                                game_length = st.number_input("Game Length (Minutes)", min_value=1, value=current_rule.get('game_length') or 40)
                            
                            description = st.text_area("Description", value=current_rule.get('description', ''))
                            
                            if st.form_submit_button("Update Rules"):
                                rules_data = {
                                    "team_size": int(team_size),
                                    "league_size": int(league_size),
                                    "season_length": int(season_length),
                                    "game_length": int(game_length),
                                    "description": description
                                }
                                
                                update_response = requests.put(f"{API_BASE}/sports/{selected_sport_id}/rules", json=rules_data)
                                if update_response.status_code == 200:
                                    st.success("Rules updated successfully!")
                                    st.rerun()
                                else:
                                    st.error(f"Error: {update_response.json().get('error', 'Unknown error')}")
                else:
                    st.info("No rules configured for this sport yet.")
                    
                    # Create rules section
                    st.divider()
                    st.subheader("Create Rules")
                    with st.form("create_rules_form"):
                        col1, col2 = st.columns(2)
                        with col1:
                            team_size = st.number_input("Team Size *", min_value=1, value=5)
                            league_size = st.number_input("League Size (Max Teams) *", min_value=1, value=10)
                        with col2:
                            season_length = st.number_input("Season Length (Weeks) *", min_value=1, value=10)
                            game_length = st.number_input("Game Length (Minutes) *", min_value=1, value=40)
                        
                        description = st.text_area("Description", placeholder="e.g., Basketball: 5v5, 10 week season, 40 min games")
                        
                        if st.form_submit_button("Create Rules"):
                            rules_data = {
                                "team_size": int(team_size),
                                "league_size": int(league_size),
                                "season_length": int(season_length),
                                "game_length": int(game_length),
                                "description": description
                            }
                            
                            create_response = requests.post(f"{API_BASE}/sports/{selected_sport_id}/rules", json=rules_data)
                            if create_response.status_code == 201:
                                st.success("Rules created successfully!")
                                st.rerun()
                            else:
                                st.error(f"Error: {create_response.json().get('error', 'Unknown error')}")
            else:
                st.info("No sports found. Please add a sport first.")
        else:
            st.error(f"Error loading sports: {sports_response.json().get('error', 'Unknown error')}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

