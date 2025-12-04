USE im_league_tracker;

-- ============================================================
-- SAMPLE DATA INSERTION (with 2 or more value rows each)
-- ============================================================

-- Insert Sports
INSERT INTO Sports (name) VALUES
('Basketball'),
('Soccer'),
('Volleyball');

/* -- Insert Leagues
INSERT INTO Leagues (name, sport_played, league_start, league_end, semester, year) VALUES
('Fall Basketball League', 1, '2025-09-01', '2025-12-15',
 'Fall', 2025),
('Spring Soccer League', 2, '2026-01-15', '2026-05-15',
 'Spring', 2026),
('Fall Volleyball League', 3, '2025-09-01', '2025-12-15',
 'Fall', 2025); */

-- Insert Rules
INSERT INTO Rules (sports_id, team_size, league_size, season_length, game_length, description) VALUES
(1, 5, 12, 10, 40, 'Basketball: 5v5, 10 week
season, 40 min games'),
(2, 11, 10, 12, 90, 'Soccer: 11v11, 12 week
season, 90 min games'),
(3, 6, 8, 8, 60, 'Volleyball: 6v6, 8 week
season, best of 5 sets');

-- Insert Teams
INSERT INTO Teams (name, league_played, wins, losses) VALUES
('Duncan''s Dunkers', 1, 8, 2),
('Springfield Warriors', 1, 6, 4),
('Riverside Panthers', 1, 5, 5),
('Hoop Dreams', 1, 3, 7),
('Oakdale United', 2, 10, 2),
('Metro City FC', 2, 7, 5);

-- Insert Players
INSERT INTO Players (first_name, last_name, email) VALUES
('Miles', 'Duncan', 'duncan.m@northeastern.edu'),
('Joey', 'Smith', 'smith.jo@northeastern.edu'),
('John', 'Cena', 'cena.jo@northeastern.edu'),
('Brad', 'Pitt', 'pitt.br@northeastern.edu'),
('LeBum', 'James', 'james.le@northeastern.edu'),
('Kevin', 'De Burger', 'deburger.ke@northeastern.edu'),
('Ben', 'Dover', 'dover.be@northeastern.edu'),
('Roberto', 'Calories', 'calories.ro@northeastern.edu'),
('Lionel', 'Pepsi', 'pepsi.li@northeastern.edu');

-- Insert Stat_Keepers
INSERT INTO Stat_Keepers (first_name, last_name, email, total_games_tracked) VALUES
('Jim', 'Datten', 'datten.ji@northeastern.edu', 47),
('Sarah', 'Lee', 'lee.sa@northeastern.edu', 32),
('Mike', 'Hawk', 'hawk.mi@northeastern.edu', 28);

-- Insert Games
INSERT INTO Games (league_played, date_played, start_time, location, home_score, away_score) VALUES
(1, '2025-11-12', '18:00:00', 'Court A', 78, 72),
(1, '2025-11-15', '19:00:00', 'Court B', 65, 68),
(1, '2025-11-20', '18:30:00', 'Court A', 82, 75),
(2, '2025-11-13', '17:00:00', 'Field 1', 3, 2),
(2, '2025-11-18', '16:00:00', 'Field 2', 1, 1);

-- Insert Teams_Players (player roster)
INSERT INTO Teams_Players (player_id, team_id, role) VALUES
(1, 1, 'captain'),
(2, 1, 'player'),
(3, 2, 'player'),
(4, 2, 'player'),
(5, 3, 'player'),
(6, 3, 'player'),
(7, 2, 'player'),
(8, 2, 'player'),
(9, 3, 'player');

-- Insert Teams_Games (which teams played in which games)
INSERT INTO Teams_Games (team_id, game_id, is_home_team) VALUES
(2, 1, TRUE),
(3, 1, FALSE),
(1, 2, TRUE),
(4, 2, FALSE),
(2, 3, TRUE),
(3, 3, FALSE),
(5, 4, TRUE),
(6, 4, FALSE);

-- Insert Players_Games (game lineups)
INSERT INTO Players_Games (player_id, game_id, is_starter, position) VALUES
(3, 1, TRUE, 'Guard'),
(4, 1, TRUE, 'Forward'),
(7, 1, TRUE, 'Center'),
(8, 1, FALSE, 'Guard'),
(5, 1, TRUE, 'Guard'),
(6, 1, TRUE, 'Forward'),
(9, 1, FALSE, 'Forward');

-- Insert Games_Keepers (stat keeper assignments)
INSERT INTO Games_Keepers (keeper_id, game_id, assignment_date) VALUES
(1, 1, '2025-11-10'),
(1, 2, '2025-11-13'),
(2, 3, '2025-11-18'),
(1, 4, '2025-11-11'),
(3, 5, '2025-11-16');

-- Insert StatEvents
INSERT INTO StatEvent (performed_by, scored_during, description, time_entered) VALUES
(3, 1, '24 points scored', '2025-11-12 18:15:00'),
(5, 1, '22 points scored', '2025-11-12 18:20:00'),
(4, 1, '18 points scored', '2025-11-12 18:25:00'),
(3, 1, '12 rebounds', '2025-11-12 18:30:00'),
(8, 1, '10 rebounds', '2025-11-12 18:35:00'),
(4, 1, '5 assists', '2025-11-12 18:40:00'),
(3, 1, '3 steals', '2025-11-12 18:45:00');

-- Insert Reminders
INSERT INTO Reminders (message, time_sent, status, team_id, game_id) VALUES
('Don''t forget to log your stats for tonight''s game!', '2025-11-12 15:00:00',
 'sent', 2, 1),
('Game tomorrow at 7 PM - be there 15 mins early or Jim Datten will be pissed >:(', '2025-11-14 09:00:00',
 'sent', 1, 2),
('Stats from last game need review ASAP', '2025-11-13 10:00:00',
 'pending', 2, 1);

-- Insert Player_Awards
INSERT INTO Player_Awards (recipient, award_type, year) VALUES
(3, 'MVP', 2025),
(5, 'Top Scorer', 2025),
(4, 'Most Assists', 2025);

-- Insert Champions
INSERT INTO Champions (winner, league_id, year) VALUES
(1, 1, 2024),
(5, 2, 2024);
