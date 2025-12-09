#!/usr/bin/env python3
"""
Script to improve data distribution for more realistic demo data.
- Ensures 80-90% of players are on teams
- Ensures each player on a team has 10-50 stat events across 2-5 games
- Uses realistic stat distributions
"""

import random
from datetime import datetime, timedelta

# Configuration
TARGET_PLAYER_TEAM_PERCENTAGE = 0.85  # 85% of players should be on teams
MIN_STATS_PER_PLAYER = 10
MAX_STATS_PER_PLAYER = 50
MIN_GAMES_PER_PLAYER = 2
MAX_GAMES_PER_PLAYER = 5

# Stat distributions (realistic ratios for basketball)
STAT_TYPES_BASKETBALL = {
    '2 pointer': 0.35,      # Most common scoring
    '3 pointer': 0.15,      # Less common
    'free throw': 0.10,     # Less common
    'rebound': 0.20,        # Common
    'assist': 0.12,         # Common
    'steal': 0.05,          # Less common
    'block': 0.03,          # Rare
}

STAT_TYPES_SOCCER = {
    'goal': 0.15,
    'assist': 0.20,
    'corner kick taken': 0.10,
    'free kick scored': 0.05,
    'penalty scored': 0.02,
    'yellow card given': 0.08,
    'red card given': 0.02,
    'offsides': 0.15,
    'shots on target': 0.23,
}

STAT_TYPES_VOLLEYBALL = {
    'kill': 0.25,
    'assist': 0.20,
    'ace': 0.10,
    'block': 0.15,
    'dig': 0.20,
    'failed serve': 0.10,
}

# Note: 'assist' is valid for all sports, 'block' is valid for basketball and volleyball

def get_stat_type_for_sport(sport_id):
    """Return stat types based on sport"""
    if sport_id == 1:  # Basketball
        return STAT_TYPES_BASKETBALL
    elif sport_id == 2:  # Soccer
        return STAT_TYPES_SOCCER
    elif sport_id == 3:  # Volleyball
        return STAT_TYPES_VOLLEYBALL
    else:
        return STAT_TYPES_BASKETBALL  # Default

def weighted_choice(choices):
    """Choose a stat type based on weighted probabilities"""
    r = random.random()
    cumulative = 0
    for stat_type, weight in choices.items():
        cumulative += weight
        if r <= cumulative:
            return stat_type
    return list(choices.keys())[0]  # Fallback

def parse_existing_data():
    """Parse existing SQL files to understand current state"""
    import re
    print("Parsing existing data...")
    
    # Build mappings
    league_to_sport = {}  # {league_id: sport_id}
    team_to_league = {}  # {team_id: league_id}
    player_to_teams = {}  # {player_id: [team_ids]} - players can be on multiple teams
    game_to_league = {}  # {game_id: league_id}
    games_by_league = {}  # {league_id: [game_ids]}
    
    # Parse leagues: league_id → sport_id
    # Format: values ('Name', sport_id, ...)
    try:
        with open('database-files/03_leagues.sql', 'r') as f:
            league_id = 1
            for line in f:
                if 'values (' in line.lower():
                    # Extract sport_played (2nd value after quoted string)
                    match = re.search(r"values\s*\(\s*'[^']+',\s*(\d+)", line, re.IGNORECASE)
                    if match:
                        sport_id = int(match.group(1))
                        league_to_sport[league_id] = sport_id
                        league_id += 1
    except Exception as e:
        print(f"  Warning: Could not parse leagues: {e}")
    
    # Parse teams: team_id → league_id
    # Format: values ('Name', league_id, wins, losses)
    try:
        with open('database-files/05_teams.sql', 'r') as f:
            team_id = 1
            for line in f:
                if 'values (' in line.lower():
                    # Extract league_played (2nd value after quoted string)
                    match = re.search(r"values\s*\(\s*'[^']+',\s*(\d+)", line, re.IGNORECASE)
                    if match:
                        league_id = int(match.group(1))
                        team_to_league[team_id] = league_id
                        team_id += 1
    except Exception as e:
        print(f"  Warning: Could not parse teams: {e}")
    
    # Parse existing team-player assignments: player_id → [team_ids]
    # Format: values (player_id, team_id, 'role')
    existing_assignments = set()
    try:
        with open('database-files/07_teams_players.sql', 'r') as f:
            for line in f:
                if 'values (' in line.lower():
                    match = re.search(r"values\s*\(\s*(\d+),\s*(\d+)", line, re.IGNORECASE)
                    if match:
                        player_id = int(match.group(1))
                        team_id = int(match.group(2))
                        existing_assignments.add(player_id)
                        if player_id not in player_to_teams:
                            player_to_teams[player_id] = []
                        player_to_teams[player_id].append(team_id)
    except Exception as e:
        print(f"  Warning: Could not parse teams_players: {e}")
    
    # Parse games: game_id → league_id
    # Format: values (league_id, 'date', ...)
    try:
        with open('database-files/06_games.sql', 'r') as f:
            game_id = 1
            for line in f:
                if 'values (' in line.lower():
                    # Extract league_played (1st value)
                    match = re.search(r"values\s*\(\s*(\d+),\s*'", line, re.IGNORECASE)
                    if match:
                        league_id = int(match.group(1))
                        game_to_league[game_id] = league_id
                        if league_id not in games_by_league:
                            games_by_league[league_id] = []
                        games_by_league[league_id].append(game_id)
                        game_id += 1
    except Exception as e:
        print(f"  Warning: Could not parse games: {e}")
    
    print(f"  Found {len(existing_assignments)} players already on teams")
    print(f"  Found {len(league_to_sport)} leagues")
    print(f"  Found {len(team_to_league)} teams")
    print(f"  Found {len(game_to_league)} games")
    
    return existing_assignments, league_to_sport, team_to_league, player_to_teams, game_to_league, games_by_league

def generate_improved_data():
    """Generate improved data distribution"""
    print("\nGenerating improved data distribution...")
    
    existing_assignments, league_to_sport, team_to_league, player_to_teams, game_to_league, games_by_league = parse_existing_data()
    
    # Build teams_by_league for assignment logic
    teams_by_league = {}
    for team_id, league_id in team_to_league.items():
        if league_id not in teams_by_league:
            teams_by_league[league_id] = []
        teams_by_league[league_id].append(team_id)
    
    # Assume we have 1000 players (IDs 1-1000)
    total_players = 1000
    target_assigned = int(total_players * TARGET_PLAYER_TEAM_PERCENTAGE)
    need_to_assign = max(0, target_assigned - len(existing_assignments))
    
    print(f"  Target: {target_assigned} players on teams")
    print(f"  Need to assign: {need_to_assign} more players")
    
    # Generate new team assignments
    new_assignments = []
    unassigned_players = [i for i in range(1, total_players + 1) if i not in existing_assignments]
    random.shuffle(unassigned_players)
    
    # Assign players to teams
    for i in range(min(need_to_assign, len(unassigned_players))):
        player_id = unassigned_players[i]
        # Choose a random league
        if teams_by_league:
            league_id = random.choice(list(teams_by_league.keys()))
            team_id = random.choice(teams_by_league[league_id])
            role = 'Captain' if random.random() < 0.1 else 'Player'  # 10% captains
            new_assignments.append((player_id, team_id, role))
            if player_id not in player_to_teams:
                player_to_teams[player_id] = []
            player_to_teams[player_id].append(team_id)
    
    # Generate stat events for players (both existing and new)
    all_assigned_players = list(existing_assignments) + [a[0] for a in new_assignments]
    new_stat_events = []
    player_game_combinations = set()  # Track (player_id, game_id) pairs for Players_Games
    
    print(f"\nGenerating stat events for {len(all_assigned_players)} players...")
    
    for player_id in all_assigned_players:
        # Get player's teams
        if player_id not in player_to_teams or not player_to_teams[player_id]:
            continue
        
        # For each team the player is on, generate stats
        for team_id in player_to_teams[player_id]:
            # Find team's league
            if team_id not in team_to_league:
                continue
            
            league_id = team_to_league[team_id]
            
            # Find league's sport
            if league_id not in league_to_sport:
                continue
            
            sport_id = league_to_sport[league_id]
            
            # Get stat types for this sport
            stat_types = get_stat_type_for_sport(sport_id)
            
            # Get games for this league ONLY
            if league_id not in games_by_league or not games_by_league[league_id]:
                continue
            
            available_games = games_by_league[league_id]
            
            # Verify games belong to this league (double-check)
            verified_games = [gid for gid in available_games if gid in game_to_league and game_to_league[gid] == league_id]
            
            if not verified_games:
                continue
            
            # Determine how many games this player played (2-5)
            num_games = random.randint(MIN_GAMES_PER_PLAYER, min(MAX_GAMES_PER_PLAYER, len(verified_games)))
            
            # Select random games for this player from their league
            player_games = random.sample(verified_games, num_games)
            
            # Track player-game combinations for Players_Games table
            for game_id in player_games:
                player_game_combinations.add((player_id, game_id))
            
            # Generate stats for each game
            total_stats = random.randint(MIN_STATS_PER_PLAYER, MAX_STATS_PER_PLAYER)
            stats_per_game = total_stats // num_games
            remainder = total_stats % num_games
            
            for game_idx, game_id in enumerate(player_games):
                game_stat_count = stats_per_game + (1 if game_idx < remainder else 0)
                
                # Get game's date from the games file (or generate reasonable date)
                base_date = datetime(2025, 11, 1) + timedelta(days=random.randint(0, 120))
                base_time = random.randint(10, 20)  # 10 AM to 8 PM
                
                for stat_idx in range(game_stat_count):
                    stat_type = weighted_choice(stat_types)
                    # Timestamp: spread across game duration
                    minutes_offset = random.randint(0, 80)
                    timestamp = base_date.replace(hour=base_time, minute=minutes_offset % 60, second=random.randint(0, 59))
                    
                    new_stat_events.append((player_id, game_id, stat_type, timestamp))
    
    print(f"  Generated {len(new_stat_events)} new stat events")
    print(f"  Generated {len(player_game_combinations)} player-game combinations for Players_Games")
    
    return new_assignments, new_stat_events, player_game_combinations

def write_sql_files(new_assignments, new_stat_events, player_game_combinations):
    """Write generated data to SQL files"""
    print("\nWriting SQL files...")
    
    # Write additional team-player assignments
    if new_assignments:
        with open('database-files/14_additional_teams_players.sql', 'w') as f:
            f.write("USE im_league_tracker;\n\n")
            f.write("-- Additional team-player assignments for better data distribution\n\n")
            for player_id, team_id, role in new_assignments:
                f.write(f"INSERT INTO Teams_Players (player_id, team_id, role) VALUES ({player_id}, {team_id}, '{role}');\n")
        print(f"  ✓ Wrote {len(new_assignments)} team-player assignments to 14_additional_teams_players.sql")
    
    # Write additional stat events
    if new_stat_events:
        with open('database-files/15_additional_stat_events.sql', 'w') as f:
            f.write("USE im_league_tracker;\n\n")
            f.write("-- Additional stat events for better data distribution\n\n")
            for player_id, game_id, stat_type, timestamp in new_stat_events:
                timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"INSERT INTO StatEvent (performed_by, scored_during, description, time_entered) VALUES ({player_id}, {game_id}, '{stat_type}', '{timestamp_str}');\n")
        print(f"  ✓ Wrote {len(new_stat_events)} stat events to 15_additional_stat_events.sql")
    
    # Write Players_Games entries (needed for Performance Over Time chart)
    if player_game_combinations:
        with open('database-files/16_additional_player_games.sql', 'w') as f:
            f.write("USE im_league_tracker;\n\n")
            f.write("-- Additional Players_Games entries for Performance Over Time chart\n\n")
            for player_id, game_id in sorted(player_game_combinations):
                f.write(f"INSERT INTO Players_Games (player_id, game_id) VALUES ({player_id}, {game_id});\n")
        print(f"  ✓ Wrote {len(player_game_combinations)} Players_Games entries to 16_additional_player_games.sql")

if __name__ == '__main__':
    import sys
    
    print("=" * 60)
    print("Data Distribution Improvement Script")
    print("=" * 60)
    
    try:
        new_assignments, new_stat_events, player_game_combinations = generate_improved_data()
        write_sql_files(new_assignments, new_stat_events, player_game_combinations)
        
        print("\n" + "=" * 60)
        print("✓ Successfully generated improved data distribution!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Review the generated SQL files:")
        print("   - database-files/14_additional_teams_players.sql")
        print("   - database-files/15_additional_stat_events.sql")
        print("   - database-files/16_additional_player_games.sql")
        print("2. Restart the database to apply changes:")
        print("   docker compose stop db")
        print("   docker compose rm -f db")
        print("   docker volume rm project-app-team-repo_mysql_data")
        print("   docker compose up db -d")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

