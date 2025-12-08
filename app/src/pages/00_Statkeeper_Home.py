import logging
logger = logging.getLogger(__name__)

import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

SideBarLinks()

st.title(f"Welcome Statkeeper, {st.session_state['first_name']}!")
st.write('')
st.write('')
st.write('### What would you like to do today?')

# Workflow: My Assigned Games → Live Stat Entry → Game Finalization
if st.button('My Assigned Games', 
             type='primary',
             use_container_width=True):
    st.switch_page('pages/01_My_Assigned_Games.py')

if st.button('Live Stat Entry', 
             type='primary',
             use_container_width=True):
    st.switch_page('pages/02_Live_Stat_Entry.py')

if st.button('Game Finalization', 
             type='primary',
             use_container_width=True):
    st.switch_page('pages/03_Game_Finalization.py')

