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
            query += " AND g.date_played >= CURDATE()"
        else:
            query += " AND g.date_played < CURDATE()"
        
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
        
        cursor = db.get_db().cursor()
        
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


@team_captain.route("/games/<int:game_id>/teams/<int:team_id>/stats", methods=["GET"])
def get_team_game_stats(game_id, team_id):
    try:
        cursor = db.get_db().cursor()
        
        query = """
        SELECT p.player_id, p.first_name, p.last_name,
               COUNT(se.event_id) AS total_stat_events,
               GROUP_CONCAT(DISTINCT se.description SEPARATOR ', ') AS stat_types
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
        
        query = """
        SELECT t.name, t.wins, t.losses,
               COUNT(g.game_id) AS games_played,
               AVG(g.home_score) AS avg_home_score,
               AVG(g.away_score) AS avg_away_score
        FROM Teams t
        JOIN Teams_Games tg ON t.team_id = tg.team_id
        JOIN Games g ON tg.game_id = g.game_id
        WHERE t.team_id = %s
        GROUP BY t.team_id, t.name, t.wins, t.losses
        """
        
        cursor.execute(query, (team_id,))
        performance = cursor.fetchone()
        cursor.close()
        
        if not performance:
            return jsonify({"error": "Team not found"}), 404
        
        return jsonify(performance), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@team_captain.route("/teams/<int:team_id>/performance-over-time", methods=["GET"])
def get_team_performance_over_time(team_id):
    try:
        cursor = db.get_db().cursor()
        
        query = """
        SELECT g.date_played,
               CASE WHEN tg.is_home_team = TRUE THEN g.home_score ELSE g.away_score END AS points_scored,
               CASE WHEN tg.is_home_team = TRUE THEN g.away_score ELSE g.home_score END AS points_allowed,
               CASE WHEN tg.is_home_team = TRUE AND g.home_score > g.away_score THEN 'W'
                    WHEN tg.is_home_team = FALSE AND g.away_score > g.home_score THEN 'W'
                    ELSE 'L' END AS result
        FROM Games g
        JOIN Teams_Games tg ON g.game_id = tg.game_id
        WHERE tg.team_id = %s AND g.date_played < CURRENT_DATE()
        ORDER BY g.date_played ASC
        """
        
        cursor.execute(query, (team_id,))
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
        
        query = """
        SELECT t.name, t.wins, t.losses,
               COUNT(DISTINCT tp.player_id) AS total_players,
               COUNT(DISTINCT g.game_id) AS games_played,
               COUNT(se.event_id) AS total_stat_events
        FROM Teams t
        JOIN Teams_Players tp ON t.team_id = tp.team_id
        LEFT JOIN Teams_Games tg ON t.team_id = tg.team_id
        LEFT JOIN Games g ON tg.game_id = g.game_id
        LEFT JOIN StatEvent se ON g.game_id = se.scored_during
        WHERE t.team_id = %s
        GROUP BY t.team_id, t.name, t.wins, t.losses
        """
        
        cursor.execute(query, (team_id,))
        summary = cursor.fetchone()
        
        if not summary:
            cursor.close()
            return jsonify({"error": "Team not found"}), 404
        
        cursor.execute("""
            SELECT l.name AS league_name
            FROM Teams t
            JOIN Leagues l ON t.league_played = l.league_id
            WHERE t.team_id = %s
        """, (team_id,))
        league = cursor.fetchone()
        cursor.close()
        
        if league:
            summary["league_name"] = league["league_name"]
        
        return jsonify(summary), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@team_captain.route("/reminders", methods=["POST"])
def create_reminder():
    try:
        data = request.get_json()
        
        required_fields = ["message", "team_id"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        cursor = db.get_db().cursor()
        
        insert_query = """
        INSERT INTO Reminders (message, time_sent, status, team_id, game_id)
        VALUES (%s, NOW(), 'sent', %s, %s)
        """
        cursor.execute(
            insert_query,
            (
                data["message"],
                data["team_id"],
                data.get("game_id")
            ),
        )
        
        db.get_db().commit()
        new_reminder_id = cursor.lastrowid
        cursor.close()
        
        return jsonify({"message": "Reminder created successfully", "reminder_id": new_reminder_id}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500


@team_captain.route("/teams/<int:team_id>/reminders", methods=["GET"])
def get_team_reminders(team_id):
    try:
        cursor = db.get_db().cursor()
        
        query = """
        SELECT r.reminder_id, r.message, r.time_sent, r.status, r.game_id, g.date_played
        FROM Reminders r
        LEFT JOIN Games g ON r.game_id = g.game_id
        WHERE r.team_id = %s
        ORDER BY r.time_sent DESC
        """
        
        cursor.execute(query, (team_id,))
        reminders = cursor.fetchall()
        cursor.close()
        
        reminders = convert_datetime_for_json(reminders)
        
        return jsonify(reminders), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@team_captain.route("/games/<int:game_id>/teams/<int:team_id>/stat-events", methods=["GET"])
def get_game_stat_events(game_id, team_id):
    try:
        cursor = db.get_db().cursor()
        
        query = """
        SELECT se.event_id, se.performed_by, se.description, se.time_entered,
               p.first_name, p.last_name
        FROM StatEvent se
        JOIN Players p ON se.performed_by = p.player_id
        JOIN Teams_Players tp ON p.player_id = tp.player_id
        WHERE se.scored_during = %s AND tp.team_id = %s
        ORDER BY se.time_entered ASC
        """
        
        cursor.execute(query, (game_id, team_id))
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
            CASE WHEN tg.is_home_team = TRUE THEN 'Home' ELSE 'Away' END AS location_type,
            COUNT(*) AS total_games,
            SUM(CASE WHEN tg.is_home_team = TRUE AND g.home_score > g.away_score THEN 1
                     WHEN tg.is_home_team = FALSE AND g.away_score > g.home_score THEN 1
                     ELSE 0 END) AS wins,
            AVG(CASE WHEN tg.is_home_team = TRUE THEN g.home_score ELSE g.away_score END) AS avg_points_scored,
            AVG(CASE WHEN tg.is_home_team = TRUE THEN g.away_score ELSE g.home_score END) AS avg_points_allowed
        FROM Games g
        JOIN Teams_Games tg ON g.game_id = tg.game_id
        WHERE tg.team_id = %s AND g.date_played < CURRENT_DATE()
        GROUP BY location_type
        """
        
        cursor.execute(query, (team_id,))
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
            SUM(CASE WHEN tg1.is_home_team = TRUE AND g.home_score > g.away_score THEN 1
                     WHEN tg1.is_home_team = FALSE AND g.away_score > g.home_score THEN 1
                     ELSE 0 END) AS wins,
            SUM(CASE WHEN tg1.is_home_team = TRUE AND g.home_score < g.away_score THEN 1
                     WHEN tg1.is_home_team = FALSE AND g.away_score < g.home_score THEN 1
                     ELSE 0 END) AS losses,
            AVG(CASE WHEN tg1.is_home_team = TRUE THEN g.home_score ELSE g.away_score END) AS avg_points_scored,
            AVG(CASE WHEN tg1.is_home_team = TRUE THEN g.away_score ELSE g.home_score END) AS avg_points_allowed,
            t2.name AS opponent_name
        FROM Games g
        JOIN Teams_Games tg1 ON g.game_id = tg1.game_id AND tg1.team_id = %s
        JOIN Teams_Games tg2 ON g.game_id = tg2.game_id AND tg2.team_id = %s
        JOIN Teams t2 ON tg2.team_id = t2.team_id
        WHERE g.date_played < CURRENT_DATE()
        GROUP BY t2.name
        """
        
        cursor.execute(query, (team_id, opponent_id))
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
