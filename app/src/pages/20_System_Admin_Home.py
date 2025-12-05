import logging
logger = logging.getLogger(__name__)

import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

SideBarLinks()

st.title(f"Welcome System Admin, {st.session_state['first_name']}!")
st.write('')
st.write('')
st.write('### What would you like to do today?')

if st.button('Manage Users', 
             type='primary',
             use_container_width=True):
    st.info("User management page coming soon!")

if st.button('Manage Teams', 
             type='primary',
             use_container_width=True):
    st.info("Team management page coming soon!")

if st.button('Manage Leagues', 
             type='primary',
             use_container_width=True):
    st.info("League management page coming soon!")

if st.button('View System Logs', 
             type='primary',
             use_container_width=True):
    st.info("System logs page coming soon!")

