from flask import Blueprint, jsonify, request
from backend.db_connection import db
from mysql.connector import Error
from datetime import datetime, timedelta, date, time

stat_keeper = Blueprint("stat_keeper", __name__)


def calculate_points_from_description(description, sport_name):
    """Calculate points from a stat event description based on sport type"""
    description_lower = description.lower()
    points = 0
    
    # Basketball scoring
    if 'basketball' in sport_name.lower():
        if '3 points' in description_lower or '3-point' in description_lower or 'three point' in description_lower:
            points = 3
        elif '2 points' in description_lower or '2-point' in description_lower or 'two point' in description_lower:
            points = 2
        elif '1 point' in description_lower or 'free throw' in description_lower or 'one point' in description_lower:
            points = 1
        elif 'point' in description_lower and ('3' in description_lower or 'three' in description_lower):
            points = 3
        elif 'point' in description_lower and ('2' in description_lower or 'two' in description_lower):
            points = 2
        elif 'point' in description_lower:
            points = 1  # Default to 1 point if just "point" is mentioned
    
    # Soccer/Football scoring
    elif 'soccer' in sport_name.lower() or 'football' in sport_name.lower():
        if 'goal' in description_lower or 'penalty' in description_lower:
            points = 1
    
    # Volleyball scoring
    elif 'volleyball' in sport_name.lower():
        if 'point' in description_lower:
            points = 1
    
    # Generic scoring (for other sports)
    else:
        if 'goal' in description_lower:
            points = 1
        elif 'point' in description_lower:
            # Try to extract number from description
            import re
            point_match = re.search(r'(\d+)\s*point', description_lower)
            if point_match:
                points = int(point_match.group(1))
            else:
                points = 1  # Default to 1 point
    
    return points


def recalculate_game_score(cursor, game_id):
    """Recalculate game score from all stat events"""
    import logging
    logger = logging.getLogger(__name__)
    
    # Get game info and all teams playing in this game
    cursor.execute("""
        SELECT g.home_score, g.away_score, s.name AS sport_name
        FROM Games g
        JOIN Leagues l ON g.league_played = l.league_id
        JOIN Sports s ON l.sport_played = s.sport_id
        WHERE g.game_id = %s
    """, (game_id,))
    
    game_data = cursor.fetchone()
    if not game_data:
        return False
    
    sport_name = game_data.get('sport_name', '')
    
    # Get all teams playing in this game (home and away)
    cursor.execute("""
        SELECT team_id, is_home_team
        FROM Teams_Games
        WHERE game_id = %s
    """, (game_id,))
    
    teams_in_game = cursor.fetchall()
    if not teams_in_game:
        return False
    
    # Separate home and away teams (games can have multiple teams, but we track home_score/away_score)
    home_team_ids = [t['team_id'] for t in teams_in_game if t.get('is_home_team')]
    away_team_ids = [t['team_id'] for t in teams_in_game if not t.get('is_home_team')]
    
    # For score calculation, use first home/away team if multiple exist
    home_team_id = home_team_ids[0] if home_team_ids else None
    away_team_id = away_team_ids[0] if away_team_ids else None
    
    if not home_team_id or not away_team_id:
        return False
    
    # Get all stat events for this game
    cursor.execute("""
        SELECT se.description, se.performed_by, se.event_id
        FROM StatEvent se
        WHERE se.scored_during = %s
        ORDER BY se.time_entered ASC
    """, (game_id,))
    
    stat_events = cursor.fetchall()
    logger.info(f"Recalculating score for game {game_id}: Found {len(stat_events)} stat events")
    
    # Calculate scores - start from 0 and add all points from stat events
    home_score = 0
    away_score = 0
    
    for event in stat_events:
        points = calculate_points_from_description(event['description'], sport_name)
        player_id = event.get('performed_by')
        
        if points > 0 and player_id:
            # First try: Find team using Teams_Games (team must be in this game)
            cursor.execute("""
                SELECT tp.team_id
                FROM Players p
                JOIN Teams_Players tp ON p.player_id = tp.player_id
                JOIN Teams_Games tg ON tp.team_id = tg.team_id
                WHERE p.player_id = %s AND tg.game_id = %s
                LIMIT 1
            """, (player_id, game_id))
            
            player_team = cursor.fetchone()
            team_id = None
            
            if player_team:
                team_id = player_team['team_id']
            else:
                # Fallback: Find player's team from Teams_Players, then check if it's in the game
                cursor.execute("""
                    SELECT tp.team_id
                    FROM Players p
                    JOIN Teams_Players tp ON p.player_id = tp.player_id
                    WHERE p.player_id = %s
                    LIMIT 1
                """, (player_id,))
                
                fallback_team = cursor.fetchone()
                if fallback_team:
                    fallback_team_id = fallback_team['team_id']
                    # Check if this team is playing in the game
                    if fallback_team_id in [t['team_id'] for t in teams_in_game]:
                        team_id = fallback_team_id
            
            if team_id:
                # Check if team is home or away (handle multiple teams)
                if team_id in home_team_ids:
                    home_score += points
                    logger.debug(f"Event {event.get('event_id')}: Added {points} to home team (player {player_id}, team {team_id})")
                elif team_id in away_team_ids:
                    away_score += points
                    logger.debug(f"Event {event.get('event_id')}: Added {points} to away team (player {player_id}, team {team_id})")
                else:
                    logger.warning(f"Event {event.get('event_id')}: Player {player_id} team {team_id} is in game but not classified as home/away")
            else:
                logger.warning(f"Event {event.get('event_id')}: Could not find team for player {player_id} in game {game_id} - event skipped")
        elif points == 0:
            logger.debug(f"Event {event.get('event_id')}: No points calculated from description '{event.get('description')}'")
    
    logger.info(f"Final calculated scores: Home={home_score}, Away={away_score}")
    
    # Update game scores - this recalculates from ALL stat events, so it's cumulative
    cursor.execute("UPDATE Games SET home_score = %s, away_score = %s WHERE game_id = %s", 
                   (home_score, away_score, game_id))
    
    return True


def convert_datetime_for_json(data):
    if isinstance(data, list):
        for item in data:
            convert_datetime_for_json(item)
    elif isinstance(data, dict):
        for key, value in data.items():
            if value is None:
                continue
            elif isinstance(value, timedelta):
                total_seconds = int(value.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                data[key] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            elif isinstance(value, time):
                data[key] = value.strftime('%H:%M:%S')
            elif isinstance(value, date):
                data[key] = value.isoformat()
            elif isinstance(value, datetime):
                data[key] = value.isoformat()
    return data


@stat_keeper.route("/stat-keepers/<int:keeper_id>/games", methods=["GET"])
def get_stat_keeper_games(keeper_id):
    try:
        cursor = db.get_db().cursor()
        
        # First check if stat keeper exists
        cursor.execute("SELECT keeper_id FROM Stat_Keepers WHERE keeper_id = %s", (keeper_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Stat keeper not found"}), 404
        
        # Check if is_finalized column exists
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'Games' 
            AND COLUMN_NAME = 'is_finalized'
        """)
        result = cursor.fetchone()
        has_finalized_column = False
        if result:
            # Handle both tuple and dict cursor types
            count = result[0] if isinstance(result, tuple) else result.get('COUNT(*)', 0)
            has_finalized_column = count > 0
        
        # Get parameters from query string
        upcoming_only = request.args.get("upcoming_only", "false").lower() == "true"
        all_games = request.args.get("all", "false").lower() == "true"
        
        # Build query with or without is_finalized column
        if has_finalized_column:
            finalized_select = "COALESCE(g.is_finalized, FALSE) AS is_finalized,"
            finalized_filter_upcoming = "AND COALESCE(g.is_finalized, FALSE) = FALSE"
            finalized_filter_past = "OR COALESCE(g.is_finalized, FALSE) = TRUE"
        else:
            finalized_select = "FALSE AS is_finalized,"
            finalized_filter_upcoming = ""
            finalized_filter_past = ""
        
        query = f"""
        SELECT g.game_id, g.date_played, g.start_time, g.location,
               g.home_score, g.away_score, g.league_played,
               {finalized_select}
               (SELECT t.name FROM Teams_Games tg 
                JOIN Teams t ON tg.team_id = t.team_id 
                WHERE tg.game_id = g.game_id AND tg.is_home_team = TRUE 
                LIMIT 1) AS home_team,
               (SELECT t.team_id FROM Teams_Games tg 
                JOIN Teams t ON tg.team_id = t.team_id 
                WHERE tg.game_id = g.game_id AND tg.is_home_team = TRUE 
                LIMIT 1) AS home_team_id,
               (SELECT t.name FROM Teams_Games tg 
                JOIN Teams t ON tg.team_id = t.team_id 
                WHERE tg.game_id = g.game_id AND tg.is_home_team = FALSE 
                LIMIT 1) AS away_team,
               (SELECT t.team_id FROM Teams_Games tg 
                JOIN Teams t ON tg.team_id = t.team_id 
                WHERE tg.game_id = g.game_id AND tg.is_home_team = FALSE 
                LIMIT 1) AS away_team_id,
               l.name AS league_name, s.name AS sport_name,
               gk.assignment_date,
               (EXISTS(SELECT 1 FROM Teams_Games tg 
                       JOIN Teams t ON tg.team_id = t.team_id 
                       WHERE tg.game_id = g.game_id AND tg.is_home_team = TRUE)
                AND EXISTS(SELECT 1 FROM Teams_Games tg 
                          JOIN Teams t ON tg.team_id = t.team_id 
                          WHERE tg.game_id = g.game_id AND tg.is_home_team = FALSE)) AS has_both_teams
        FROM Games_Keepers gk
        JOIN Games g ON gk.game_id = g.game_id
        JOIN Leagues l ON g.league_played = l.league_id
        JOIN Sports s ON l.sport_played = s.sport_id
        WHERE gk.keeper_id = %s
        """
        
        params = [keeper_id]
        
        # Add filtering based on parameters
        if all_games:
            # Return all games, no filtering
            query += " ORDER BY has_both_teams DESC, g.date_played DESC, g.start_time DESC"
        elif upcoming_only:
            # Upcoming: games on or after today that are NOT finalized
            # Finalized games should appear in past games, not upcoming
            query += " AND DATE(g.date_played) >= DATE(CURDATE())"
            if finalized_filter_upcoming:
                query += f" {finalized_filter_upcoming}"
            query += " ORDER BY g.date_played ASC, g.start_time ASC"  # Soonest games first
        else:
            # Past: games before today OR finalized games (regardless of date)
            if finalized_filter_past:
                query += f" AND (DATE(g.date_played) < DATE(CURDATE()) {finalized_filter_past})"
            else:
                query += " AND DATE(g.date_played) < DATE(CURDATE())"
            query += " ORDER BY g.date_played DESC, g.start_time DESC"  # Most recent games first
        
        cursor.execute(query, params)
        games = cursor.fetchall()
        cursor.close()
        
        games = convert_datetime_for_json(games)
        
        return jsonify(games), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@stat_keeper.route("/games/<int:game_id>", methods=["GET"])
def get_game(game_id):
    try:
        cursor = db.get_db().cursor()
        
        # Check if is_finalized column exists
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'Games' 
            AND COLUMN_NAME = 'is_finalized'
        """)
        result = cursor.fetchone()
        has_finalized_column = False
        if result:
            # Handle both tuple and dict cursor types
            count = result[0] if isinstance(result, tuple) else result.get('COUNT(*)', 0)
            has_finalized_column = count > 0
        
        finalized_select = "COALESCE(g.is_finalized, FALSE) AS is_finalized," if has_finalized_column else "FALSE AS is_finalized,"
        
        query = f"""
        SELECT g.game_id, g.date_played, g.start_time, g.location, 
               g.home_score, g.away_score, g.league_played,
               {finalized_select}
               (SELECT t.name FROM Teams_Games tg 
                JOIN Teams t ON tg.team_id = t.team_id 
                WHERE tg.game_id = g.game_id AND tg.is_home_team = TRUE 
                LIMIT 1) AS home_team,
               (SELECT t.team_id FROM Teams_Games tg 
                JOIN Teams t ON tg.team_id = t.team_id 
                WHERE tg.game_id = g.game_id AND tg.is_home_team = TRUE 
                LIMIT 1) AS home_team_id,
               (SELECT t.name FROM Teams_Games tg 
                JOIN Teams t ON tg.team_id = t.team_id 
                WHERE tg.game_id = g.game_id AND tg.is_home_team = FALSE 
                LIMIT 1) AS away_team,
               (SELECT t.team_id FROM Teams_Games tg 
                JOIN Teams t ON tg.team_id = t.team_id 
                WHERE tg.game_id = g.game_id AND tg.is_home_team = FALSE 
                LIMIT 1) AS away_team_id,
               l.name AS league_name, s.name AS sport_name
        FROM Games g
        JOIN Leagues l ON g.league_played = l.league_id
        JOIN Sports s ON l.sport_played = s.sport_id
        WHERE g.game_id = %s
        """
        
        cursor.execute(query, (game_id,))
        game = cursor.fetchone()
        cursor.close()
        
        if not game:
            return jsonify({"error": "Game not found"}), 404
        
        game = convert_datetime_for_json(game)
        
        return jsonify(game), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@stat_keeper.route("/games/<int:game_id>/players", methods=["GET"])
def get_game_players(game_id):
    try:
        cursor = db.get_db().cursor()
        
        # First check if game exists
        cursor.execute("SELECT game_id FROM Games WHERE game_id = %s", (game_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Game not found"}), 404
        
        query = """
        SELECT p.player_id, p.first_name, p.last_name, p.email,
               pg.is_starter, pg.position,
               t.team_id, t.name AS team_name
        FROM Players_Games pg
        JOIN Players p ON pg.player_id = p.player_id
        JOIN Teams_Players tp ON p.player_id = tp.player_id
        JOIN Teams t ON tp.team_id = t.team_id
        JOIN Teams_Games tg ON t.team_id = tg.team_id
        WHERE pg.game_id = %s AND tg.game_id = %s
        ORDER BY t.name, pg.is_starter DESC, p.last_name
        """
        
        cursor.execute(query, (game_id, game_id))
        players = cursor.fetchall()
        cursor.close()
        
        players = convert_datetime_for_json(players)
        
        return jsonify(players), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@stat_keeper.route("/games/<int:game_id>/stat-events", methods=["GET"])
def get_game_stat_events(game_id):
    try:
        cursor = db.get_db().cursor()
        
        # First check if game exists
        cursor.execute("SELECT game_id FROM Games WHERE game_id = %s", (game_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Game not found"}), 404
        
        query = """
        SELECT se.event_id, se.performed_by, se.description, se.time_entered,
               p.first_name, p.last_name, p.player_id,
               MIN(t.name) AS team_name, MIN(t.team_id) AS team_id
        FROM StatEvent se
        JOIN Players p ON se.performed_by = p.player_id
        JOIN Teams_Players tp ON p.player_id = tp.player_id
        JOIN Teams_Games tg ON tp.team_id = tg.team_id
        JOIN Teams t ON tp.team_id = t.team_id
        WHERE se.scored_during = %s AND tg.game_id = %s
        GROUP BY se.event_id, se.performed_by, se.description, se.time_entered,
                 p.first_name, p.last_name, p.player_id
        ORDER BY se.time_entered ASC
        """
        
        cursor.execute(query, (game_id, game_id))
        stat_events = cursor.fetchall()
        cursor.close()
        
        stat_events = convert_datetime_for_json(stat_events)
        
        return jsonify(stat_events), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@stat_keeper.route("/games/<int:game_id>/summary", methods=["GET"])
def get_game_summary(game_id):
    try:
        cursor = db.get_db().cursor()
        
        # Get game details
        game_query = """
        SELECT g.game_id, g.date_played, g.start_time, g.location,
               g.home_score, g.away_score, g.league_played,
               (SELECT t.name FROM Teams_Games tg 
                JOIN Teams t ON tg.team_id = t.team_id 
                WHERE tg.game_id = g.game_id AND tg.is_home_team = TRUE 
                LIMIT 1) AS home_team,
               (SELECT t.team_id FROM Teams_Games tg 
                JOIN Teams t ON tg.team_id = t.team_id 
                WHERE tg.game_id = g.game_id AND tg.is_home_team = TRUE 
                LIMIT 1) AS home_team_id,
               (SELECT t.name FROM Teams_Games tg 
                JOIN Teams t ON tg.team_id = t.team_id 
                WHERE tg.game_id = g.game_id AND tg.is_home_team = FALSE 
                LIMIT 1) AS away_team,
               (SELECT t.team_id FROM Teams_Games tg 
                JOIN Teams t ON tg.team_id = t.team_id 
                WHERE tg.game_id = g.game_id AND tg.is_home_team = FALSE 
                LIMIT 1) AS away_team_id,
               l.name AS league_name, s.name AS sport_name
        FROM Games g
        JOIN Leagues l ON g.league_played = l.league_id
        JOIN Sports s ON l.sport_played = s.sport_id
        WHERE g.game_id = %s
        """
        
        cursor.execute(game_query, (game_id,))
        game = cursor.fetchone()
        
        if not game:
            cursor.close()
            return jsonify({"error": "Game not found"}), 404
        
        # Get team totals and individual leaders
        home_team_stats_query = """
        SELECT p.player_id, p.first_name, p.last_name,
               COUNT(se.event_id) AS total_stat_events
        FROM Players p
        JOIN Teams_Players tp ON p.player_id = tp.player_id
        LEFT JOIN StatEvent se ON p.player_id = se.performed_by AND se.scored_during = %s
        WHERE tp.team_id = %s
        GROUP BY p.player_id, p.first_name, p.last_name
        ORDER BY total_stat_events DESC
        LIMIT 5
        """
        
        away_team_stats_query = """
        SELECT p.player_id, p.first_name, p.last_name,
               COUNT(se.event_id) AS total_stat_events
        FROM Players p
        JOIN Teams_Players tp ON p.player_id = tp.player_id
        LEFT JOIN StatEvent se ON p.player_id = se.performed_by AND se.scored_during = %s
        WHERE tp.team_id = %s
        GROUP BY p.player_id, p.first_name, p.last_name
        ORDER BY total_stat_events DESC
        LIMIT 5
        """
        
        cursor.execute(home_team_stats_query, (game_id, game["home_team_id"]))
        home_team_leaders = cursor.fetchall()
        
        cursor.execute(away_team_stats_query, (game_id, game["away_team_id"]))
        away_team_leaders = cursor.fetchall()
        
        # Get total stat events per team
        team_totals_query = """
        SELECT 
            SUM(tp.team_id = %s) AS home_team_stat_count,
            SUM(tp.team_id = %s) AS away_team_stat_count
        FROM StatEvent se
        JOIN Players p ON se.performed_by = p.player_id
        JOIN Teams_Players tp ON p.player_id = tp.player_id
        WHERE se.scored_during = %s AND (tp.team_id = %s OR tp.team_id = %s)
        """
        
        cursor.execute(team_totals_query, (
            game["home_team_id"], game["away_team_id"], 
            game_id, game["home_team_id"], game["away_team_id"]
        ))
        team_totals = cursor.fetchone()
        
        cursor.close()
        
        game = convert_datetime_for_json(game)
        home_team_leaders = convert_datetime_for_json(home_team_leaders)
        away_team_leaders = convert_datetime_for_json(away_team_leaders)
        team_totals = convert_datetime_for_json(team_totals)
        
        result = {
            "game": game,
            "team_totals": team_totals,
            "home_team_leaders": home_team_leaders,
            "away_team_leaders": away_team_leaders
        }
        
        return jsonify(result), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@stat_keeper.route("/games/<int:game_id>/stat-events", methods=["POST"])
def create_stat_event(game_id):
    try:
        data = request.get_json()
        
        cursor = db.get_db().cursor()
        
        # Check if game exists and get current scores and team info
        cursor.execute("""
            SELECT g.home_score, g.away_score,
                   (SELECT tg.team_id FROM Teams_Games tg 
                    WHERE tg.game_id = g.game_id AND tg.is_home_team = TRUE LIMIT 1) AS home_team_id,
                   (SELECT tg.team_id FROM Teams_Games tg 
                    WHERE tg.game_id = g.game_id AND tg.is_home_team = FALSE LIMIT 1) AS away_team_id,
                   s.name AS sport_name
            FROM Games g
            JOIN Leagues l ON g.league_played = l.league_id
            JOIN Sports s ON l.sport_played = s.sport_id
            WHERE g.game_id = %s
        """, (game_id,))
        
        game_data = cursor.fetchone()
        if not game_data:
            cursor.close()
            return jsonify({"error": "Game not found"}), 404
        
        # Validate required fields
        if "performed_by" not in data or "description" not in data:
            cursor.close()
            return jsonify({"error": "Missing required fields: performed_by, description"}), 400
        
        # Check if player exists and get their team (must be playing in this game)
        cursor.execute("""
            SELECT tp.team_id, tg.is_home_team
            FROM Players p
            JOIN Teams_Players tp ON p.player_id = tp.player_id
            JOIN Teams_Games tg ON tp.team_id = tg.team_id
            WHERE p.player_id = %s AND tg.game_id = %s
            LIMIT 1
        """, (data["performed_by"], game_id))
        
        player_team = cursor.fetchone()
        if not player_team:
            cursor.close()
            # Get player name for better error message
            cursor = db.get_db().cursor()
            cursor.execute("SELECT first_name, last_name FROM Players WHERE player_id = %s", (data["performed_by"],))
            player_info = cursor.fetchone()
            player_name = f"{player_info['first_name']} {player_info['last_name']}" if player_info else f"Player ID {data['performed_by']}"
            cursor.close()
            return jsonify({
                "error": f"Player {player_name} is not on a team playing in this game. Players must be on a team that is participating in the game to record stats."
            }), 404
        
        player_team_id = player_team['team_id']
        home_team_id = game_data.get('home_team_id')
        away_team_id = game_data.get('away_team_id')
        sport_name = game_data.get('sport_name', '').lower()
        
        # Insert stat event
        insert_query = """
        INSERT INTO StatEvent (performed_by, scored_during, description, time_entered)
        VALUES (%s, %s, %s, NOW())
        """
        
        cursor.execute(insert_query, (
            data["performed_by"],
            game_id,
            data["description"]
        ))
        
        db.get_db().commit()
        event_id = cursor.lastrowid
        
        # Calculate points from description
        points = calculate_points_from_description(data["description"], sport_name)
        
        # Recalculate game score from all stat events (including the new one)
        recalculate_game_score(cursor, game_id)
        
        db.get_db().commit()
        cursor.close()
        
        return jsonify({
            "message": "Stat event created successfully",
            "event_id": event_id,
            "points_added": points if points > 0 else None
        }), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500


@stat_keeper.route("/games/<int:game_id>", methods=["PUT"])
def update_game(game_id):
    try:
        data = request.get_json()
        
        cursor = db.get_db().cursor()
        
        # Check if game exists and get current scores and team IDs
        cursor.execute("""
            SELECT g.home_score, g.away_score,
                   (SELECT tg.team_id FROM Teams_Games tg 
                    WHERE tg.game_id = g.game_id AND tg.is_home_team = TRUE LIMIT 1) AS home_team_id,
                   (SELECT tg.team_id FROM Teams_Games tg 
                    WHERE tg.game_id = g.game_id AND tg.is_home_team = FALSE LIMIT 1) AS away_team_id
            FROM Games g
            WHERE g.game_id = %s
        """, (game_id,))
        
        game_data = cursor.fetchone()
        if not game_data:
            cursor.close()
            return jsonify({"error": "Game not found"}), 404
        
        # Handle both tuple and dict cursor types
        if isinstance(game_data, tuple):
            old_home_score = game_data[0] if len(game_data) > 0 else None
            old_away_score = game_data[1] if len(game_data) > 1 else None
            home_team_id = game_data[2] if len(game_data) > 2 else None
            away_team_id = game_data[3] if len(game_data) > 3 else None
        else:
            old_home_score = game_data.get('home_score')
            old_away_score = game_data.get('away_score')
            home_team_id = game_data.get('home_team_id')
            away_team_id = game_data.get('away_team_id')
        
        # Build update query dynamically based on provided fields
        update_fields = []
        params = []
        
        if "home_score" in data:
            update_fields.append("home_score = %s")
            params.append(data["home_score"])
        
        if "away_score" in data:
            update_fields.append("away_score = %s")
            params.append(data["away_score"])
        
        if "date_played" in data:
            update_fields.append("date_played = %s")
            params.append(data["date_played"])
        
        if "start_time" in data:
            update_fields.append("start_time = %s")
            params.append(data["start_time"])
        
        if "location" in data:
            update_fields.append("location = %s")
            params.append(data["location"])
        
        # Handle finalization flag - if is_finalized is True, mark game as finalized
        # First check if column exists
        if "is_finalized" in data:
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'Games' 
                AND COLUMN_NAME = 'is_finalized'
            """)
            result = cursor.fetchone()
            has_finalized_column = False
            if result:
                count = result[0] if isinstance(result, tuple) else result.get('COUNT(*)', 0)
                has_finalized_column = count > 0
            
            if has_finalized_column:
                update_fields.append("is_finalized = %s")
                params.append(data["is_finalized"])
            # If column doesn't exist, silently skip (column will be added when DB is recreated)
        # If scores are being set and not explicitly setting is_finalized, check if we should auto-finalize
        elif "home_score" in data and "away_score" in data:
            # If both scores are provided and non-zero, this is likely a finalization
            if data.get("home_score") is not None and data.get("away_score") is not None:
                # Check if this is coming from the finalize button (we'll set is_finalized in frontend)
                # For now, don't auto-finalize - let frontend explicitly set it
                pass
        
        if not update_fields:
            cursor.close()
            return jsonify({"error": "No fields to update"}), 400
        
        params.append(game_id)
        
        update_query = f"""
        UPDATE Games
        SET {', '.join(update_fields)}
        WHERE game_id = %s
        """
        
        cursor.execute(update_query, params)
        
        # Update team wins/losses if scores are being updated and teams exist
        if ("home_score" in data or "away_score" in data) and home_team_id and away_team_id:
            new_home_score = data.get("home_score", old_home_score)
            new_away_score = data.get("away_score", old_away_score)
            
            # Only proceed if new scores are valid
            if new_home_score is not None and new_away_score is not None:
                # If old scores existed, reverse the old result first
                if old_home_score is not None and old_away_score is not None:
                    # Reverse old result
                    if old_home_score > old_away_score:
                        cursor.execute("UPDATE Teams SET wins = wins - 1 WHERE team_id = %s", (home_team_id,))
                        cursor.execute("UPDATE Teams SET losses = losses - 1 WHERE team_id = %s", (away_team_id,))
                    elif old_away_score > old_home_score:
                        cursor.execute("UPDATE Teams SET wins = wins - 1 WHERE team_id = %s", (away_team_id,))
                        cursor.execute("UPDATE Teams SET losses = losses - 1 WHERE team_id = %s", (home_team_id,))
                    # If old was a tie, nothing to reverse
                
                # Apply new result
                if new_home_score > new_away_score:
                    cursor.execute("UPDATE Teams SET wins = wins + 1 WHERE team_id = %s", (home_team_id,))
                    cursor.execute("UPDATE Teams SET losses = losses + 1 WHERE team_id = %s", (away_team_id,))
                elif new_away_score > new_home_score:
                    cursor.execute("UPDATE Teams SET wins = wins + 1 WHERE team_id = %s", (away_team_id,))
                    cursor.execute("UPDATE Teams SET losses = losses + 1 WHERE team_id = %s", (home_team_id,))
                # If tie, no wins/losses are updated
        
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Game updated successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@stat_keeper.route("/games/<int:game_id>/stat-events/<int:event_id>", methods=["PUT"])
def update_stat_event(game_id, event_id):
    try:
        data = request.get_json()
        
        cursor = db.get_db().cursor()
        
        # Check if stat event exists and belongs to this game
        cursor.execute(
            "SELECT event_id FROM StatEvent WHERE event_id = %s AND scored_during = %s",
            (event_id, game_id)
        )
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Stat event not found or does not belong to this game"}), 404
        
        update_fields = []
        params = []
        
        if "description" in data:
            update_fields.append("description = %s")
            params.append(data["description"])
        
        if "performed_by" in data:
            cursor.execute("SELECT player_id FROM Players WHERE player_id = %s", (data["performed_by"],))
            if not cursor.fetchone():
                cursor.close()
                return jsonify({"error": "Player not found"}), 404
            update_fields.append("performed_by = %s")
            params.append(data["performed_by"])
        
        if not update_fields:
            cursor.close()
            return jsonify({"error": "No fields to update"}), 400
        
        params.extend([event_id, game_id])
        
        update_query = f"""
        UPDATE StatEvent
        SET {', '.join(update_fields)}
        WHERE event_id = %s AND scored_during = %s
        """
        
        cursor.execute(update_query, params)
        
        # Recalculate game score if description or player changed
        if "description" in data or "performed_by" in data:
            recalculate_game_score(cursor, game_id)
        
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Stat event updated successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@stat_keeper.route("/games/<int:game_id>/stat-events/<int:event_id>", methods=["DELETE"])
def delete_stat_event(game_id, event_id):
    try:
        cursor = db.get_db().cursor()
        
        # Check if stat event exists and belongs to this game
        cursor.execute(
            "SELECT event_id FROM StatEvent WHERE event_id = %s AND scored_during = %s",
            (event_id, game_id)
        )
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Stat event not found or does not belong to this game"}), 404
        
        cursor.execute(
            "DELETE FROM StatEvent WHERE event_id = %s AND scored_during = %s",
            (event_id, game_id)
        )
        
        # Recalculate game score after deletion
        recalculate_game_score(cursor, game_id)
        
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Stat event deleted successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500

