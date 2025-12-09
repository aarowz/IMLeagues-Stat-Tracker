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
    print("Parsing existing data...")
    
    # Read existing team-player assignments
    existing_assignments = set()
    try:
        with open('database-files/07_teams_players.sql', 'r') as f:
            for line in f:
                if 'player_id, team_id' in line.lower() or 'values (' in line:
                    # Extract player_id from line like: (801, 17, 'Player')
                    import re
                    match = re.search(r'\((\d+),\s*\d+', line)
                    if match:
                        existing_assignments.add(int(match.group(1)))
    except:
        pass
    
    # Read existing games and their leagues
    games_by_league = {}  # {league_id: [game_ids]}
    try:
        with open('database-files/06_games.sql', 'r') as f:
            for line in f:
                if 'league_played, date_played' in line.lower() or 'values (' in line:
                    import re
                    # Extract league_id and game_id
                    match = re.search(r'\((\d+),\s*\'[^\']+\',', line)
                    if match:
                        league_id = int(match.group(1))
                        # Try to find game_id (would need to track line numbers or parse differently)
                        # For now, we'll generate based on league_id
                        if league_id not in games_by_league:
                            games_by_league[league_id] = []
                        games_by_league[league_id].append(len(games_by_league[league_id]) + 1)
    except:
        pass
    
    # Read teams and their leagues
    teams_by_league = {}  # {league_id: [team_ids]}
    try:
        with open('database-files/05_teams.sql', 'r') as f:
            team_id = 1
            for line in f:
                if 'name, league_played' in line.lower() or 'values (' in line:
                    import re
                    # Extract league_id from line like: ('Team Name', 1, 4, 7)
                    match = re.search(r'\'[^\']+\',\s*(\d+)', line)
                    if match:
                        league_id = int(match.group(1))
                        if league_id not in teams_by_league:
                            teams_by_league[league_id] = []
                        teams_by_league[league_id].append(team_id)
                        team_id += 1
    except:
        pass
    
    print(f"  Found {len(existing_assignments)} players already on teams")
    print(f"  Found {len(teams_by_league)} leagues with teams")
    print(f"  Found {len(games_by_league)} leagues with games")
    
    return existing_assignments, teams_by_league, games_by_league

def generate_improved_data():
    """Generate improved data distribution"""
    print("\nGenerating improved data distribution...")
    
    existing_assignments, teams_by_league, games_by_league = parse_existing_data()
    
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
    
    # Generate stat events for players (both existing and new)
    all_assigned_players = list(existing_assignments) + [a[0] for a in new_assignments]
    new_stat_events = []
    
    print(f"\nGenerating stat events for {len(all_assigned_players)} players...")
    
    for player_id in all_assigned_players:
        # Determine which team/league this player is in
        # For simplicity, assign to league 1 (basketball) if we can't determine
        league_id = 1
        sport_id = 1  # Basketball
        
        # Find player's team
        player_team_id = None
        for pid, tid, _ in new_assignments:
            if pid == player_id:
                player_team_id = tid
                break
        
        # If we can't find team, skip (player might be in existing data)
        if not player_team_id and player_id not in existing_assignments:
            continue
        
        # Get stat types for this sport
        stat_types = get_stat_type_for_sport(sport_id)
        
        # Determine how many games this player played (2-5)
        num_games = random.randint(MIN_GAMES_PER_PLAYER, MAX_GAMES_PER_PLAYER)
        
        # Get games for this league
        if league_id in games_by_league and games_by_league[league_id]:
            available_games = games_by_league[league_id]
        else:
            # Generate game IDs (assume games 1-1000 exist)
            available_games = list(range(1, min(1001, 1000)))
        
        if not available_games:
            continue
        
        # Select random games for this player
        player_games = random.sample(available_games, min(num_games, len(available_games)))
        
        # Generate stats for each game
        total_stats = random.randint(MIN_STATS_PER_PLAYER, MAX_STATS_PER_PLAYER)
        stats_per_game = total_stats // num_games
        remainder = total_stats % num_games
        
        for game_idx, game_id in enumerate(player_games):
            game_stat_count = stats_per_game + (1 if game_idx < remainder else 0)
            
            # Generate base timestamp for this game (spread across game duration)
            base_date = datetime(2025, 11, 1) + timedelta(days=random.randint(0, 120))
            base_time = random.randint(10, 20)  # 10 AM to 8 PM
            
            for stat_idx in range(game_stat_count):
                stat_type = weighted_choice(stat_types)
                # Timestamp: spread across 40-90 minutes (game duration)
                minutes_offset = random.randint(0, 80)
                timestamp = base_date.replace(hour=base_time, minute=minutes_offset % 60, second=random.randint(0, 59))
                
                new_stat_events.append((player_id, game_id, stat_type, timestamp))
    
    print(f"  Generated {len(new_stat_events)} new stat events")
    
    return new_assignments, new_stat_events

def write_sql_files(new_assignments, new_stat_events):
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

if __name__ == '__main__':
    import sys
    
    print("=" * 60)
    print("Data Distribution Improvement Script")
    print("=" * 60)
    
    try:
        new_assignments, new_stat_events = generate_improved_data()
        write_sql_files(new_assignments, new_stat_events)
        
        print("\n" + "=" * 60)
        print("✓ Successfully generated improved data distribution!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Review the generated SQL files:")
        print("   - database-files/14_additional_teams_players.sql")
        print("   - database-files/15_additional_stat_events.sql")
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

