import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime
from modules.nav import SideBarLinks

SideBarLinks()
st.set_page_config(layout='wide')

st.title("🏆 Awards Management")
st.write("Assign badges, awards, and champions to players, teams, and leagues.")

API_BASE = "http://web-api:4000/system-admin"

# Add CSS for fade-out animation (only once)
if "fade_css_added" not in st.session_state:
    st.markdown("""
    <style>
    @keyframes fadeOut {
        from { opacity: 1; }
        to { opacity: 0; }
    }
    .stSuccess {
        animation: fadeOut 0.5s ease-out forwards;
        animation-delay: 4.5s;
    }
    </style>
    """, unsafe_allow_html=True)
    st.session_state["fade_css_added"] = True

# Helper function for fade-out success messages
def show_success_fade(message, duration=5):
    """Display a success message that fades out smoothly after the specified duration."""
    # Display the message - CSS will handle the smooth fade-out animation
    st.success(message)
    
    # Wait for fade-out to complete (CSS handles the visual fade smoothly)
    # The CSS animation starts after 4.5s and takes 0.5s, so total is 5s
    time.sleep(duration + 0.5)  # Wait for animation to complete
    st.rerun()  # Refresh to remove the faded message

# Create tabs for different award types
tab1, tab2, tab3 = st.tabs(["👤 Player Awards", "🏅 League Champions", "📋 View All Awards"])

# ==================== PLAYER AWARDS TAB ====================
with tab1:
    st.subheader("Assign Awards to Players")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("Assign badges and awards to players based on their performance and achievements.")
    with col2:
        if st.button("🔄 Refresh", key="refresh_player_awards"):
            st.rerun()
    
    try:
        # Search filter (applied at API/database level)
        search_filter = st.text_input("Search Players", key="award_player_search")
        
        # Build API request with search parameter
        player_params = {}
        if search_filter:
            player_params["search"] = search_filter
        
        # Fetch players with search filter applied via SQL
        players_response = requests.get(f"{API_BASE}/players", params=player_params)
        if players_response.status_code == 200:
            players = players_response.json()
            
            if players:
                # Sort players by last_name, first_name (like Data Management page)
                sorted_players = sorted(players, key=lambda x: (x.get('last_name', '').lower(), x.get('first_name', '').lower()))
                
                # Players already filtered by backend
                filtered_players = sorted_players
                
                # Select player
                player_options = {f"{p['last_name']}, {p['first_name']} ({p['email']}) (ID: {p['player_id']})": p['player_id'] for p in filtered_players}
                selected_player_display = st.selectbox("Select Player", options=list(player_options.keys()))
                selected_player_id = player_options[selected_player_display]
                
                # Get player's existing awards
                existing_awards_response = requests.get(f"{API_BASE}/players/{selected_player_id}/awards")
                existing_awards = []
                if existing_awards_response.status_code == 200:
                    existing_awards = existing_awards_response.json()
                
                # Display existing awards
                if existing_awards:
                    st.write("**Existing Awards:**")
                    awards_df = pd.DataFrame(existing_awards)
                    display_cols = ['award_type', 'year']
                    if 'description' in awards_df.columns:
                        display_cols.append('description')
                    st.dataframe(awards_df[display_cols], use_container_width=True, hide_index=True)
                    
                    # Delete award option
                    st.divider()
                    st.subheader("Remove Award")
                    award_options = {f"{a['award_type']} ({a['year']}) (ID: {a['award_id']})": a['award_id'] for a in existing_awards}
                    award_to_delete = st.selectbox("Select Award to Remove", options=list(award_options.keys()))
                    
                    if st.button("Delete Award", type="secondary"):
                        delete_response = requests.delete(f"{API_BASE}/players/{selected_player_id}/awards", 
                                                        json={"award_id": award_options[award_to_delete]})
                        if delete_response.status_code == 200:
                            show_success_fade("Award removed successfully!")
                        else:
                            st.error(f"Error: {delete_response.json().get('error', 'Unknown error')}")
                else:
                    st.info("This player has no awards yet.")
                
                # Assign new award
                st.divider()
                st.subheader("Assign New Award")
                with st.form("assign_player_award"):
                    award_type = st.text_input("Award Type *", placeholder="e.g., MVP, Most Improved, Top Scorer")
                    award_year = st.number_input("Year *", min_value=2020, max_value=2030, value=datetime.now().year)
                    award_description = st.text_area("Description (Optional)", placeholder="Additional details about the award")
                    
                    if st.form_submit_button("Assign Award"):
                        if award_type:
                            award_data = {
                                "award_type": award_type,
                                "year": int(award_year)
                            }
                            if award_description:
                                award_data["description"] = award_description
                            
                            create_response = requests.post(f"{API_BASE}/players/{selected_player_id}/awards", json=award_data)
                            if create_response.status_code == 201:
                                show_success_fade("Award assigned successfully!")
                            else:
                                st.error(f"Error: {create_response.json().get('error', 'Unknown error')}")
                        else:
                            st.error("Award type is required")
            else:
                st.info("No players found.")
        else:
            st.error(f"Error loading players: {players_response.json().get('error', 'Unknown error')}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

# ==================== LEAGUE CHAMPIONS TAB ====================
with tab2:
    st.subheader("Assign League Champions")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("Record league champions at the end of each season.")
    with col2:
        if st.button("🔄 Refresh", key="refresh_champions"):
            st.rerun()
    
    try:
        # Fetch all leagues
        leagues_response = requests.get(f"{API_BASE}/leagues")
        if leagues_response.status_code == 200:
            leagues = leagues_response.json()
            
            # Fetch sports for display
            sports_response = requests.get(f"{API_BASE}/sports")
            sports = sports_response.json() if sports_response.status_code == 200 else []
            sport_map = {s['sport_id']: s['name'] for s in sports}
            
            if leagues:
                # Sort leagues by year (desc), then name (like Data Management page)
                sorted_leagues = sorted(leagues, key=lambda x: (-x.get('year', 0), x.get('name', '').lower()))
                
                # Select league (persist selection in session state)
                league_options = {f"{l['name']} ({l.get('year', 'N/A')}) ({sport_map.get(l.get('sport_played'), 'Unknown')}) (ID: {l['league_id']})": l['league_id'] for l in sorted_leagues}
                league_option_keys = list(league_options.keys())
                
                # Use session state to persist selection across reruns
                if "selected_champion_league" not in st.session_state:
                    st.session_state["selected_champion_league"] = league_option_keys[0] if league_option_keys else None
                elif st.session_state["selected_champion_league"] not in league_option_keys:
                    # If stored selection is no longer valid, use first option
                    st.session_state["selected_champion_league"] = league_option_keys[0] if league_option_keys else None
                
                selected_league_display = st.selectbox("Select League", 
                                                       options=league_option_keys,
                                                       key="selected_champion_league")
                selected_league_id = league_options[selected_league_display]
                
                # Get league's existing champions
                existing_champions_response = requests.get(f"{API_BASE}/leagues/{selected_league_id}/champions")
                existing_champions = []
                if existing_champions_response.status_code == 200:
                    existing_champions = existing_champions_response.json()
                
                # Display existing champions
                if existing_champions:
                    st.write("**Previous Champions:**")
                    champions_df = pd.DataFrame(existing_champions)
                    display_cols = ['year', 'winner_team_name']
                    available_cols = [col for col in display_cols if col in champions_df.columns]
                    st.dataframe(champions_df[available_cols], use_container_width=True, hide_index=True)
                    
                    # Delete champion option
                    st.divider()
                    st.subheader("Remove Champion")
                    champion_options = {f"{c['winner_team_name']} ({c['year']}) (ID: {c['champion_id']})": c['champion_id'] for c in existing_champions}
                    champion_to_delete = st.selectbox("Select Champion to Remove", options=list(champion_options.keys()))
                    
                    if st.button("🗑️ Delete Champion", type="secondary"):
                        delete_response = requests.delete(f"{API_BASE}/leagues/{selected_league_id}/champions", 
                                                        json={"champion_id": champion_options[champion_to_delete]})
                        if delete_response.status_code == 200:
                            show_success_fade("Champion removed successfully!")
                        else:
                            try:
                                error_msg = delete_response.json().get('error', f'HTTP {delete_response.status_code}')
                            except:
                                error_msg = f'HTTP {delete_response.status_code}: {delete_response.text[:200]}'
                            st.error(f"Error: {error_msg}")
                else:
                    st.info("This league has no recorded champions yet.")
                
                # Get teams in this league
                teams_response = requests.get(f"{API_BASE}/leagues/{selected_league_id}/teams")
                teams = []
                if teams_response.status_code == 200:
                    teams = teams_response.json()
                
                if teams:
                    # Sort teams by name
                    sorted_teams = sorted(teams, key=lambda x: x.get('team_name', '').lower())
                    
                    # Assign new champion
                    st.divider()
                    st.subheader("Record New Champion")
                    with st.form("assign_champion"):
                        team_options = {f"{t.get('team_name', 'Unknown Team')} (Wins: {t.get('wins', 0)}, Losses: {t.get('losses', 0)}) (ID: {t['team_id']})": t['team_id'] for t in sorted_teams}
                        winner_team = st.selectbox("Champion Team *", options=list(team_options.keys()))
                        champion_year = st.number_input("Year *", min_value=2020, max_value=2030, value=datetime.now().year)
                        
                        if st.form_submit_button("Record Champion"):
                            champion_data = {
                                "winner": team_options[winner_team],
                                "year": int(champion_year)
                            }
                            
                            create_response = requests.post(f"{API_BASE}/leagues/{selected_league_id}/champions", json=champion_data)
                            if create_response.status_code == 201:
                                show_success_fade("Champion recorded successfully!")
                            else:
                                st.error(f"Error: {create_response.json().get('error', 'Unknown error')}")
                else:
                    st.warning("No teams found in this league. Please add teams to the league first.")
            else:
                st.info("No leagues found.")
        else:
            st.error(f"Error loading leagues: {leagues_response.json().get('error', 'Unknown error')}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

# ==================== VIEW ALL AWARDS TAB ====================
with tab3:
    st.subheader("View All Awards and Champions")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("Browse all awards and champions across the system.")
    with col2:
        if st.button("🔄 Refresh", key="refresh_all_awards"):
            st.rerun()
    
    try:
        # Player Awards Section with Filters
        st.subheader("🏅 Player Awards")
        
        # Filter inputs for player awards
        col1, col2, col3 = st.columns(3)
        with col1:
            player_search = st.text_input("Search Player (name or email)", key="view_player_search")
        with col2:
            award_type_search = st.text_input("Search Award Type", key="view_award_type_search")
        with col3:
            award_year_filter = st.number_input("Filter by Year", min_value=2020, max_value=2030, value=None, key="view_award_year_filter", help="Leave empty to show all years")
        
        # Build API request with filter parameters
        award_params = {}
        if player_search:
            award_params["player_search"] = player_search
        if award_type_search:
            award_params["award_type_search"] = award_type_search
        if award_year_filter is not None:
            award_params["year"] = int(award_year_filter)
        
        # Fetch player awards with filters applied via SQL
        awards_response = requests.get(f"{API_BASE}/player-awards", params=award_params)
        all_player_awards = awards_response.json() if awards_response.status_code == 200 else []
        
        if all_player_awards:
            awards_df = pd.DataFrame(all_player_awards)
            display_cols = ['player_name', 'award_type', 'year']
            if 'description' in awards_df.columns:
                display_cols.append('description')
            # Only use columns that exist
            available_cols = [col for col in display_cols if col in awards_df.columns]
            st.dataframe(awards_df[available_cols], use_container_width=True, hide_index=True)
        else:
            st.info("No player awards found matching the filters.")
        
        st.divider()
        
        # League Champions Section with Filters
        st.subheader("🏆 League Champions")
        
        # Filter inputs for champions
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            league_search = st.text_input("Search League", key="view_league_search")
        with col2:
            team_search = st.text_input("Search Team", key="view_team_search")
        with col3:
            sport_search = st.text_input("Search Sport", key="view_sport_search")
        with col4:
            champion_year_filter = st.number_input("Filter by Year", min_value=2020, max_value=2030, value=None, key="view_champion_year_filter", help="Leave empty to show all years")
        
        # Build API request with filter parameters
        champion_params = {}
        if league_search:
            champion_params["league_search"] = league_search
        if team_search:
            champion_params["team_search"] = team_search
        if sport_search:
            champion_params["sport_search"] = sport_search
        if champion_year_filter is not None:
            champion_params["year"] = int(champion_year_filter)
        
        # Fetch champions with filters applied via SQL
        champions_response = requests.get(f"{API_BASE}/champions", params=champion_params)
        all_champions = champions_response.json() if champions_response.status_code == 200 else []
        
        if all_champions:
            champions_df = pd.DataFrame(all_champions)
            display_cols = ['league_name', 'sport_name', 'year', 'winner_team_name']
            # Only use columns that exist
            available_cols = [col for col in display_cols if col in champions_df.columns]
            st.dataframe(champions_df[available_cols], use_container_width=True, hide_index=True)
        else:
            st.info("No league champions found matching the filters.")
            
    except Exception as e:
        st.error(f"Error: {str(e)}")
