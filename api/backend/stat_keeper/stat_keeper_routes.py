from flask import Blueprint, jsonify, request
from backend.db_connection import db
from mysql.connector import Error
from datetime import datetime, timedelta, date, time

stat_keeper = Blueprint("stat_keeper", __name__)


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
        
        # Get parameters from query string
        upcoming_only = request.args.get("upcoming_only", "false").lower() == "true"
        all_games = request.args.get("all", "false").lower() == "true"
        
        query = """
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
               l.name AS league_name, s.name AS sport_name,
               gk.assignment_date,
               CASE 
                   WHEN (SELECT t.team_id FROM Teams_Games tg 
                         JOIN Teams t ON tg.team_id = t.team_id 
                         WHERE tg.game_id = g.game_id AND tg.is_home_team = TRUE LIMIT 1) IS NOT NULL
                   AND (SELECT t.team_id FROM Teams_Games tg 
                        JOIN Teams t ON tg.team_id = t.team_id 
                        WHERE tg.game_id = g.game_id AND tg.is_home_team = FALSE LIMIT 1) IS NOT NULL
                   THEN 1 ELSE 0 END AS has_both_teams
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
            # Upcoming: future games that haven't been finalized
            query += " AND g.date_played > CURDATE() AND (g.home_score IS NULL OR g.away_score IS NULL)"
            query += " ORDER BY g.date_played ASC, g.start_time ASC"  # Soonest games first
        else:
            # Past: finalized games (regardless of date) - these are the official records
            # Only include games that have both teams assigned
            query += """ AND g.home_score IS NOT NULL AND g.away_score IS NOT NULL
                         AND (SELECT t.team_id FROM Teams_Games tg 
                              JOIN Teams t ON tg.team_id = t.team_id 
                              WHERE tg.game_id = g.game_id AND tg.is_home_team = TRUE LIMIT 1) IS NOT NULL
                         AND (SELECT t.team_id FROM Teams_Games tg 
                              JOIN Teams t ON tg.team_id = t.team_id 
                              WHERE tg.game_id = g.game_id AND tg.is_home_team = FALSE LIMIT 1) IS NOT NULL"""
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
        
        query = """
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
               p.first_name, p.last_name, p.player_id
        FROM StatEvent se
        JOIN Players p ON se.performed_by = p.player_id
        WHERE se.scored_during = %s
        ORDER BY se.time_entered ASC
        """
        
        cursor.execute(query, (game_id,))
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
            COUNT(CASE WHEN tp.team_id = %s THEN se.event_id END) AS home_team_stat_count,
            COUNT(CASE WHEN tp.team_id = %s THEN se.event_id END) AS away_team_stat_count
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
        
        # Check if game exists
        cursor.execute("SELECT game_id FROM Games WHERE game_id = %s", (game_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Game not found"}), 404
        
        # Validate required fields
        if "performed_by" not in data or "description" not in data:
            cursor.close()
            return jsonify({"error": "Missing required fields: performed_by, description"}), 400
        
        # Check if player exists
        cursor.execute("SELECT player_id FROM Players WHERE player_id = %s", (data["performed_by"],))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Player not found"}), 404
        
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
        cursor.close()
        
        return jsonify({
            "message": "Stat event created successfully",
            "event_id": event_id
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
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Stat event deleted successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500

