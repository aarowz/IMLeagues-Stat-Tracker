import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

SideBarLinks()

st.title(f"Welcome Team Captain, {st.session_state['first_name']}.")
st.write('')
st.write('')
st.write('### What would you like to do today?')

if st.button('Schedule & Manage Games', 
             type='primary',
             use_container_width=True):
    st.switch_page('pages/18_Game_Scheduling.py')

if st.button('Team Stats Dashboard', 
             type='primary',
             use_container_width=True):
    st.switch_page('pages/19_Team_Stats_Dashboard.py')

if st.button('Team Performance Comparison', 
             type='primary',
             use_container_width=True):
    st.switch_page('pages/20_Team_Performance_Comparison.py')

