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

if st.button('Data Management', 
             type='primary',
             use_container_width=True):
    st.switch_page('pages/25_Data_Management.py')

if st.button('Awards Management', 
             type='primary',
             use_container_width=True):
    st.switch_page('pages/26_Awards_Management.py')

if st.button('System Analytics & Configuration', 
             type='primary',
             use_container_width=True):
    st.switch_page('pages/27_System_Analytics.py')

