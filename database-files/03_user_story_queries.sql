USE im_league_tracker;

-- ====================
-- PERSONA 1: SYSTEM ADMIN (John Smith)
-- ====================

-- 1.1: View and filter all data (game schedule with teams and leagues)
SELECT g.game_id, g.date_played, g.start_time,
       t1.name AS home_team, t2.name AS away_team,
       l.name AS league_name, s.name AS sport_name
FROM Games g
JOIN Teams_Games tg1 ON g.game_id = tg1.game_id AND tg1.is_home_team = TRUE
JOIN Teams t1 ON tg1.team_id = t1.team_id
JOIN Teams_Games tg2 ON g.game_id = tg2.game_id AND tg2.is_home_team = FALSE
JOIN Teams t2 ON tg2.team_id = t2.team_id
JOIN Leagues l ON g.league_played = l.league_id
JOIN Sports s ON l.sport_played = s.sport_id
ORDER BY g.date_played;

-- 1.2: Update all data through the app (update game scores)
UPDATE Games
SET home_score = 78, away_score = 72
WHERE game_id = 1;

-- 1.3: Assign badges and awards to players based on statistics
INSERT INTO Player_Awards (recipient, award_type, year)
VALUES (3, 'MVP', 2025);

-- 1.4: Add new sports leagues as app expands
INSERT INTO Leagues (name, sport_played, league_start, league_end, semester, year)
VALUES ('Winter Hockey League', 1, '2026-01-01', '2026-03-31',
        'Winter', 2026);

-- 1.5: Access data dashboard with usage statistics
SELECT s.name AS sport_name,
       COUNT(DISTINCT l.league_id) AS total_leagues,
       COUNT(DISTINCT g.game_id) AS total_games,
       COUNT(DISTINCT t.team_id) AS total_teams
FROM Sports s
LEFT JOIN Leagues l ON s.sport_id = l.sport_played
LEFT JOIN Games g ON l.league_id = g.league_played
LEFT JOIN Teams t ON l.league_id = t.league_played
GROUP BY s.sport_id, s.name
ORDER BY total_games DESC;

-- 1.6: Set rules for leagues (insert sport rules)
INSERT INTO Rules (sports_id, team_size, league_size, season_length, game_length, description)
VALUES (1, 5, 12, 10, 40, 'Basketball: 5v5,
10 week season, 40 min games');

-- ====================
-- PERSONA 2: PLAYER (Joey Smith)
-- ====================

-- 2.1: Visualize own statistics in different ways
SELECT se.description, se.time_entered, g.date_played,
       t.name AS opponent_team, l.name AS league_name
FROM StatEvent se
JOIN Games g ON se.scored_during = g.game_id
JOIN Leagues l ON g.league_played = l.league_id
JOIN Teams_Games tg ON g.game_id = tg.game_id
JOIN Teams t ON tg.team_id = t.team_id
WHERE se.performed_by = 2
ORDER BY g.date_played DESC;

-- 2.2: View upcoming matches with date, time, and teams
SELECT g.game_id, g.date_played, g.start_time, g.location,
       t1.name AS home_team, t2.name AS away_team
FROM Games g
JOIN Teams_Games tg1 ON g.game_id = tg1.game_id AND tg1.is_home_team = TRUE
JOIN Teams t1 ON tg1.team_id = t1.team_id
JOIN Teams_Games tg2 ON g.game_id = tg2.game_id AND tg2.is_home_team = FALSE
JOIN Teams t2 ON tg2.team_id = t2.team_id
JOIN Teams_Players tp ON (t1.team_id = tp.team_id OR t2.team_id = tp.team_id)
WHERE tp.player_id = 2
  AND g.date_played >= CURRENT_DATE()
ORDER BY g.date_played;

-- 2.3: Access all teams' stats and lineups
SELECT p.first_name, p.last_name, tp.role,
       COUNT(DISTINCT se.event_id) AS total_stat_events,
       COUNT(DISTINCT pg.game_id) AS games_played
FROM Players p
JOIN Teams_Players tp ON p.player_id = tp.player_id
LEFT JOIN StatEvent se ON p.player_id = se.performed_by
LEFT JOIN Players_Games pg ON p.player_id = pg.player_id
WHERE tp.team_id = 1
GROUP BY p.player_id, p.first_name, p.last_name, tp.role
ORDER BY total_stat_events DESC;

-- 2.4: See graphic tracking team performance over time
SELECT g.date_played,
       g.home_score,
       g.away_score,
       t.name AS team_name
FROM Games g
JOIN Teams_Games tg ON g.game_id = tg.game_id
JOIN Teams t ON tg.team_id = t.team_id
WHERE tg.team_id = 1
ORDER BY g.date_played;

-- 2.5: Explore other sports and teams friends are on
SELECT DISTINCT p.first_name, p.last_name,
       t.name AS team_name, s.name AS sport_name, l.name AS league_name
FROM Players p
JOIN Teams_Players tp ON p.player_id = tp.player_id
JOIN Teams t ON tp.team_id = t.team_id
JOIN Leagues l ON t.league_played = l.league_id
JOIN Sports s ON l.sport_played = s.sport_id
WHERE p.player_id IN (3, 4, 5)
ORDER BY p.last_name, s.name;

-- 2.6: See rankings for important stats across the league
SELECT p.first_name, p.last_name, t.name AS team_name,
       COUNT(se.event_id) AS stat_count,
       se.description
FROM Players p
JOIN StatEvent se ON p.player_id = se.performed_by
JOIN Teams_Players tp ON p.player_id = tp.player_id
JOIN Teams t ON tp.team_id = t.team_id
JOIN Games g ON se.scored_during = g.game_id
WHERE se.description LIKE '%points%'
  AND g.league_played = 1
GROUP BY p.player_id, p.first_name, p.last_name, t.name, se.description
ORDER BY stat_count DESC
LIMIT 10;

-- ====================
-- PERSONA 3: TEAM CAPTAIN (Miles Duncan)
-- ====================

-- 3.1: Create and schedule games
INSERT INTO Games (league_played, date_played, start_time, location)
VALUES (1, '2025-11-25', '18:00:00', 'Court A');

-- 3.2: Review and edit team stats after each game
UPDATE StatEvent
SET description = '3 points scored'
WHERE event_id = 1;

-- 3.3: See dashboard tracking team performance and improvement over time
SELECT t.name, t.wins, t.losses,
       COUNT(g.game_id) AS games_played,
       AVG(g.home_score) AS avg_home_score,
       AVG(g.away_score) AS avg_away_score
FROM Teams t
JOIN Teams_Games tg ON t.team_id = tg.team_id
JOIN Games g ON tg.game_id = g.game_id
WHERE t.team_id = 1
GROUP BY t.team_id, t.name, t.wins, t.losses;

-- 3.4: Send reminders to teammates to record stats
INSERT INTO Reminders (message, time_sent, status, team_id, game_id)
VALUES ('Don''t forget to log your stats for tonight''s game!', NOW(), 'sent',
        1, 2);

-- 3.5: Compare team performance to league averages
SELECT t.name AS team_name,
       AVG(g.home_score) AS avg_home_score,
       AVG(g.away_score) AS avg_away_score,
       (SELECT AVG(home_score) FROM Games WHERE league_played = 1) AS league_avg_home_score,
       (SELECT AVG(away_score) FROM Games WHERE league_played = 1) AS league_avg_away_score
FROM Teams t
JOIN Teams_Games tg ON t.team_id = tg.team_id
JOIN Games g ON tg.game_id = g.game_id
WHERE t.team_id = 1
GROUP BY t.team_id, t.name;

-- 3.6: Share visual summaries of team stats
SELECT t.name, t.wins, t.losses,
       COUNT(DISTINCT tp.player_id) AS total_players,
       COUNT(DISTINCT g.game_id) AS games_played,
       COUNT(se.event_id) AS total_stat_events
FROM Teams t
JOIN Teams_Players tp ON t.team_id = tp.team_id
LEFT JOIN Teams_Games tg ON t.team_id = tg.team_id
LEFT JOIN Games g ON tg.game_id = g.game_id
LEFT JOIN StatEvent se ON g.game_id = se.scored_during
WHERE t.team_id = 1
GROUP BY t.team_id, t.name, t.wins, t.losses;

-- ====================
-- PERSONA 4: STAT KEEPER (Jim Datten)
-- ====================

-- 4.1: Quickly log player stats in real-time during a game
INSERT INTO StatEvent (performed_by, scored_during, description, time_entered)
VALUES (3, 1, '2 points scored', NOW());

-- 4.2: Customize which stats are visible for each sport
SELECT DISTINCT se.description, COUNT(*) AS usage_count
FROM StatEvent se
JOIN Games g ON se.scored_during = g.game_id
JOIN Leagues l ON g.league_played = l.league_id
WHERE l.sport_played = 1
GROUP BY se.description
ORDER BY usage_count DESC;

-- 4.3: Edit or delete recently entered stats with undo/correction
DELETE FROM StatEvent
WHERE event_id = 7
  AND time_entered > NOW() - INTERVAL 5 MINUTE;

-- 4.4: Access streamlined mobile interface (get current game details)
SELECT g.game_id, g.date_played, g.start_time, g.location,
       t1.name AS home_team, t2.name AS away_team,
       g.home_score, g.away_score
FROM Games g
JOIN Teams_Games tg1 ON g.game_id = tg1.game_id AND tg1.is_home_team = TRUE
JOIN Teams t1 ON tg1.team_id = t1.team_id
JOIN Teams_Games tg2 ON g.game_id = tg2.game_id AND tg2.is_home_team = FALSE
JOIN Teams t2 ON tg2.team_id = t2.team_id
WHERE g.game_id = 1;

-- 4.5: View live summary of game stats (team totals and individual leaders)
SELECT p.first_name, p.last_name, t.name AS team_name,
       COUNT(se.event_id) AS total_stats
FROM Players p
JOIN StatEvent se ON p.player_id = se.performed_by
JOIN Teams_Players tp ON p.player_id = tp.player_id
JOIN Teams t ON tp.team_id = t.team_id
WHERE se.scored_during = 1
GROUP BY p.player_id, p.first_name, p.last_name, t.name
ORDER BY total_stats DESC
LIMIT 5;

-- 4.6: Mark game as complete and submit final stats
UPDATE Games
SET home_score = 78, away_score = 72
WHERE game_id = 1;

