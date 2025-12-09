import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from modules.nav import SideBarLinks

SideBarLinks()
st.set_page_config(layout='wide')

st.title("My Stats & Analytics")
st.write("View your personal statistics and league rankings.")

# Player ID - get from session state (set during login)
PLAYER_ID = st.session_state.get('player_id', 2)  # Default to 2 if not set
API_BASE = "http://web-api:4000/player"
ADMIN_API_BASE = "http://web-api:4000/system-admin"

# Fetch player stats and analytics
try:
    stats_response = requests.get(f"{API_BASE}/players/{PLAYER_ID}/stats")
    analytics_response = requests.get(f"{API_BASE}/analytics/players/{PLAYER_ID}")
    
    if stats_response.status_code == 200:
        stats_data = stats_response.json()
    else:
        stats_data = None
        st.error(f"Error loading stats: {stats_response.json().get('error', 'Unknown error')}")
    
    if analytics_response.status_code == 200:
        analytics_data = analytics_response.json()
    else:
        analytics_data = None
        st.error(f"Error loading analytics: {analytics_response.json().get('error', 'Unknown error')}")
except Exception as e:
    st.error(f"Error: {str(e)}")
    stats_data = None
    analytics_data = None

if not stats_data and not analytics_data:
    st.warning("Unable to load player statistics.")
    st.stop()

# Display summary metrics
if analytics_data and analytics_data.get('statistics'):
    stats = analytics_data['statistics']
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Stat Events", stats.get('total_stat_events', 0))
    with col2:
        st.metric("Games with Stats", stats.get('games_with_stats', 0))
    with col3:
        st.metric("Teams Played For", stats.get('teams_played_for', 0))
    with col4:
        st.metric("Total Games Played", stats.get('total_games_played', 0))

st.divider()

# Create tabs for different views
tab1, tab2, tab3, tab4 = st.tabs(["📈 Stat Breakdown", "📅 Recent Stats", "📊 Performance Over Time", "🏆 League Rankings"])

with tab1:
    st.subheader("Stat Breakdown by Type")
    
    if stats_data and stats_data.get('aggregated_stats'):
        agg_stats = stats_data['aggregated_stats']
        
        if agg_stats:
            # Create DataFrame for visualization
            df = pd.DataFrame(agg_stats)
            df = df.sort_values('count', ascending=False)
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.bar_chart(df.set_index('description')['count'], use_container_width=True)
            
            with col2:
                st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No statistics recorded yet.")
    else:
        st.info("No aggregated statistics available.")

with tab2:
    st.subheader("Recent Stat Events")
    
    if stats_data and stats_data.get('stat_events'):
        stat_events = stats_data['stat_events']
        
        # Show last 20 events
        recent_events = stat_events[:20]
        
        if recent_events:
            for event in recent_events:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 2])
                    
                    with col1:
                        st.write(f"**{event['description']}**")
                    
                    with col2:
                        game_info = f"{event.get('home_team', 'TBD')} vs {event.get('away_team', 'TBD')}"
                        st.write(game_info)
                        st.caption(f"{event.get('league_name', 'N/A')} - {event.get('sport_name', 'N/A')}")
                    
                    with col3:
                        if event.get('date_played'):
                            st.write(f"📅 {event['date_played']}")
                        if event.get('time_entered'):
                            st.caption(f"⏰ {event['time_entered']}")
                    
                    st.divider()
        else:
            st.info("No stat events recorded yet.")
    else:
        st.info("No stat events available.")

with tab3:
    st.subheader("Performance Over Time")
    
    if analytics_data and analytics_data.get('performance_over_time'):
        perf_data = analytics_data['performance_over_time']
        
        if perf_data:
            df = pd.DataFrame(perf_data)
            df['date_played'] = pd.to_datetime(df['date_played'])
            df = df.sort_values('date_played')
            
            st.line_chart(df.set_index('date_played')['stat_count'], use_container_width=True)
            st.caption("Stat Events Per Game Over Time")
            
            st.dataframe(df[['date_played', 'stat_count']], use_container_width=True, hide_index=True)
        else:
            st.info("No performance data available yet.")
    else:
        st.info("No performance over time data available.")

with tab4:
    st.subheader("League Rankings")
    st.write("View rankings for important stats across your leagues.")
    
    # Get player's teams to find leagues
    try:
        teams_response = requests.get(f"{API_BASE}/players/{PLAYER_ID}/teams")
        if teams_response.status_code == 200:
            player_teams = teams_response.json()
        else:
            player_teams = []
    except Exception as e:
        st.error(f"Error fetching teams: {str(e)}")
        player_teams = []
    
    if player_teams:
        # Get unique leagues and fetch their details directly to ensure correct sport
        leagues = {}
        
        # Get unique league IDs
        unique_league_ids = set()
        for team in player_teams:
            league_id = team.get('league_id')
            if league_id:
                unique_league_ids.add(league_id)
        
        # Fetch all leagues from system admin API to get correct sport mapping
        try:
            all_leagues_response = requests.get(f"{ADMIN_API_BASE}/leagues")
            if all_leagues_response.status_code == 200:
                all_leagues_data = all_leagues_response.json()
                # Create a mapping of league_id to league info
                leagues_map = {league.get('league_id'): league for league in all_leagues_data}
                
                # Use the mapping to get correct sport for each unique league
                for league_id in unique_league_ids:
                    if league_id in leagues_map:
                        league_info = leagues_map[league_id]
                        leagues[league_id] = {
                            'name': league_info.get('name', f'League {league_id}'),
                            'sport': league_info.get('sport_name', 'Unknown')
                        }
                    else:
                        # League not found in API, fallback to team data
                        for team in player_teams:
                            if team.get('league_id') == league_id:
                                leagues[league_id] = {
                                    'name': team.get('league_name', f'League {league_id}'),
                                    'sport': team.get('sport_name', 'Unknown')
                                }
                                break
            else:
                # API failed, use team data as fallback
                for league_id in unique_league_ids:
                    for team in player_teams:
                        if team.get('league_id') == league_id:
                            leagues[league_id] = {
                                'name': team.get('league_name', f'League {league_id}'),
                                'sport': team.get('sport_name', 'Unknown')
                            }
                            break
        except Exception as e:
            # Exception occurred, use team data as fallback
            for league_id in unique_league_ids:
                for team in player_teams:
                    if team.get('league_id') == league_id:
                        leagues[league_id] = {
                            'name': team.get('league_name', f'League {league_id}'),
                            'sport': team.get('sport_name', 'Unknown')
                        }
                        break
        
        if leagues:
            selected_league_id = st.selectbox(
                "Select League",
                options=list(leagues.keys()),
                format_func=lambda x: f"{leagues[x]['name']} ({leagues[x]['sport']})"
            )
            
            if selected_league_id:
                try:
                    standings_response = requests.get(f"{API_BASE}/leagues/{selected_league_id}/standings")
                    if standings_response.status_code == 200:
                        standings = standings_response.json()
                        
                        if standings:
                            df = pd.DataFrame(standings)
                            df['rank'] = range(1, len(df) + 1)
                            
                            # Reorder columns
                            df = df[['rank', 'team_name', 'wins', 'losses', 'games_played', 'win_percentage']]
                            
                            st.dataframe(df, use_container_width=True, hide_index=True)
                            
                            # Find player's team rank
                            player_team_ids = [t['team_id'] for t in player_teams if t.get('league_id') == selected_league_id]
                            if player_team_ids:
                                player_team_rank = None
                                for idx, team in enumerate(standings, 1):
                                    if team['team_id'] in player_team_ids:
                                        player_team_rank = idx
                                        st.success(f"🎯 Your team '{team['team_name']}' is ranked #{player_team_rank} in this league!")
                                        break
                        else:
                            st.info("No standings data available for this league.")
                    else:
                        st.error(f"Error loading standings: {standings_response.json().get('error', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        else:
            st.info("No leagues found.")
    else:
        st.info("You are not currently on any teams.")

