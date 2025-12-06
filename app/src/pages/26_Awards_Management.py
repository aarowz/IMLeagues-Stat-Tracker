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
        # Fetch all players
        players_response = requests.get(f"{API_BASE}/players")
        if players_response.status_code == 200:
            players = players_response.json()
            
            if players:
                # Search filter
                search_filter = st.text_input("Search Players", key="award_player_search")
                filtered_players = players
                if search_filter:
                    filtered_players = [p for p in players if 
                                       search_filter.lower() in p.get('first_name', '').lower() or
                                       search_filter.lower() in p.get('last_name', '').lower() or
                                       search_filter.lower() in p.get('email', '').lower()]
                
                # Select player
                player_options = {f"{p['first_name']} {p['last_name']} ({p['email']})": p['player_id'] for p in filtered_players}
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
                    st.dataframe(awards_df[['award_type', 'year', 'description']] if 'description' in awards_df.columns else awards_df[['award_type', 'year']], 
                                use_container_width=True, hide_index=True)
                    
                    # Delete award option
                    st.divider()
                    st.subheader("Remove Award")
                    award_options = {f"{a['award_type']} ({a['year']})": a['award_id'] for a in existing_awards}
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
                # Select league
                league_options = {f"{l['name']} ({sport_map.get(l.get('sport_played'), 'Unknown')})": l['league_id'] for l in leagues}
                selected_league_display = st.selectbox("Select League", options=list(league_options.keys()))
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
                    if 'description' in champions_df.columns:
                        display_cols.append('description')
                    st.dataframe(champions_df[display_cols], use_container_width=True, hide_index=True)
                else:
                    st.info("This league has no recorded champions yet.")
                
                # Get teams in this league
                teams_response = requests.get(f"{API_BASE}/leagues/{selected_league_id}/teams")
                teams = []
                if teams_response.status_code == 200:
                    teams = teams_response.json()
                
                if teams:
                    # Assign new champion
                    st.divider()
                    st.subheader("Record New Champion")
                    with st.form("assign_champion"):
                        team_options = {f"{t.get('team_name', 'Unknown Team')} (Wins: {t.get('wins', 0)}, Losses: {t.get('losses', 0)})": t['team_id'] for t in teams}
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
        # Fetch all players with their awards
        players_response = requests.get(f"{API_BASE}/players")
        players = players_response.json() if players_response.status_code == 200 else []
        player_map = {p['player_id']: f"{p['first_name']} {p['last_name']}" for p in players}
        
        # Collect all player awards
        all_player_awards = []
        for player in players[:50]:  # Limit to first 50 players for performance
            awards_response = requests.get(f"{API_BASE}/players/{player['player_id']}/awards")
            if awards_response.status_code == 200:
                awards = awards_response.json()
                for award in awards:
                    award['player_name'] = player_map.get(player['player_id'], 'Unknown')
                    all_player_awards.append(award)
        
        if all_player_awards:
            st.subheader("Player Awards")
            awards_df = pd.DataFrame(all_player_awards)
            display_cols = ['player_name', 'award_type', 'year']
            if 'description' in awards_df.columns:
                display_cols.append('description')
            st.dataframe(awards_df[display_cols], use_container_width=True, hide_index=True)
        else:
            st.info("No player awards found.")
        
        st.divider()
        
        # Fetch all leagues with their champions
        leagues_response = requests.get(f"{API_BASE}/leagues")
        leagues = leagues_response.json() if leagues_response.status_code == 200 else []
        
        # Fetch sports for display
        sports_response = requests.get(f"{API_BASE}/sports")
        sports = sports_response.json() if sports_response.status_code == 200 else []
        sport_map = {s['sport_id']: s['name'] for s in sports}
        
        # Collect all champions
        all_champions = []
        for league in leagues:
            champions_response = requests.get(f"{API_BASE}/leagues/{league['league_id']}/champions")
            if champions_response.status_code == 200:
                champions = champions_response.json()
                for champion in champions:
                    champion['league_name'] = league['name']
                    champion['sport_name'] = sport_map.get(league.get('sport_played'), 'Unknown')
                    all_champions.append(champion)
        
        if all_champions:
            st.subheader("League Champions")
            champions_df = pd.DataFrame(all_champions)
            display_cols = ['league_name', 'sport_name', 'year', 'winner_team_name']
            if 'description' in champions_df.columns:
                display_cols.append('description')
            st.dataframe(champions_df[display_cols], use_container_width=True, hide_index=True)
        else:
            st.info("No league champions found.")
            
    except Exception as e:
        st.error(f"Error: {str(e)}")

