import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from modules.nav import SideBarLinks

SideBarLinks()
st.set_page_config(layout='wide')

st.title("Teams & Leagues Explorer")
st.write("Explore teams, view stats and lineups, track performance over time, and discover other sports and leagues.")

# Player ID - get from session state (set during login)
PLAYER_ID = st.session_state.get('player_id', 2)  # Default to 2 if not set
API_BASE = "http://web-api:4000/player"
ADMIN_API_BASE = "http://web-api:4000/system-admin"

# Get player's teams to find their leagues
try:
    teams_response = requests.get(f"{API_BASE}/players/{PLAYER_ID}/teams")
    if teams_response.status_code == 200:
        player_teams = teams_response.json()
    else:
        player_teams = []
except Exception as e:
    st.error(f"Error fetching your teams: {str(e)}")
    player_teams = []

# Get all leagues (using system admin endpoint)
try:
    leagues_response = requests.get(f"{ADMIN_API_BASE}/leagues")
    if leagues_response.status_code == 200:
        all_leagues = leagues_response.json()
    else:
        all_leagues = []
except Exception as e:
    all_leagues = []
    # If system admin endpoint fails, we'll work with player's leagues only

# Get all sports (using system admin endpoint)
try:
    sports_response = requests.get(f"{ADMIN_API_BASE}/sports")
    if sports_response.status_code == 200:
        all_sports = sports_response.json()
    else:
        all_sports = []
except Exception as e:
    all_sports = []

# Browse by League section
st.subheader("Browse Teams by League")

if all_leagues:
    # Group leagues by sport
    leagues_by_sport = {}
    for league in all_leagues:
        sport_id = league.get('sport_played')
        if sport_id:
            if sport_id not in leagues_by_sport:
                leagues_by_sport[sport_id] = []
            leagues_by_sport[sport_id].append(league)
    
    # Get sport names
    sport_names = {}
    for sport in all_sports:
        sport_names[sport.get('sport_id')] = sport.get('name', 'Unknown')
    
    # League selector
    if leagues_by_sport:
        selected_league_id = st.selectbox(
            "Select League",
            options=[l['league_id'] for l in all_leagues],
            format_func=lambda x: next(
                (f"{l['name']} ({sport_names.get(l.get('sport_played'), 'Unknown')}) [ID: {l['league_id']}]" 
                 for l in all_leagues if l['league_id'] == x),
                f"League {x}"
            )
        )
        
        if selected_league_id:
            try:
                # Get teams in selected league
                teams_response = requests.get(f"{API_BASE}/leagues/{selected_league_id}/teams")
                if teams_response.status_code == 200:
                    league_teams = teams_response.json()
                    
                    if league_teams:
                        st.write(f"**Teams in League:**")
                        
                        # Deduplicate teams by team_id to prevent duplicates
                        seen_team_ids = set()
                        unique_teams = []
                        for team in league_teams:
                            team_id = team.get('team_id')
                            if team_id and team_id not in seen_team_ids:
                                seen_team_ids.add(team_id)
                                unique_teams.append(team)
                        
                        # Display teams in a grid
                        for idx, team in enumerate(unique_teams):
                            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                            
                            with col1:
                                st.write(f"**{team['team_name']}**")
                            
                            with col2:
                                st.metric("Wins", team.get('wins', 0))
                            
                            with col3:
                                st.metric("Losses", team.get('losses', 0))
                            
                            with col4:
                                # Use team_id only for stable keys (not idx, which can change)
                                view_key = f"view_team_{team['team_id']}"
                                if st.button("View Team", key=view_key, use_container_width=True):
                                    # Set to True directly instead of toggling to ensure expander shows on first click
                                    st.session_state[f"viewing_team_{team['team_id']}"] = True
                                    st.rerun()
                            
                            # Show team details inline if viewing
                            if st.session_state.get(f"viewing_team_{team['team_id']}", False):
                                try:
                                    team_details_response = requests.get(f"{API_BASE}/teams/{team['team_id']}")
                                    team_players_response = requests.get(f"{API_BASE}/teams/{team['team_id']}/players")
                                    
                                    if team_details_response.status_code == 200 and team_players_response.status_code == 200:
                                        team_details = team_details_response.json()
                                        team_players = team_players_response.json()
                                        
                                        with st.expander(f"📋 Team Details: {team['team_name']}", expanded=True):
                                            col1, col2 = st.columns(2)
                                            
                                            with col1:
                                                st.write(f"**League:** {team_details.get('league_name', 'N/A')}")
                                                st.write(f"**Sport:** {team_details.get('sport_name', 'N/A')}")
                                                st.write(f"**Record:** {team_details.get('wins', 0)}-{team_details.get('losses', 0)}")
                                            
                                            with col2:
                                                if team_players:
                                                    st.write("**Roster:**")
                                                    for player in team_players:
                                                        role_text = f" ({player.get('role', 'player')})" if player.get('role') else ""
                                                        st.write(f"- {player['first_name']} {player['last_name']}{role_text}")
                                                else:
                                                    st.info("No players found on this team.")
                                            
                                            if st.button("Close", key=f"close_team_{team['team_id']}"):
                                                st.session_state[f"viewing_team_{team['team_id']}"] = False
                                                st.rerun()
                                    else:
                                        st.error("Error loading team details")
                                except Exception as e:
                                    st.error(f"Error loading team details: {str(e)}")
                            
                            st.divider()
                    else:
                        st.info("No teams found in this league.")
                else:
                    st.error(f"Error loading teams: {teams_response.json().get('error', 'Unknown error')}")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    else:
        st.info("No leagues available.")
else:
    st.info("Unable to load leagues. Please check your connection.")

# Explore other sports section
st.divider()
st.subheader("Explore Other Sports")

if all_sports:
    sport_cols = st.columns(min(len(all_sports), 3))
    
    for idx, sport in enumerate(all_sports[:3]):
        with sport_cols[idx]:
            st.write(f"**{sport.get('name', 'Unknown')}**")
            if sport.get('description'):
                st.caption(sport['description'])
            
            # Find leagues for this sport
            sport_leagues = [l for l in all_leagues if l.get('sport_played') == sport.get('sport_id')]
            if sport_leagues:
                st.write(f"**{len(sport_leagues)} league(s)**")
                
                # Single dropdown for all leagues
                selected_league_id = st.selectbox(
                    f"Select {sport.get('name', 'Sport')} League",
                    options=[l['league_id'] for l in sport_leagues],
                    format_func=lambda x: next(
                        (f"{l.get('name', 'League')} [ID: {l['league_id']}]" 
                         for l in sport_leagues if l['league_id'] == x),
                        f"League {x}"
                    ),
                    key=f"league_select_{sport.get('sport_id')}"
                )
                
                if selected_league_id:
                    if st.button(f"View Selected League", key=f"view_selected_{selected_league_id}"):
                        st.session_state[f"viewing_league_{selected_league_id}"] = True
                        st.rerun()
                    
                    # Show league details if viewing
                    if st.session_state.get(f"viewing_league_{selected_league_id}", False):
                        try:
                            # Get league teams and games
                            league_teams_response = requests.get(f"{API_BASE}/leagues/{selected_league_id}/teams")
                            league_games_response = requests.get(f"{API_BASE}/leagues/{selected_league_id}/games")
                            
                            if league_teams_response.status_code == 200 and league_games_response.status_code == 200:
                                league_teams = league_teams_response.json()
                                league_games = league_games_response.json()
                                
                                # Get the selected league info
                                selected_league = next((l for l in sport_leagues if l['league_id'] == selected_league_id), None)
                                
                                with st.expander(f"📋 League Details: {selected_league.get('name', 'Unknown') if selected_league else 'Unknown'}", expanded=True):
                                    st.write(f"**Sport:** {sport.get('name', 'Unknown')}")
                                    if selected_league:
                                        st.write(f"**Semester:** {selected_league.get('semester', 'N/A')} {selected_league.get('year', 'N/A')}")
                                        if selected_league.get('league_start'):
                                            st.write(f"**Start Date:** {selected_league.get('league_start')}")
                                        if selected_league.get('league_end'):
                                            st.write(f"**End Date:** {selected_league.get('league_end')}")
                                    
                                    st.write(f"**Teams:** {len(league_teams) if league_teams else 0}")
                                    st.write(f"**Games:** {len(league_games) if league_games else 0}")
                                    
                                    if league_teams:
                                        st.write("**Teams in League:**")
                                        for team in league_teams[:5]:  # Show first 5 teams
                                            st.write(f"- {team.get('team_name', 'Unknown')} ({team.get('wins', 0)}-{team.get('losses', 0)})")
                                        if len(league_teams) > 5:
                                            st.caption(f"... and {len(league_teams) - 5} more teams")
                                    
                                    if st.button("Close", key=f"close_league_{selected_league_id}"):
                                        st.session_state[f"viewing_league_{selected_league_id}"] = False
                                        st.rerun()
                            else:
                                st.error("Error loading league details")
                        except Exception as e:
                            st.error(f"Error loading league details: {str(e)}")
            else:
                st.caption("No leagues available")
else:
    st.info("Unable to load sports information.")

