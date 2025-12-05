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


#### ------------------------ Player Role ------------------------
def PlayerHomeNav():
    st.sidebar.page_link(
        "pages/10_Player_Home.py", label="Player Home", icon="🏃"
    )





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
    st.sidebar.page_link("pages/22_Team_Performance_Comparison.py", label="Team Performance Comparison", icon="📈")


#### ------------------------ System Admin Role ------------------------
def AdminPageNav():
    st.sidebar.page_link("pages/20_Admin_Home.py", label="System Admin", icon="🖥️")
    st.sidebar.page_link(
        "pages/21_ML_Model_Mgmt.py", label="ML Model Management", icon="🏢"
    )


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

        # If the user is a statkeeper, show statkeeper pages
        if st.session_state["role"] == "statkeeper":
            StatkeeperHomeNav()

        # If the user is a player, show player pages
        if st.session_state["role"] == "player":
            PlayerHomeNav()

        # If the user is a team captain, show team captain pages
        if st.session_state["role"] == "team_captain":
            TeamCaptainHomeNav()
            GameSchedulingNav()
            TeamStatsDashboardNav()
            TeamPerformanceComparisonNav()

        # If the user is an administrator, give them access to the administrator pages
        if st.session_state["role"] == "administrator":
            AdminPageNav()

    # Always show the About page at the bottom of the list of links
    AboutPageNav()

    if st.session_state["authenticated"]:
        # Always show a logout button if there is a logged in user
        if st.sidebar.button("Logout"):
            del st.session_state["role"]
            del st.session_state["authenticated"]
            st.switch_page("Home.py")
