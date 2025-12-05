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

if st.button('Record Game Stats', 
             type='primary',
             use_container_width=True):
    st.info("Game stats recording page coming soon!")

if st.button('View Recent Games', 
             type='primary',
             use_container_width=True):
    st.info("Recent games page coming soon!")

if st.button('Manage Players', 
             type='primary',
             use_container_width=True):
    st.info("Player management page coming soon!")

