from flask import Blueprint, jsonify, request
from backend.db_connection import db
from mysql.connector import Error
from datetime import datetime, timedelta, date, time

team_captain = Blueprint("team_captain", __name__)


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


@team_captain.route("/teams/<int:team_id>/games", methods=["GET"])
def get_team_games(team_id):
    try:
        cursor = db.get_db().cursor()
        
        upcoming_only = request.args.get("upcoming_only", "false").lower() == "true"
        
        query = """
        SELECT g.game_id, g.date_played, g.start_time, g.location, 
               g.home_score, g.away_score, g.league_played,
               t1.name AS home_team, t1.team_id AS home_team_id,
               t2.name AS away_team, t2.team_id AS away_team_id,
               l.name AS league_name
        FROM Games g
        JOIN Teams_Games tg1 ON g.game_id = tg1.game_id AND tg1.is_home_team = TRUE
        JOIN Teams t1 ON tg1.team_id = t1.team_id
        JOIN Teams_Games tg2 ON g.game_id = tg2.game_id AND tg2.is_home_team = FALSE
        JOIN Teams t2 ON tg2.team_id = t2.team_id
        JOIN Leagues l ON g.league_played = l.league_id
        WHERE (tg1.team_id = %s OR tg2.team_id = %s)
        """
        
        params = [team_id, team_id]
        
        if upcoming_only:
            query += " AND g.date_played >= CURRENT_DATE()"
            query += " ORDER BY g.date_played ASC, g.start_time ASC"
        else:
            query += " AND g.date_played < CURRENT_DATE()"
            query += " ORDER BY g.date_played DESC, g.start_time DESC"
        
        cursor.execute(query, params)
        games = cursor.fetchall()
        cursor.close()
        
        games = convert_datetime_for_json(games)
        
        return jsonify(games), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@team_captain.route("/games/<int:game_id>", methods=["GET"])
def get_game(game_id):
    try:
        cursor = db.get_db().cursor()
        
        query = """
        SELECT g.game_id, g.date_played, g.start_time, g.location, 
               g.home_score, g.away_score, g.league_played,
               t1.name AS home_team, t1.team_id AS home_team_id,
               t2.name AS away_team, t2.team_id AS away_team_id,
               l.name AS league_name, s.name AS sport_name
        FROM Games g
        JOIN Teams_Games tg1 ON g.game_id = tg1.game_id AND tg1.is_home_team = TRUE
        JOIN Teams t1 ON tg1.team_id = t1.team_id
        JOIN Teams_Games tg2 ON g.game_id = tg2.game_id AND tg2.is_home_team = FALSE
        JOIN Teams t2 ON tg2.team_id = t2.team_id
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


@team_captain.route("/games", methods=["POST"])
def create_game():
    try:
        data = request.get_json()
        
        required_fields = ["league_played", "date_played", "start_time", "location", "home_team_id", "away_team_id"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        if data["home_team_id"] == data["away_team_id"]:
            return jsonify({"error": "Home team and away team cannot be the same"}), 400
        
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT league_id FROM Leagues WHERE league_id = %s", (data["league_played"],))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "League not found"}), 404
        
        cursor.execute("SELECT team_id FROM Teams WHERE team_id = %s AND league_played = %s", (data["home_team_id"], data["league_played"]))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Home team not found or not in specified league"}), 404
        
        cursor.execute("SELECT team_id FROM Teams WHERE team_id = %s AND league_played = %s", (data["away_team_id"], data["league_played"]))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Away team not found or not in specified league"}), 404
        
        insert_query = """
        INSERT INTO Games (league_played, date_played, start_time, location)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(
            insert_query,
            (
                data["league_played"],
                data["date_played"],
                data["start_time"],
                data["location"],
            ),
        )
        
        new_game_id = cursor.lastrowid
        
        cursor.execute(
            "INSERT INTO Teams_Games (team_id, game_id, is_home_team) VALUES (%s, %s, TRUE)",
            (data["home_team_id"], new_game_id)
        )
        
        cursor.execute(
            "INSERT INTO Teams_Games (team_id, game_id, is_home_team) VALUES (%s, %s, FALSE)",
            (data["away_team_id"], new_game_id)
        )
        
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Game created successfully", "game_id": new_game_id}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@team_captain.route("/games/<int:game_id>", methods=["PUT"])
def update_game(game_id):
    try:
        data = request.get_json()
        
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT * FROM Games WHERE game_id = %s", (game_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Game not found"}), 404
        
        update_fields = []
        params = []
        allowed_fields = ["date_played", "start_time", "location", "home_score", "away_score"]
        
        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                params.append(data[field])
        
        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400
        
        params.append(game_id)
        query = f"UPDATE Games SET {', '.join(update_fields)} WHERE game_id = %s"
        
        cursor.execute(query, params)
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Game updated successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@team_captain.route("/games/<int:game_id>", methods=["DELETE"])
def delete_game(game_id):
    try:
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT game_id, date_played FROM Games WHERE game_id = %s", (game_id,))
        game = cursor.fetchone()
        
        if not game:
            cursor.close()
            return jsonify({"error": "Game not found"}), 404
        
        from datetime import date
        date_played = game['date_played']
        game_date = date_played if isinstance(date_played, date) else date.fromisoformat(str(date_played))
        today = date.today()
        
        if game_date < today:
            cursor.close()
            return jsonify({"error": "Cannot delete past games"}), 400
        cursor.execute("DELETE FROM Teams_Games WHERE game_id = %s", (game_id,))
        cursor.execute("DELETE FROM Games WHERE game_id = %s", (game_id,))
        
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Game deleted successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@team_captain.route("/games/<int:game_id>/teams/<int:team_id>/stats", methods=["GET"])
def get_team_game_stats(game_id, team_id):
    try:
        cursor = db.get_db().cursor()
        
        query = """
        SELECT p.player_id, p.first_name, p.last_name,
               COUNT(se.event_id) AS total_stat_events
        FROM Players p
        JOIN Teams_Players tp ON p.player_id = tp.player_id
        LEFT JOIN StatEvent se ON p.player_id = se.performed_by AND se.scored_during = %s
        WHERE tp.team_id = %s
        GROUP BY p.player_id, p.first_name, p.last_name
        ORDER BY total_stat_events DESC
        """
        
        cursor.execute(query, (game_id, team_id))
        stats = cursor.fetchall()
        cursor.close()
        
        return jsonify(stats), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@team_captain.route("/stats/<int:event_id>", methods=["PUT"])
def update_stat_event(event_id):
    try:
        data = request.get_json()
        
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT * FROM StatEvent WHERE event_id = %s", (event_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Stat event not found"}), 404
        
        if "description" not in data:
            return jsonify({"error": "Missing required field: description"}), 400
        
        update_query = """
        UPDATE StatEvent
        SET description = %s
        WHERE event_id = %s
        """
        cursor.execute(update_query, (data["description"], event_id))
        
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Stat event updated successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@team_captain.route("/stats/<int:event_id>", methods=["DELETE"])
def delete_stat_event(event_id):
    try:
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT * FROM StatEvent WHERE event_id = %s", (event_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Stat event not found"}), 404
        
        cursor.execute("DELETE FROM StatEvent WHERE event_id = %s", (event_id,))
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Stat event deleted successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@team_captain.route("/teams/<int:team_id>/performance", methods=["GET"])
def get_team_performance(team_id):
    try:
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT team_id FROM Teams WHERE team_id = %s", (team_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Team not found"}), 404
        query = """
        SELECT 
            (SELECT COUNT(*) FROM Games g2
             JOIN Teams_Games tg2 ON g2.game_id = tg2.game_id
             WHERE tg2.team_id = %s AND g2.date_played < CURRENT_DATE() 
             AND g2.home_score IS NOT NULL AND g2.away_score IS NOT NULL
             AND ((tg2.is_home_team = TRUE AND g2.home_score > g2.away_score) OR 
                  (tg2.is_home_team = FALSE AND g2.away_score > g2.home_score))) AS wins,
            (SELECT COUNT(*) FROM Games g2
             JOIN Teams_Games tg2 ON g2.game_id = tg2.game_id
             WHERE tg2.team_id = %s AND g2.date_played < CURRENT_DATE() 
             AND g2.home_score IS NOT NULL AND g2.away_score IS NOT NULL
             AND ((tg2.is_home_team = TRUE AND g2.home_score < g2.away_score) OR 
                  (tg2.is_home_team = FALSE AND g2.away_score < g2.home_score))) AS losses,
            (SELECT COUNT(*) FROM Games g2
             JOIN Teams_Games tg2 ON g2.game_id = tg2.game_id
             WHERE tg2.team_id = %s AND g2.date_played < CURRENT_DATE() 
             AND g2.home_score IS NOT NULL AND g2.away_score IS NOT NULL
             AND g2.home_score = g2.away_score) AS ties,
            (SELECT AVG(points) FROM (
                SELECT g2.home_score AS points FROM Games g2
                JOIN Teams_Games tg2 ON g2.game_id = tg2.game_id
                WHERE tg2.team_id = %s AND tg2.is_home_team = TRUE AND g2.date_played < CURRENT_DATE() 
                AND g2.home_score IS NOT NULL AND g2.away_score IS NOT NULL
                UNION ALL
                SELECT g2.away_score AS points FROM Games g2
                JOIN Teams_Games tg2 ON g2.game_id = tg2.game_id
                WHERE tg2.team_id = %s AND tg2.is_home_team = FALSE AND g2.date_played < CURRENT_DATE() 
                AND g2.home_score IS NOT NULL AND g2.away_score IS NOT NULL
            ) AS combined_points) AS avg_points_scored
        """
        
        cursor.execute(query, (team_id, team_id, team_id, team_id, team_id))
        performance = cursor.fetchone()
        cursor.close()
        
        if not performance:
            return jsonify({
                "games_played": 0,
                "wins": 0,
                "losses": 0,
                "ties": 0,
                "avg_points_scored": 0
            }), 200
        
        performance["wins"] = performance["wins"] or 0
        performance["losses"] = performance["losses"] or 0
        performance["ties"] = performance["ties"] or 0
        performance["games_played"] = performance["wins"] + performance["losses"] + performance["ties"]
        performance["avg_points_scored"] = float(performance["avg_points_scored"]) if performance["avg_points_scored"] else 0.0
        
        return jsonify(performance), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@team_captain.route("/teams/<int:team_id>/performance-over-time", methods=["GET"])
def get_team_performance_over_time(team_id):
    try:
        cursor = db.get_db().cursor()
        
        query = """
        SELECT g.date_played,
               (SELECT g2.home_score FROM Games g2
                JOIN Teams_Games tg2 ON g2.game_id = tg2.game_id
                WHERE tg2.game_id = g.game_id AND tg2.team_id = %s AND tg2.is_home_team = TRUE
                UNION ALL
                SELECT g2.away_score FROM Games g2
                JOIN Teams_Games tg2 ON g2.game_id = tg2.game_id
                WHERE tg2.game_id = g.game_id AND tg2.team_id = %s AND tg2.is_home_team = FALSE
                LIMIT 1) AS points_scored,
               (SELECT g2.away_score FROM Games g2
                JOIN Teams_Games tg2 ON g2.game_id = tg2.game_id
                WHERE tg2.game_id = g.game_id AND tg2.team_id = %s AND tg2.is_home_team = TRUE
                UNION ALL
                SELECT g2.home_score FROM Games g2
                JOIN Teams_Games tg2 ON g2.game_id = tg2.game_id
                WHERE tg2.game_id = g.game_id AND tg2.team_id = %s AND tg2.is_home_team = FALSE
                LIMIT 1) AS points_allowed,
               (SELECT 'W' FROM Teams_Games tg2 JOIN Games g2 ON tg2.game_id = g2.game_id
                WHERE tg2.game_id = g.game_id AND tg2.team_id = %s 
                AND ((tg2.is_home_team = TRUE AND g2.home_score > g2.away_score) OR 
                     (tg2.is_home_team = FALSE AND g2.away_score > g2.home_score))
                UNION ALL
                SELECT 'L'
                LIMIT 1) AS result
        FROM Games g
        JOIN Teams_Games tg ON g.game_id = tg.game_id
        WHERE tg.team_id = %s AND g.date_played < CURRENT_DATE()
        ORDER BY g.date_played ASC
        """
        
        cursor.execute(query, (team_id, team_id, team_id, team_id, team_id, team_id))
        performance_data = cursor.fetchall()
        cursor.close()
        
        performance_data = convert_datetime_for_json(performance_data)
        
        return jsonify(performance_data), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@team_captain.route("/teams/<int:team_id>/league-comparison", methods=["GET"])
def get_team_league_comparison(team_id):
    try:
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT league_played FROM Teams WHERE team_id = %s", (team_id,))
        team = cursor.fetchone()
        if not team:
            return jsonify({"error": "Team not found"}), 404
        
        league_id = team["league_played"]
        
        query = """
        SELECT t.name AS team_name,
               AVG(g.home_score) AS avg_home_score,
               AVG(g.away_score) AS avg_away_score,
               (SELECT AVG(home_score) FROM Games WHERE league_played = %s) AS league_avg_home_score,
               (SELECT AVG(away_score) FROM Games WHERE league_played = %s) AS league_avg_away_score
        FROM Teams t
        JOIN Teams_Games tg ON t.team_id = tg.team_id
        JOIN Games g ON tg.game_id = g.game_id
        WHERE t.team_id = %s
        GROUP BY t.team_id, t.name
        """
        cursor.execute(query, (league_id, league_id, team_id))
        result = cursor.fetchone()
        cursor.close()
        
        if not result:
            return jsonify({"error": "Team not found"}), 404
        
        team_avg_scored = 0
        if result["avg_home_score"]:
            team_avg_scored = float(result["avg_home_score"])
        
        team_avg_allowed = 0
        if result["avg_away_score"]:
            team_avg_allowed = float(result["avg_away_score"])
        
        league_avg_scored = 0
        if result["league_avg_home_score"]:
            league_avg_scored = float(result["league_avg_home_score"])
        
        league_avg_allowed = 0
        if result["league_avg_away_score"]:
            league_avg_allowed = float(result["league_avg_away_score"])
        
        comparison = {
            "team": {
                "avg_points_scored": team_avg_scored,
                "avg_points_allowed": team_avg_allowed
            },
            "league": {
                "avg_points_scored": league_avg_scored,
                "avg_points_allowed": league_avg_allowed
            }
        }
        
        return jsonify(comparison), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@team_captain.route("/teams/<int:team_id>/summary", methods=["GET"])
def get_team_summary(team_id):
    try:
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT team_id, name FROM Teams WHERE team_id = %s", (team_id,))
        team = cursor.fetchone()
        if not team:
            cursor.close()
            return jsonify({"error": "Team not found"}), 404
        
        cursor.execute("""
            SELECT COUNT(DISTINCT player_id) AS total_players
            FROM Teams_Players
            WHERE team_id = %s
        """, (team_id,))
        players_result = cursor.fetchone()
        total_players = players_result["total_players"] if players_result else 0
        
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM Games g2
                 JOIN Teams_Games tg2 ON g2.game_id = tg2.game_id
                 WHERE tg2.team_id = %s AND g2.date_played < CURRENT_DATE() 
                 AND g2.home_score IS NOT NULL AND g2.away_score IS NOT NULL
                 AND ((tg2.is_home_team = TRUE AND g2.home_score > g2.away_score) OR 
                      (tg2.is_home_team = FALSE AND g2.away_score > g2.home_score))) AS wins,
                (SELECT COUNT(*) FROM Games g2
                 JOIN Teams_Games tg2 ON g2.game_id = tg2.game_id
                 WHERE tg2.team_id = %s AND g2.date_played < CURRENT_DATE() 
                 AND g2.home_score IS NOT NULL AND g2.away_score IS NOT NULL
                 AND ((tg2.is_home_team = TRUE AND g2.home_score < g2.away_score) OR 
                      (tg2.is_home_team = FALSE AND g2.away_score < g2.home_score))) AS losses,
                (SELECT COUNT(*) FROM Games g2
                 JOIN Teams_Games tg2 ON g2.game_id = tg2.game_id
                 WHERE tg2.team_id = %s AND g2.date_played < CURRENT_DATE() 
                 AND g2.home_score IS NOT NULL AND g2.away_score IS NOT NULL
                 AND g2.home_score = g2.away_score) AS ties
        """, (team_id, team_id, team_id))
        game_stats = cursor.fetchone()
        
        wins = game_stats["wins"] or 0 if game_stats else 0
        losses = game_stats["losses"] or 0 if game_stats else 0
        ties = game_stats["ties"] or 0 if game_stats else 0
        games_played = wins + losses + ties
        
        cursor.execute("""
            SELECT COUNT(se.event_id) AS total_stat_events
            FROM StatEvent se
            JOIN Games g ON se.scored_during = g.game_id
            JOIN Teams_Games tg ON g.game_id = tg.game_id
            JOIN Teams_Players tp ON se.performed_by = tp.player_id
            WHERE tg.team_id = %s AND tp.team_id = %s
        """, (team_id, team_id))
        stat_events_result = cursor.fetchone()
        total_stat_events = stat_events_result["total_stat_events"] if stat_events_result else 0
        
        cursor.execute("""
            SELECT l.name AS league_name
            FROM Teams t
            JOIN Leagues l ON t.league_played = l.league_id
            WHERE t.team_id = %s
        """, (team_id,))
        league = cursor.fetchone()
        cursor.close()
        
        summary = {
            "name": team["name"],
            "wins": wins,
            "losses": losses,
            "ties": ties,
            "games_played": games_played,
            "total_players": total_players,
            "total_stat_events": total_stat_events
        }
        
        if league:
            summary["league_name"] = league["league_name"]
        
        return jsonify(summary), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@team_captain.route("/reminders", methods=["POST"])
def create_reminder():
    cursor = None
    try:
        data = request.get_json()
        
        required_fields = ["message", "team_id"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        cursor = db.get_db().cursor()
        
        # Validate team_id exists
        cursor.execute("SELECT team_id, name FROM Teams WHERE team_id = %s", (data["team_id"],))
        team_result = cursor.fetchone()
        if not team_result:
            cursor.close()
            # Check if any teams exist at all
            cursor = db.get_db().cursor()
            cursor.execute("SELECT COUNT(*) as count FROM Teams")
            team_count = cursor.fetchone()
            cursor.close()
            if team_count and team_count.get("count", 0) == 0:
                return jsonify({"error": f"Team with ID {data['team_id']} not found. No teams exist in the database. Please ensure the database is properly initialized."}), 404
            else:
                return jsonify({"error": f"Team with ID {data['team_id']} not found. Available teams may have different IDs. Please check your database."}), 404
        
        # Validate game_id if provided
        game_id = data.get("game_id")
        if game_id is not None:
            cursor.execute("SELECT game_id FROM Games WHERE game_id = %s", (game_id,))
            if not cursor.fetchone():
                cursor.close()
                return jsonify({"error": f"Game with ID {game_id} not found"}), 404
        
        insert_query = """
        INSERT INTO Reminders (message, time_sent, status, team_id, game_id, priority)
        VALUES (%s, NOW(), 'sent', %s, %s, %s)
        """
        cursor.execute(
            insert_query,
            (
                data["message"],
                data["team_id"],
                game_id,  # Use the validated game_id variable
                data.get("priority", "medium")
            ),
        )
        
        db.get_db().commit()
        new_reminder_id = cursor.lastrowid
        cursor.close()
        
        return jsonify({"message": "Reminder created successfully", "reminder_id": new_reminder_id}), 201
    except Error as e:
        # Return more detailed error message
        error_msg = str(e)
        if cursor:
            cursor.close()
        return jsonify({"error": f"Database error: {error_msg}"}), 500
    except Exception as e:
        # Catch any other exceptions
        error_msg = str(e)
        if cursor:
            cursor.close()
        return jsonify({"error": f"Unexpected error: {error_msg}"}), 500


@team_captain.route("/teams/<int:team_id>/reminders", methods=["GET"])
def get_team_reminders(team_id):
    try:
        cursor = db.get_db().cursor()
        
        query = """
        SELECT r.reminder_id, r.message, r.time_sent, r.status, r.game_id, r.priority, 
               g.date_played, g.home_score, g.away_score,
               (SELECT t.name FROM Teams_Games tg 
                JOIN Teams t ON tg.team_id = t.team_id 
                WHERE tg.game_id = g.game_id AND tg.is_home_team = TRUE 
                LIMIT 1) AS home_team,
               (SELECT t.name FROM Teams_Games tg 
                JOIN Teams t ON tg.team_id = t.team_id 
                WHERE tg.game_id = g.game_id AND tg.is_home_team = FALSE 
                LIMIT 1) AS away_team
        FROM Reminders r
        LEFT JOIN Games g ON r.game_id = g.game_id
        WHERE r.team_id = %s
        ORDER BY r.time_sent DESC
        """
        
        cursor.execute(query, (team_id,))
        reminders = cursor.fetchall()
        cursor.close()
        
        if not reminders:
            return jsonify([]), 200
        
        reminders = convert_datetime_for_json(reminders)
        
        return jsonify(reminders), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@team_captain.route("/games/<int:game_id>/teams/<int:team_id>/stat-events", methods=["GET"])
def get_game_stat_events(game_id, team_id):
    try:
        cursor = db.get_db().cursor()
        
        cursor.execute("""
            SELECT tg.team_id 
            FROM Teams_Games tg 
            WHERE tg.game_id = %s AND tg.team_id = %s
        """, (game_id, team_id))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Team not found in this game"}), 404
        
        query = """
        SELECT se.event_id, se.performed_by, se.description, se.time_entered,
               p.first_name, p.last_name
        FROM StatEvent se
        JOIN Players p ON se.performed_by = p.player_id
        WHERE se.scored_during = %s 
        AND (
            EXISTS (
                SELECT 1 
                FROM Teams_Players tp 
                WHERE tp.player_id = se.performed_by 
                AND tp.team_id = %s
            )
            OR EXISTS (
                SELECT 1
                FROM Players_Games pg
                JOIN Teams_Games tg ON pg.game_id = tg.game_id
                WHERE pg.player_id = se.performed_by
                AND pg.game_id = %s
                AND tg.team_id = %s
            )
        )
        ORDER BY se.time_entered ASC
        """
        
        cursor.execute(query, (game_id, team_id, game_id, team_id))
        stat_events = cursor.fetchall()
        cursor.close()
        
        stat_events = convert_datetime_for_json(stat_events)
        
        return jsonify(stat_events), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@team_captain.route("/teams/<int:team_id>/home-away-splits", methods=["GET"])
def get_home_away_splits(team_id):
    try:
        cursor = db.get_db().cursor()
        
        query = """
        SELECT 
            'Home' AS location_type,
            COUNT(*) AS total_games,
            (SELECT COUNT(*) FROM Games g2
             JOIN Teams_Games tg2 ON g2.game_id = tg2.game_id
             WHERE tg2.team_id = %s AND tg2.is_home_team = TRUE AND g2.date_played < CURRENT_DATE()
             AND g2.home_score > g2.away_score) AS wins,
            AVG(g.home_score) AS avg_points_scored,
            AVG(g.away_score) AS avg_points_allowed
        FROM Games g
        JOIN Teams_Games tg ON g.game_id = tg.game_id
        WHERE tg.team_id = %s AND tg.is_home_team = TRUE AND g.date_played < CURRENT_DATE()
        UNION ALL
        SELECT 
            'Away' AS location_type,
            COUNT(*) AS total_games,
            (SELECT COUNT(*) FROM Games g2
             JOIN Teams_Games tg2 ON g2.game_id = tg2.game_id
             WHERE tg2.team_id = %s AND tg2.is_home_team = FALSE AND g2.date_played < CURRENT_DATE()
             AND g2.away_score > g2.home_score) AS wins,
            AVG(g.away_score) AS avg_points_scored,
            AVG(g.home_score) AS avg_points_allowed
        FROM Games g
        JOIN Teams_Games tg ON g.game_id = tg.game_id
        WHERE tg.team_id = %s AND tg.is_home_team = FALSE AND g.date_played < CURRENT_DATE()
        """
        
        cursor.execute(query, (team_id, team_id, team_id, team_id))
        splits = cursor.fetchall()
        cursor.close()
        
        splits = convert_datetime_for_json(splits)
        
        return jsonify(splits), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@team_captain.route("/teams/<int:team_id>/opponent/<int:opponent_id>", methods=["GET"])
def get_opponent_stats(team_id, opponent_id):
    try:
        cursor = db.get_db().cursor()
        
        query = """
        SELECT 
            COUNT(*) AS total_games,
            (SELECT COUNT(*) FROM Games g2
             JOIN Teams_Games tg1_2 ON g2.game_id = tg1_2.game_id AND tg1_2.team_id = %s
             JOIN Teams_Games tg2_2 ON g2.game_id = tg2_2.game_id AND tg2_2.team_id = %s
             WHERE g2.date_played < CURRENT_DATE()
             AND ((tg1_2.is_home_team = TRUE AND g2.home_score > g2.away_score) OR 
                  (tg1_2.is_home_team = FALSE AND g2.away_score > g2.home_score))) AS wins,
            (SELECT COUNT(*) FROM Games g2
             JOIN Teams_Games tg1_2 ON g2.game_id = tg1_2.game_id AND tg1_2.team_id = %s
             JOIN Teams_Games tg2_2 ON g2.game_id = tg2_2.game_id AND tg2_2.team_id = %s
             WHERE g2.date_played < CURRENT_DATE()
             AND ((tg1_2.is_home_team = TRUE AND g2.home_score < g2.away_score) OR 
                  (tg1_2.is_home_team = FALSE AND g2.away_score < g2.home_score))) AS losses,
            (SELECT AVG(points) FROM (
                SELECT g2.home_score AS points FROM Games g2
                JOIN Teams_Games tg1_2 ON g2.game_id = tg1_2.game_id AND tg1_2.team_id = %s
                JOIN Teams_Games tg2_2 ON g2.game_id = tg2_2.game_id AND tg2_2.team_id = %s
                WHERE g2.date_played < CURRENT_DATE() AND tg1_2.is_home_team = TRUE
                UNION ALL
                SELECT g2.away_score AS points FROM Games g2
                JOIN Teams_Games tg1_2 ON g2.game_id = tg1_2.game_id AND tg1_2.team_id = %s
                JOIN Teams_Games tg2_2 ON g2.game_id = tg2_2.game_id AND tg2_2.team_id = %s
                WHERE g2.date_played < CURRENT_DATE() AND tg1_2.is_home_team = FALSE
            ) AS combined_points) AS avg_points_scored,
            (SELECT AVG(points) FROM (
                SELECT g2.away_score AS points FROM Games g2
                JOIN Teams_Games tg1_2 ON g2.game_id = tg1_2.game_id AND tg1_2.team_id = %s
                JOIN Teams_Games tg2_2 ON g2.game_id = tg2_2.game_id AND tg2_2.team_id = %s
                WHERE g2.date_played < CURRENT_DATE() AND tg1_2.is_home_team = TRUE
                UNION ALL
                SELECT g2.home_score AS points FROM Games g2
                JOIN Teams_Games tg1_2 ON g2.game_id = tg1_2.game_id AND tg1_2.team_id = %s
                JOIN Teams_Games tg2_2 ON g2.game_id = tg2_2.game_id AND tg2_2.team_id = %s
                WHERE g2.date_played < CURRENT_DATE() AND tg1_2.is_home_team = FALSE
            ) AS combined_points) AS avg_points_allowed,
            t2.name AS opponent_name
        FROM Games g
        JOIN Teams_Games tg1 ON g.game_id = tg1.game_id AND tg1.team_id = %s
        JOIN Teams_Games tg2 ON g.game_id = tg2.game_id AND tg2.team_id = %s
        JOIN Teams t2 ON tg2.team_id = t2.team_id
        WHERE g.date_played < CURRENT_DATE()
        GROUP BY t2.name
        """
        
        cursor.execute(query, (team_id, opponent_id, team_id, opponent_id, team_id, opponent_id, team_id, opponent_id, team_id, opponent_id, team_id, opponent_id, team_id, opponent_id))
        opponent_stats = cursor.fetchone()
        cursor.close()
        
        if not opponent_stats:
            return jsonify({"error": "No games found against this opponent"}), 404
        
        opponent_stats = convert_datetime_for_json(opponent_stats)
        
        return jsonify(opponent_stats), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@team_captain.route("/teams/<int:team_id>/opponents", methods=["GET"])
def get_opponents(team_id):
    try:
        cursor = db.get_db().cursor()
        
        query = """
        SELECT DISTINCT t2.team_id, t2.name
        FROM Games g
        JOIN Teams_Games tg1 ON g.game_id = tg1.game_id AND tg1.team_id = %s
        JOIN Teams_Games tg2 ON g.game_id = tg2.game_id AND tg2.team_id != %s
        JOIN Teams t2 ON tg2.team_id = t2.team_id
        WHERE tg1.team_id = %s
        ORDER BY t2.name
        """
        
        cursor.execute(query, (team_id, team_id, team_id))
        opponents = cursor.fetchall()
        cursor.close()
        
        return jsonify(opponents), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@team_captain.route("/games/<int:game_id>/stat-keepers", methods=["GET"])
def get_game_stat_keepers(game_id):
    try:
        cursor = db.get_db().cursor()
        
        cursor.execute("""
            SELECT g.game_id 
            FROM Games g
            JOIN Teams_Games tg ON g.game_id = tg.game_id
            WHERE g.game_id = %s
        """, (game_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Game not found"}), 404
        
        query = """
        SELECT sk.keeper_id, sk.first_name, sk.last_name, sk.email,
               sk.total_games_tracked, gk.assignment_date
        FROM Games_Keepers gk
        JOIN Stat_Keepers sk ON gk.keeper_id = sk.keeper_id
        WHERE gk.game_id = %s
        ORDER BY gk.assignment_date DESC
        """
        
        cursor.execute(query, (game_id,))
        stat_keepers = cursor.fetchall()
        cursor.close()
        
        stat_keepers = convert_datetime_for_json(stat_keepers)
        
        return jsonify(stat_keepers), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@team_captain.route("/games/<int:game_id>/stat-keepers", methods=["POST"])
def assign_stat_keeper_to_game(game_id):
    try:
        data = request.get_json()
        
        if "keeper_id" not in data:
            return jsonify({"error": "Missing required field: keeper_id"}), 400
        
        cursor = db.get_db().cursor()
        cursor.execute("SELECT game_id FROM Games WHERE game_id = %s", (game_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Game not found"}), 404
        cursor.execute("SELECT keeper_id FROM Stat_Keepers WHERE keeper_id = %s", (data["keeper_id"],))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Stat keeper not found"}), 404
        
        insert_query = """
        INSERT INTO Games_Keepers (keeper_id, game_id, assignment_date)
        VALUES (%s, %s, CURDATE())
        ON DUPLICATE KEY UPDATE assignment_date = CURDATE()
        """
        
        cursor.execute(insert_query, (data["keeper_id"], game_id))
        
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Stat keeper assigned to game successfully"}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500


@team_captain.route("/games/<int:game_id>/stat-keepers", methods=["DELETE"])
def remove_stat_keeper_from_game(game_id):
    try:
        data = request.get_json()
        
        if "keeper_id" not in data:
            return jsonify({"error": "Missing required field: keeper_id"}), 400
        
        cursor = db.get_db().cursor()
        
        cursor.execute("""
            SELECT * FROM Games_Keepers 
            WHERE game_id = %s AND keeper_id = %s
        """, (game_id, data["keeper_id"]))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Stat keeper not assigned to this game"}), 404
        
        cursor.execute("""
            DELETE FROM Games_Keepers 
            WHERE game_id = %s AND keeper_id = %s
        """, (game_id, data["keeper_id"]))
        
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Stat keeper removed from game successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@team_captain.route("/stat-keepers", methods=["GET"])
def get_all_stat_keepers():
    try:
        cursor = db.get_db().cursor()
        
        query = """
        SELECT keeper_id, first_name, last_name, email, total_games_tracked
        FROM Stat_Keepers
        ORDER BY last_name, first_name
        """
        
        cursor.execute(query)
        stat_keepers = cursor.fetchall()
        cursor.close()
        
        stat_keepers = convert_datetime_for_json(stat_keepers)
        
        return jsonify(stat_keepers), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@team_captain.route("/leagues", methods=["GET"])
def get_all_leagues():
    """Get all leagues for team captain to select from when scheduling games"""
    try:
        cursor = db.get_db().cursor()
        
        query = """
        SELECT league_id, name, sport_played, semester, year
        FROM Leagues
        ORDER BY year DESC, semester DESC, name ASC
        """
        
        cursor.execute(query)
        leagues = cursor.fetchall()
        cursor.close()
        
        leagues = convert_datetime_for_json(leagues)
        
        return jsonify(leagues), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@team_captain.route("/leagues/<int:league_id>/teams", methods=["GET"])
def get_league_teams(league_id):
    """Get all teams in a specific league for team captain to select opponents"""
    try:
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT league_id FROM Leagues WHERE league_id = %s", (league_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "League not found"}), 404
        
        query = """
        SELECT team_id, name, league_played
        FROM Teams
        WHERE league_played = %s
        ORDER BY name ASC
        """
        
        cursor.execute(query, (league_id,))
        teams = cursor.fetchall()
        cursor.close()
        
        teams = convert_datetime_for_json(teams)
        
        return jsonify(teams), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
