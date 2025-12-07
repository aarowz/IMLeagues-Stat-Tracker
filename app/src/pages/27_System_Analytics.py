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
st.write("View system usage statistics and configure league rules.")

API_BASE = "http://web-api:4000/system-admin"

# Create tabs for different functionalities
tab1, tab2 = st.tabs(["📊 Analytics Dashboard", "⚙️ League Rules"])

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

# ==================== LEAGUE RULES TAB ====================
with tab2:
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
                sport_options = {f"{s['name']} (ID: {s['sport_id']})": s['sport_id'] for s in sports}
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
                    display_cols = ['rules_id', 'team_size', 'league_size', 'season_length', 'game_length', 'description']
                    display_cols = [c for c in display_cols if c in rules_df.columns]
                    st.dataframe(rules_df[display_cols], use_container_width=True, hide_index=True)
                else:
                    st.info("No rules configured for this sport yet.")
                
                # Add Rules section (always visible)
                st.divider()
                st.subheader("Add New Rules")
                with st.form("create_rules_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        team_size = st.number_input("Team Size *", min_value=1, value=5, key="add_team_size")
                        league_size = st.number_input("League Size (Max Teams) *", min_value=1, value=10, key="add_league_size")
                    with col2:
                        season_length = st.number_input("Season Length (Weeks) *", min_value=1, value=10, key="add_season_length")
                        game_length = st.number_input("Game Length (Minutes) *", min_value=1, value=40, key="add_game_length")
                    
                    description = st.text_area("Description", placeholder="e.g., Basketball: 5v5, 10 week season, 40 min games", key="add_description")
                    
                    if st.form_submit_button("Add Rules"):
                        rules_data = {
                            "team_size": int(team_size),
                            "league_size": int(league_size),
                            "season_length": int(season_length),
                            "game_length": int(game_length),
                            "description": description
                        }
                        
                        create_response = requests.post(f"{API_BASE}/sports/{selected_sport_id}/rules", json=rules_data)
                        if create_response.status_code == 201:
                            st.success("Rules added successfully!")
                            st.rerun()
                        else:
                            try:
                                error_msg = create_response.json().get('error', f'HTTP {create_response.status_code}')
                            except:
                                error_msg = f'HTTP {create_response.status_code}: {create_response.text[:200]}'
                            st.error(f"Error: {error_msg}")
                
                # Update and Delete sections (only show if rules exist)
                if existing_rules:
                    # Update rules section
                    st.divider()
                    st.subheader("Update Rules")
                    
                    # If multiple rules exist, let user select which one to update
                    if len(existing_rules) > 1:
                        rule_options = {f"Rules ID: {r['rules_id']} (Team Size: {r.get('team_size', 'N/A')}, League Size: {r.get('league_size', 'N/A')})": r['rules_id'] for r in existing_rules}
                        selected_rule_display = st.selectbox("Select Rules to Update", options=list(rule_options.keys()))
                        selected_rules_id = rule_options[selected_rule_display]
                        current_rule = next((r for r in existing_rules if r['rules_id'] == selected_rules_id), existing_rules[0])
                    else:
                        current_rule = existing_rules[0]
                        selected_rules_id = current_rule['rules_id']
                    
                    with st.form(f"update_rules_form_{selected_rules_id}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            team_size = st.number_input("Team Size", min_value=1, value=current_rule.get('team_size') or 5, key=f"update_team_size_{selected_rules_id}")
                            league_size = st.number_input("League Size (Max Teams)", min_value=1, value=current_rule.get('league_size') or 10, key=f"update_league_size_{selected_rules_id}")
                        with col2:
                            season_length = st.number_input("Season Length (Weeks)", min_value=1, value=current_rule.get('season_length') or 10, key=f"update_season_length_{selected_rules_id}")
                            game_length = st.number_input("Game Length (Minutes)", min_value=1, value=current_rule.get('game_length') or 40, key=f"update_game_length_{selected_rules_id}")
                        
                        description = st.text_area("Description", value=current_rule.get('description', ''), key=f"update_description_{selected_rules_id}")
                        
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
                                try:
                                    error_msg = update_response.json().get('error', f'HTTP {update_response.status_code}')
                                except:
                                    error_msg = f'HTTP {update_response.status_code}: {update_response.text[:200]}'
                                st.error(f"Error: {error_msg}")
                    
                    # Delete rules section
                    st.divider()
                    st.subheader("Delete Rules")
                    
                    rule_delete_options = {f"Rules ID: {r['rules_id']} (Team Size: {r.get('team_size', 'N/A')}, League Size: {r.get('league_size', 'N/A')})": r['rules_id'] for r in existing_rules}
                    rule_to_delete_display = st.selectbox("Select Rules to Delete", options=list(rule_delete_options.keys()), key="delete_rule_select")
                    rule_to_delete_id = rule_delete_options[rule_to_delete_display]
                    
                    if st.button("🗑️ Delete Rules", type="secondary", key="delete_rules_button"):
                        delete_response = requests.delete(f"{API_BASE}/sports/{selected_sport_id}/rules", 
                                                        json={"rules_id": rule_to_delete_id})
                        if delete_response.status_code == 200:
                            st.success("Rules deleted successfully!")
                            st.rerun()
                        else:
                            try:
                                error_msg = delete_response.json().get('error', f'HTTP {delete_response.status_code}')
                            except:
                                error_msg = f'HTTP {delete_response.status_code}: {delete_response.text[:200]}'
                            st.error(f"Error: {error_msg}")
            else:
                st.info("No sports found. Please add a sport first.")
        else:
            st.error(f"Error loading sports: {sports_response.json().get('error', 'Unknown error')}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

