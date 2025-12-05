import logging
logger = logging.getLogger(__name__)

import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

SideBarLinks()

st.title(f"Welcome Player, {st.session_state['first_name']}!")
st.write('')
st.write('')
st.write('### What would you like to do today?')

if st.button('View My Stats', 
             type='primary',
             use_container_width=True):
    st.info("Player stats page coming soon!")

if st.button('View Upcoming Games', 
             type='primary',
             use_container_width=True):
    st.info("Upcoming games page coming soon!")

if st.button('View Team Standings', 
             type='primary',
             use_container_width=True):
    st.info("Team standings page coming soon!")

