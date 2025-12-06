from flask import Blueprint, jsonify, request
from backend.db_connection import db
from mysql.connector import Error
from datetime import datetime, timedelta, date, time

player = Blueprint("player", __name__)


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


@player.route("/players", methods=["GET"])
def get_all_players():
    try:
        cursor = db.get_db().cursor()
        
        query = """
        SELECT player_id, phone_number, first_name, last_name, email
        FROM Players
        ORDER BY last_name, first_name
        """
        
        cursor.execute(query)
        players = cursor.fetchall()
        cursor.close()
        
        players = convert_datetime_for_json(players)
        
        return jsonify(players), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@player.route("/players/<int:player_id>", methods=["GET"])
def get_player(player_id):
    try:
        cursor = db.get_db().cursor()
        
        query = """
        SELECT player_id, phone_number, first_name, last_name, email
        FROM Players
        WHERE player_id = %s
        """
        
        cursor.execute(query, (player_id,))
        player_data = cursor.fetchone()
        cursor.close()
        
        if not player_data:
            return jsonify({"error": "Player not found"}), 404
        
        player_data = convert_datetime_for_json(player_data)
        
        return jsonify(player_data), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@player.route("/players/<int:player_id>/teams", methods=["GET"])
def get_player_teams(player_id):
    try:
        cursor = db.get_db().cursor()
        
        # First check if player exists
        cursor.execute("SELECT player_id FROM Players WHERE player_id = %s", (player_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Player not found"}), 404
        
        query = """
        SELECT t.team_id, t.name AS team_name, t.wins, t.losses,
               tp.role, l.name AS league_name, l.league_id, s.name AS sport_name
        FROM Teams_Players tp
        JOIN Teams t ON tp.team_id = t.team_id
        JOIN Leagues l ON t.league_played = l.league_id
        JOIN Sports s ON l.sport_played = s.sport_id
        WHERE tp.player_id = %s
        ORDER BY l.name, t.name
        """
        
        cursor.execute(query, (player_id,))
        teams = cursor.fetchall()
        cursor.close()
        
        teams = convert_datetime_for_json(teams)
        
        return jsonify(teams), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@player.route("/players/<int:player_id>/games", methods=["GET"])
def get_player_games(player_id):
    try:
        cursor = db.get_db().cursor()
        
        # First check if player exists
        cursor.execute("SELECT player_id FROM Players WHERE player_id = %s", (player_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Player not found"}), 404
        
        upcoming_only = request.args.get("upcoming_only", "false").lower() == "true"
        
        query = """
        SELECT g.game_id, g.date_played, g.start_time, g.location,
               g.home_score, g.away_score, g.league_played,
               t1.name AS home_team, t1.team_id AS home_team_id,
               t2.name AS away_team, t2.team_id AS away_team_id,
               l.name AS league_name, s.name AS sport_name,
               pg.is_starter, pg.position
        FROM Players_Games pg
        JOIN Games g ON pg.game_id = g.game_id
        JOIN Teams_Games tg1 ON g.game_id = tg1.game_id AND tg1.is_home_team = TRUE
        JOIN Teams t1 ON tg1.team_id = t1.team_id
        JOIN Teams_Games tg2 ON g.game_id = tg2.game_id AND tg2.is_home_team = FALSE
        JOIN Teams t2 ON tg2.team_id = t2.team_id
        JOIN Leagues l ON g.league_played = l.league_id
        JOIN Sports s ON l.sport_played = s.sport_id
        WHERE pg.player_id = %s
        """
        
        params = [player_id]
        
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


@player.route("/players/<int:player_id>/stats", methods=["GET"])
def get_player_stats(player_id):
    try:
        cursor = db.get_db().cursor()
        
        # First check if player exists
        cursor.execute("SELECT player_id FROM Players WHERE player_id = %s", (player_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Player not found"}), 404
        
        # Get all stat events for the player with game details
        query = """
        SELECT se.event_id, se.description, se.time_entered,
               g.game_id, g.date_played, g.start_time, g.location,
               t1.name AS home_team, t2.name AS away_team,
               l.name AS league_name, s.name AS sport_name
        FROM StatEvent se
        JOIN Games g ON se.scored_during = g.game_id
        JOIN Teams_Games tg1 ON g.game_id = tg1.game_id AND tg1.is_home_team = TRUE
        JOIN Teams t1 ON tg1.team_id = t1.team_id
        JOIN Teams_Games tg2 ON g.game_id = tg2.game_id AND tg2.is_home_team = FALSE
        JOIN Teams t2 ON tg2.team_id = t2.team_id
        JOIN Leagues l ON g.league_played = l.league_id
        JOIN Sports s ON l.sport_played = s.sport_id
        WHERE se.performed_by = %s
        ORDER BY g.date_played DESC, se.time_entered DESC
        """
        
        cursor.execute(query, (player_id,))
        stat_events = cursor.fetchall()
        
        # Also get aggregated stats grouped by description
        agg_query = """
        SELECT se.description, COUNT(*) AS count
        FROM StatEvent se
        WHERE se.performed_by = %s
        GROUP BY se.description
        ORDER BY count DESC
        """
        
        cursor.execute(agg_query, (player_id,))
        aggregated_stats = cursor.fetchall()
        cursor.close()
        
        stat_events = convert_datetime_for_json(stat_events)
        aggregated_stats = convert_datetime_for_json(aggregated_stats)
        
        result = {
            "player_id": player_id,
            "total_stat_events": len(stat_events),
            "stat_events": stat_events,
            "aggregated_stats": aggregated_stats
        }
        
        return jsonify(result), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@player.route("/games/<int:game_id>", methods=["GET"])
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


@player.route("/leagues/<int:league_id>/teams", methods=["GET"])
def get_league_teams(league_id):
    try:
        cursor = db.get_db().cursor()
        
        # First check if league exists
        cursor.execute("SELECT league_id FROM Leagues WHERE league_id = %s", (league_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "League not found"}), 404
        
        query = """
        SELECT t.team_id, t.name AS team_name, t.wins, t.losses,
               COUNT(DISTINCT tp.player_id) AS total_players
        FROM Teams t
        LEFT JOIN Teams_Players tp ON t.team_id = tp.team_id
        WHERE t.league_played = %s
        GROUP BY t.team_id, t.name, t.wins, t.losses
        ORDER BY t.wins DESC, t.losses ASC, t.name
        """
        
        cursor.execute(query, (league_id,))
        teams = cursor.fetchall()
        cursor.close()
        
        teams = convert_datetime_for_json(teams)
        
        return jsonify(teams), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@player.route("/leagues/<int:league_id>/games", methods=["GET"])
def get_league_games(league_id):
    try:
        cursor = db.get_db().cursor()
        
        # First check if league exists
        cursor.execute("SELECT league_id FROM Leagues WHERE league_id = %s", (league_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "League not found"}), 404
        
        upcoming_only = request.args.get("upcoming_only", "false").lower() == "true"
        
        query = """
        SELECT g.game_id, g.date_played, g.start_time, g.location,
               g.home_score, g.away_score,
               t1.name AS home_team, t1.team_id AS home_team_id,
               t2.name AS away_team, t2.team_id AS away_team_id
        FROM Games g
        JOIN Teams_Games tg1 ON g.game_id = tg1.game_id AND tg1.is_home_team = TRUE
        JOIN Teams t1 ON tg1.team_id = t1.team_id
        JOIN Teams_Games tg2 ON g.game_id = tg2.game_id AND tg2.is_home_team = FALSE
        JOIN Teams t2 ON tg2.team_id = t2.team_id
        WHERE g.league_played = %s
        """
        
        params = [league_id]
        
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


@player.route("/leagues/<int:league_id>/standings", methods=["GET"])
def get_league_standings(league_id):
    try:
        cursor = db.get_db().cursor()
        
        # First check if league exists
        cursor.execute("SELECT league_id FROM Leagues WHERE league_id = %s", (league_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "League not found"}), 404
        
        query = """
        SELECT t.team_id, t.name AS team_name, t.wins, t.losses,
               (t.wins + t.losses) AS games_played,
               CASE 
                   WHEN (t.wins + t.losses) > 0 
                   THEN ROUND((t.wins / (t.wins + t.losses)) * 100, 2)
                   ELSE 0 
               END AS win_percentage
        FROM Teams t
        WHERE t.league_played = %s
        ORDER BY win_percentage DESC, t.wins DESC, t.losses ASC, t.name
        """
        
        cursor.execute(query, (league_id,))
        standings = cursor.fetchall()
        cursor.close()
        
        standings = convert_datetime_for_json(standings)
        
        return jsonify(standings), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@player.route("/teams/<int:team_id>", methods=["GET"])
def get_team(team_id):
    try:
        cursor = db.get_db().cursor()
        
        query = """
        SELECT t.team_id, t.name AS team_name, t.wins, t.losses, t.founded_date,
               l.name AS league_name, l.league_id, s.name AS sport_name
        FROM Teams t
        JOIN Leagues l ON t.league_played = l.league_id
        JOIN Sports s ON l.sport_played = s.sport_id
        WHERE t.team_id = %s
        """
        
        cursor.execute(query, (team_id,))
        team = cursor.fetchone()
        cursor.close()
        
        if not team:
            return jsonify({"error": "Team not found"}), 404
        
        team = convert_datetime_for_json(team)
        
        return jsonify(team), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@player.route("/teams/<int:team_id>/players", methods=["GET"])
def get_team_players(team_id):
    try:
        cursor = db.get_db().cursor()
        
        # First check if team exists
        cursor.execute("SELECT team_id FROM Teams WHERE team_id = %s", (team_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Team not found"}), 404
        
        query = """
        SELECT p.player_id, p.first_name, p.last_name, p.email,
               tp.role
        FROM Teams_Players tp
        JOIN Players p ON tp.player_id = p.player_id
        WHERE tp.team_id = %s
        ORDER BY tp.role, p.last_name, p.first_name
        """
        
        cursor.execute(query, (team_id,))
        players = cursor.fetchall()
        cursor.close()
        
        players = convert_datetime_for_json(players)
        
        return jsonify(players), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@player.route("/teams/<int:team_id>/games", methods=["GET"])
def get_team_games(team_id):
    try:
        cursor = db.get_db().cursor()
        
        # First check if team exists
        cursor.execute("SELECT team_id FROM Teams WHERE team_id = %s", (team_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Team not found"}), 404
        
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


@player.route("/teams/<int:team_id>/stats", methods=["GET"])
def get_team_stats(team_id):
    try:
        cursor = db.get_db().cursor()
        
        # First check if team exists
        cursor.execute("SELECT team_id FROM Teams WHERE team_id = %s", (team_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Team not found"}), 404
        
        query = """
        SELECT t.team_id, t.name AS team_name, t.wins, t.losses,
               COUNT(DISTINCT tp.player_id) AS total_players,
               COUNT(DISTINCT g.game_id) AS games_played,
               COUNT(se.event_id) AS total_stat_events,
               AVG(g.home_score) AS avg_home_score,
               AVG(g.away_score) AS avg_away_score
        FROM Teams t
        JOIN Teams_Players tp ON t.team_id = tp.team_id
        LEFT JOIN Teams_Games tg ON t.team_id = tg.team_id
        LEFT JOIN Games g ON tg.game_id = g.game_id
        LEFT JOIN StatEvent se ON g.game_id = se.scored_during
        WHERE t.team_id = %s
        GROUP BY t.team_id, t.name, t.wins, t.losses
        """
        
        cursor.execute(query, (team_id,))
        stats = cursor.fetchone()
        
        if not stats:
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
            stats["league_name"] = league["league_name"]
        
        stats = convert_datetime_for_json(stats)
        
        return jsonify(stats), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@player.route("/analytics/leagues/<int:league_id>", methods=["GET"])
def get_league_analytics(league_id):
    try:
        cursor = db.get_db().cursor()
        
        # First check if league exists
        cursor.execute("SELECT league_id, name FROM Leagues WHERE league_id = %s", (league_id,))
        league = cursor.fetchone()
        if not league:
            cursor.close()
            return jsonify({"error": "League not found"}), 404
        
        # Get league-wide statistics
        query = """
        SELECT 
            COUNT(DISTINCT t.team_id) AS total_teams,
            COUNT(DISTINCT g.game_id) AS total_games,
            COUNT(DISTINCT tp.player_id) AS total_players,
            AVG(g.home_score) AS avg_home_score,
            AVG(g.away_score) AS avg_away_score,
            COUNT(se.event_id) AS total_stat_events
        FROM Leagues l
        LEFT JOIN Teams t ON l.league_id = t.league_played
        LEFT JOIN Teams_Players tp ON t.team_id = tp.team_id
        LEFT JOIN Games g ON l.league_id = g.league_played
        LEFT JOIN StatEvent se ON g.game_id = se.scored_during
        WHERE l.league_id = %s
        """
        
        cursor.execute(query, (league_id,))
        analytics = cursor.fetchone()
        
        # Get top teams by wins
        top_teams_query = """
        SELECT t.team_id, t.name AS team_name, t.wins, t.losses
        FROM Teams t
        WHERE t.league_played = %s
        ORDER BY t.wins DESC, t.losses ASC
        LIMIT 5
        """
        
        cursor.execute(top_teams_query, (league_id,))
        top_teams = cursor.fetchall()
        
        cursor.close()
        
        analytics = convert_datetime_for_json(analytics)
        top_teams = convert_datetime_for_json(top_teams)
        
        result = {
            "league_id": league_id,
            "league_name": league["name"],
            "statistics": analytics,
            "top_teams": top_teams
        }
        
        return jsonify(result), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@player.route("/analytics/players/<int:player_id>", methods=["GET"])
def get_player_analytics(player_id):
    try:
        cursor = db.get_db().cursor()
        
        # First check if player exists
        cursor.execute("SELECT player_id, first_name, last_name FROM Players WHERE player_id = %s", (player_id,))
        player_info = cursor.fetchone()
        if not player_info:
            cursor.close()
            return jsonify({"error": "Player not found"}), 404
        
        # Get player performance statistics
        query = """
        SELECT 
            COUNT(DISTINCT se.event_id) AS total_stat_events,
            COUNT(DISTINCT se.scored_during) AS games_with_stats,
            COUNT(DISTINCT tp.team_id) AS teams_played_for,
            COUNT(DISTINCT pg.game_id) AS total_games_played
        FROM Players p
        LEFT JOIN StatEvent se ON p.player_id = se.performed_by
        LEFT JOIN Teams_Players tp ON p.player_id = tp.player_id
        LEFT JOIN Players_Games pg ON p.player_id = pg.player_id
        WHERE p.player_id = %s
        """
        
        cursor.execute(query, (player_id,))
        analytics = cursor.fetchone()
        
        # Get stat breakdown by type
        stat_breakdown_query = """
        SELECT se.description, COUNT(*) AS count
        FROM StatEvent se
        WHERE se.performed_by = %s
        GROUP BY se.description
        ORDER BY count DESC
        LIMIT 10
        """
        
        cursor.execute(stat_breakdown_query, (player_id,))
        stat_breakdown = cursor.fetchall()
        
        # Get performance over time (last 10 games)
        performance_query = """
        SELECT g.game_id, g.date_played, COUNT(se.event_id) AS stat_count
        FROM Players_Games pg
        JOIN Games g ON pg.game_id = g.game_id
        LEFT JOIN StatEvent se ON se.performed_by = %s AND se.scored_during = g.game_id
        WHERE pg.player_id = %s
        GROUP BY g.game_id, g.date_played
        ORDER BY g.date_played DESC
        LIMIT 10
        """
        
        cursor.execute(performance_query, (player_id, player_id))
        performance_over_time = cursor.fetchall()
        
        cursor.close()
        
        analytics = convert_datetime_for_json(analytics)
        stat_breakdown = convert_datetime_for_json(stat_breakdown)
        performance_over_time = convert_datetime_for_json(performance_over_time)
        
        result = {
            "player_id": player_id,
            "player_name": f"{player_info['first_name']} {player_info['last_name']}",
            "statistics": analytics,
            "stat_breakdown": stat_breakdown,
            "performance_over_time": performance_over_time
        }
        
        return jsonify(result), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500

