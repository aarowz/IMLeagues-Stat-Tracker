##################################################
# This is the main/entry-point file for the 
# IMLeagues Stat Tracker application
##################################################

# Set up basic logging infrastructure
import logging
logging.basicConfig(format='%(filename)s:%(lineno)s:%(levelname)s -- %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# import the main streamlit library as well
# as SideBarLinks function from src/modules folder
import streamlit as st
import requests
from modules.nav import SideBarLinks

# streamlit supports reguarl and wide layout (how the controls
# are organized/displayed on the screen).
st.set_page_config(layout = 'wide')

# If a user is at this page, we assume they are not 
# authenticated.  So we change the 'authenticated' value
# in the streamlit session_state to false. 
st.session_state['authenticated'] = False

# Use the SideBarLinks function from src/modules/nav.py to control
# the links displayed on the left-side panel. 
# IMPORTANT: ensure src/.streamlit/config.toml sets
# showSidebarNavigation = false in the [client] section
SideBarLinks(show_home=True)

# ***************************************************
#    The major content of this page
# ***************************************************

# set the title of the page and provide a simple prompt. 
logger.info("Loading the Home page of the app")
st.title('IMLeagues Stat Tracker')
st.markdown("---")
st.subheader('Welcome!')
st.write('Select your role and user to continue.')

# API base URLs
API_BASE = "http://web-api:4000"
SYSTEM_ADMIN_API = f"{API_BASE}/system-admin"
PLAYER_API = f"{API_BASE}/player"

# Fetch users for each role
stat_keepers = []
players = []
team_captains = []

try:
    # Fetch Stat Keepers
    stat_keepers_response = requests.get(f"{SYSTEM_ADMIN_API}/stat-keepers", timeout=5)
    if stat_keepers_response.status_code == 200:
        stat_keepers = stat_keepers_response.json()
    else:
        logger.warning(f"Failed to fetch stat keepers: {stat_keepers_response.status_code}")
except Exception as e:
    logger.error(f"Error fetching stat keepers: {str(e)}")
    st.warning("Unable to load stat keepers. Using default options.")

try:
    # Fetch Players
    players_response = requests.get(f"{PLAYER_API}/players", timeout=5)
    if players_response.status_code == 200:
        players = players_response.json()
    else:
        logger.warning(f"Failed to fetch players: {players_response.status_code}")
except Exception as e:
    logger.error(f"Error fetching players: {str(e)}")
    st.warning("Unable to load players. Using default options.")

try:
    # Fetch Team Captains (players with role='captain' in Teams_Players)
    # We'll fetch all teams and their players, then filter for captains
    teams_response = requests.get(f"{SYSTEM_ADMIN_API}/teams", timeout=5)
    if teams_response.status_code == 200:
        teams = teams_response.json()
        captains_set = set()  # Use set to avoid duplicates
        
        for team in teams:
            team_id = team.get('team_id')
            if team_id:
                try:
                    team_players_response = requests.get(
                        f"{SYSTEM_ADMIN_API}/teams/{team_id}/players", 
                        timeout=5
                    )
                    if team_players_response.status_code == 200:
                        team_players = team_players_response.json()
                        for tp in team_players:
                            if tp.get('role', '').lower() == 'captain':
                                # Add player info if not already added
                                player_id = tp.get('player_id')
                                if player_id and player_id not in captains_set:
                                    captains_set.add(player_id)
                                    # Find full player info
                                    player_info = next(
                                        (p for p in players if p.get('player_id') == player_id),
                                        None
                                    )
                                    if player_info:
                                        team_captains.append({
                                            'player_id': player_id,
                                            'first_name': player_info.get('first_name'),
                                            'last_name': player_info.get('last_name'),
                                            'email': player_info.get('email'),
                                            'team_id': team_id,
                                            'team_name': team.get('name')
                                        })
                except Exception as e:
                    logger.warning(f"Error fetching players for team {team_id}: {str(e)}")
                    continue
    else:
        logger.warning(f"Failed to fetch teams: {teams_response.status_code}")
except Exception as e:
    logger.error(f"Error fetching team captains: {str(e)}")
    st.warning("Unable to load team captains. Using default options.")

# Select Role
st.write("")
selected_role = st.radio(
    "Select your role:",
    options=["Stat Keeper", "Player", "Team Captain", "System Administrator"],
    horizontal=True
)

st.write("")

selected_stat_keeper = None
selected_player = None
selected_team_captain = None
selected_admin = None

# Select User from the chosen role
if selected_role == "Stat Keeper":
    if stat_keepers:
        stat_keeper_options = {
            f"{sk['first_name']} {sk['last_name']} ({sk['email']})": sk 
            for sk in stat_keepers
        }
        selected_stat_keeper_display = st.selectbox(
            "Select a Stat Keeper:",
            options=list(stat_keeper_options.keys()),
            index=0 if stat_keeper_options else None
        )
        selected_stat_keeper = stat_keeper_options.get(selected_stat_keeper_display) if stat_keeper_options else None
    else:
        st.selectbox("Select a Stat Keeper:", options=["No stat keepers available"], disabled=True)
        st.warning("No stat keepers available in the database.")
        selected_stat_keeper = None

elif selected_role == "Player":
    if players:
        player_options = {
            f"{p['first_name']} {p['last_name']} ({p['email']})": p 
            for p in players
        }
        selected_player_display = st.selectbox(
            "Select a Player:",
            options=list(player_options.keys()),
            index=0 if player_options else None
        )
        selected_player = player_options.get(selected_player_display) if player_options else None
    else:
        st.selectbox("Select a Player:", options=["No players available"], disabled=True)
        st.warning("No players available in the database.")
        selected_player = None

elif selected_role == "Team Captain":
    if team_captains:
        team_captain_options = {
            f"{tc['first_name']} {tc['last_name']} ({tc['email']}) - {tc.get('team_name', 'Team')}": tc 
            for tc in team_captains
        }
        selected_team_captain_display = st.selectbox(
            "Select a Team Captain:",
            options=list(team_captain_options.keys()),
            index=0 if team_captain_options else None
        )
        selected_team_captain = team_captain_options.get(selected_team_captain_display) if team_captain_options else None
    else:
        st.selectbox("Select a Team Captain:", options=["No team captains available"], disabled=True)
        st.warning("No team captains available in the database.")
        selected_team_captain = None

elif selected_role == "System Administrator":
    # System Admin is a special role - we'll use a simple option
    admin_options = {
        "System Administrator": {
            'first_name': 'SysAdmin',
            'last_name': '',
            'email': 'admin@northeastern.edu',
            'role': 'administrator'
        }
    }
    selected_admin_display = st.selectbox(
        "Select a System Administrator:",
        options=list(admin_options.keys()),
        index=0
    )
    selected_admin = admin_options.get(selected_admin_display)

st.write("")

# Login Button
if st.button("Login", type='primary', use_container_width=True):
    # Determine which role was selected and log in accordingly
    if selected_role == "Stat Keeper" and selected_stat_keeper:
        st.session_state['authenticated'] = True
        st.session_state['role'] = 'statkeeper'
        st.session_state['first_name'] = selected_stat_keeper['first_name']
        st.session_state['last_name'] = selected_stat_keeper['last_name']
        st.session_state['email'] = selected_stat_keeper['email']
        st.session_state['keeper_id'] = selected_stat_keeper['keeper_id']
        logger.info(f"Logging in as Statkeeper: {selected_stat_keeper['first_name']} {selected_stat_keeper['last_name']}")
        st.switch_page('pages/00_Statkeeper_Home.py')
    elif selected_role == "Player" and selected_player:
        st.session_state['authenticated'] = True
        st.session_state['role'] = 'player'
        st.session_state['first_name'] = selected_player['first_name']
        st.session_state['last_name'] = selected_player['last_name']
        st.session_state['email'] = selected_player['email']
        st.session_state['player_id'] = selected_player['player_id']
        logger.info(f"Logging in as Player: {selected_player['first_name']} {selected_player['last_name']}")
        st.switch_page('pages/10_Player_Home.py')
    elif selected_role == "Team Captain" and selected_team_captain:
        st.session_state['authenticated'] = True
        st.session_state['role'] = 'team_captain'
        st.session_state['first_name'] = selected_team_captain['first_name']
        st.session_state['last_name'] = selected_team_captain['last_name']
        st.session_state['email'] = selected_team_captain['email']
        st.session_state['player_id'] = selected_team_captain['player_id']
        st.session_state['team_id'] = selected_team_captain['team_id']
        logger.info(f"Logging in as Team Captain: {selected_team_captain['first_name']} {selected_team_captain['last_name']}")
        st.switch_page('pages/17_Team_Captain_Home.py')
    elif selected_role == "System Administrator" and selected_admin:
        st.session_state['authenticated'] = True
        st.session_state['role'] = 'administrator'
        st.session_state['first_name'] = selected_admin['first_name']
        st.session_state['last_name'] = selected_admin['last_name']
        st.session_state['email'] = selected_admin['email']
        logger.info("Logging in as System Administrator")
        st.switch_page('pages/24_System_Admin_Home.py')
    else:
        st.error("Please select a user from the dropdown above.")



