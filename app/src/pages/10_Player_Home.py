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

if st.button('My Stats & Analytics', 
             type='primary',
             use_container_width=True):
    st.switch_page('pages/11_My_Stats_Analytics.py')

if st.button('My Games & Schedule', 
             type='primary',
             use_container_width=True):
    st.switch_page('pages/12_My_Games_Schedule.py')

if st.button('Teams & Leagues Explorer', 
             type='primary',
             use_container_width=True):
    st.switch_page('pages/13_Teams_Leagues_Explorer.py')

