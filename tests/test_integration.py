#!/usr/bin/env python3
"""
Integration Test Script for IMLeagues Stat Tracker
Tests all REST API endpoints and data flow across personas
"""

import requests
import json
import sys
from datetime import datetime

# API Base URLs
API_BASE = "http://localhost:4000"
SYSTEM_ADMIN_BASE = f"{API_BASE}/system-admin"
PLAYER_BASE = f"{API_BASE}/player"
STAT_KEEPER_BASE = f"{API_BASE}/stat-keeper"
TEAM_CAPTAIN_BASE = f"{API_BASE}/team-captain"

# Test results
passed_tests = []
failed_tests = []

def log_test(name, passed, message=""):
    """Log test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {name}")
    if message:
        print(f"   {message}")
    if passed:
        passed_tests.append(name)
    else:
        failed_tests.append((name, message))

def test_endpoint(method, url, expected_status=200, data=None, description=""):
    """Test an API endpoint"""
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        elif method == "PUT":
            response = requests.put(url, json=data, timeout=5)
        elif method == "DELETE":
            response = requests.delete(url, json=data, timeout=5)
        else:
            return False, f"Unknown method: {method}"
        
        if response.status_code == expected_status:
            return True, f"Status {response.status_code}"
        else:
            return False, f"Expected {expected_status}, got {response.status_code}: {response.text[:200]}"
    except requests.exceptions.ConnectionError:
        return False, "Connection error - is the API running?"
    except Exception as e:
        return False, f"Error: {str(e)}"

def test_get_json(url, description=""):
    """Test GET endpoint and return JSON data"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"Status {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return False, f"Error: {str(e)}"

print("=" * 80)
print("IMLeagues Stat Tracker - Integration Test Suite")
print("=" * 80)
print()

# ==================== SYSTEM ADMIN TESTS ====================
print("\n📊 SYSTEM ADMIN TESTS")
print("-" * 80)

# Test 1: Get all sports
success, result = test_get_json(f"{SYSTEM_ADMIN_BASE}/sports", "Get all sports")
log_test("System Admin: GET /sports", success, result if isinstance(result, str) else f"Found {len(result)} sports")
sports_data = result if success and isinstance(result, list) else []

# Test 2: Get all leagues
success, result = test_get_json(f"{SYSTEM_ADMIN_BASE}/leagues", "Get all leagues")
log_test("System Admin: GET /leagues", success, result if isinstance(result, str) else f"Found {len(result)} leagues")
leagues_data = result if success and isinstance(result, list) else []

# Test 3: Get all teams
success, result = test_get_json(f"{SYSTEM_ADMIN_BASE}/teams", "Get all teams")
log_test("System Admin: GET /teams", success, result if isinstance(result, str) else f"Found {len(result)} teams")
teams_data = result if success and isinstance(result, list) else []

# Test 4: Get all players
success, result = test_get_json(f"{SYSTEM_ADMIN_BASE}/players", "Get all players")
log_test("System Admin: GET /players", success, result if isinstance(result, str) else f"Found {len(result)} players")
players_data = result if success and isinstance(result, list) else []

# Test 5: Get all games
success, result = test_get_json(f"{SYSTEM_ADMIN_BASE}/games", "Get all games")
log_test("System Admin: GET /games", success, result if isinstance(result, str) else f"Found {len(result)} games")
games_data = result if success and isinstance(result, list) else []

# Test 6: Analytics dashboard
success, result = test_get_json(f"{SYSTEM_ADMIN_BASE}/analytics/dashboard", "Get analytics dashboard")
if success and isinstance(result, dict):
    has_overall = "overall_statistics" in result
    has_popular = "popular_sports" in result
    has_busiest = "busiest_days" in result
    log_test("System Admin: GET /analytics/dashboard", has_overall and has_popular and has_busiest,
             f"Has overall_stats: {has_overall}, popular_sports: {has_popular}, busiest_days: {has_busiest}")
else:
    log_test("System Admin: GET /analytics/dashboard", False, result if isinstance(result, str) else "Invalid response")

# Test 7: Get specific sport
if sports_data:
    sport_id = sports_data[0].get('sport_id')
    success, result = test_get_json(f"{SYSTEM_ADMIN_BASE}/sports/{sport_id}", f"Get sport {sport_id}")
    log_test(f"System Admin: GET /sports/{sport_id}", success, result if isinstance(result, str) else "Sport retrieved")

# Test 8: Get specific league
if leagues_data:
    league_id = leagues_data[0].get('league_id')
    success, result = test_get_json(f"{SYSTEM_ADMIN_BASE}/leagues/{league_id}", f"Get league {league_id}")
    log_test(f"System Admin: GET /leagues/{league_id}", success, result if isinstance(result, str) else "League retrieved")

# Test 9: Get league teams
if leagues_data:
    league_id = leagues_data[0].get('league_id')
    success, result = test_get_json(f"{SYSTEM_ADMIN_BASE}/leagues/{league_id}/teams", f"Get teams for league {league_id}")
    log_test(f"System Admin: GET /leagues/{league_id}/teams", success,
             result if isinstance(result, str) else f"Found {len(result)} teams")

# Test 10: Get league games
if leagues_data:
    league_id = leagues_data[0].get('league_id')
    success, result = test_get_json(f"{SYSTEM_ADMIN_BASE}/leagues/{league_id}/games", f"Get games for league {league_id}")
    log_test(f"System Admin: GET /leagues/{league_id}/games", success,
             result if isinstance(result, str) else f"Found {len(result)} games")

# Test 11: Get league champions
if leagues_data:
    league_id = leagues_data[0].get('league_id')
    success, result = test_get_json(f"{SYSTEM_ADMIN_BASE}/leagues/{league_id}/champions", f"Get champions for league {league_id}")
    log_test(f"System Admin: GET /leagues/{league_id}/champions", success,
             result if isinstance(result, str) else f"Found {len(result)} champions")

# Test 12: Get team details
if teams_data:
    team_id = teams_data[0].get('team_id')
    success, result = test_get_json(f"{SYSTEM_ADMIN_BASE}/teams/{team_id}", f"Get team {team_id}")
    log_test(f"System Admin: GET /teams/{team_id}", success, result if isinstance(result, str) else "Team retrieved")

# Test 13: Get team players
if teams_data:
    team_id = teams_data[0].get('team_id')
    success, result = test_get_json(f"{SYSTEM_ADMIN_BASE}/teams/{team_id}/players", f"Get players for team {team_id}")
    log_test(f"System Admin: GET /teams/{team_id}/players", success,
             result if isinstance(result, str) else f"Found {len(result)} players")

# Test 14: Get team games
if teams_data:
    team_id = teams_data[0].get('team_id')
    success, result = test_get_json(f"{SYSTEM_ADMIN_BASE}/teams/{team_id}/games", f"Get games for team {team_id}")
    log_test(f"System Admin: GET /teams/{team_id}/games", success,
             result if isinstance(result, str) else f"Found {len(result)} games")

# Test 15: Get team stats
if teams_data:
    team_id = teams_data[0].get('team_id')
    success, result = test_get_json(f"{SYSTEM_ADMIN_BASE}/teams/{team_id}/stats", f"Get stats for team {team_id}")
    log_test(f"System Admin: GET /teams/{team_id}/stats", success, result if isinstance(result, str) else "Stats retrieved")

# Test 16: Get player details
if players_data:
    player_id = players_data[0].get('player_id')
    success, result = test_get_json(f"{SYSTEM_ADMIN_BASE}/players/{player_id}", f"Get player {player_id}")
    log_test(f"System Admin: GET /players/{player_id}", success, result if isinstance(result, str) else "Player retrieved")

# Test 17: Get player teams
if players_data:
    player_id = players_data[0].get('player_id')
    success, result = test_get_json(f"{SYSTEM_ADMIN_BASE}/players/{player_id}/teams", f"Get teams for player {player_id}")
    log_test(f"System Admin: GET /players/{player_id}/teams", success,
             result if isinstance(result, str) else f"Found {len(result)} teams")

# Test 18: Get player games
if players_data:
    player_id = players_data[0].get('player_id')
    success, result = test_get_json(f"{SYSTEM_ADMIN_BASE}/players/{player_id}/games", f"Get games for player {player_id}")
    log_test(f"System Admin: GET /players/{player_id}/games", success,
             result if isinstance(result, str) else f"Found {len(result)} games")

# Test 19: Get player stats
if players_data:
    player_id = players_data[0].get('player_id')
    success, result = test_get_json(f"{SYSTEM_ADMIN_BASE}/players/{player_id}/stats", f"Get stats for player {player_id}")
    log_test(f"System Admin: GET /players/{player_id}/stats", success, result if isinstance(result, str) else "Stats retrieved")

# Test 20: Get game details
if games_data:
    game_id = games_data[0].get('game_id')
    success, result = test_get_json(f"{SYSTEM_ADMIN_BASE}/games/{game_id}", f"Get game {game_id}")
    log_test(f"System Admin: GET /games/{game_id}", success, result if isinstance(result, str) else "Game retrieved")

# ==================== PLAYER TESTS ====================
print("\n🏃 PLAYER TESTS")
print("-" * 80)

# Test 21: Get all players (Player endpoint)
success, result = test_get_json(f"{PLAYER_BASE}/players", "Get all players")
log_test("Player: GET /players", success, result if isinstance(result, str) else f"Found {len(result)} players")

# Test 22: Get player details
if players_data:
    player_id = players_data[0].get('player_id')
    success, result = test_get_json(f"{PLAYER_BASE}/players/{player_id}", f"Get player {player_id}")
    log_test(f"Player: GET /players/{player_id}", success, result if isinstance(result, str) else "Player retrieved")

# Test 23: Get player teams
if players_data:
    player_id = players_data[0].get('player_id')
    success, result = test_get_json(f"{PLAYER_BASE}/players/{player_id}/teams", f"Get teams for player {player_id}")
    log_test(f"Player: GET /players/{player_id}/teams", success,
             result if isinstance(result, str) else f"Found {len(result)} teams")

# Test 24: Get player games (upcoming)
if players_data:
    player_id = players_data[0].get('player_id')
    success, result = test_get_json(f"{PLAYER_BASE}/players/{player_id}/games?upcoming_only=true", f"Get upcoming games for player {player_id}")
    log_test(f"Player: GET /players/{player_id}/games (upcoming)", success,
             result if isinstance(result, str) else f"Found {len(result)} upcoming games")

# Test 25: Get player games (all)
if players_data:
    player_id = players_data[0].get('player_id')
    success, result = test_get_json(f"{PLAYER_BASE}/players/{player_id}/games", f"Get all games for player {player_id}")
    log_test(f"Player: GET /players/{player_id}/games (all)", success,
             result if isinstance(result, str) else f"Found {len(result)} games")

# Test 26: Get player stats
if players_data:
    player_id = players_data[0].get('player_id')
    success, result = test_get_json(f"{PLAYER_BASE}/players/{player_id}/stats", f"Get stats for player {player_id}")
    log_test(f"Player: GET /players/{player_id}/stats", success, result if isinstance(result, str) else "Stats retrieved")

# Test 27: Get game details
if games_data:
    game_id = games_data[0].get('game_id')
    success, result = test_get_json(f"{PLAYER_BASE}/games/{game_id}", f"Get game {game_id}")
    log_test(f"Player: GET /games/{game_id}", success, result if isinstance(result, str) else "Game retrieved")

# Test 28: Get league teams
if leagues_data:
    league_id = leagues_data[0].get('league_id')
    success, result = test_get_json(f"{PLAYER_BASE}/leagues/{league_id}/teams", f"Get teams for league {league_id}")
    log_test(f"Player: GET /leagues/{league_id}/teams", success,
             result if isinstance(result, str) else f"Found {len(result)} teams")

# Test 29: Get league games
if leagues_data:
    league_id = leagues_data[0].get('league_id')
    success, result = test_get_json(f"{PLAYER_BASE}/leagues/{league_id}/games", f"Get games for league {league_id}")
    log_test(f"Player: GET /leagues/{league_id}/games", success,
             result if isinstance(result, str) else f"Found {len(result)} games")

# Test 30: Get league standings
if leagues_data:
    league_id = leagues_data[0].get('league_id')
    success, result = test_get_json(f"{PLAYER_BASE}/leagues/{league_id}/standings", f"Get standings for league {league_id}")
    log_test(f"Player: GET /leagues/{league_id}/standings", success,
             result if isinstance(result, str) else f"Standings retrieved")

# Test 31: Get team details
if teams_data:
    team_id = teams_data[0].get('team_id')
    success, result = test_get_json(f"{PLAYER_BASE}/teams/{team_id}", f"Get team {team_id}")
    log_test(f"Player: GET /teams/{team_id}", success, result if isinstance(result, str) else "Team retrieved")

# Test 32: Get team players
if teams_data:
    team_id = teams_data[0].get('team_id')
    success, result = test_get_json(f"{PLAYER_BASE}/teams/{team_id}/players", f"Get players for team {team_id}")
    log_test(f"Player: GET /teams/{team_id}/players", success,
             result if isinstance(result, str) else f"Found {len(result)} players")

# Test 33: Get team games
if teams_data:
    team_id = teams_data[0].get('team_id')
    success, result = test_get_json(f"{PLAYER_BASE}/teams/{team_id}/games", f"Get games for team {team_id}")
    log_test(f"Player: GET /teams/{team_id}/games", success,
             result if isinstance(result, str) else f"Found {len(result)} games")

# Test 34: Get team stats
if teams_data:
    team_id = teams_data[0].get('team_id')
    success, result = test_get_json(f"{PLAYER_BASE}/teams/{team_id}/stats", f"Get stats for team {team_id}")
    log_test(f"Player: GET /teams/{team_id}/stats", success, result if isinstance(result, str) else "Stats retrieved")

# Test 35: Get league analytics
if leagues_data:
    league_id = leagues_data[0].get('league_id')
    success, result = test_get_json(f"{PLAYER_BASE}/analytics/leagues/{league_id}", f"Get analytics for league {league_id}")
    log_test(f"Player: GET /analytics/leagues/{league_id}", success, result if isinstance(result, str) else "Analytics retrieved")

# Test 36: Get player analytics
if players_data:
    player_id = players_data[0].get('player_id')
    success, result = test_get_json(f"{PLAYER_BASE}/analytics/players/{player_id}", f"Get analytics for player {player_id}")
    log_test(f"Player: GET /analytics/players/{player_id}", success, result if isinstance(result, str) else "Analytics retrieved")

# ==================== STAT KEEPER TESTS ====================
print("\n📝 STAT KEEPER TESTS")
print("-" * 80)

# Test 37: Get stat keeper games
success, result = test_get_json(f"{STAT_KEEPER_BASE}/stat-keepers/1/games", "Get games for stat keeper 1")
log_test("Stat Keeper: GET /stat-keepers/1/games", success,
         result if isinstance(result, str) else f"Found {len(result)} games")

# Test 38: Get game details
if games_data:
    game_id = games_data[0].get('game_id')
    success, result = test_get_json(f"{STAT_KEEPER_BASE}/games/{game_id}", f"Get game {game_id}")
    log_test(f"Stat Keeper: GET /games/{game_id}", success, result if isinstance(result, str) else "Game retrieved")

# Test 39: Get game players
if games_data:
    game_id = games_data[0].get('game_id')
    success, result = test_get_json(f"{STAT_KEEPER_BASE}/games/{game_id}/players", f"Get players for game {game_id}")
    log_test(f"Stat Keeper: GET /games/{game_id}/players", success,
             result if isinstance(result, str) else f"Found {len(result)} players")

# Test 40: Get game stat events
if games_data:
    game_id = games_data[0].get('game_id')
    success, result = test_get_json(f"{STAT_KEEPER_BASE}/games/{game_id}/stat-events", f"Get stat events for game {game_id}")
    log_test(f"Stat Keeper: GET /games/{game_id}/stat-events", success,
             result if isinstance(result, str) else f"Found {len(result)} stat events")

# Test 41: Get game summary
if games_data:
    game_id = games_data[0].get('game_id')
    success, result = test_get_json(f"{STAT_KEEPER_BASE}/games/{game_id}/summary", f"Get summary for game {game_id}")
    log_test(f"Stat Keeper: GET /games/{game_id}/summary", success, result if isinstance(result, str) else "Summary retrieved")

# ==================== TEAM CAPTAIN TESTS ====================
print("\n👔 TEAM CAPTAIN TESTS")
print("-" * 80)

# Test 42: Get team games
if teams_data:
    team_id = teams_data[0].get('team_id')
    success, result = test_get_json(f"{TEAM_CAPTAIN_BASE}/teams/{team_id}/games", f"Get games for team {team_id}")
    log_test(f"Team Captain: GET /teams/{team_id}/games", success,
             result if isinstance(result, str) else f"Found {len(result)} games")

# Test 43: Get team performance
if teams_data:
    team_id = teams_data[0].get('team_id')
    success, result = test_get_json(f"{TEAM_CAPTAIN_BASE}/teams/{team_id}/performance", f"Get performance for team {team_id}")
    log_test(f"Team Captain: GET /teams/{team_id}/performance", success, result if isinstance(result, str) else "Performance retrieved")

# Test 44: Get team summary
if teams_data:
    team_id = teams_data[0].get('team_id')
    success, result = test_get_json(f"{TEAM_CAPTAIN_BASE}/teams/{team_id}/summary", f"Get summary for team {team_id}")
    log_test(f"Team Captain: GET /teams/{team_id}/summary", success, result if isinstance(result, str) else "Summary retrieved")

# ==================== DATA CONSISTENCY TESTS ====================
print("\n🔗 DATA CONSISTENCY TESTS")
print("-" * 80)

# Test 45: Verify league-team relationships
if leagues_data and teams_data:
    league_id = leagues_data[0].get('league_id')
    success, league_teams = test_get_json(f"{SYSTEM_ADMIN_BASE}/leagues/{league_id}/teams")
    if success and isinstance(league_teams, list):
        team_ids_in_league = {t.get('team_id') for t in league_teams}
        all_team_ids = {t.get('team_id') for t in teams_data if t.get('league_played') == league_id}
        consistency = len(team_ids_in_league) == len(all_team_ids)
        log_test("Data Consistency: League-Team relationships", consistency,
                 f"League {league_id} has {len(team_ids_in_league)} teams")
    else:
        log_test("Data Consistency: League-Team relationships", False, "Could not verify")

# Test 46: Verify game-team relationships
if games_data and teams_data:
    game_id = games_data[0].get('game_id')
    success, game_data = test_get_json(f"{SYSTEM_ADMIN_BASE}/games/{game_id}")
    if success and isinstance(game_data, dict):
        has_home_team = 'home_team' in game_data or 'home_team_id' in game_data
        has_away_team = 'away_team' in game_data or 'away_team_id' in game_data
        log_test("Data Consistency: Game-Team relationships", has_home_team and has_away_team,
                 f"Game {game_id} has home and away teams")
    else:
        log_test("Data Consistency: Game-Team relationships", False, "Could not verify")

# ==================== SUMMARY ====================
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print(f"Total Tests: {len(passed_tests) + len(failed_tests)}")
print(f"✅ Passed: {len(passed_tests)}")
print(f"❌ Failed: {len(failed_tests)}")
print()

if failed_tests:
    print("FAILED TESTS:")
    print("-" * 80)
    for test_name, error in failed_tests:
        print(f"❌ {test_name}")
        print(f"   Error: {error}")
    print()

if len(failed_tests) == 0:
    print("🎉 All tests passed!")
    sys.exit(0)
else:
    print(f"⚠️  {len(failed_tests)} test(s) failed. Please review the errors above.")
    sys.exit(1)

