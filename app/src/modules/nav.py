# Idea borrowed from https://github.com/fsmosca/sample-streamlit-authenticator

# This file has function to add certain functionality to the left side bar of the app

import streamlit as st


#### ------------------------ General ------------------------
def HomeNav():
    st.sidebar.page_link("Home.py", label="Home", icon="🏠")


def AboutPageNav():
    st.sidebar.page_link("pages/30_About.py", label="About", icon="🧠")


#### ------------------------ Statkeeper Role ------------------------
def StatkeeperHomeNav():
    st.sidebar.page_link(
        "pages/00_Statkeeper_Home.py", label="Statkeeper Home", icon="📋"
    )

def MyAssignedGamesNav():
    st.sidebar.page_link("pages/01_My_Assigned_Games.py", label="My Assigned Games", icon="📅")

def LiveStatEntryNav():
    st.sidebar.page_link("pages/02_Live_Stat_Entry.py", label="Live Stat Entry", icon="⚡")

def GameFinalizationNav():
    st.sidebar.page_link("pages/03_Game_Finalization.py", label="Game Finalization", icon="✅")


#### ------------------------ Player Role ------------------------
def PlayerHomeNav():
    st.sidebar.page_link(
        "pages/10_Player_Home.py", label="Player Home", icon="🏃"
    )

def MyStatsAnalyticsNav():
    st.sidebar.page_link("pages/11_My_Stats_Analytics.py", label="My Stats & Analytics", icon="📊")

def MyGamesScheduleNav():
    st.sidebar.page_link("pages/12_My_Games_Schedule.py", label="My Games & Schedule", icon="📅")

def TeamsLeaguesExplorerNav():
    st.sidebar.page_link("pages/13_Teams_Leagues_Explorer.py", label="Teams & Leagues Explorer", icon="🔍")





#### ------------------------ Team Captain Role ------------------------
def TeamCaptainHomeNav():
    st.sidebar.page_link(
        "pages/17_Team_Captain_Home.py", label="Team Captain Home", icon="🏠"
    )

def GameSchedulingNav():
    st.sidebar.page_link("pages/18_Game_Scheduling.py", label="Game Scheduling", icon="📅")

def TeamStatsDashboardNav():
    st.sidebar.page_link("pages/19_Team_Stats_Dashboard.py", label="Team Stats Dashboard", icon="📊")

def TeamPerformanceComparisonNav():
    st.sidebar.page_link("pages/20_Team_Performance_Comparison.py", label="Team Performance Comparison", icon="📈")


#### ------------------------ System Admin Role ------------------------
def SystemAdminHomeNav():
    st.sidebar.page_link(
        "pages/24_System_Admin_Home.py", label="System Admin Home", icon="🖥️"
    )

def DataManagementNav():
    st.sidebar.page_link("pages/25_Data_Management.py", label="Data Management", icon="📊")

def AwardsManagementNav():
    st.sidebar.page_link("pages/26_Awards_Management.py", label="Awards Management", icon="🏆")

def SystemAnalyticsNav():
    st.sidebar.page_link("pages/27_System_Analytics.py", label="System Analytics", icon="📈")


# --------------------------------Links Function -----------------------------------------------
def SideBarLinks(show_home=False):
    """
    This function handles adding links to the sidebar of the app based upon the logged-in user's role, which was put in the streamlit session_state object when logging in.
    """

    # add a logo to the sidebar always
    st.sidebar.image("assets/logo.png", width=150)

    # If there is no logged in user, redirect to the Home (Landing) page
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.switch_page("Home.py")

    if show_home:
        # Show the Home page link (the landing page)
        HomeNav()

    # Show the other page navigators depending on the users' role.
    if st.session_state["authenticated"]:

        # If the user is a statkeeper, show statkeeper pages (workflow order)
        if st.session_state["role"] == "statkeeper":
            StatkeeperHomeNav()
            MyAssignedGamesNav()
            LiveStatEntryNav()
            GameFinalizationNav()

        # If the user is a player, show player pages
        if st.session_state["role"] == "player":
            PlayerHomeNav()
            MyStatsAnalyticsNav()
            MyGamesScheduleNav()
            TeamsLeaguesExplorerNav()

        # If the user is a team captain, show team captain pages
        if st.session_state["role"] == "team_captain":
            TeamCaptainHomeNav()
            GameSchedulingNav()
            TeamStatsDashboardNav()
            TeamPerformanceComparisonNav()

        # If the user is an administrator, give them access to the administrator pages
        if st.session_state["role"] == "administrator":
            SystemAdminHomeNav()
            DataManagementNav()
            AwardsManagementNav()
            SystemAnalyticsNav()

    # Always show the About page at the bottom of the list of links
    AboutPageNav()

    if st.session_state["authenticated"]:
        # Always show a logout button if there is a logged in user
        if st.sidebar.button("Logout"):
            del st.session_state["role"]
            del st.session_state["authenticated"]
            st.switch_page("Home.py")