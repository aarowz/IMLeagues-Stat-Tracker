import streamlit as st
from streamlit_extras.app_logo import add_logo
from modules.nav import SideBarLinks

SideBarLinks()

st.write("# About IMLeagues Stat Tracker")

st.markdown(
    """
    **IMLeagues Stat Tracker** is a live stat tracking application for intramural sports participants 
    who want a personalized, analytical, and user-friendly way to track their performance across their leagues.

    ## Features
    
    - **Real-time stat entry** during games
    - **Performance analytics** and dashboards
    - **Team management** for captains
    - **League-wide comparisons** and rankings
    - **Game scheduling** and management
    
    ## User Roles
    
    - **Team Captain**: Schedule games, manage team stats, send reminders, and analyze performance
    - **Player**: View personal stats, upcoming games, and league rankings
    - **Stat Keeper**: Enter stats in real-time during games
    - **System Administrator**: Manage leagues, sports, and system-wide data
    
    Built with Streamlit, Flask, and MySQL.
    """
)

# Add a button to return to home page
if st.button("Return to Home", type="primary"):
    st.switch_page("Home.py")
