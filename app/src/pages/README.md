# Pages Directory

This folder contains all the pages that are part of the IMLeagues Stat Tracker application. Each page provides specific functionality for different user personas.

## Page Organization

The pages are organized by Role using numerical prefixes to control their order in the Streamlit sidebar:

- Pages starting with `0` - Stat Keeper role pages
- Pages starting with `1` - Player and Team Captain role pages
- Pages starting with `2` - System Administrator role pages
- Pages starting with `3` - General/About pages

Streamlit automatically discovers and orders pages alphanumerically by filename. For more information about how Streamlit's multi-page apps work, see the [official Streamlit documentation](https://docs.streamlit.io/library/get-started/multipage-apps).

## Stat Keeper Pages

- `00_Statkeeper_Home.py` - Stat keeper landing page
- `01_My_Assigned_Games.py` - View and manage assigned games
- `02_Live_Stat_Entry.py` - Enter statistics during live games
- `03_Game_Finalization.py` - Review and finalize game statistics

## Player Pages

- `10_Player_Home.py` - Player landing page
- `11_My_Stats_Analytics.py` - View personal statistics and analytics
- `12_My_Games_Schedule.py` - View personal game schedule
- `13_Teams_Leagues_Explorer.py` - Browse teams and leagues

## Team Captain Pages

- `16_Team_Performance_Comparison.py` - Compare team performance
- `17_Team_Captain_Home.py` - Team captain landing page
- `18_Game_Scheduling.py` - Schedule new games
- `19_Team_Stats_Dashboard.py` - View team statistics and performance

## System Administrator Pages

- `24_System_Admin_Home.py` - System administrator landing page
- `25_Data_Management.py` - Manage system data and configurations
- `26_Awards_Management.py` - Manage player awards and league champions
- `27_System_Analytics.py` - View system-wide analytics and statistics

## General Pages

- `30_About.py` - About page with project information
