from flask import Blueprint, jsonify, request
from backend.db_connection import db
from mysql.connector import Error
import pymysql.err
from datetime import datetime, timedelta, date, time

system_admin = Blueprint("system_admin", __name__)


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


@system_admin.route("/sports", methods=["GET"])
def get_all_sports():
    try:
        cursor = db.get_db().cursor()
        
        query = """
        SELECT sport_id, name, description
        FROM Sports
        ORDER BY name
        """
        
        cursor.execute(query)
        sports = cursor.fetchall()
        cursor.close()
        
        sports = convert_datetime_for_json(sports)
        
        return jsonify(sports), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/sports/<int:sport_id>", methods=["GET"])
def get_sport(sport_id):
    try:
        cursor = db.get_db().cursor()
        
        query = """
        SELECT sport_id, name, description
        FROM Sports
        WHERE sport_id = %s
        """
        
        cursor.execute(query, (sport_id,))
        sport = cursor.fetchone()
        cursor.close()
        
        if not sport:
            return jsonify({"error": "Sport not found"}), 404
        
        sport = convert_datetime_for_json(sport)
        
        return jsonify(sport), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/sports", methods=["POST"])
def create_sport():
    try:
        data = request.get_json()
        
        if "name" not in data:
            return jsonify({"error": "Missing required field: name"}), 400
        
        cursor = db.get_db().cursor()
        
        insert_query = """
        INSERT INTO Sports (name, description)
        VALUES (%s, %s)
        """
        
        cursor.execute(insert_query, (
            data["name"],
            data.get("description")
        ))
        
        db.get_db().commit()
        sport_id = cursor.lastrowid
        cursor.close()
        
        return jsonify({
            "message": "Sport created successfully",
            "sport_id": sport_id
        }), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/sports/<int:sport_id>", methods=["PUT"])
def update_sport(sport_id):
    try:
        data = request.get_json()
        
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT sport_id FROM Sports WHERE sport_id = %s", (sport_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Sport not found"}), 404
        
        update_fields = []
        params = []
        
        if "name" in data:
            update_fields.append("name = %s")
            params.append(data["name"])
        
        if "description" in data:
            update_fields.append("description = %s")
            params.append(data["description"])
        
        if not update_fields:
            cursor.close()
            return jsonify({"error": "No fields to update"}), 400
        
        params.append(sport_id)
        
        update_query = f"""
        UPDATE Sports
        SET {', '.join(update_fields)}
        WHERE sport_id = %s
        """
        
        cursor.execute(update_query, params)
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Sport updated successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/sports/<int:sport_id>", methods=["DELETE"])
def delete_sport(sport_id):
    try:
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT sport_id FROM Sports WHERE sport_id = %s", (sport_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Sport not found"}), 404
        
        cursor.execute("DELETE FROM Sports WHERE sport_id = %s", (sport_id,))
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Sport deleted successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/sports/<int:sport_id>/rules", methods=["GET"])
def get_sport_rules(sport_id):
    try:
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT sport_id FROM Sports WHERE sport_id = %s", (sport_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Sport not found"}), 404
        
        query = """
        SELECT rules_id, sports_id, team_size, league_size, season_length, game_length, description
        FROM Rules
        WHERE sports_id = %s
        """
        
        cursor.execute(query, (sport_id,))
        rules = cursor.fetchall()
        cursor.close()
        
        rules = convert_datetime_for_json(rules)
        
        return jsonify(rules), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/sports/<int:sport_id>/rules", methods=["POST"])
def create_sport_rules(sport_id):
    try:
        data = request.get_json()
        
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT sport_id FROM Sports WHERE sport_id = %s", (sport_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Sport not found"}), 404
        
        insert_query = """
        INSERT INTO Rules (sports_id, team_size, league_size, season_length, game_length, description)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(insert_query, (
            sport_id,
            data.get("team_size"),
            data.get("league_size"),
            data.get("season_length"),
            data.get("game_length"),
            data.get("description")
        ))
        
        db.get_db().commit()
        rules_id = cursor.lastrowid
        cursor.close()
        
        return jsonify({
            "message": "Rules created successfully",
            "rules_id": rules_id
        }), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/sports/<int:sport_id>/rules", methods=["PUT"])
def update_sport_rules(sport_id):
    try:
        data = request.get_json()
        
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT rules_id FROM Rules WHERE sports_id = %s LIMIT 1", (sport_id,))
        rule = cursor.fetchone()
        if not rule:
            cursor.close()
            return jsonify({"error": "Rules not found for this sport"}), 404
        
        rules_id = rule["rules_id"]
        
        update_fields = []
        params = []
        
        if "team_size" in data:
            update_fields.append("team_size = %s")
            params.append(data["team_size"])
        
        if "league_size" in data:
            update_fields.append("league_size = %s")
            params.append(data["league_size"])
        
        if "season_length" in data:
            update_fields.append("season_length = %s")
            params.append(data["season_length"])
        
        if "game_length" in data:
            update_fields.append("game_length = %s")
            params.append(data["game_length"])
        
        if "description" in data:
            update_fields.append("description = %s")
            params.append(data["description"])
        
        if not update_fields:
            cursor.close()
            return jsonify({"error": "No fields to update"}), 400
        
        params.append(rules_id)
        
        update_query = f"""
        UPDATE Rules
        SET {', '.join(update_fields)}
        WHERE rules_id = %s
        """
        
        cursor.execute(update_query, params)
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Rules updated successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/leagues", methods=["GET"])
def get_all_leagues():
    try:
        cursor = db.get_db().cursor()
        
        sport_filter = request.args.get("sport_id")
        semester_filter = request.args.get("semester")
        min_year_filter = request.args.get("min_year")
        max_year_filter = request.args.get("max_year")
        
        query = """
        SELECT l.league_id, l.name, l.sport_played, l.max_teams,
               l.league_start, l.league_end, l.semester, l.year,
               s.name AS sport_name
        FROM Leagues l
        JOIN Sports s ON l.sport_played = s.sport_id
        WHERE 1=1
        """
        
        params = []
        
        if sport_filter:
            query += " AND l.sport_played = %s"
            params.append(sport_filter)
        
        if semester_filter:
            query += " AND l.semester = %s"
            params.append(semester_filter)
        
        if min_year_filter:
            query += " AND l.year >= %s"
            params.append(min_year_filter)
        
        if max_year_filter:
            query += " AND l.year <= %s"
            params.append(max_year_filter)
        
        query += " ORDER BY l.year ASC, l.semester, l.name"
        
        cursor.execute(query, params)
        leagues = cursor.fetchall()
        cursor.close()
        
        leagues = convert_datetime_for_json(leagues)
        
        return jsonify(leagues), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/leagues/<int:league_id>", methods=["GET"])
def get_league(league_id):
    try:
        cursor = db.get_db().cursor()
        
        query = """
        SELECT l.league_id, l.name, l.sport_played, l.max_teams,
               l.league_start, l.league_end, l.semester, l.year,
               s.name AS sport_name
        FROM Leagues l
        JOIN Sports s ON l.sport_played = s.sport_id
        WHERE l.league_id = %s
        """
        
        cursor.execute(query, (league_id,))
        league = cursor.fetchone()
        cursor.close()
        
        if not league:
            return jsonify({"error": "League not found"}), 404
        
        league = convert_datetime_for_json(league)
        
        return jsonify(league), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/leagues", methods=["POST"])
def create_league():
    try:
        data = request.get_json()
        
        if "name" not in data or "sport_played" not in data:
            return jsonify({"error": "Missing required fields: name, sport_played"}), 400
        
        cursor = db.get_db().cursor()
        
        # Check if sport exists
        cursor.execute("SELECT sport_id FROM Sports WHERE sport_id = %s", (data["sport_played"],))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Sport not found"}), 404
        
        insert_query = """
        INSERT INTO Leagues (name, sport_played, max_teams, league_start, league_end, semester, year)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(insert_query, (
            data["name"],
            data["sport_played"],
            data.get("max_teams"),
            data.get("league_start"),
            data.get("league_end"),
            data.get("semester"),
            data.get("year")
        ))
        
        db.get_db().commit()
        league_id = cursor.lastrowid
        cursor.close()
        
        return jsonify({
            "message": "League created successfully",
            "league_id": league_id
        }), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/leagues/<int:league_id>", methods=["PUT"])
def update_league(league_id):
    try:
        data = request.get_json()
        
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT league_id FROM Leagues WHERE league_id = %s", (league_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "League not found"}), 404
        
        update_fields = []
        params = []
        
        if "name" in data:
            update_fields.append("name = %s")
            params.append(data["name"])
        
        if "sport_played" in data:
            update_fields.append("sport_played = %s")
            params.append(data["sport_played"])
        
        if "max_teams" in data:
            update_fields.append("max_teams = %s")
            params.append(data["max_teams"])
        
        if "league_start" in data:
            update_fields.append("league_start = %s")
            params.append(data["league_start"])
        
        if "league_end" in data:
            update_fields.append("league_end = %s")
            params.append(data["league_end"])
        
        if "semester" in data:
            update_fields.append("semester = %s")
            params.append(data["semester"])
        
        if "year" in data:
            update_fields.append("year = %s")
            params.append(data["year"])
        
        if not update_fields:
            cursor.close()
            return jsonify({"error": "No fields to update"}), 400
        
        params.append(league_id)
        
        update_query = f"""
        UPDATE Leagues
        SET {', '.join(update_fields)}
        WHERE league_id = %s
        """
        
        cursor.execute(update_query, params)
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "League updated successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/leagues/<int:league_id>", methods=["DELETE"])
def delete_league(league_id):
    try:
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT league_id FROM Leagues WHERE league_id = %s", (league_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "League not found"}), 404
        
        cursor.execute("DELETE FROM Leagues WHERE league_id = %s", (league_id,))
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "League deleted successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/leagues/<int:league_id>/teams", methods=["GET"])
def get_league_teams(league_id):
    try:
        cursor = db.get_db().cursor()
        
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
        ORDER BY t.name
        """
        
        cursor.execute(query, (league_id,))
        teams = cursor.fetchall()
        cursor.close()
        
        teams = convert_datetime_for_json(teams)
        
        return jsonify(teams), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/leagues/<int:league_id>/teams", methods=["POST"])
def add_team_to_league(league_id):
    try:
        data = request.get_json()
        
        if "team_id" not in data:
            return jsonify({"error": "Missing required field: team_id"}), 400
        
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT league_id FROM Leagues WHERE league_id = %s", (league_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "League not found"}), 404
        
        cursor.execute("SELECT team_id FROM Teams WHERE team_id = %s", (data["team_id"],))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Team not found"}), 404
        
        update_query = """
        UPDATE Teams
        SET league_played = %s
        WHERE team_id = %s
        """
        
        cursor.execute(update_query, (league_id, data["team_id"]))
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Team added to league successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/leagues/<int:league_id>/games", methods=["GET"])
def get_league_games(league_id):
    try:
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT league_id FROM Leagues WHERE league_id = %s", (league_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "League not found"}), 404
        
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
        ORDER BY g.date_played DESC, g.start_time DESC
        """
        
        cursor.execute(query, (league_id,))
        games = cursor.fetchall()
        cursor.close()
        
        games = convert_datetime_for_json(games)
        
        return jsonify(games), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/leagues/<int:league_id>/games", methods=["POST"])
def create_league_game(league_id):
    try:
        data = request.get_json()
        
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT league_id FROM Leagues WHERE league_id = %s", (league_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "League not found"}), 404
        
        if "home_team_id" not in data or "away_team_id" not in data:
            cursor.close()
            return jsonify({"error": "Missing required fields: home_team_id, away_team_id"}), 400
        
        # Insert game
        insert_query = """
        INSERT INTO Games (league_played, date_played, start_time, location, home_score, away_score)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(insert_query, (
            league_id,
            data.get("date_played"),
            data.get("start_time"),
            data.get("location"),
            data.get("home_score"),
            data.get("away_score")
        ))
        
        game_id = cursor.lastrowid
        
        # Add teams to game
        cursor.execute("""
            INSERT INTO Teams_Games (team_id, game_id, is_home_team)
            VALUES (%s, %s, TRUE)
        """, (data["home_team_id"], game_id))
        
        cursor.execute("""
            INSERT INTO Teams_Games (team_id, game_id, is_home_team)
            VALUES (%s, %s, FALSE)
        """, (data["away_team_id"], game_id))
        
        db.get_db().commit()
        cursor.close()
        
        return jsonify({
            "message": "Game created successfully",
            "game_id": game_id
        }), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/leagues/<int:league_id>/champions", methods=["GET"])
def get_league_champions(league_id):
    try:
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT league_id FROM Leagues WHERE league_id = %s", (league_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "League not found"}), 404
        
        query = """
        SELECT c.champion_id, c.winner, c.league_id, c.year,
               t.name AS winner_team_name
        FROM Champions c
        JOIN Teams t ON c.winner = t.team_id
        WHERE c.league_id = %s
        ORDER BY c.year DESC
        """
        
        cursor.execute(query, (league_id,))
        champions = cursor.fetchall()
        cursor.close()
        
        champions = convert_datetime_for_json(champions)
        
        return jsonify(champions), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/leagues/<int:league_id>/champions", methods=["POST"])
def create_league_champion(league_id):
    try:
        data = request.get_json()
        
        if "winner" not in data or "year" not in data:
            return jsonify({"error": "Missing required fields: winner, year"}), 400
        
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT league_id FROM Leagues WHERE league_id = %s", (league_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "League not found"}), 404
        
        cursor.execute("SELECT team_id FROM Teams WHERE team_id = %s", (data["winner"],))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Team not found"}), 404
        
        insert_query = """
        INSERT INTO Champions (winner, league_id, year)
        VALUES (%s, %s, %s)
        """
        
        cursor.execute(insert_query, (
            data["winner"],
            league_id,
            data["year"]
        ))
        
        db.get_db().commit()
        champion_id = cursor.lastrowid
        cursor.close()
        
        return jsonify({
            "message": "Champion recorded successfully",
            "champion_id": champion_id
        }), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/teams", methods=["GET"])
def get_all_teams():
    try:
        cursor = db.get_db().cursor()
        
        league_filter = request.args.get("league_id")
        name_search = request.args.get("name_search")
        
        query = """
        SELECT t.team_id, t.name, t.wins, t.losses, t.founded_date,
               t.league_played, l.name AS league_name, s.name AS sport_name
        FROM Teams t
        LEFT JOIN Leagues l ON t.league_played = l.league_id
        LEFT JOIN Sports s ON l.sport_played = s.sport_id
        WHERE 1=1
        """
        
        params = []
        
        if league_filter:
            query += " AND t.league_played = %s"
            params.append(league_filter)
        
        if name_search:
            query += " AND LOWER(t.name) LIKE LOWER(%s)"
            params.append(f"%{name_search}%")
        
        query += " ORDER BY t.name"
        
        cursor.execute(query, params)
        teams = cursor.fetchall()
        cursor.close()
        
        teams = convert_datetime_for_json(teams)
        
        return jsonify(teams), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/teams/<int:team_id>", methods=["GET"])
def get_team(team_id):
    try:
        cursor = db.get_db().cursor()
        
        query = """
        SELECT t.team_id, t.name, t.wins, t.losses, t.founded_date,
               t.league_played, l.name AS league_name, s.name AS sport_name
        FROM Teams t
        LEFT JOIN Leagues l ON t.league_played = l.league_id
        LEFT JOIN Sports s ON l.sport_played = s.sport_id
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


@system_admin.route("/teams", methods=["POST"])
def create_team():
    try:
        data = request.get_json()
        
        if "name" not in data or "league_played" not in data:
            return jsonify({"error": "Missing required fields: name, league_played"}), 400
        
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT league_id FROM Leagues WHERE league_id = %s", (data["league_played"],))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "League not found"}), 404
        
        insert_query = """
        INSERT INTO Teams (name, league_played, wins, losses, founded_date)
        VALUES (%s, %s, %s, %s, %s)
        """
        
        cursor.execute(insert_query, (
            data["name"],
            data["league_played"],
            data.get("wins", 0),
            data.get("losses", 0),
            data.get("founded_date")
        ))
        
        db.get_db().commit()
        team_id = cursor.lastrowid
        cursor.close()
        
        return jsonify({
            "message": "Team created successfully",
            "team_id": team_id
        }), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/teams/<int:team_id>", methods=["PUT"])
def update_team(team_id):
    try:
        data = request.get_json()
        
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT team_id FROM Teams WHERE team_id = %s", (team_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Team not found"}), 404
        
        update_fields = []
        params = []
        
        if "name" in data:
            update_fields.append("name = %s")
            params.append(data["name"])
        
        if "league_played" in data:
            update_fields.append("league_played = %s")
            params.append(data["league_played"])
        
        if "wins" in data:
            update_fields.append("wins = %s")
            params.append(data["wins"])
        
        if "losses" in data:
            update_fields.append("losses = %s")
            params.append(data["losses"])
        
        if "founded_date" in data:
            update_fields.append("founded_date = %s")
            params.append(data["founded_date"])
        
        if not update_fields:
            cursor.close()
            return jsonify({"error": "No fields to update"}), 400
        
        params.append(team_id)
        
        update_query = f"""
        UPDATE Teams
        SET {', '.join(update_fields)}
        WHERE team_id = %s
        """
        
        cursor.execute(update_query, params)
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Team updated successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/teams/<int:team_id>", methods=["DELETE"])
def delete_team(team_id):
    try:
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT team_id FROM Teams WHERE team_id = %s", (team_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Team not found"}), 404
        
        cursor.execute("DELETE FROM Teams WHERE team_id = %s", (team_id,))
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Team deleted successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/teams/<int:team_id>/players", methods=["GET"])
def get_team_players(team_id):
    try:
        cursor = db.get_db().cursor()
        
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


@system_admin.route("/teams/<int:team_id>/players", methods=["POST"])
def add_player_to_team(team_id):
    try:
        data = request.get_json()
        
        if "player_id" not in data:
            return jsonify({"error": "Missing required field: player_id"}), 400
        
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT team_id FROM Teams WHERE team_id = %s", (team_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Team not found"}), 404
        
        cursor.execute("SELECT player_id FROM Players WHERE player_id = %s", (data["player_id"],))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Player not found"}), 404
        
        insert_query = """
        INSERT INTO Teams_Players (player_id, team_id, role)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE role = VALUES(role)
        """
        
        cursor.execute(insert_query, (
            data["player_id"],
            team_id,
            data.get("role", "player")
        ))
        
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Player added to team successfully"}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/teams/<int:team_id>/players", methods=["PUT"])
def update_player_role(team_id):
    try:
        data = request.get_json()
        
        if "player_id" not in data or "role" not in data:
            return jsonify({"error": "Missing required fields: player_id, role"}), 400
        
        cursor = db.get_db().cursor()
        
        cursor.execute("""
            SELECT * FROM Teams_Players 
            WHERE team_id = %s AND player_id = %s
        """, (team_id, data["player_id"]))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Player not found on this team"}), 404
        
        update_query = """
        UPDATE Teams_Players
        SET role = %s
        WHERE team_id = %s AND player_id = %s
        """
        
        cursor.execute(update_query, (data["role"], team_id, data["player_id"]))
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Player role updated successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/teams/<int:team_id>/players", methods=["DELETE"])
def remove_player_from_team(team_id):
    try:
        data = request.get_json()
        
        if "player_id" not in data:
            return jsonify({"error": "Missing required field: player_id"}), 400
        
        cursor = db.get_db().cursor()
        
        cursor.execute("""
            SELECT * FROM Teams_Players 
            WHERE team_id = %s AND player_id = %s
        """, (team_id, data["player_id"]))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Player not found on this team"}), 404
        
        cursor.execute("""
            DELETE FROM Teams_Players 
            WHERE team_id = %s AND player_id = %s
        """, (team_id, data["player_id"]))
        
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Player removed from team successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/teams/<int:team_id>/games", methods=["GET"])
def get_team_games(team_id):
    try:
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT team_id FROM Teams WHERE team_id = %s", (team_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Team not found"}), 404
        
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
        ORDER BY g.date_played DESC, g.start_time DESC
        """
        
        cursor.execute(query, (team_id, team_id))
        games = cursor.fetchall()
        cursor.close()
        
        games = convert_datetime_for_json(games)
        
        return jsonify(games), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/teams/<int:team_id>/stats", methods=["GET"])
def get_team_stats(team_id):
    try:
        cursor = db.get_db().cursor()
        
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


@system_admin.route("/teams/<int:team_id>/awards", methods=["GET"])
def get_team_awards(team_id):
    try:
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT team_id FROM Teams WHERE team_id = %s", (team_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Team not found"}), 404
        
        # Get awards for players on this team
        query = """
        SELECT pa.award_id, pa.award_type, pa.year, pa.description,
               p.player_id, p.first_name, p.last_name
        FROM Player_Awards pa
        JOIN Players p ON pa.recipient = p.player_id
        JOIN Teams_Players tp ON p.player_id = tp.player_id
        WHERE tp.team_id = %s
        ORDER BY pa.year DESC, pa.award_type
        """
        
        cursor.execute(query, (team_id,))
        awards = cursor.fetchall()
        cursor.close()
        
        awards = convert_datetime_for_json(awards)
        
        return jsonify(awards), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/teams/<int:team_id>/awards", methods=["DELETE"])
def delete_team_award(team_id):
    try:
        data = request.get_json()
        
        if "award_id" not in data:
            return jsonify({"error": "Missing required field: award_id"}), 400
        
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT award_id FROM Player_Awards WHERE award_id = %s", (data["award_id"],))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Award not found"}), 404
        
        cursor.execute("DELETE FROM Player_Awards WHERE award_id = %s", (data["award_id"],))
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Award deleted successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/players", methods=["GET"])
def get_all_players():
    try:
        cursor = db.get_db().cursor()
        
        # Get search parameter from query string
        search = request.args.get("search", "").strip()
        
        query = """
        SELECT player_id, phone_number, first_name, last_name, email
        FROM Players
        """
        
        params = []
        
        # Add WHERE clause if search parameter is provided
        if search:
            query += """
            WHERE LOWER(first_name) LIKE %s 
               OR LOWER(last_name) LIKE %s 
               OR LOWER(email) LIKE %s
            """
            search_pattern = f"%{search.lower()}%"
            params = [search_pattern, search_pattern, search_pattern]
        
        query += " ORDER BY last_name, first_name"
        
        cursor.execute(query, params if params else None)
        players = cursor.fetchall()
        cursor.close()
        
        players = convert_datetime_for_json(players)
        
        return jsonify(players), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/players/<int:player_id>", methods=["GET"])
def get_player(player_id):
    try:
        cursor = db.get_db().cursor()
        
        query = """
        SELECT player_id, phone_number, first_name, last_name, email
        FROM Players
        WHERE player_id = %s
        """
        
        cursor.execute(query, (player_id,))
        player = cursor.fetchone()
        cursor.close()
        
        if not player:
            return jsonify({"error": "Player not found"}), 404
        
        player = convert_datetime_for_json(player)
        
        return jsonify(player), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/players", methods=["POST"])
def create_player():
    cursor = None
    try:
        data = request.get_json()
        
        if "first_name" not in data or "last_name" not in data or "email" not in data:
            return jsonify({"error": "Missing required fields: first_name, last_name, email"}), 400
        
        # Validate email contains @northeastern.edu
        if "@northeastern.edu" not in data["email"]:
            return jsonify({"error": "Email must be a valid Northeastern email address (@northeastern.edu)"}), 400
        
        cursor = db.get_db().cursor()
        
        insert_query = """
        INSERT INTO Players (first_name, last_name, email, phone_number)
        VALUES (%s, %s, %s, %s)
        """
        
        cursor.execute(insert_query, (
            data["first_name"],
            data["last_name"],
            data["email"],
            data.get("phone_number")
        ))
        
        db.get_db().commit()
        player_id = cursor.lastrowid
        cursor.close()
        
        return jsonify({
            "message": "Player created successfully",
            "player_id": player_id
        }), 201
    except pymysql.err.IntegrityError as e:
        # Check if it's a duplicate email error (error code 1062)
        if cursor:
            cursor.close()
        if e.args[0] == 1062 and "email" in str(e).lower():
            return jsonify({"error": f"A player with email '{data.get('email', '')}' already exists. Please use a different email address."}), 400
        return jsonify({"error": "Database integrity error. Please check your input."}), 400
    except Error as e:
        if cursor:
            cursor.close()
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        if cursor:
            cursor.close()
        return jsonify({"error": "An unexpected error occurred. Please try again."}), 500


@system_admin.route("/players/<int:player_id>", methods=["PUT"])
def update_player(player_id):
    cursor = None
    try:
        data = request.get_json()
        
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT player_id FROM Players WHERE player_id = %s", (player_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Player not found"}), 404
        
        # Validate email contains @northeastern.edu if email is being updated
        if "email" in data and "@northeastern.edu" not in data["email"]:
            cursor.close()
            return jsonify({"error": "Email must be a valid Northeastern email address (@northeastern.edu)"}), 400
        
        update_fields = []
        params = []
        
        if "first_name" in data:
            update_fields.append("first_name = %s")
            params.append(data["first_name"])
        
        if "last_name" in data:
            update_fields.append("last_name = %s")
            params.append(data["last_name"])
        
        if "email" in data:
            update_fields.append("email = %s")
            params.append(data["email"])
        
        if "phone_number" in data:
            update_fields.append("phone_number = %s")
            params.append(data["phone_number"])
        
        if not update_fields:
            cursor.close()
            return jsonify({"error": "No fields to update"}), 400
        
        params.append(player_id)
        
        update_query = f"""
        UPDATE Players
        SET {', '.join(update_fields)}
        WHERE player_id = %s
        """
        
        cursor.execute(update_query, params)
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Player updated successfully"}), 200
    except pymysql.err.IntegrityError as e:
        # Check if it's a duplicate email error (error code 1062)
        if cursor:
            cursor.close()
        if e.args[0] == 1062 and "email" in str(e).lower():
            return jsonify({"error": f"A player with email '{data.get('email', '')}' already exists. Please use a different email address."}), 400
        return jsonify({"error": "Database integrity error. Please check your input."}), 400
    except Error as e:
        if cursor:
            cursor.close()
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        if cursor:
            cursor.close()
        return jsonify({"error": "An unexpected error occurred. Please try again."}), 500


@system_admin.route("/players/<int:player_id>", methods=["DELETE"])
def delete_player(player_id):
    try:
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT player_id FROM Players WHERE player_id = %s", (player_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Player not found"}), 404
        
        cursor.execute("DELETE FROM Players WHERE player_id = %s", (player_id,))
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Player deleted successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/players/<int:player_id>/teams", methods=["GET"])
def get_player_teams(player_id):
    try:
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT player_id FROM Players WHERE player_id = %s", (player_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Player not found"}), 404
        
        query = """
        SELECT t.team_id, t.name AS team_name, t.wins, t.losses,
               tp.role, l.name AS league_name, l.league_id, l.year AS league_year, s.name AS sport_name
        FROM Teams_Players tp
        JOIN Teams t ON tp.team_id = t.team_id
        JOIN Leagues l ON t.league_played = l.league_id
        JOIN Sports s ON l.sport_played = s.sport_id
        WHERE tp.player_id = %s
        ORDER BY l.year ASC, l.name, t.name
        """
        
        cursor.execute(query, (player_id,))
        teams = cursor.fetchall()
        cursor.close()
        
        teams = convert_datetime_for_json(teams)
        
        return jsonify(teams), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/players/<int:player_id>/games", methods=["GET"])
def get_player_games(player_id):
    try:
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT player_id FROM Players WHERE player_id = %s", (player_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Player not found"}), 404
        
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
        ORDER BY g.date_played DESC, g.start_time DESC
        """
        
        cursor.execute(query, (player_id,))
        games = cursor.fetchall()
        cursor.close()
        
        games = convert_datetime_for_json(games)
        
        return jsonify(games), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/players/<int:player_id>/games", methods=["POST"])
def add_player_to_game(player_id):
    try:
        data = request.get_json()
        
        if "game_id" not in data:
            return jsonify({"error": "Missing required field: game_id"}), 400
        
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT player_id FROM Players WHERE player_id = %s", (player_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Player not found"}), 404
        
        cursor.execute("SELECT game_id FROM Games WHERE game_id = %s", (data["game_id"],))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Game not found"}), 404
        
        insert_query = """
        INSERT INTO Players_Games (player_id, game_id, is_starter, position)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE is_starter = VALUES(is_starter), position = VALUES(position)
        """
        
        cursor.execute(insert_query, (
            player_id,
            data["game_id"],
            data.get("is_starter", False),
            data.get("position")
        ))
        
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Player added to game successfully"}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/players/<int:player_id>/games", methods=["PUT"])
def update_player_game_status(player_id):
    try:
        data = request.get_json()
        
        if "game_id" not in data:
            return jsonify({"error": "Missing required field: game_id"}), 400
        
        cursor = db.get_db().cursor()
        
        cursor.execute("""
            SELECT * FROM Players_Games 
            WHERE player_id = %s AND game_id = %s
        """, (player_id, data["game_id"]))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Player not found in this game"}), 404
        
        update_fields = []
        params = []
        
        if "is_starter" in data:
            update_fields.append("is_starter = %s")
            params.append(data["is_starter"])
        
        if "position" in data:
            update_fields.append("position = %s")
            params.append(data["position"])
        
        if not update_fields:
            cursor.close()
            return jsonify({"error": "No fields to update"}), 400
        
        params.extend([player_id, data["game_id"]])
        
        update_query = f"""
        UPDATE Players_Games
        SET {', '.join(update_fields)}
        WHERE player_id = %s AND game_id = %s
        """
        
        cursor.execute(update_query, params)
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Player game status updated successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/players/<int:player_id>/games", methods=["DELETE"])
def remove_player_from_game(player_id):
    try:
        data = request.get_json()
        
        if "game_id" not in data:
            return jsonify({"error": "Missing required field: game_id"}), 400
        
        cursor = db.get_db().cursor()
        
        cursor.execute("""
            SELECT * FROM Players_Games 
            WHERE player_id = %s AND game_id = %s
        """, (player_id, data["game_id"]))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Player not found in this game"}), 404
        
        cursor.execute("""
            DELETE FROM Players_Games 
            WHERE player_id = %s AND game_id = %s
        """, (player_id, data["game_id"]))
        
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Player removed from game successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/players/<int:player_id>/stats", methods=["GET"])
def get_player_stats(player_id):
    try:
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT player_id FROM Players WHERE player_id = %s", (player_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Player not found"}), 404
        
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


@system_admin.route("/players/<int:player_id>/awards", methods=["GET"])
def get_player_awards(player_id):
    try:
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT player_id FROM Players WHERE player_id = %s", (player_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Player not found"}), 404
        
        query = """
        SELECT award_id, award_type, year, description
        FROM Player_Awards
        WHERE recipient = %s
        ORDER BY year DESC, award_type
        """
        
        cursor.execute(query, (player_id,))
        awards = cursor.fetchall()
        cursor.close()
        
        awards = convert_datetime_for_json(awards)
        
        return jsonify(awards), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/players/<int:player_id>/awards", methods=["POST"])
def create_player_award(player_id):
    try:
        data = request.get_json()
        
        if "award_type" not in data or "year" not in data:
            return jsonify({"error": "Missing required fields: award_type, year"}), 400
        
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT player_id FROM Players WHERE player_id = %s", (player_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Player not found"}), 404
        
        insert_query = """
        INSERT INTO Player_Awards (recipient, award_type, year, description)
        VALUES (%s, %s, %s, %s)
        """
        
        cursor.execute(insert_query, (
            player_id,
            data["award_type"],
            data["year"],
            data.get("description")
        ))
        
        db.get_db().commit()
        award_id = cursor.lastrowid
        cursor.close()
        
        return jsonify({
            "message": "Award assigned successfully",
            "award_id": award_id
        }), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/players/<int:player_id>/awards", methods=["DELETE"])
def delete_player_award(player_id):
    try:
        data = request.get_json()
        
        if "award_id" not in data:
            return jsonify({"error": "Missing required field: award_id"}), 400
        
        cursor = db.get_db().cursor()
        
        cursor.execute("""
            SELECT award_id FROM Player_Awards 
            WHERE award_id = %s AND recipient = %s
        """, (data["award_id"], player_id))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Award not found for this player"}), 404
        
        cursor.execute("DELETE FROM Player_Awards WHERE award_id = %s", (data["award_id"],))
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Award deleted successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/player-awards", methods=["GET"])
def get_all_player_awards():
    """Get all player awards with player names - efficient single query"""
    try:
        cursor = db.get_db().cursor()
        
        query = """
        SELECT pa.award_id, pa.award_type, pa.year, pa.description,
               p.player_id, p.first_name, p.last_name, p.email
        FROM Player_Awards pa
        JOIN Players p ON pa.recipient = p.player_id
        ORDER BY pa.year DESC, p.last_name, p.first_name
        """
        
        cursor.execute(query)
        awards = cursor.fetchall()
        cursor.close()
        
        # Add player_name field for convenience
        for award in awards:
            award['player_name'] = f"{award['first_name']} {award['last_name']}"
        
        awards = convert_datetime_for_json(awards)
        
        return jsonify(awards), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/champions", methods=["GET"])
def get_all_champions():
    """Get all champions with team and league info - efficient single query"""
    try:
        cursor = db.get_db().cursor()
        
        query = """
        SELECT c.champion_id, c.winner, c.league_id, c.year,
               t.name AS winner_team_name,
               l.name AS league_name, l.semester, l.year AS league_year,
               s.name AS sport_name, s.sport_id
        FROM Champions c
        JOIN Teams t ON c.winner = t.team_id
        JOIN Leagues l ON c.league_id = l.league_id
        JOIN Sports s ON l.sport_played = s.sport_id
        ORDER BY c.year DESC, l.name, t.name
        """
        
        cursor.execute(query)
        champions = cursor.fetchall()
        cursor.close()
        
        champions = convert_datetime_for_json(champions)
        
        return jsonify(champions), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/leagues/without-champions", methods=["GET"])
def get_leagues_without_champions():
    """Get all leagues that don't have a champion assigned yet"""
    try:
        cursor = db.get_db().cursor()
        
        query = """
        SELECT l.league_id, l.name, l.sport_played, l.max_teams,
               l.league_start, l.league_end, l.semester, l.year,
               s.name AS sport_name
        FROM Leagues l
        JOIN Sports s ON l.sport_played = s.sport_id
        LEFT JOIN Champions c ON l.league_id = c.league_id
        WHERE c.champion_id IS NULL
        ORDER BY l.year DESC, l.semester, l.name
        """
        
        cursor.execute(query)
        leagues = cursor.fetchall()
        cursor.close()
        
        leagues = convert_datetime_for_json(leagues)
        
        return jsonify(leagues), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/games", methods=["GET"])
def get_all_games():
    try:
        cursor = db.get_db().cursor()
        
        league_filter = request.args.get("league_id")
        min_date_filter = request.args.get("min_date")
        max_date_filter = request.args.get("max_date")
        team_filter = request.args.get("team_id")
        
        query = """
        SELECT g.game_id, g.date_played, g.start_time, g.location,
               g.home_score, g.away_score, g.league_played,
               t1.name AS home_team, t1.team_id AS home_team_id,
               t2.name AS away_team, t2.team_id AS away_team_id,
               l.name AS league_name
        FROM Games g
        LEFT JOIN Teams_Games tg1 ON g.game_id = tg1.game_id AND tg1.is_home_team = TRUE
        LEFT JOIN Teams t1 ON tg1.team_id = t1.team_id
        LEFT JOIN Teams_Games tg2 ON g.game_id = tg2.game_id AND tg2.is_home_team = FALSE
        LEFT JOIN Teams t2 ON tg2.team_id = t2.team_id
        JOIN Leagues l ON g.league_played = l.league_id
        WHERE t1.team_id IS NOT NULL AND t2.team_id IS NOT NULL
        """
        
        params = []
        
        if league_filter:
            query += " AND g.league_played = %s"
            params.append(league_filter)
        
        if min_date_filter:
            query += " AND g.date_played >= %s"
            params.append(min_date_filter)
        
        if max_date_filter:
            query += " AND g.date_played <= %s"
            params.append(max_date_filter)
        
        if team_filter:
            query += " AND (tg1.team_id = %s OR tg2.team_id = %s)"
            params.extend([team_filter, team_filter])
        
        query += " ORDER BY g.date_played DESC, g.start_time DESC"
        
        cursor.execute(query, params)
        games = cursor.fetchall()
        cursor.close()
        
        games = convert_datetime_for_json(games)
        
        return jsonify(games), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/games/<int:game_id>", methods=["GET"])
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


@system_admin.route("/games", methods=["POST"])
def create_game():
    try:
        data = request.get_json()
        
        if "league_played" not in data:
            return jsonify({"error": "Missing required field: league_played"}), 400
        
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT league_id FROM Leagues WHERE league_id = %s", (data["league_played"],))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "League not found"}), 404
        
        insert_query = """
        INSERT INTO Games (league_played, date_played, start_time, location, home_score, away_score)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(insert_query, (
            data["league_played"],
            data.get("date_played"),
            data.get("start_time"),
            data.get("location"),
            data.get("home_score"),
            data.get("away_score")
        ))
        
        game_id = cursor.lastrowid
        
        # Only add teams if they are provided (optional)
        if "home_team_id" in data and data["home_team_id"]:
            cursor.execute("""
                INSERT INTO Teams_Games (team_id, game_id, is_home_team)
                VALUES (%s, %s, TRUE)
            """, (data["home_team_id"], game_id))
        
        if "away_team_id" in data and data["away_team_id"]:
            cursor.execute("""
                INSERT INTO Teams_Games (team_id, game_id, is_home_team)
                VALUES (%s, %s, FALSE)
            """, (data["away_team_id"], game_id))
        
        db.get_db().commit()
        cursor.close()
        
        return jsonify({
            "message": "Game created successfully",
            "game_id": game_id
        }), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/games/<int:game_id>", methods=["PUT"])
def update_game(game_id):
    try:
        data = request.get_json()
        
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT game_id FROM Games WHERE game_id = %s", (game_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Game not found"}), 404
        
        update_fields = []
        params = []
        
        if "date_played" in data:
            update_fields.append("date_played = %s")
            params.append(data["date_played"])
        
        if "start_time" in data:
            update_fields.append("start_time = %s")
            params.append(data["start_time"])
        
        if "location" in data:
            update_fields.append("location = %s")
            params.append(data["location"])
        
        if "home_score" in data:
            update_fields.append("home_score = %s")
            params.append(data["home_score"])
        
        if "away_score" in data:
            update_fields.append("away_score = %s")
            params.append(data["away_score"])
        
        if "league_played" in data:
            update_fields.append("league_played = %s")
            params.append(data["league_played"])
        
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
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Game updated successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/games/<int:game_id>", methods=["DELETE"])
def delete_game(game_id):
    try:
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT game_id FROM Games WHERE game_id = %s", (game_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Game not found"}), 404
        
        cursor.execute("DELETE FROM Games WHERE game_id = %s", (game_id,))
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Game deleted successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/games/<int:game_id>/teams", methods=["GET"])
def get_game_teams(game_id):
    try:
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT game_id FROM Games WHERE game_id = %s", (game_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Game not found"}), 404
        
        query = """
        SELECT t.team_id, t.name AS team_name, tg.is_home_team
        FROM Teams_Games tg
        JOIN Teams t ON tg.team_id = t.team_id
        WHERE tg.game_id = %s
        ORDER BY tg.is_home_team DESC
        """
        
        cursor.execute(query, (game_id,))
        teams = cursor.fetchall()
        cursor.close()
        
        teams = convert_datetime_for_json(teams)
        
        return jsonify(teams), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/games/<int:game_id>/teams", methods=["POST"])
def assign_teams_to_game(game_id):
    try:
        data = request.get_json()
        
        if "home_team_id" not in data or "away_team_id" not in data:
            return jsonify({"error": "Missing required fields: home_team_id, away_team_id"}), 400
        
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT game_id FROM Games WHERE game_id = %s", (game_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Game not found"}), 404
        
        cursor.execute("""
            INSERT INTO Teams_Games (team_id, game_id, is_home_team)
            VALUES (%s, %s, TRUE)
            ON DUPLICATE KEY UPDATE is_home_team = TRUE
        """, (data["home_team_id"], game_id))
        
        cursor.execute("""
            INSERT INTO Teams_Games (team_id, game_id, is_home_team)
            VALUES (%s, %s, FALSE)
            ON DUPLICATE KEY UPDATE is_home_team = FALSE
        """, (data["away_team_id"], game_id))
        
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Teams assigned to game successfully"}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/games/<int:game_id>/teams", methods=["PUT"])
def update_game_teams(game_id):
    try:
        data = request.get_json()
        
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT game_id FROM Games WHERE game_id = %s", (game_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Game not found"}), 404
        
        if "home_team_id" in data:
            cursor.execute("""
                UPDATE Teams_Games
                SET team_id = %s
                WHERE game_id = %s AND is_home_team = TRUE
            """, (data["home_team_id"], game_id))
        
        if "away_team_id" in data:
            cursor.execute("""
                UPDATE Teams_Games
                SET team_id = %s
                WHERE game_id = %s AND is_home_team = FALSE
            """, (data["away_team_id"], game_id))
        
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Game teams updated successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/games/<int:game_id>/players", methods=["GET"])
def get_game_players(game_id):
    try:
        cursor = db.get_db().cursor()
        
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


@system_admin.route("/games/<int:game_id>/players", methods=["POST"])
def add_player_to_game_lineup_admin(game_id):
    try:
        data = request.get_json()
        
        if "player_id" not in data:
            return jsonify({"error": "Missing required field: player_id"}), 400
        
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT game_id FROM Games WHERE game_id = %s", (game_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Game not found"}), 404
        
        cursor.execute("SELECT player_id FROM Players WHERE player_id = %s", (data["player_id"],))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Player not found"}), 404
        
        insert_query = """
        INSERT INTO Players_Games (player_id, game_id, is_starter, position)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE is_starter = VALUES(is_starter), position = VALUES(position)
        """
        
        cursor.execute(insert_query, (
            data["player_id"],
            game_id,
            data.get("is_starter", False),
            data.get("position")
        ))
        
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Player added to game lineup successfully"}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/games/<int:game_id>/players", methods=["PUT"])
def update_game_player_status(game_id):
    try:
        data = request.get_json()
        
        if "player_id" not in data:
            return jsonify({"error": "Missing required field: player_id"}), 400
        
        cursor = db.get_db().cursor()
        
        cursor.execute("""
            SELECT * FROM Players_Games 
            WHERE game_id = %s AND player_id = %s
        """, (game_id, data["player_id"]))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Player not found in this game"}), 404
        
        update_fields = []
        params = []
        
        if "is_starter" in data:
            update_fields.append("is_starter = %s")
            params.append(data["is_starter"])
        
        if "position" in data:
            update_fields.append("position = %s")
            params.append(data["position"])
        
        if not update_fields:
            cursor.close()
            return jsonify({"error": "No fields to update"}), 400
        
        params.extend([game_id, data["player_id"]])
        
        update_query = f"""
        UPDATE Players_Games
        SET {', '.join(update_fields)}
        WHERE game_id = %s AND player_id = %s
        """
        
        cursor.execute(update_query, params)
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Player game status updated successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/games/<int:game_id>/players", methods=["DELETE"])
def remove_player_from_game_lineup(game_id):
    try:
        data = request.get_json()
        
        if "player_id" not in data:
            return jsonify({"error": "Missing required field: player_id"}), 400
        
        cursor = db.get_db().cursor()
        
        cursor.execute("""
            SELECT * FROM Players_Games 
            WHERE game_id = %s AND player_id = %s
        """, (game_id, data["player_id"]))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Player not found in this game"}), 404
        
        cursor.execute("""
            DELETE FROM Players_Games 
            WHERE game_id = %s AND player_id = %s
        """, (game_id, data["player_id"]))
        
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Player removed from game successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/games/<int:game_id>/stat-keepers", methods=["GET"])
def get_game_stat_keepers(game_id):
    try:
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT game_id FROM Games WHERE game_id = %s", (game_id,))
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


@system_admin.route("/games/<int:game_id>/stat-keepers", methods=["POST"])
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


@system_admin.route("/games/<int:game_id>/stat-keepers", methods=["DELETE"])
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


@system_admin.route("/stat-keepers", methods=["GET"])
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


@system_admin.route("/stat-keepers/<int:keeper_id>", methods=["GET"])
def get_stat_keeper(keeper_id):
    try:
        cursor = db.get_db().cursor()
        
        query = """
        SELECT keeper_id, first_name, last_name, email, total_games_tracked
        FROM Stat_Keepers
        WHERE keeper_id = %s
        """
        
        cursor.execute(query, (keeper_id,))
        stat_keeper_data = cursor.fetchone()
        cursor.close()
        
        if not stat_keeper_data:
            return jsonify({"error": "Stat keeper not found"}), 404
        
        stat_keeper_data = convert_datetime_for_json(stat_keeper_data)
        
        return jsonify(stat_keeper_data), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/stat-keepers", methods=["POST"])
def create_stat_keeper():
    try:
        data = request.get_json()
        
        if "first_name" not in data or "last_name" not in data or "email" not in data:
            return jsonify({"error": "Missing required fields: first_name, last_name, email"}), 400
        
        cursor = db.get_db().cursor()
        
        insert_query = """
        INSERT INTO Stat_Keepers (first_name, last_name, email, total_games_tracked)
        VALUES (%s, %s, %s, %s)
        """
        
        cursor.execute(insert_query, (
            data["first_name"],
            data["last_name"],
            data["email"],
            data.get("total_games_tracked", 0)
        ))
        
        db.get_db().commit()
        keeper_id = cursor.lastrowid
        cursor.close()
        
        return jsonify({
            "message": "Stat keeper created successfully",
            "keeper_id": keeper_id
        }), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/stat-keepers/<int:keeper_id>", methods=["PUT"])
def update_stat_keeper(keeper_id):
    try:
        data = request.get_json()
        
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT keeper_id FROM Stat_Keepers WHERE keeper_id = %s", (keeper_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Stat keeper not found"}), 404
        
        update_fields = []
        params = []
        
        if "first_name" in data:
            update_fields.append("first_name = %s")
            params.append(data["first_name"])
        
        if "last_name" in data:
            update_fields.append("last_name = %s")
            params.append(data["last_name"])
        
        if "email" in data:
            update_fields.append("email = %s")
            params.append(data["email"])
        
        if "total_games_tracked" in data:
            update_fields.append("total_games_tracked = %s")
            params.append(data["total_games_tracked"])
        
        if not update_fields:
            cursor.close()
            return jsonify({"error": "No fields to update"}), 400
        
        params.append(keeper_id)
        
        update_query = f"""
        UPDATE Stat_Keepers
        SET {', '.join(update_fields)}
        WHERE keeper_id = %s
        """
        
        cursor.execute(update_query, params)
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Stat keeper updated successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/stat-keepers/<int:keeper_id>/games", methods=["GET"])
def get_stat_keeper_games(keeper_id):
    try:
        cursor = db.get_db().cursor()
        
        cursor.execute("SELECT keeper_id FROM Stat_Keepers WHERE keeper_id = %s", (keeper_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Stat keeper not found"}), 404
        
        query = """
        SELECT g.game_id, g.date_played, g.start_time, g.location,
               g.home_score, g.away_score, g.league_played,
               t1.name AS home_team, t1.team_id AS home_team_id,
               t2.name AS away_team, t2.team_id AS away_team_id,
               l.name AS league_name, s.name AS sport_name,
               gk.assignment_date
        FROM Games_Keepers gk
        JOIN Games g ON gk.game_id = g.game_id
        JOIN Teams_Games tg1 ON g.game_id = tg1.game_id AND tg1.is_home_team = TRUE
        JOIN Teams t1 ON tg1.team_id = t1.team_id
        JOIN Teams_Games tg2 ON g.game_id = tg2.game_id AND tg2.is_home_team = FALSE
        JOIN Teams t2 ON tg2.team_id = t2.team_id
        JOIN Leagues l ON g.league_played = l.league_id
        JOIN Sports s ON l.sport_played = s.sport_id
        WHERE gk.keeper_id = %s
        ORDER BY g.date_played DESC, g.start_time DESC
        """
        
        cursor.execute(query, (keeper_id,))
        games = cursor.fetchall()
        cursor.close()
        
        games = convert_datetime_for_json(games)
        
        return jsonify(games), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


@system_admin.route("/analytics/dashboard", methods=["GET"])
def get_analytics_dashboard():
    try:
        cursor = db.get_db().cursor()
        
        # Overall statistics
        overall_query = """
        SELECT 
            COUNT(DISTINCT s.sport_id) AS total_sports,
            COUNT(DISTINCT l.league_id) AS total_leagues,
            COUNT(DISTINCT t.team_id) AS total_teams,
            COUNT(DISTINCT p.player_id) AS total_players,
            COUNT(DISTINCT g.game_id) AS total_games,
            COUNT(DISTINCT sk.keeper_id) AS total_stat_keepers,
            COUNT(se.event_id) AS total_stat_events
        FROM Sports s
        LEFT JOIN Leagues l ON s.sport_id = l.sport_played
        LEFT JOIN Teams t ON l.league_id = t.league_played
        LEFT JOIN Teams_Players tp ON t.team_id = tp.team_id
        LEFT JOIN Players p ON tp.player_id = p.player_id
        LEFT JOIN Games g ON l.league_id = g.league_played
        LEFT JOIN StatEvent se ON g.game_id = se.scored_during
        LEFT JOIN Stat_Keepers sk ON 1=1
        """
        
        cursor.execute(overall_query)
        overall_stats = cursor.fetchone()
        
        # Most popular sports
        popular_sports_query = """
        SELECT s.name AS sport_name, COUNT(DISTINCT l.league_id) AS league_count,
               COUNT(DISTINCT t.team_id) AS team_count,
               COUNT(DISTINCT g.game_id) AS game_count
        FROM Sports s
        LEFT JOIN Leagues l ON s.sport_id = l.sport_played
        LEFT JOIN Teams t ON l.league_id = t.league_played
        LEFT JOIN Games g ON l.league_id = g.league_played
        GROUP BY s.sport_id, s.name
        ORDER BY game_count DESC
        """
        
        cursor.execute(popular_sports_query)
        popular_sports = cursor.fetchall()
        
        # Busiest days (by game count)
        busiest_days_query = """
        SELECT DATE(date_played) AS game_date, COUNT(*) AS game_count
        FROM Games
        WHERE date_played IS NOT NULL
        GROUP BY DATE(date_played)
        ORDER BY game_count DESC
        LIMIT 10
        """
        
        cursor.execute(busiest_days_query)
        busiest_days = cursor.fetchall()
        
        cursor.close()
        
        overall_stats = convert_datetime_for_json(overall_stats)
        popular_sports = convert_datetime_for_json(popular_sports)
        busiest_days = convert_datetime_for_json(busiest_days)
        
        result = {
            "overall_statistics": overall_stats,
            "popular_sports": popular_sports,
            "busiest_days": busiest_days
        }
        
        return jsonify(result), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
