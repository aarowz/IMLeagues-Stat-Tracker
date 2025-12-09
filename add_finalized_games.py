#!/usr/bin/env python3
"""
Script to add finalized games for teams that don't have any performance data.
This ensures more teams have data for the Performance Over Time dashboard.
"""

import re
import random
from datetime import datetime, timedelta

def parse_existing_data():
    """Parse existing SQL files to understand current state"""
    print("Parsing existing data...")
    
    # Build mappings
    team_to_league = {}  # {team_id: league_id}
    league_to_sport = {}  # {league_id: sport_id}
    teams_with_finalized_games = set()  # Teams that already have finalized games
    
    # Parse teams: team_id → league_id
    try:
        with open('database-files/05_teams.sql', 'r') as f:
            team_id = 1
            for line in f:
                if 'values (' in line.lower():
                    match = re.search(r"values\s*\(\s*'[^']+',\s*(\d+)", line, re.IGNORECASE)
                    if match:
                        league_id = int(match.group(1))
                        team_to_league[team_id] = league_id
                        team_id += 1
    except Exception as e:
        print(f"  Warning: Could not parse teams: {e}")
    
    # Parse leagues: league_id → sport_id
    try:
        with open('database-files/03_leagues.sql', 'r') as f:
            league_id = 1
            for line in f:
                if 'values (' in line.lower():
                    match = re.search(r"values\s*\(\s*'[^']+',\s*(\d+)", line, re.IGNORECASE)
                    if match:
                        sport_id = int(match.group(1))
                        league_to_sport[league_id] = sport_id
                        league_id += 1
    except Exception as e:
        print(f"  Warning: Could not parse leagues: {e}")
    
    # Parse Teams_Games to find teams that already have games
    try:
        with open('database-files/09_team_games.sql', 'r') as f:
            for line in f:
                if 'INSERT INTO Teams_Games' in line.upper():
                    match = re.search(r"\((\d+),\s*(\d+),", line, re.IGNORECASE)
                    if match:
                        team_id = int(match.group(1))
                        game_id = int(match.group(2))
                        teams_with_finalized_games.add(team_id)
    except Exception as e:
        print(f"  Warning: Could not parse team_games: {e}")
    
    # Also check games with scores (finalized games)
    try:
        with open('database-files/06_games.sql', 'r') as f:
            finalized_game_ids = set()
            game_id = 1
            for line in f:
                if 'INSERT INTO Games' in line.upper() and 'home_score' in line.lower() and 'away_score' in line.lower():
                    # Check if scores are not NULL
                    match = re.search(r"home_score,\s*away_score\)\s*values\s*\([^,]+,\s*'[^']+',\s*'[^']+',\s*'[^']+',\s*(\d+),\s*(\d+)", line, re.IGNORECASE)
                    if match:
                        home_score = int(match.group(1))
                        away_score = int(match.group(2))
                        finalized_game_ids.add(game_id)
                    game_id += 1
            
            # Now find teams that have finalized games
            with open('database-files/09_team_games.sql', 'r') as f2:
                for line in f2:
                    if 'INSERT INTO Teams_Games' in line.upper():
                        match = re.search(r"\((\d+),\s*(\d+),", line, re.IGNORECASE)
                        if match:
                            team_id = int(match.group(1))
                            game_id = int(match.group(2))
                            if game_id in finalized_game_ids:
                                teams_with_finalized_games.add(team_id)
    except Exception as e:
        print(f"  Warning: Could not parse finalized games: {e}")
    
    print(f"  Found {len(team_to_league)} teams")
    print(f"  Found {len(teams_with_finalized_games)} teams with finalized games")
    
    return team_to_league, league_to_sport, teams_with_finalized_games

def get_sport_scoring_ranges(sport_id):
    """Get realistic scoring ranges based on sport"""
    if sport_id == 1:  # Basketball
        return (50, 150)  # Typical basketball scores
    elif sport_id == 2:  # Soccer
        return (0, 5)  # Typical soccer scores
    elif sport_id == 3:  # Volleyball
        return (15, 30)  # Typical volleyball set scores
    else:
        return (0, 100)  # Generic

def generate_finalized_games():
    """Generate finalized games for teams without any"""
    print("\nGenerating finalized games...")
    
    team_to_league, league_to_sport, teams_with_finalized_games = parse_existing_data()
    
    # Find teams without finalized games
    teams_needing_games = []
    for team_id, league_id in team_to_league.items():
        if team_id not in teams_with_finalized_games:
            teams_needing_games.append((team_id, league_id))
    
    print(f"  Found {len(teams_needing_games)} teams needing finalized games")
    
    if not teams_needing_games:
        print("  All teams already have finalized games!")
        return [], []
    
    # Group teams by league
    teams_by_league = {}
    for team_id, league_id in teams_needing_games:
        if league_id not in teams_by_league:
            teams_by_league[league_id] = []
        teams_by_league[league_id].append(team_id)
    
    # Generate games: each team gets 2-5 finalized games
    new_games = []
    new_team_games = []
    
    # Find the highest existing game_id
    max_game_id = 1000  # Start from a safe high number
    try:
        with open('database-files/06_games.sql', 'r') as f:
            for line in f:
                if 'INSERT INTO Games' in line.upper():
                    max_game_id += 1
    except:
        pass
    
    game_id = max_game_id + 1
    base_date = datetime(2025, 10, 1)
    
    locations = [
        'Marino Center Court 1', 'Marino Center Court 2', 'Marino Center Court 3',
        'Cabot Cage', 'Cabot Racketball Court', 'Carter Field'
    ]
    
    for league_id, team_list in teams_by_league.items():
        if league_id not in league_to_sport:
            continue
        
        sport_id = league_to_sport[league_id]
        score_min, score_max = get_sport_scoring_ranges(sport_id)
        
        # Create games by pairing teams
        random.shuffle(team_list)
        
        # Ensure each team gets at least 2 games
        for team_idx, team_id in enumerate(team_list):
            num_games = random.randint(2, 5)
            
            for game_num in range(num_games):
                # Find an opponent (another team in the same league)
                opponents = [t for t in team_list if t != team_id]
                if not opponents:
                    # If no opponents, create a game against a random team from another league
                    all_other_teams = [tid for tid, lid in team_to_league.items() if lid != league_id]
                    if all_other_teams:
                        opponent_id = random.choice(all_other_teams)
                    else:
                        continue
                else:
                    opponent_id = random.choice(opponents)
                
                # Generate game date (past dates)
                days_ago = random.randint(1, 120)
                game_date = base_date - timedelta(days=days_ago)
                
                # Generate scores
                home_score = random.randint(score_min, score_max)
                away_score = random.randint(score_min, score_max)
                
                # Ensure scores are different (no ties for simplicity)
                while home_score == away_score:
                    away_score = random.randint(score_min, score_max)
                
                # Random location and time
                location = random.choice(locations)
                hour = random.randint(10, 20)
                minute = random.choice([0, 15, 30, 45])
                start_time = f"{hour:02d}:{minute:02d}:00"
                
                # Determine home/away
                is_home = random.choice([True, False])
                
                new_games.append({
                    'game_id': game_id,
                    'league_id': league_id,
                    'date_played': game_date.strftime('%Y-%m-%d'),
                    'start_time': start_time,
                    'location': location,
                    'home_score': home_score if is_home else away_score,
                    'away_score': away_score if is_home else home_score
                })
                
                # Add Teams_Games entries
                new_team_games.append({
                    'team_id': team_id,
                    'game_id': game_id,
                    'is_home_team': is_home
                })
                new_team_games.append({
                    'team_id': opponent_id,
                    'game_id': game_id,
                    'is_home_team': not is_home
                })
                
                game_id += 1
    
    print(f"  Generated {len(new_games)} new finalized games")
    print(f"  Generated {len(new_team_games)} team-game associations")
    
    return new_games, new_team_games

def write_sql_files(new_games, new_team_games):
    """Write generated data to SQL files"""
    print("\nWriting SQL files...")
    
    if new_games:
        with open('database-files/17_additional_finalized_games.sql', 'w') as f:
            f.write("USE im_league_tracker;\n\n")
            f.write("-- Additional finalized games for teams without performance data\n\n")
            for game in new_games:
                f.write(f"INSERT INTO Games (league_played, date_played, start_time, location, home_score, away_score) VALUES ({game['league_id']}, '{game['date_played']}', '{game['start_time']}', '{game['location']}', {game['home_score']}, {game['away_score']});\n")
        print(f"  ✓ Wrote {len(new_games)} games to 17_additional_finalized_games.sql")
    
    if new_team_games:
        with open('database-files/18_additional_team_games_finalized.sql', 'w') as f:
            f.write("USE im_league_tracker;\n\n")
            f.write("-- Additional Teams_Games entries for finalized games\n\n")
            for tg in new_team_games:
                is_home = 'TRUE' if tg['is_home_team'] else 'FALSE'
                f.write(f"INSERT INTO Teams_Games (team_id, game_id, is_home_team) VALUES ({tg['team_id']}, {tg['game_id']}, {is_home});\n")
        print(f"  ✓ Wrote {len(new_team_games)} team-game associations to 18_additional_team_games_finalized.sql")

if __name__ == "__main__":
    print("=" * 60)
    print("Adding Finalized Games for Teams Without Performance Data")
    print("=" * 60)
    
    new_games, new_team_games = generate_finalized_games()
    
    if new_games:
        write_sql_files(new_games, new_team_games)
        print("\n✓ Successfully generated finalized games!")
        print("\nNext steps:")
        print("1. Review the generated SQL files")
        print("2. Restart the database container to load the new data")
        print("3. Teams should now have performance over time data")
    else:
        print("\n✓ No new games needed - all teams already have finalized games!")

